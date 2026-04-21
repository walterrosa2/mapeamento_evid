#!/bin/bash

# Script de Inicialização para Linux (Ubuntu/Docker Ready)

echo "🚀 Iniciando Agente Mapeamento no Linux..."

# Garantir que estamos no diretório correto
cd "$(dirname "$0")"

# Criar venv se não existir
if [ ! -d ".venv" ]; then
    echo "📦 Criando ambiente virtual..."
    python3 -m venv .venv
fi

# Ativar venv
source .venv/bin/activate

# Instalar dependências
echo "🛠️ Instalando/Atualizando dependências..."
pip install --upgrade pip
pip install -r requirements.txt

# Exportar PYTHONPATH
export PYTHONPATH=$PYTHONPATH:.

# Carregar .env se existir (opcional para containers que já injetam env vars)
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Rodar Streamlit
echo "🌐 Iniciando aplicação na porta 8515..."
streamlit run app.py --server.port 8515 --server.address 0.0.0.0 --server.headless true
