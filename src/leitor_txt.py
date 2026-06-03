# leitor_txt.py

import os
import re
from loguru import logger
from config import CAMINHO_ENTRADA, ARQUIVO_PADRAO_TXT, TAMANHO_BLOCO, PAGINAS_POR_BLOCO

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

def carregar_texto_completo(nome_arquivo=ARQUIVO_PADRAO_TXT) -> str:
    """T04: Lê o texto bruto sem chunking (para Agente 1 — resumidor)."""
    return ler_arquivo_txt(nome_arquivo)

def detectar_paginas(texto: str) -> list:
    """T05: Split por [fls. N] com regex; retorna list[(num_pagina, texto_pagina)]."""
    paginas = []
    # Split mantém os delimitadores
    partes = re.split(r'(\[fls\.\s*\d+\])', texto)

    current_num = None
    current_texto = []

    for i, parte in enumerate(partes):
        if re.match(r'\[fls\.\s*(\d+)\]', parte):
            # Extrair número da página
            match = re.match(r'\[fls\.\s*(\d+)\]', parte)
            if match:
                if current_texto and current_num is not None:
                    paginas.append((current_num, " ".join(current_texto)))
                current_num = int(match.group(1))
                current_texto = [parte]
        elif parte.strip():
            if current_num is None:
                current_num = 0
            current_texto.append(parte)

    if current_texto and current_num is not None:
        paginas.append((current_num, " ".join(current_texto)))

    return paginas

def dividir_por_paginas(texto: str, paginas_por_bloco: int = PAGINAS_POR_BLOCO) -> list:
    """T06: Agrupa N páginas por bloco, aplica limpeza dentro de cada bloco."""
    paginas = detectar_paginas(texto)

    if not paginas:
        return []

    blocos = []
    for i in range(0, len(paginas), paginas_por_bloco):
        chunk_paginas = paginas[i:i+paginas_por_bloco]
        texto_bloco = " ".join([p[1] for p in chunk_paginas])
        limpo = limpar_texto(texto_bloco)
        if limpo:
            blocos.append(limpo)

    return blocos

def carregar_blocos(nome_arquivo=ARQUIVO_PADRAO_TXT):
    """T07–T09: Fluxo completo v3.0 — tenta page-aware, fallback char-based."""
    bruto = ler_arquivo_txt(nome_arquivo)

    paginas = detectar_paginas(bruto)

    if paginas and len(paginas) > 0:
        # Sucesso: chunking por páginas
        blocos = dividir_por_paginas(bruto)
        logger.info(f"✅ Documento: {len(paginas)} páginas detectadas → {len(blocos)} blocos de {PAGINAS_POR_BLOCO} páginas")
        return blocos
    else:
        # Fallback: chunking por caracteres
        logger.warning(f"⚠️ Nenhum marcador [fls.] detectado — usando chunking por caracteres")
        limpo = limpar_texto(bruto)
        blocos = dividir_em_blocos(limpo)
        logger.info(f"✅ Documento dividido em {len(blocos)} blocos de ~{TAMANHO_BLOCO} caracteres")
        return blocos