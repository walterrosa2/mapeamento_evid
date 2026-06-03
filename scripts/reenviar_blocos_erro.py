"""
Reenvio isolado de blocos com erro para teste de novo modelo.

Uso:
    python scripts/reenviar_blocos_erro.py --blocos 9 10
    python scripts/reenviar_blocos_erro.py --blocos 9 10 --modelo gemini-2.5-flash

Lê os arquivos logs/bloco_enviado_XXX.txt (prompt já montado) e reenvia
ao Gemini salvando em logs/reenvio_resposta_XXX.txt, sem alterar a run atual.
"""

import sys
import os
import argparse
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from loguru import logger
from dotenv import load_dotenv

load_dotenv(override=True)

try:
    from google import genai
except ImportError:
    import google.genai as genai

from google.genai import types

MODELO_PADRAO = "gemini-2.5-flash"
CAMINHO_LOGS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")


def enviar_bloco(prompt: str, modelo: str, bloco_id: int) -> dict:
    """Envia prompt para Gemini e retorna diagnóstico completo."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY não encontrada no .env")

    client = genai.Client(api_key=api_key)

    config = types.GenerateContentConfig(
        max_output_tokens=16384,
    )

    logger.info(f"Enviando bloco {bloco_id} → modelo={modelo}, max_output_tokens=16384")
    inicio = time.time()

    response = client.models.generate_content(
        model=modelo,
        contents=prompt,
        config=config,
    )

    duracao = time.time() - inicio

    candidate = response.candidates[0] if response.candidates else None
    finish_reason = str(candidate.finish_reason) if candidate else "UNKNOWN"
    texto = response.text or ""

    # Contar linhas da tabela na resposta
    linhas_dados = [
        l for l in texto.splitlines()
        if l.strip().startswith("|") and not set(l.replace("|", "").replace("-", "").replace(":", "").replace(" ", "")) == set()
    ]
    # Subtrair cabeçalho e separador
    linhas_evidencias = max(0, len(linhas_dados) - 2)

    return {
        "bloco_id": bloco_id,
        "modelo": modelo,
        "finish_reason": finish_reason,
        "duracao_s": round(duracao, 1),
        "chars_resposta": len(texto),
        "linhas_evidencias": linhas_evidencias,
        "texto": texto,
    }


def processar_blocos(ids: list[int], modelo: str):
    resultados = []

    for bloco_id in ids:
        caminho_enviado = os.path.join(CAMINHO_LOGS, f"bloco_enviado_{bloco_id:03}.txt")

        if not os.path.exists(caminho_enviado):
            logger.error(f"Arquivo não encontrado: {caminho_enviado}")
            continue

        with open(caminho_enviado, encoding="utf-8") as f:
            prompt = f.read()

        logger.info(f"--- Bloco {bloco_id} | {len(prompt):,} chars de entrada ---")

        try:
            resultado = enviar_bloco(prompt, modelo, bloco_id)
        except Exception as e:
            logger.error(f"Erro ao enviar bloco {bloco_id}: {e}")
            continue

        # Salvar resposta em arquivo separado (não sobrescreve o original)
        caminho_saida = os.path.join(CAMINHO_LOGS, f"reenvio_resposta_{bloco_id:03}.txt")
        with open(caminho_saida, "w", encoding="utf-8") as f:
            f.write(resultado["texto"])

        status = "✅ OK" if resultado["finish_reason"] in ("FinishReason.STOP", "STOP", "1") else f"⚠️ {resultado['finish_reason']}"
        logger.info(
            f"Bloco {bloco_id}: {status} | "
            f"{resultado['duracao_s']}s | "
            f"{resultado['chars_resposta']:,} chars | "
            f"{resultado['linhas_evidencias']} evidências | "
            f"Salvo em reenvio_resposta_{bloco_id:03}.txt"
        )

        resultados.append(resultado)

    # Resumo final
    print("\n" + "=" * 60)
    print(f"RESUMO — modelo: {modelo}")
    print("=" * 60)
    print(f"{'Bloco':<8} {'Status':<30} {'Tempo':>7} {'Evidências':>12}")
    print("-" * 60)
    for r in resultados:
        ok = r["finish_reason"] in ("FinishReason.STOP", "STOP", "1")
        status = "STOP" if ok else r["finish_reason"]
        print(f"{r['bloco_id']:<8} {status:<30} {r['duracao_s']:>6}s {r['linhas_evidencias']:>12}")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Reenvio isolado de blocos com erro")
    parser.add_argument(
        "--blocos", nargs="+", type=int, required=True,
        help="IDs dos blocos a reenviar (ex: --blocos 9 10)"
    )
    parser.add_argument(
        "--modelo", default=MODELO_PADRAO,
        help=f"Modelo Gemini a usar (padrão: {MODELO_PADRAO})"
    )
    args = parser.parse_args()

    logger.info(f"Iniciando reenvio de {len(args.blocos)} bloco(s) com modelo={args.modelo}")
    processar_blocos(args.blocos, args.modelo)


if __name__ == "__main__":
    main()
