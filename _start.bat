@echo off
set PYTHONPATH=.
set STREAMLIT_SERVER_PORT=8515
set STREAMLIT_SERVER_ADDRESS=localhost

if not exist .venv (
    echo --- Criando Ambiente Virtual (.venv) ---
    py -3 -m venv .venv
)

echo --- Ativando Ambiente Virtual ---
call .venv\Scripts\activate.bat

echo --- Verificando Dependencias ---
pip install -r requirements.txt

if not exist .env (
    echo --- Criando .env a partir de .env.example ---
    copy .env.example .env
)

echo --- Iniciando Aplicacao Streamlit ---
streamlit run app.py
