"""
Teste de comunicação com a API Gemini.
Descobre automaticamente qual modelo está funcional agora.
Uso: python scripts/test_gemini.py
"""
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from dotenv import load_dotenv
load_dotenv(override=True)

from config import GOOGLE_API_KEY
from src.gemini_api import MODEL_ID

try:
    from google import genai
except ImportError:
    import google.genai as genai

SEP = "=" * 55

print(SEP)
print("  TESTE DE COMUNICACAO - GEMINI API")
print(SEP)
print(f"  Modelo atual : {MODEL_ID}")
print(f"  API Key      : ...{GOOGLE_API_KEY[-6:]}")
print(SEP)

client = genai.Client(api_key=GOOGLE_API_KEY)

# ---------------------------------------------------------------------------
# 1. Listar modelos disponíveis
# ---------------------------------------------------------------------------
print("\n[1/4] Modelos disponiveis para esta chave:")
try:
    todos = [
        m.name.replace("models/", "")
        for m in client.models.list()
        if "generateContent" in (m.supported_actions or [])
        and "gemini" in m.name
    ]
    for m in sorted(todos):
        marca = " <-- ATUAL" if m == MODEL_ID else ""
        print(f"      - {m}{marca}")
except Exception as e:
    print(f"      ERRO ao listar: {e}")
    sys.exit(1)

# ---------------------------------------------------------------------------
# 2. Testar modelo atual
# ---------------------------------------------------------------------------
print(f"\n[2/4] Testando modelo atual: {MODEL_ID}")
t0 = time.monotonic()
modelo_funcional = None

try:
    r = client.models.generate_content(model=MODEL_ID, contents="Responda apenas: OK")
    elapsed = time.monotonic() - t0
    resposta = (r.text or "").strip()
    print(f"      PASSOU em {elapsed:.2f}s | Resposta: '{resposta}'")
    modelo_funcional = MODEL_ID
except Exception as e:
    elapsed = time.monotonic() - t0
    print(f"      FALHOU em {elapsed:.2f}s | Erro: {str(e)[:100]}")

# ---------------------------------------------------------------------------
# 3. Se o atual falhou, testar alternativas
# ---------------------------------------------------------------------------
CANDIDATOS = [
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash",
    "gemini-2.0-flash-001",
    "gemini-2.5-pro",
]

if not modelo_funcional:
    print("\n[3/4] Testando modelos alternativos...")
    for candidato in CANDIDATOS:
        if candidato == MODEL_ID:
            continue
        t0 = time.monotonic()
        try:
            r = client.models.generate_content(model=candidato, contents="Responda apenas: OK")
            elapsed = time.monotonic() - t0
            resposta = (r.text or "").strip()
            print(f"      [PASSOU] {candidato} ({elapsed:.2f}s) -> '{resposta}'")
            modelo_funcional = candidato
            break
        except Exception as e:
            elapsed = time.monotonic() - t0
            msg = str(e)[:90]
            print(f"      [FALHOU] {candidato} ({elapsed:.2f}s) -> {msg}")
else:
    print("\n[3/4] Modelo atual operacional - teste de alternativas ignorado.")

# ---------------------------------------------------------------------------
# 4. Resultado final
# ---------------------------------------------------------------------------
print()
print(SEP)
if modelo_funcional:
    print(f"  RESULTADO: API operacional")
    print(f"  Modelo funcional: {modelo_funcional}")
    if modelo_funcional != MODEL_ID:
        print(f"\n  ACAO NECESSARIA: Altere MODEL_ID em src/gemini_api.py")
        print(f"  De: MODEL_ID = \"{MODEL_ID}\"")
        print(f"  Para: MODEL_ID = \"{modelo_funcional}\"")
    else:
        print(f"  Nenhuma alteracao necessaria.")
else:
    print("  RESULTADO: Nenhum modelo respondeu.")
    print("  Provavel causa: cota diaria esgotada.")
    print("  Solucao: aguardar reset a meia-noite (horario de Brasilia)")
    print("  ou usar uma chave de API diferente.")
print(SEP)
