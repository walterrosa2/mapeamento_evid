# leitor_txt.py

import os
from config import CAMINHO_ENTRADA, ARQUIVO_PADRAO_TXT, TAMANHO_BLOCO

def ler_arquivo_txt(nome_arquivo=ARQUIVO_PADRAO_TXT):
    """Lê o conteúdo de um arquivo .txt na pasta de entrada."""
    caminho_completo = os.path.join(CAMINHO_ENTRADA, nome_arquivo)
    
    if not os.path.exists(caminho_completo):
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho_completo}")
    
    with open(caminho_completo, "r", encoding="utf-8") as f:
        conteudo = f.read()

    return conteudo

def limpar_texto(conteudo: str) -> str:
    """Remove espaços excessivos e quebras de páginas comuns em OCR."""
    linhas = conteudo.splitlines()
    texto_limpo = []

    for linha in linhas:
        linha = linha.strip()
        if linha and not linha.lower().startswith("página") and not linha.startswith("___"):
            texto_limpo.append(linha)

    return " ".join(texto_limpo)

def dividir_em_blocos(texto: str, tamanho=TAMANHO_BLOCO) -> list:
    """Divide o texto em blocos de tamanho aproximado."""
    blocos = []
    while len(texto) > tamanho:
        corte = texto.rfind(".", 0, tamanho)
        if corte == -1:
            corte = tamanho
        blocos.append(texto[:corte+1].strip())
        texto = texto[corte+1:].strip()
    if texto:
        blocos.append(texto)
    return blocos

def carregar_blocos(nome_arquivo=ARQUIVO_PADRAO_TXT):
    """Fluxo completo: lê, limpa e divide o texto em blocos."""
    bruto = ler_arquivo_txt(nome_arquivo)
    limpo = limpar_texto(bruto)
    blocos = dividir_em_blocos(limpo)
    return blocos