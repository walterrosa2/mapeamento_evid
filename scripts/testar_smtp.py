"""
Teste isolado de envio de email (SMTP).

Confirma se as credenciais SMTP do .env estão funcionais, sem precisar rodar
todo o pipeline de processamento. Envia um email de teste e reporta o erro exato
em caso de falha (ex.: 535 → senha-de-app ausente no Gmail).

Uso:
    py scripts/testar_smtp.py [destino@exemplo.com]

Se o destino for omitido, usa SMTP_USER como destinatário.
"""
import os
import sys

# Console do Windows pode usar cp1252; força UTF-8 para imprimir acentos/emojis
try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

# Garante que a raiz do projeto está no path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_TLS
from src.mailer import enviar_resultado, smtp_configurado


def main() -> int:
    destino = sys.argv[1] if len(sys.argv) > 1 else SMTP_USER

    print("=== Diagnóstico SMTP ===")
    print(f"  Host    : {SMTP_HOST or '(vazio)'}")
    print(f"  Porta   : {SMTP_PORT}")
    print(f"  TLS     : {SMTP_TLS}")
    print(f"  Usuário : {SMTP_USER or '(vazio)'}")
    print(f"  Destino : {destino or '(vazio)'}")
    print()

    if not smtp_configurado():
        print("❌ SMTP não configurado. Preencha SMTP_HOST, SMTP_USER e SMTP_PASS no .env.")
        return 1

    if not destino:
        print("❌ Nenhum destino informado e SMTP_USER vazio.")
        return 1

    print("→ Enviando email de teste...")
    ok = enviar_resultado(
        destino=destino,
        run_nome="Teste de configuração SMTP",
        xlsx_path=None,
        resumo="Este é um email de teste do Agente Mapeamento Pericial.\n"
               "Se você recebeu esta mensagem, o envio de resultados por email está funcional.",
    )

    if ok:
        print(f"✅ Email enviado com sucesso para {destino}.")
        print("   Verifique a caixa de entrada (e a pasta de spam).")
        return 0

    print("❌ Falha ao enviar. Veja o log acima (loguru) para o erro exato.")
    print("   Causas comuns no Gmail:")
    print("   - SMTP_PASS deve ser uma SENHA DE APP (não a senha normal):")
    print("     https://myaccount.google.com/apppasswords")
    print("   - Verifique se a porta/TLS estão corretos (587 + TLS=true para STARTTLS).")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
