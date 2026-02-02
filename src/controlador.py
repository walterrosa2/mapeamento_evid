import re
import json
from loguru import logger
from src.leitor_txt import carregar_blocos
from src.gemini_api import enviar_bloco_para_gemini
from src.planilha import inicializar_planilha, adicionar_linha_excel
from config import ARQUIVO_PADRAO_TXT


# ============================================================
#  FUNÇÕES DE LIMPEZA E NORMALIZAÇÃO
# ============================================================

def limpar_texto_bruto(valor: str) -> str:
    """Remove quebras de linha, múltiplos espaços e caracteres estranhos."""
    if not isinstance(valor, str):
        return ""
    valor = re.sub(r"[\r\n\t]+", " ", valor)
    valor = re.sub(r"\s{2,}", " ", valor)
    return valor.strip()


def normalizar_chaves(lista_dados: list) -> list:
    """Padroniza nomes de colunas para evitar duplicações e inconsistências."""
    mapa_equivalencias = {
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
        "tipo de evidencia": "Tipo de Evidência"
    }

    normalizados = []
    for item in lista_dados:
        novo = {}
        for chave, valor in item.items():
            chave_norm = mapa_equivalencias.get(chave.strip().lower(), chave.strip())
            novo[chave_norm] = limpar_texto_bruto(valor)
        normalizados.append(novo)
    return normalizados


# ============================================================
#  FUNÇÃO DE PARSE ROBUSTA PARA TABELAS MARKDOWN
# ============================================================

def parse_markdown_tabela(texto: str) -> list:
    """Extrai dados de tabelas Markdown tolerando desalinhamentos e pipes extras."""
    linhas = [l.strip() for l in texto.splitlines() if l.strip()]
    dados, cabecalho = [], []

    for i, linha in enumerate(linhas):
        # Detecta linha divisória (--- ou :---)
        if re.match(r"^\|?[\-\:\s\|]+$", linha):
            # Tenta pegar o cabeçalho na linha anterior
            if i > 0:
                cabecalho = [c.strip(" :") for c in re.split(r"\s*\|\s*", linhas[i - 1]) if c.strip()]
            continue

        # Processa linhas de dados
        if cabecalho and linha.startswith("|"):
            colunas = [c.strip() for c in re.split(r"\s*\|\s*", linha) if c.strip()]
            # Corrige desalinhamentos
            if len(colunas) < len(cabecalho):
                colunas += [""] * (len(cabecalho) - len(colunas))
            elif len(colunas) > len(cabecalho):
                colunas = colunas[:len(cabecalho)]
            dados.append(dict(zip(cabecalho, colunas)))

    return dados


# ============================================================
#  FUNÇÃO HÍBRIDA DE EXTRAÇÃO (JSON + MARKDOWN)
# ============================================================

def extrair_campos(texto: str) -> list:
    """
    Tenta interpretar a resposta da IA:
    1) JSON válido
    2) Tabela Markdown
    Retorna lista de dicionários com colunas padronizadas.
    """
    texto = texto.strip()

    # Tentativa 1 — JSON
    try:
        # Remover blocos de código markdown se presentes
        json_clean = re.sub(r"```json\s*|\s*```", "", texto).strip()
        data = json.loads(json_clean)
        if isinstance(data, list):
            return normalizar_chaves(data)
    except json.JSONDecodeError:
        pass

    # Tentativa 2 — Markdown
    dados_md = parse_markdown_tabela(texto)
    if dados_md:
        return normalizar_chaves(dados_md)

    return []


# ============================================================
#  FUNÇÃO DE LIMPEZA FINAL DE LINHAS
# ============================================================

def limpar_linha_vazia(evidencia: dict) -> dict:
    """Remove chaves com valores vazios antes de salvar."""
    return {k: v for k, v in evidencia.items() if v not in ("", None, "null")}


# ============================================================
#  PIPELINE PRINCIPAL DE PROCESSAMENTO
# ============================================================

def processar_todos_os_blocos():
    """
    Pipeline completo:
    1) Divide o arquivo em blocos
    2) Envia cada bloco à Gemini
    3) Extrai e grava evidências normalizadas no Excel
    """
    logger.info("📚 Carregando blocos do arquivo TXT...")
    blocos = carregar_blocos(ARQUIVO_PADRAO_TXT)
    total_blocos = len(blocos)

    logger.info("📄 Inicializando planilha...")
    inicializar_planilha()

    for i, bloco in enumerate(blocos):
        logger.info(f"🚀 Processando bloco {i+1}/{total_blocos}...")

        resposta = enviar_bloco_para_gemini(bloco, bloco_id=i)
        if not resposta:
            logger.error(f"Erro: nenhum retorno recebido da Gemini para o bloco {i}.")
            continue

        evidencias = extrair_campos(resposta)
        if not evidencias:
            logger.warning(f"Nenhum dado extraído do bloco {i}. Verifique o retorno.")
            continue

        linhas_validas = 0
        for evidencia in evidencias:
            evidencia_limpa = limpar_linha_vazia(evidencia)
            if evidencia_limpa:
                adicionar_linha_excel(evidencia_limpa)
                linhas_validas += 1

        logger.success(f"✅ {linhas_validas} evidência(s) válidas salva(s) na planilha.")

    logger.info("🏁 Processamento finalizado com sucesso.")
