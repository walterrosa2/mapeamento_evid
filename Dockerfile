# Usar imagem Python slim (Debian Bullseye) conforme workflow
FROM python:3.12-slim-bullseye

# Garantir que logs do Python apareçam imediatamente e evitar arquivos .pyc
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app

# Definir diretório de trabalho
WORKDIR /app

# Instalar dependências do sistema necessárias e limpar cache em seguida
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar apenas o requirements.txt para aproveitar o cache de camada do Docker
COPY requirements.txt .

# Instalar dependências Python sem cache para reduzir o tamanho da imagem
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar o restante do código da aplicação
COPY . .

# Criar diretórios necessários para volumes persistentes (ignorados no build via .dockerignore)
RUN mkdir -p entrada saida logs

# Expor as portas conforme documentado (Streamlit usa 8501 por padrão)
EXPOSE 8515

# Configurar Streamlit para produção (Headless)
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
ENV STREAMLIT_SERVER_FILE_WATCHER_TYPE=none
ENV STREAMLIT_SERVER_PORT=8515
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0

# Healthcheck usando a porta padrão do Streamlit
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl --fail http://localhost:8515/_stcore/health || exit 1

# No Ubuntu/Docker Compose, o comando de execução real será injetado pelo docker-compose.yml.
# Deixamos o CMD genérico ou apontando para a aplicação principal.
CMD ["streamlit", "run", "app.py"]
