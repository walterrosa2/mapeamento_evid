import os
from dotenv import load_dotenv
from loguru import logger

def verify():
    # Caminho absoluto para garantir que estamos pegando o .env correto
    env_path = os.path.join(os.getcwd(), ".env")
    
    logger.info(f"💾 Tentando carregar .env de: {env_path}")
    
    # Carregando explicitly para o teste
    load_dotenv(env_path, override=True)
    
    key = os.getenv("GOOGLE_API_KEY")
    
    if not key:
        logger.error("❌ GOOGLE_API_KEY não encontrada no ambiente!")
        return

    # Mostrar apenas prefixo e sufixo por segurança
    masked_key = f"{key[:7]}...{key[-4:]}"
    logger.success(f"🔑 Chave carregada com sucesso: {masked_key}")
    
    if key == "AIzaSyBnB53v9E0fVo-DOfxqRe14-I_SzTeyGDg":
        logger.warning("⚠️ Você está usando a chave HARDCODED (Fallback)!")
    elif key == "AIzaSyBSpxbZJDM-5wHAKGZ240YxiFC94cCrvg8":
        logger.success("✅ Confirmado: A chave é a que está no seu arquivo .env!")
    else:
        logger.info("ℹ️ A chave é diferente do fallback e do template padrão.")

if __name__ == "__main__":
    verify()
