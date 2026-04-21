import os
import time
from loguru import logger

# Importação robusta para evitar conflito de namespace 'google'
try:
    from google import genai
except ImportError:
    import google.genai as genai

from google.genai import types
from config import GOOGLE_API_KEY, PROMPT_PADRAO, CAMINHO_LOGS

# Inicializar cliente Gemini
client = genai.Client(api_key=GOOGLE_API_KEY)
MODEL_ID = "gemini-2.5-flash"

def enviar_bloco_para_gemini(texto_bloco: str, bloco_id: int = 0) -> str:
    """
    Envia um único bloco de texto para a API Gemini com Retentativa Exponencial.
    """
    max_retries = 5
    retry_delay = 3

    for attempt in range(max_retries):
        try:
            prompt_final = PROMPT_PADRAO + "\n\n" + texto_bloco
            salvar_bloco_enviado(bloco_id, prompt_final)

            logger.info(f"🚀 Enviando bloco {bloco_id} (Tentativa {attempt + 1}/{max_retries} - Modelo: {MODEL_ID})...")
            
            response = client.models.generate_content(
                model=MODEL_ID,
                contents=prompt_final
            )

            if not response.text:
                logger.warning(f"⚠️ Resposta vazia no bloco {bloco_id}")
                return ""

            resposta_texto = response.text.strip()
            salvar_resposta_em_log(bloco_id, resposta_texto)

            return resposta_texto

        except Exception as e:
            error_msg = str(e).lower()
            if "429" in error_msg or "exhausted" in error_msg or "too many requests" in error_msg:
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)
                    logger.warning(f"⏳ Cota atingida (429). Aguardando {wait_time}s antes de tentar novamente...")
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
