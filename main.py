# main.py

import sys
from src.controlador import processar_todos_os_blocos
from config import ARQUIVO_PADRAO_TXT

def main():
    print("\n🧠 PROJETO: Extração Automatizada de Evidências Jurídicas")
    print("🔎 Entrada esperada: arquivo .txt extraído via OCR contendo o processo.")
    print(f"📥 Nome padrão do arquivo de entrada: {ARQUIVO_PADRAO_TXT}")
    print("📊 Saída: planilha Excel com as evidências organizadas\n")

    # Futuro: permitir passar nome do arquivo como argumento
    if len(sys.argv) > 1:
        print("⚠️ Entrada via argumento ainda não implementada. Usando arquivo padrão.\n")

    processar_todos_os_blocos()

if __name__ == '__main__':
    processar_todos_os_blocos()