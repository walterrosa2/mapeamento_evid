# planilha.py (versão corrigida 2025-10-30)

import os
import pandas as pd
from config import CAMINHO_SAIDA

# Nome fixo do arquivo de saída
NOME_ARQUIVO_EXCEL = "evidencias_extraidas.xlsx"

# Estrutura padrão da planilha
COLUNAS_PADRAO = [
    "Tipo de Evidência",
    "Trecho",
    "Conteúdo",
    "Resumo",
    "Referência"
]


# ============================================================
#  CRIAÇÃO E VALIDAÇÃO DA PLANILHA
# ============================================================

def inicializar_planilha():
    """Cria a planilha de evidências com cabeçalho padronizado, se não existir."""
    caminho_arquivo = os.path.join(CAMINHO_SAIDA, NOME_ARQUIVO_EXCEL)

    if not os.path.exists(caminho_arquivo):
        df = pd.DataFrame(columns=COLUNAS_PADRAO)
        df.to_excel(caminho_arquivo, index=False)
        print(f"📄 Planilha inicial criada em: {caminho_arquivo}")
    else:
        # Garante que planilhas antigas sejam ajustadas ao padrão
        df = pd.read_excel(caminho_arquivo)
        colunas_corrigidas = [c for c in df.columns if c in COLUNAS_PADRAO]
        for col in COLUNAS_PADRAO:
            if col not in colunas_corrigidas:
                df[col] = ""
        df = df[COLUNAS_PADRAO]
        df.to_excel(caminho_arquivo, index=False)


# ============================================================
#  INSERÇÃO E LIMPEZA DE LINHAS
# ============================================================

def adicionar_linha_excel(dados_linha: dict):
    """Adiciona uma linha à planilha, filtrando e reordenando as colunas."""
    caminho_arquivo = os.path.join(CAMINHO_SAIDA, NOME_ARQUIVO_EXCEL)

    # Lê a planilha existente
    df_existente = pd.read_excel(caminho_arquivo)

    # Filtra apenas as colunas relevantes
    dados_filtrados = {k: v for k, v in dados_linha.items() if k in COLUNAS_PADRAO}

    # Garante que todas as colunas existam (mesmo se faltarem no dicionário)
    for col in COLUNAS_PADRAO:
        if col not in dados_filtrados:
            dados_filtrados[col] = ""

    # Reordena e adiciona
    nova_linha = pd.DataFrame([dados_filtrados])[COLUNAS_PADRAO]
    df_atualizado = pd.concat([df_existente, nova_linha], ignore_index=True)

    # Remove linhas totalmente vazias ou duplicadas
    df_atualizado.dropna(how="all", inplace=True)
    df_atualizado.drop_duplicates(subset=COLUNAS_PADRAO, keep="first", inplace=True)

    df_atualizado.to_excel(caminho_arquivo, index=False)


# ============================================================
#  ABA DE RESUMO FINAL (OPCIONAL)
# ============================================================

def salvar_resumo_final(resumo_texto: str):
    """Salva o resumo consolidado das evidências em uma nova aba."""
    caminho_arquivo = os.path.join(CAMINHO_SAIDA, NOME_ARQUIVO_EXCEL)

    with pd.ExcelWriter(caminho_arquivo, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
        df_resumo = pd.DataFrame({"Resumo": [resumo_texto]})
        df_resumo.to_excel(writer, sheet_name="Resumo Final", index=False)
