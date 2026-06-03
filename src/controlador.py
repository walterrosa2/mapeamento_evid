import re
import json
from typing import Callable, Optional
from loguru import logger
from src.leitor_txt import carregar_blocos, carregar_texto_completo
from src.gemini_api import enviar_bloco_para_gemini, gerar_resumo_processo
from src.planilha import inicializar_planilha, adicionar_linhas_excel, escrever_resumo_primeira_aba
from src import persistence
from config import ARQUIVO_PADRAO_TXT

# ---------------------------------------------------------------------------
# Limpeza e Normalização
# ---------------------------------------------------------------------------

def limpar_texto_bruto(valor: str) -> str:
    if not isinstance(valor, str):
        return ""
    valor = re.sub(r"[\r\n\t]+", " ", valor)
    valor = re.sub(r"\s{2,}", " ", valor)
    return valor.strip()


def normalizar_chaves(lista_dados: list) -> list:
    mapa = {
        "trecho": "Trecho",
        "trecho/página": "Trecho",
        "trecho / página": "Trecho",
        "pagina": "Referência",
        "página": "Referência",
        "referencia": "Referência",
        "referência": "Referência",
        "conteudo": "Conteúdo",
        "conteúdo": "Conteúdo",
        "resumo": "Resumo",
        "tipo": "Tipo de Evidência",
        "tipo de evidência": "Tipo de Evidência",
        "tipo de evidencia": "Tipo de Evidência",
    }
    normalizados = []
    for item in lista_dados:
        novo = {}
        for chave, valor in item.items():
            chave_norm = mapa.get(chave.strip().lower(), chave.strip())
            novo[chave_norm] = limpar_texto_bruto(valor)
        normalizados.append(novo)
    return normalizados


# ---------------------------------------------------------------------------
# Parse de tabela Markdown
# ---------------------------------------------------------------------------

def parse_markdown_tabela(texto: str) -> list:
    linhas = [l.strip() for l in texto.splitlines() if l.strip()]
    dados, cabecalho = [], []

    for i, linha in enumerate(linhas):
        if re.match(r"^\|?[\-\:\s\|]+$", linha):
            if i > 0:
                cabecalho = [c.strip(" :") for c in re.split(r"\s*\|\s*", linhas[i - 1]) if c.strip()]
            continue
        if cabecalho and linha.startswith("|"):
            colunas = [c.strip() for c in re.split(r"\s*\|\s*", linha) if c.strip()]
            if len(colunas) < len(cabecalho):
                colunas += [""] * (len(cabecalho) - len(colunas))
            elif len(colunas) > len(cabecalho):
                colunas = colunas[:len(cabecalho)]
            dados.append(dict(zip(cabecalho, colunas)))

    return dados


# ---------------------------------------------------------------------------
# Extração híbrida JSON + Markdown
# ---------------------------------------------------------------------------

def _recuperar_objetos_json(trecho: str) -> list:
    """Extrai objetos {...} completos de um JSON possivelmente truncado.

    Tolera respostas cortadas pelo limite de tokens: percorre o texto e fecha
    cada objeto de nível superior, ignorando chaves dentro de strings.
    """
    objetos = []
    nivel = 0
    inicio = None
    em_string = False
    escape = False
    for i, ch in enumerate(trecho):
        if em_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                em_string = False
            continue
        if ch == '"':
            em_string = True
        elif ch == "{":
            if nivel == 0:
                inicio = i
            nivel += 1
        elif ch == "}":
            if nivel > 0:
                nivel -= 1
                if nivel == 0 and inicio is not None:
                    try:
                        objetos.append(json.loads(trecho[inicio:i + 1]))
                    except json.JSONDecodeError:
                        pass
                    inicio = None
    return objetos


def extrair_campos(texto: str) -> list:
    texto = texto.strip()

    # 1) JSON (formato primário v3.2): remove cercas e isola o array
    json_clean = re.sub(r"```json\s*|\s*```", "", texto).strip()
    ini, fim = json_clean.find("["), json_clean.rfind("]")
    candidato = json_clean[ini:fim + 1] if ini != -1 and fim > ini else json_clean
    try:
        data = json.loads(candidato)
        if isinstance(data, list) and data:
            return normalizar_chaves(data)
    except json.JSONDecodeError:
        # 2) JSON truncado/inválido: recupera objetos completos
        objetos = _recuperar_objetos_json(json_clean)
        if objetos:
            logger.warning(f"JSON inválido/truncado — recuperados {len(objetos)} objeto(s) parciais.")
            return normalizar_chaves(objetos)

    # 3) Fallback: tabela Markdown (compatibilidade)
    dados_md = parse_markdown_tabela(texto)
    if dados_md:
        return normalizar_chaves(dados_md)

    return []


def limpar_linha_vazia(evidencia: dict) -> dict:
    return {k: v for k, v in evidencia.items() if v not in ("", None, "null")}


# ---------------------------------------------------------------------------
# Pipeline v2 — com run_id, skip_ids e progress_cb
# ---------------------------------------------------------------------------

def processar_blocos_run(
    run_id: str,
    blocos: list,
    arquivo_origem: str = "",
    skip_ids: Optional[set] = None,
    progress_cb: Optional[Callable] = None,
    texto_completo: str = "",
    usar_sac: bool = False,
) -> int:
    """
    Processa blocos para uma run específica (v3.0 com SAC opcional).

    Fase 1 (se usar_sac=True): Gera resumo do processo completo.
    Fase 2: Extrai evidências bloco a bloco com contexto global (se disponível).

    progress_cb(bloco_id, total, evidencias_acumuladas, status_bloco)
      status_bloco: 'ok' | 'vazio' | 'erro' | 'resumindo'
      bloco_id=-1 sinaliza Fase 1 (resumindo)

    Retorna tupla (total_evidencias_extraidas, resumo_processo).
    resumo_processo é "" quando SAC não foi usado ou falhou.
    """
    skip_ids = skip_ids or set()
    total_blocos = len(blocos)
    evidencias_acumuladas = 0
    blocos_processados = 0
    contexto_global = ""

    inicializar_planilha(run_id)

    # Fase 1: SAC — Gerar resumo do processo
    if usar_sac and texto_completo:
        if progress_cb:
            progress_cb(-1, total_blocos, 0, "resumindo")
        contexto_global = gerar_resumo_processo(texto_completo)
        if contexto_global:
            persistence.salvar_resumo_run(run_id, contexto_global)
        else:
            logger.warning("⚠️ SAC desativado — falha ao gerar resumo")

    for i, bloco in enumerate(blocos):
        if i in skip_ids:
            logger.debug(f"Bloco {i} já processado — pulando.")
            if progress_cb:
                progress_cb(i, total_blocos, evidencias_acumuladas, "pulado")
            continue

        logger.info(f"Bloco {i+1}/{total_blocos} enviado para Gemini...")
        resposta = enviar_bloco_para_gemini(bloco, bloco_id=i, contexto_global=contexto_global)

        if not resposta:
            logger.error(f"Sem retorno da Gemini no bloco {i}.")
            persistence.salvar_run_item(run_id, i, persistence.ITEM_ERRO_LLM, 0, "Sem resposta da API")
            blocos_processados += 1
            persistence.atualizar_progresso_run(run_id, total_blocos, blocos_processados, evidencias_acumuladas)
            if progress_cb:
                progress_cb(i, total_blocos, evidencias_acumuladas, "erro")
            continue

        evidencias = extrair_campos(resposta)

        if not evidencias:
            logger.warning(f"Nenhuma evidência extraída do bloco {i}.")
            persistence.salvar_run_item(run_id, i, persistence.ITEM_ERRO_PARSE, 0, "Nenhuma evidência")
            blocos_processados += 1
            persistence.atualizar_progresso_run(run_id, total_blocos, blocos_processados, evidencias_acumuladas)
            if progress_cb:
                progress_cb(i, total_blocos, evidencias_acumuladas, "vazio")
            continue

        limpas = [limpar_linha_vazia(e) for e in evidencias if limpar_linha_vazia(e)]
        linhas_validas = adicionar_linhas_excel(limpas, run_id=run_id, arquivo_origem=arquivo_origem)

        evidencias_acumuladas += linhas_validas
        blocos_processados += 1
        persistence.salvar_run_item(run_id, i, persistence.ITEM_OK, linhas_validas)
        persistence.atualizar_progresso_run(run_id, total_blocos, blocos_processados, evidencias_acumuladas)
        logger.success(f"Bloco {i+1}: {linhas_validas} evidência(s) salva(s).")

        if progress_cb:
            progress_cb(i, total_blocos, evidencias_acumuladas, "ok")

    # Grava o resumo como primeira aba do Excel APÓS todas as evidências
    # (adicionar_linhas_excel reescreve o arquivo e apagaria abas extras).
    if contexto_global:
        escrever_resumo_primeira_aba(run_id, contexto_global)

    return evidencias_acumuladas, contexto_global


# ---------------------------------------------------------------------------
# Retrocompatibilidade — main.py CLI (sem run_id)
# ---------------------------------------------------------------------------

def processar_todos_os_blocos():
    """Pipeline legado para uso via main.py (sem persistência SQLite)."""
    from src.planilha import inicializar_planilha_legado, adicionar_linha_excel_legado

    logger.info("Carregando blocos do arquivo TXT...")
    blocos = carregar_blocos(ARQUIVO_PADRAO_TXT)
    total_blocos = len(blocos)

    inicializar_planilha_legado()

    for i, bloco in enumerate(blocos):
        logger.info(f"Processando bloco {i+1}/{total_blocos}...")
        resposta = enviar_bloco_para_gemini(bloco, bloco_id=i)
        if not resposta:
            logger.error(f"Sem retorno da Gemini no bloco {i}.")
            continue
        evidencias = extrair_campos(resposta)
        if not evidencias:
            logger.warning(f"Nenhuma evidência no bloco {i}.")
            continue
        linhas_validas = 0
        for evidencia in evidencias:
            evidencia_limpa = limpar_linha_vazia(evidencia)
            if evidencia_limpa:
                adicionar_linha_excel_legado(evidencia_limpa)
                linhas_validas += 1
        logger.success(f"{linhas_validas} evidência(s) salva(s).")

    logger.info("Processamento finalizado.")
