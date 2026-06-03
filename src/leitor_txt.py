# leitor_txt.py

import os
import re
from loguru import logger
from config import (
    CAMINHO_ENTRADA,
    ARQUIVO_PADRAO_TXT,
    TAMANHO_BLOCO,
    PAGINAS_POR_BLOCO,
    DELIMITADOR_PAGINA_PADRAO,
    MAX_CHARS_BLOCO,
)

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

def detectar_paginas(texto: str, delimitador: str = DELIMITADOR_PAGINA_PADRAO) -> list:
    """v3.2: Divide o texto pelo delimitador de página configurável.

    Retorna list[(num_pagina, texto_pagina)]. Se o delimitador não existir no
    texto, retorna [] — sinalizando ao chamador para usar o fallback por caracteres.
    """
    if not delimitador or delimitador not in texto:
        return []

    partes = texto.split(delimitador)
    paginas = []
    for parte in partes:
        if not parte.strip():
            continue
        # Quando o delimitador é seguido do número da página (ex: "---Página--- 12"),
        # extrai esse número; caso contrário, usa a posição sequencial.
        match = re.match(r'\s*(\d+)', parte)
        num = int(match.group(1)) if match else len(paginas) + 1
        paginas.append((num, parte))

    return paginas

def dividir_por_paginas(texto: str, delimitador: str = DELIMITADOR_PAGINA_PADRAO,
                        paginas_por_bloco: int = PAGINAS_POR_BLOCO) -> list:
    """v3.2: Agrupa N páginas por bloco; subdivide se exceder MAX_CHARS_BLOCO."""
    paginas = detectar_paginas(texto, delimitador)
    if not paginas:
        return []

    blocos = []
    for i in range(0, len(paginas), paginas_por_bloco):
        chunk_paginas = paginas[i:i+paginas_por_bloco]
        texto_bloco = " ".join(p[1] for p in chunk_paginas)
        limpo = limpar_texto(texto_bloco)
        if not limpo:
            continue
        # Teto de segurança: evita blocos gigantes (e respostas truncadas)
        if len(limpo) > MAX_CHARS_BLOCO:
            blocos.extend(dividir_em_blocos(limpo, tamanho=MAX_CHARS_BLOCO))
        else:
            blocos.append(limpo)

    return blocos

def carregar_blocos(nome_arquivo=ARQUIVO_PADRAO_TXT, delimitador: str = DELIMITADOR_PAGINA_PADRAO):
    """v3.2: Tenta dividir por páginas (delimitador configurável); fallback char-based."""
    bruto = ler_arquivo_txt(nome_arquivo)

    paginas = detectar_paginas(bruto, delimitador)

    if paginas:
        blocos = dividir_por_paginas(bruto, delimitador)
        logger.info(
            f"✅ Documento: {len(paginas)} páginas detectadas (delim='{delimitador}') "
            f"→ {len(blocos)} blocos (até {PAGINAS_POR_BLOCO} págs/bloco, teto {MAX_CHARS_BLOCO} chars)"
        )
        return blocos
    else:
        logger.warning(
            f"⚠️ Delimitador '{delimitador}' não encontrado — usando chunking por caracteres"
        )
        limpo = limpar_texto(bruto)
        blocos = dividir_em_blocos(limpo)
        logger.info(f"✅ Documento dividido em {len(blocos)} blocos de ~{TAMANHO_BLOCO} caracteres")
        return blocos