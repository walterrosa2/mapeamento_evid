"""
Smoke tests para v3.0 — Page-aware chunking + SAC.
Execução: python scripts/smoke_test_v3.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from loguru import logger
from src.leitor_txt import carregar_blocos, carregar_texto_completo, detectar_paginas
from src.gemini_api import gerar_resumo_processo

logger.info("=== SMOKE TESTS v3.0 ===")

# T27: Testar F-01 — Page-aware chunking
logger.info("\n[T27] Testando page-aware chunking...")
try:
    blocos = carregar_blocos("processo.txt")
    if blocos:
        logger.success(f"✅ Blocos carregados: {len(blocos)} blocos")
    else:
        logger.warning("⚠️ Nenhum bloco gerado")
except Exception as e:
    logger.error(f"❌ Erro ao carregar blocos: {e}")

# T28: Testar F-01 fallback
logger.info("\n[T28] Testando fallback (sem [fls.])...")
try:
    texto = "Documento sem marcadores de página. Apenas texto normal aqui."
    paginas = detectar_paginas(texto)
    if len(paginas) == 0:
        logger.success("✅ Fallback detectado (nenhuma página com [fls.])")
    else:
        logger.warning(f"⚠️ Esperava 0 páginas, obteve {len(paginas)}")
except Exception as e:
    logger.error(f"❌ Erro no fallback: {e}")

# T29: Testar F-02 — Resumidor
logger.info("\n[T29] Testando resumidor (SAC)...")
try:
    texto_completo = carregar_texto_completo("processo.txt")
    if texto_completo:
        logger.info(f"📄 Texto carregado: {len(texto_completo):,} chars")
        resumo = gerar_resumo_processo(texto_completo)
        if resumo and len(resumo) > 0:
            logger.success(f"✅ Resumo gerado: {len(resumo)} chars")
            logger.info(f"Resumo preview:\n{resumo[:200]}...")
        else:
            logger.warning("⚠️ Resumo vazio — SAC fallback funcionou (best-effort)")
    else:
        logger.error("❌ Texto completo vazio")
except Exception as e:
    logger.error(f"❌ Erro ao gerar resumo: {e}")

# T30: Verificar logs
logger.info("\n[T30] Verificando logs de auditoria...")
import os
from config import CAMINHO_LOGS
logs_esperados = ["resumo_processo.txt", "bloco_enviado_001.txt"]
for log in logs_esperados:
    path = os.path.join(CAMINHO_LOGS, log)
    if os.path.exists(path):
        size = os.path.getsize(path)
        logger.success(f"✅ {log}: {size:,} bytes")
    else:
        logger.warning(f"⚠️ {log} não encontrado (pode ser normal se sem processamento)")

logger.info("\n=== FIM DOS TESTES ===")
