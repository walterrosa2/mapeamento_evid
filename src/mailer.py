"""
Envio de email best-effort com smtplib (stdlib).
Qualquer falha retorna False sem propagar exceção.
"""
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from loguru import logger
from config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, SMTP_TLS

_MAX_ANEXO_BYTES = 25 * 1024 * 1024  # 25 MB


def smtp_configurado() -> bool:
    return bool(SMTP_HOST and SMTP_USER and SMTP_PASS)


def _build_message(
    destino: str,
    run_nome: str,
    resumo: str,
    xlsx_path: str | None,
) -> MIMEMultipart:
    msg = MIMEMultipart()
    msg["From"] = SMTP_USER
    msg["To"] = destino
    msg["Subject"] = f"[Mapeamento Pericial] Resultado: {run_nome}"

    corpo = (
        f"Prezado(a),\n\n"
        f"O processamento da execução **{run_nome}** foi concluído.\n\n"
        f"{resumo}\n\n"
        f"O arquivo de evidências está em anexo.\n\n"
        f"— Agente Mapeamento Pericial"
    )
    msg.attach(MIMEText(corpo, "plain", "utf-8"))

    if xlsx_path and os.path.exists(xlsx_path):
        tamanho = os.path.getsize(xlsx_path)
        if tamanho <= _MAX_ANEXO_BYTES:
            with open(xlsx_path, "rb") as f:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(f.read())
            encoders.encode_base64(part)
            nome_arquivo = os.path.basename(xlsx_path)
            part.add_header("Content-Disposition", f'attachment; filename="{nome_arquivo}"')
            msg.attach(part)
        else:
            aviso = MIMEText(
                f"\n\n[Arquivo muito grande ({tamanho // (1024*1024)} MB) — "
                "faça o download diretamente na aplicação.]",
                "plain", "utf-8",
            )
            msg.attach(aviso)

    return msg


def enviar_resultado(
    destino: str,
    run_nome: str,
    xlsx_path: str | None,
    resumo: str,
    smtp_factory=None,
) -> bool:
    """
    Envia email com resultado da execução.
    Best-effort: qualquer exceção retorna False.
    smtp_factory é injetável para testes.
    """
    if not destino:
        logger.debug("Email não configurado — envio ignorado.")
        return False

    if not smtp_configurado():
        logger.warning("Credenciais SMTP ausentes — envio de email ignorado.")
        return False

    try:
        msg = _build_message(destino, run_nome, resumo, xlsx_path)
        factory = smtp_factory or (
            smtplib.SMTP if not SMTP_TLS else smtplib.SMTP
        )
        with factory(SMTP_HOST, SMTP_PORT, timeout=30) as server:
            if SMTP_TLS:
                server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_USER, [destino], msg.as_string())
        logger.info(f"Email enviado para {destino} | run: {run_nome}")
        return True
    except Exception as exc:
        logger.warning(f"Falha ao enviar email (best-effort): {exc}")
        return False
