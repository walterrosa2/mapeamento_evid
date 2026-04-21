import sys
import os

# Adiciona a raiz do projeto ao PYTHONPATH para permitir imports do src
sys.path.append(os.getcwd())

from loguru import logger
from src.gemini_api import enviar_bloco_para_gemini
from config import GOOGLE_API_KEY

def smoke_test():
    logger.info("🧪 Iniciando Smoke Test: Chamada real à API Gemini...")
    
    # Teste de carregamento da chave (novamente apenas para log)
    masked_key = f"...{GOOGLE_API_KEY[-4:]}"
    logger.info(f"🔑 Usando chave final: {masked_key}")

    teste_prompt = (
        "Por favor, responda exatamente com a frase: 'Conexão Gemini OK!'. "
        "Não adicione nenhuma outra palavra."
    )
    
    try:
        # Usamos o ID 999 para diferenciar nos logs de auditoria
        resposta = enviar_bloco_para_gemini(teste_prompt, bloco_id=999)
        
        if "Conexão Gemini OK!" in resposta:
            logger.success(f"✅ RESPOSTA DA IA: {resposta}")
            logger.success("🚀 TESTE DE CONEXÃO BEM-SUCEDIDO!")
        else:
            logger.warning(f"⚠️ A IA respondeu, mas o conteúdo foi inesperado: {resposta}")
            
    except Exception as e:
        logger.error(f"❌ FALHA CRÍTICA NO TESTE: {e}")

if __name__ == "__main__":
    smoke_test()
