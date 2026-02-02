import os
import time
import google.generativeai as genai
from loguru import logger
from config import GOOGLE_API_KEY, PROMPT_PADRAO, CAMINHO_LOGS

# Inicializar configuração da API
genai.configure(api_key=GOOGLE_API_KEY)

# Carregar modelo (ajustável para Pro ou Flash)
modelo = genai.GenerativeModel(model_name="gemini-2.0-flash")

def enviar_bloco_para_gemini(texto_bloco: str, bloco_id: int = 0) -> str:
    """
    Envia um único bloco de texto para a API Gemini.
    Retorna a resposta gerada (raw text).
    """

    try:
        prompt_final = PROMPT_PADRAO + "\n\n" + texto_bloco
        
        # Salvar o bloco enviado ANTES de processar (Evidência de envio)
        salvar_bloco_enviado(bloco_id, prompt_final)

        logger.info(f"Enviando bloco {bloco_id} para Gemini...")
        response = modelo.generate_content(prompt_final)

        resposta_texto = response.text.strip()

        # Salvar a resposta ANTES de qualquer processamento (Evidência de resposta)
        salvar_resposta_em_log(bloco_id, resposta_texto)

        return resposta_texto

    except Exception as e:
        logger.error(f"Erro ao processar o bloco {bloco_id}: {e}")
        return ""

def salvar_resposta_em_log(bloco_id: int, conteudo: str):
    """Salva o retorno da LLM para auditoria/localização futura."""
    os.makedirs(CAMINHO_LOGS, exist_ok=True)
    nome_arquivo = os.path.join(CAMINHO_LOGS, f"resposta_bloco_{bloco_id:03}.txt")
    with open(nome_arquivo, "w", encoding="utf-8") as f:
        f.write(conteudo)

def salvar_bloco_enviado(bloco_id: int, texto_bloco: str):
    """Salva localmente o conteúdo enviado à Gemini para rastreamento."""
    os.makedirs(CAMINHO_LOGS, exist_ok=True)
    caminho = os.path.join(CAMINHO_LOGS, f"bloco_enviado_{bloco_id:03}.txt")
    with open(caminho, "w", encoding="utf-8") as f:
        f.write(texto_bloco)
