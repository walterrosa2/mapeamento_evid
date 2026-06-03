import os
import time
from loguru import logger

# Importação robusta para evitar conflito de namespace 'google'
try:
    from google import genai
except ImportError:
    import google.genai as genai

from google.genai import types
from config import GOOGLE_API_KEY, PROMPT_PADRAO, PROMPT_RESUMIDOR, CAMINHO_LOGS, MAX_CHARS_RESUMIDOR, MAX_TOKENS_RESUMO

# Inicializar cliente Gemini
client = genai.Client(api_key=GOOGLE_API_KEY)
MODEL_ID = "gemini-2.5-flash"

def enviar_bloco_para_gemini(texto_bloco: str, bloco_id: int = 0, contexto_global: str = "") -> str:
    """
    Envia um único bloco de texto para a API Gemini com Retentativa Exponencial.
    """
    max_retries = 5
    retry_delay = 3

    for attempt in range(max_retries):
        try:
            prompt_final = PROMPT_PADRAO
            if contexto_global:
                prompt_final += "\n\n[CONTEXTO DO PROCESSO]\n" + contexto_global + "\n[FIM DO CONTEXTO]\n\n"
            prompt_final += texto_bloco
            salvar_bloco_enviado(bloco_id, prompt_final)

            if contexto_global:
                logger.info(f"🚀 Enviando bloco {bloco_id} com contexto global ({len(contexto_global)} chars) (Tentativa {attempt + 1}/{max_retries} - Modelo: {MODEL_ID})...")
            else:
                logger.info(f"🚀 Enviando bloco {bloco_id} (Tentativa {attempt + 1}/{max_retries} - Modelo: {MODEL_ID})...")
            
            response = client.models.generate_content(
                model=MODEL_ID,
                contents=prompt_final,
                config=types.GenerateContentConfig(
                    max_output_tokens=32768,
                ),
            )

            # Inspecionar finish_reason para diagnóstico de truncamentos silenciosos
            candidate = response.candidates[0] if response.candidates else None
            finish_reason = candidate.finish_reason if candidate else "UNKNOWN"
            if str(finish_reason) not in ("FinishReason.STOP", "STOP", "1"):
                logger.warning(
                    f"⚠️ Bloco {bloco_id} encerrado com finish_reason={finish_reason}. "
                    f"Resposta pode estar incompleta ou bloqueada."
                )

            if not response.text:
                logger.warning(f"⚠️ Resposta vazia no bloco {bloco_id} (finish_reason={finish_reason})")
                return ""

            resposta_texto = response.text.strip()
            salvar_resposta_em_log(bloco_id, resposta_texto)

            return resposta_texto

        except Exception as e:
            error_msg = str(e).lower()
            # 429 = cota esgotada | 503 = servidor sobrecarregado — ambos são retriáveis
            is_retryable = (
                "429" in error_msg or "exhausted" in error_msg or "too many requests" in error_msg
                or "503" in error_msg or "unavailable" in error_msg or "high demand" in error_msg
            )
            if is_retryable:
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)
                    codigo = "429" if "429" in error_msg else "503"
                    logger.warning(f"⏳ API temporariamente indisponível ({codigo}). Aguardando {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"❌ Falha definitiva no bloco {bloco_id} após {max_retries} tentativas.")
            else:
                logger.error(f"❌ Erro na API Gemini (Bloco {bloco_id}): {e}")
                break
    
    return ""

def salvar_resposta_em_log(bloco_id: int, conteudo: str):
    os.makedirs(CAMINHO_LOGS, exist_ok=True)
    nome_arquivo = os.path.join(CAMINHO_LOGS, f"resposta_bloco_{bloco_id:03}.txt")
    with open(nome_arquivo, "w", encoding="utf-8") as f:
        f.write(conteudo)

def salvar_bloco_enviado(bloco_id: int, texto_bloco: str):
    os.makedirs(CAMINHO_LOGS, exist_ok=True)
    caminho = os.path.join(CAMINHO_LOGS, f"bloco_enviado_{bloco_id:03}.txt")
    with open(caminho, "w", encoding="utf-8") as f:
        f.write(texto_bloco)

def gerar_resumo_processo(texto_completo: str) -> str:
    """T14: Agente 1 — gera resumo estruturado do processo completo."""
    if not texto_completo:
        return ""

    # Truncagem se necessário
    if len(texto_completo) > MAX_CHARS_RESUMIDOR:
        logger.warning(f"⚠️ Texto do processo muito grande ({len(texto_completo):,} chars) — truncando para {MAX_CHARS_RESUMIDOR:,}")
        texto_completo = texto_completo[:MAX_CHARS_RESUMIDOR]

    max_retries = 3
    retry_delay = 3

    for attempt in range(max_retries):
        try:
            logger.info(f"🔍 Gerando resumo do processo (Tentativa {attempt + 1}/{max_retries})...")
            inicio = time.time()

            response = client.models.generate_content(
                model=MODEL_ID,
                contents=PROMPT_RESUMIDOR + "\n\n" + texto_completo,
                config=types.GenerateContentConfig(
                    max_output_tokens=MAX_TOKENS_RESUMO,
                    # Desabilita "thinking" para não consumir o orçamento de saída
                    # (causa do resumo truncado em gemini-2.5-flash).
                    thinking_config=types.ThinkingConfig(thinking_budget=0),
                ),
            )

            duracao = time.time() - inicio

            # Diagnóstico de truncamento (finish_reason != STOP indica corte)
            candidate = response.candidates[0] if response.candidates else None
            finish_reason = candidate.finish_reason if candidate else "UNKNOWN"
            if str(finish_reason) not in ("FinishReason.STOP", "STOP", "1"):
                logger.warning(f"⚠️ Resumo encerrado com finish_reason={finish_reason} — pode estar incompleto.")

            if not response.text:
                logger.warning("⚠️ Resumo vazio")
                return ""

            resumo = response.text.strip()

            # Salvar em auditoria
            os.makedirs(CAMINHO_LOGS, exist_ok=True)
            with open(os.path.join(CAMINHO_LOGS, "resumo_processo.txt"), "w", encoding="utf-8") as f:
                f.write(resumo)

            logger.success(f"✅ Resumo gerado em {duracao:.1f}s ({len(resumo)} chars)")
            return resumo

        except Exception as e:
            error_msg = str(e).lower()
            is_retryable = (
                "429" in error_msg or "exhausted" in error_msg or "too many requests" in error_msg
                or "503" in error_msg or "unavailable" in error_msg or "high demand" in error_msg
            )
            if is_retryable:
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)
                    logger.warning(f"⏳ API indisponível. Aguardando {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"❌ Falha ao gerar resumo após {max_retries} tentativas — SAC desativado")
            else:
                logger.error(f"❌ Erro ao gerar resumo: {e} — SAC desativado")
            break

    return ""
