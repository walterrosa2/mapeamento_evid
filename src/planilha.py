import os
from datetime import datetime, timezone
import pandas as pd
from config import CAMINHO_SAIDA, CAMINHO_RUNS

# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------
COLUNAS_EVIDENCIA = [
    "Tipo de Evidência",
    "Trecho",
    "Conteúdo",
    "Resumo",
    "Referência",
]

COLUNAS_META = [
    "Run ID",
    "Arquivo Origem",
    "Data Processamento",
]

COLUNAS_PADRAO = COLUNAS_EVIDENCIA + COLUNAS_META

NOME_ARQUIVO_EXCEL = "evidencias.xlsx"


# ---------------------------------------------------------------------------
# Caminhos
# ---------------------------------------------------------------------------

def get_caminho_excel(run_id: str) -> str:
    pasta = os.path.join(CAMINHO_RUNS, run_id)
    os.makedirs(pasta, exist_ok=True)
    return os.path.join(pasta, NOME_ARQUIVO_EXCEL)


# ---------------------------------------------------------------------------
# Criação / inicialização
# ---------------------------------------------------------------------------

def inicializar_planilha(run_id: str) -> str:
    """Cria Excel isolado para a run. Retorna caminho do arquivo."""
    caminho = get_caminho_excel(run_id)
    if not os.path.exists(caminho):
        df = pd.DataFrame(columns=COLUNAS_PADRAO)
        df.to_excel(caminho, index=False)
    return caminho


# ---------------------------------------------------------------------------
# Inserção
# ---------------------------------------------------------------------------

def _preparar_linha(dados_linha: dict, run_id: str, arquivo_origem: str, ts: str) -> dict:
    row = {k: v for k, v in dados_linha.items() if k in COLUNAS_EVIDENCIA}
    for col in COLUNAS_EVIDENCIA:
        row.setdefault(col, "")
    row["Run ID"] = run_id
    row["Arquivo Origem"] = arquivo_origem
    row["Data Processamento"] = ts
    return row


def adicionar_linhas_excel(lista_dados: list[dict], run_id: str, arquivo_origem: str = "") -> int:
    """
    Escreve todas as evidências de um bloco de uma vez (batch).
    Muito mais eficiente que chamar linha a linha.
    Retorna quantidade de linhas adicionadas após deduplicação.
    """
    if not lista_dados:
        return 0

    caminho = get_caminho_excel(run_id)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    novas_linhas = [_preparar_linha(d, run_id, arquivo_origem, ts) for d in lista_dados]
    df_novas = pd.DataFrame(novas_linhas)[COLUNAS_PADRAO]

    df_existente = pd.read_excel(caminho) if os.path.exists(caminho) else pd.DataFrame(columns=COLUNAS_PADRAO)
    antes = len(df_existente)

    df_atualizado = pd.concat([df_existente, df_novas], ignore_index=True)
    df_atualizado.dropna(how="all", inplace=True)
    df_atualizado.drop_duplicates(subset=COLUNAS_EVIDENCIA, keep="first", inplace=True)
    df_atualizado.to_excel(caminho, index=False)

    return len(df_atualizado) - antes


def adicionar_linha_excel(dados_linha: dict, run_id: str, arquivo_origem: str = "") -> None:
    """Compatibilidade: chama a versão batch com uma única linha."""
    adicionar_linhas_excel([dados_linha], run_id, arquivo_origem)


# ---------------------------------------------------------------------------
# Retrocompatibilidade (legado — main.py CLI)
# ---------------------------------------------------------------------------

def inicializar_planilha_legado():
    """Mantém compatibilidade com main.py que não usa run_id."""
    caminho_arquivo = os.path.join(CAMINHO_SAIDA, "evidencias_extraidas.xlsx")
    if not os.path.exists(caminho_arquivo):
        df = pd.DataFrame(columns=COLUNAS_EVIDENCIA)
        df.to_excel(caminho_arquivo, index=False)
    return caminho_arquivo


def adicionar_linha_excel_legado(dados_linha: dict):
    """Wrapper legado para main.py CLI (arquivo único acumulativo)."""
    caminho = os.path.join(CAMINHO_SAIDA, "evidencias_extraidas.xlsx")
    dados_filtrados = {k: v for k, v in dados_linha.items() if k in COLUNAS_EVIDENCIA}
    for col in COLUNAS_EVIDENCIA:
        dados_filtrados.setdefault(col, "")
    nova_linha = pd.DataFrame([dados_filtrados])[COLUNAS_EVIDENCIA]
    df_existente = pd.read_excel(caminho) if os.path.exists(caminho) else pd.DataFrame(columns=COLUNAS_EVIDENCIA)
    df_atualizado = pd.concat([df_existente, nova_linha], ignore_index=True)
    df_atualizado.dropna(how="all", inplace=True)
    df_atualizado.drop_duplicates(subset=COLUNAS_EVIDENCIA, keep="first", inplace=True)
    df_atualizado.to_excel(caminho, index=False)


def salvar_resumo_final(resumo_texto: str, run_id: str = None):
    """Salva aba 'Resumo Final' no Excel da run (ou legado)."""
    caminho = get_caminho_excel(run_id) if run_id else os.path.join(CAMINHO_SAIDA, "evidencias_extraidas.xlsx")
    if not os.path.exists(caminho):
        return
    with pd.ExcelWriter(caminho, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
        df_resumo = pd.DataFrame({"Resumo": [resumo_texto]})
        df_resumo.to_excel(writer, sheet_name="Resumo Final", index=False)
