# Usar imagem Python slim para reduzir tamanho
FROM python:3.11-slim

# Garantir que logs do Python apareçam imediatamente (sem buffer)
ENV PYTHONUNBUFFERED=1

# Definir diretório de trabalho
WORKDIR /app

# Instalar dependências do sistema necessárias
RUN apt-get update && apt-get install -y \
  build-essential \
  curl \
  && rm -rf /var/lib/apt/lists/*

# Copiar arquivo de dependências
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY . .

# Criar diretórios necessários
RUN mkdir -p entrada saida logs

# Expor porta (Railway injeta dinamicamente, mantemos 8501 como fallback)
# Expor porta (Railway injeta dinamicamente, mantemos 8501 como fallback)
EXPOSE 8501

# Configurar Streamlit para produção
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
ENV STREAMLIT_SERVER_FILE_WATCHER_TYPE=none
ENV STREAMLIT_SERVER_ENABLE_CORS=false
ENV STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=false

# Healthcheck robusto usando a porta dinâmica
# Nota: No Railway, a porta é injetada. O comando curl usa a variável de ambiente $PORT se disponível, ou 8501 por padrão.
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl --fail http://localhost:${PORT:-8501}/_stcore/health || exit 1

# Comando para iniciar a aplicação (Streamlit lê STREAMLIT_SERVER_PORT)
CMD ["streamlit", "run", "app.py"]
