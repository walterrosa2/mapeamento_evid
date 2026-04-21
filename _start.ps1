$env:PYTHONPATH = "."
$env:STREAMLIT_SERVER_PORT = "8515"
$env:STREAMLIT_SERVER_ADDRESS = "localhost"

if (!(Test-Path .venv)) {
    Write-Host "--- Criando Ambiente Virtual (.venv) ---" -ForegroundColor Cyan
    py -3 -m venv .venv
}

Write-Host "--- Ativando Ambiente Virtual ---" -ForegroundColor Cyan
. .venv\Scripts\Activate.ps1

Write-Host "--- Verificando Dependências ---" -ForegroundColor Cyan
pip install -r requirements.txt

if (!(Test-Path .env)) {
    Write-Host "--- Criando .env a partir de .env.example ---" -ForegroundColor Yellow
    Copy-Item .env.example .env
}

Write-Host "--- Iniciando Aplicação Streamlit ---" -ForegroundColor Green
streamlit run app.py
