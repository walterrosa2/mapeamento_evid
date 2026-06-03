import os
import time
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from loguru import logger

logger.remove()
logger.add(sys.stdout, format="<green>{time:HH:mm:ss}</green> | <level>{level}</level> | {message}", level="INFO")

try:
    import streamlit as st
    import pandas as pd
    from config import ARQUIVO_PADRAO_TXT, CAMINHO_ENTRADA, CAMINHO_SAIDA
    from src.leitor_txt import carregar_blocos
    from src.controlador import processar_blocos_run
    from src.planilha import get_caminho_excel
    from src import persistence
    from src.mailer import enviar_resultado, smtp_configurado
    logger.success("Imports carregados com sucesso.")
except Exception as e:
    logger.error(f"Erro de import: {e}")
    raise

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Mapeamento Pericial v2",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------
st.markdown("""
<style>
.main-header {
    font-size: 2rem;
    font-weight: 700;
    color: #1E3A8A;
    margin-bottom: 0.2rem;
}
.sub-header {
    font-size: 1rem;
    color: #6B7280;
    margin-bottom: 1.5rem;
}
.stProgress > div > div > div { background-color: #1E3A8A !important; }
.success-box {
    background: #ECFDF5;
    border-left: 4px solid #10B981;
    padding: 12px 16px;
    border-radius: 6px;
    margin: 8px 0;
}
.info-box {
    background: #EFF6FF;
    border-left: 4px solid #3B82F6;
    padding: 12px 16px;
    border-radius: 6px;
    margin: 8px 0;
}
.warn-box {
    background: #FFFBEB;
    border-left: 4px solid #F59E0B;
    padding: 12px 16px;
    border-radius: 6px;
    margin: 8px 0;
}
.bloco-linha { padding: 4px 0; font-size: 0.875rem; border-bottom: 1px solid #F3F4F6; }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def garantir_diretorios():
    for p in [CAMINHO_ENTRADA, CAMINHO_SAIDA]:
        os.makedirs(p, exist_ok=True)


def processar_arquivo_upload(uploaded_file):
    arquivo_path = os.path.join(CAMINHO_ENTRADA, ARQUIVO_PADRAO_TXT)
    with open(arquivo_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return arquivo_path


def _fmt_eta(segundos: float) -> str:
    if segundos <= 0:
        return "calculando..."
    if segundos < 60:
        return f"~{int(segundos)}s"
    mins = int(segundos // 60)
    segs = int(segundos % 60)
    return f"~{mins}min {segs:02d}s"


def _status_label(status: str) -> str:
    icons = {"ok": "✅", "vazio": "⚠️", "erro": "❌", "pulado": "⏭️"}
    return icons.get(status, "⏳")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    garantir_diretorios()
    persistence.init_db()

    # Header
    st.markdown('<p class="main-header">⚖️ Mapeamento Pericial</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Extração de evidências periciais via IA — v2.0</p>', unsafe_allow_html=True)

    # Sidebar
    with st.sidebar:
        st.markdown("### ℹ️ Sobre")
        st.markdown("""
        Analisa documentos OCR e extrai evidências periciais usando Google Gemini.

        **Tipos de evidências:**
        - Notas Fiscais
        - Contratos
        - Pagamentos
        - Multas Contratuais
        - Apontamentos (OSs)
        - Base de Cálculo
        - Oscilações de Gastos
        - Perdas Diretas/Indiretas
        - Reembolso/Viagens
        """)
        if smtp_configurado():
            st.success("📧 Email configurado")
        else:
            st.info("📧 Email não configurado\n(.env SMTP_*)")

    # Tabs
    tab_processar, tab_resultados, tab_historico = st.tabs([
        "📤 Processar", "📊 Resultados", "📋 Histórico"
    ])

    # -----------------------------------------------------------------------
    # TAB 1 — PROCESSAR
    # -----------------------------------------------------------------------
    with tab_processar:
        st.markdown("#### Nova execução")

        with st.form("form_processar"):
            col1, col2 = st.columns([2, 1])
            with col1:
                nome_run = st.text_input(
                    "Nome da execução *",
                    placeholder="Ex: Processo 1234/2025 — Fase 1",
                    help="Identificador amigável para esta análise",
                )
            with col2:
                email_destino = st.text_input(
                    "Email para notificação (opcional)",
                    placeholder="perito@exemplo.com",
                )

            uploaded_file = st.file_uploader(
                "Arquivo TXT (OCR do processo)",
                type=["txt"],
                help="Arquivo de texto extraído via OCR do processo judicial",
            )

            # Dropdown de retomada
            runs_incompletas = persistence.listar_runs_incompletas()
            opcoes_retomada = ["— Nova execução —"] + [
                f"{r['nome']} ({r['status']} — {r['started_at'][:10]})"
                for r in runs_incompletas
            ]
            idx_retomada = st.selectbox(
                "Retomar execução incompleta?",
                range(len(opcoes_retomada)),
                format_func=lambda i: opcoes_retomada[i],
                help="Selecione uma execução anterior para continuar do ponto onde parou",
            )

            submitted = st.form_submit_button("🚀 Iniciar Processamento", use_container_width=True)

        # -------------------------------------------------------------------
        # Processamento
        # -------------------------------------------------------------------
        if submitted:
            retomar_run = runs_incompletas[idx_retomada - 1] if idx_retomada > 0 else None

            if not retomar_run and not uploaded_file:
                st.error("Envie um arquivo TXT ou selecione uma execução para retomar.")
                st.stop()
            if not retomar_run and not nome_run.strip():
                st.error("Informe um nome para a execução.")
                st.stop()

            if uploaded_file:
                with st.spinner("Salvando arquivo..."):
                    processar_arquivo_upload(uploaded_file)
                arquivo_origem = uploaded_file.name
            else:
                arquivo_origem = retomar_run.get("arquivo_origem", "")

            arquivo_txt = os.path.join(CAMINHO_ENTRADA, ARQUIVO_PADRAO_TXT)
            if not os.path.exists(arquivo_txt):
                st.error(f"Arquivo TXT não encontrado. Faça o upload novamente.")
                st.stop()

            with st.spinner("Analisando e dividindo documento em blocos..."):
                blocos = carregar_blocos(ARQUIVO_PADRAO_TXT)
            total_blocos = len(blocos)

            if total_blocos == 0:
                st.error("O documento não gerou nenhum bloco. Verifique o arquivo.")
                st.stop()

            st.info(f"📚 Documento dividido em **{total_blocos} bloco(s)** para análise.")

            # Criar ou retomar run
            if retomar_run:
                run_id = retomar_run["run_id"]
                skip_ids = persistence.get_processed_block_ids(run_id)
                blocos_pendentes = total_blocos - len(skip_ids)
                nome_run = retomar_run["nome"]
                st.markdown(
                    f'<div class="info-box">▶️ Retomando <b>{nome_run}</b> — '
                    f'{len(skip_ids)} bloco(s) já OK, {blocos_pendentes} pendente(s).</div>',
                    unsafe_allow_html=True,
                )
            else:
                run_id = persistence.criar_run(
                    nome=nome_run.strip(),
                    arquivo_origem=arquivo_origem,
                    email_destino=email_destino.strip() or None,
                )
                skip_ids = set()

            st.session_state["run_id"] = run_id
            st.session_state["processamento_concluido"] = False

            # Elementos de progresso
            st.markdown("---")
            st.markdown(f"**Processando:** {nome_run}")
            progress_bar = st.progress(0.0)
            status_text = st.empty()
            container_blocos = st.container()

            t0 = time.monotonic()
            blocos_processados_count = [0]
            erros_count = [0]

            def progress_cb(bloco_id: int, total: int, evidencias_acum: int, status_bloco: str):
                if status_bloco == "pulado":
                    return
                blocos_processados_count[0] += 1
                if status_bloco == "erro":
                    erros_count[0] += 1

                processados = blocos_processados_count[0]
                pct = min(processados / max(total - len(skip_ids), 1), 1.0)
                progress_bar.progress(pct)

                elapsed = time.monotonic() - t0
                pendentes = max(total - len(skip_ids) - processados, 0)
                eta = (elapsed / processados) * pendentes if processados > 0 else 0

                status_text.markdown(
                    f"**Bloco {bloco_id + 1} de {total}** &nbsp;|&nbsp; "
                    f"**{evidencias_acum}** evidência(s) &nbsp;|&nbsp; "
                    f"ETA: {_fmt_eta(eta)}"
                )

                icone = _status_label(status_bloco)
                with container_blocos:
                    st.markdown(
                        f'<div class="bloco-linha">{icone} Bloco {bloco_id + 1}/{total}'
                        f'{"" if status_bloco == "ok" else f" — {status_bloco}"}</div>',
                        unsafe_allow_html=True,
                    )

            # Executar pipeline
            try:
                total_evidencias = processar_blocos_run(
                    run_id=run_id,
                    blocos=blocos,
                    arquivo_origem=arquivo_origem,
                    skip_ids=skip_ids,
                    progress_cb=progress_cb,
                )
                persistence.finalizar_run(run_id, persistence.RUN_COMPLETED)
                st.session_state["processamento_concluido"] = True
                st.session_state["total_evidencias"] = total_evidencias

            except Exception as exc:
                persistence.finalizar_run(run_id, persistence.RUN_INCOMPLETA, str(exc))
                st.error(f"Processamento interrompido: {exc}")
                logger.exception(f"Erro no processamento da run {run_id}")
                st.stop()

            # Resultado final
            progress_bar.progress(1.0)
            duracao = time.monotonic() - t0
            mins = int(duracao // 60)
            segs = int(duracao % 60)

            st.markdown(
                f'<div class="success-box">🎉 <b>Concluído!</b> &nbsp; '
                f'{total_evidencias} evidência(s) extraída(s) &nbsp;|&nbsp; '
                f'Duração: {mins}min {segs:02d}s &nbsp;|&nbsp; '
                f'Erros: {erros_count[0]} bloco(s)</div>',
                unsafe_allow_html=True,
            )

            # Envio de email
            xlsx_path = get_caminho_excel(run_id)
            if email_destino.strip():
                resumo = (
                    f"Total de evidências extraídas: {total_evidencias}\n"
                    f"Blocos processados: {total_blocos}\n"
                    f"Duração: {mins}min {segs:02d}s"
                )
                with st.spinner("Enviando email..."):
                    ok = enviar_resultado(
                        destino=email_destino.strip(),
                        run_nome=nome_run,
                        xlsx_path=xlsx_path,
                        resumo=resumo,
                    )
                if ok:
                    st.success(f"📧 Resultado enviado para {email_destino}")
                else:
                    st.warning("📧 Falha ao enviar email — verifique as configurações SMTP no .env.")
            elif not smtp_configurado():
                st.info("💡 Configure SMTP_* no .env para receber resultados por email.")

    # -----------------------------------------------------------------------
    # TAB 2 — RESULTADOS
    # -----------------------------------------------------------------------
    with tab_resultados:
        st.markdown("#### Resultados da Execução Atual")

        run_id_atual = st.session_state.get("run_id")

        if not run_id_atual:
            st.info("Nenhuma execução nesta sessão. Processe um documento na aba **Processar**.")
        else:
            xlsx_path = get_caminho_excel(run_id_atual)
            if os.path.exists(xlsx_path):
                df = pd.read_excel(xlsx_path)
                if not df.empty:
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Total de Evidências", len(df))
                    n_tipos = df["Tipo de Evidência"].nunique() if "Tipo de Evidência" in df.columns else 0
                    col2.metric("Tipos Únicos", n_tipos)
                    col3.metric("Status", "Concluído ✅")

                    st.dataframe(df, use_container_width=True, height=400)

                    with open(xlsx_path, "rb") as f:
                        st.download_button(
                            label="⬇️ Baixar Excel",
                            data=f,
                            file_name=f"evidencias_{run_id_atual[:8]}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True,
                        )

                    if "Tipo de Evidência" in df.columns:
                        st.markdown("**Distribuição por Tipo de Evidência**")
                        st.bar_chart(df["Tipo de Evidência"].value_counts())
                else:
                    st.warning("Nenhuma evidência extraída nesta execução.")
            else:
                st.warning("Arquivo de resultados não encontrado.")

    # -----------------------------------------------------------------------
    # TAB 3 — HISTÓRICO
    # -----------------------------------------------------------------------
    with tab_historico:
        st.markdown("#### Histórico de Execuções")

        if st.button("🔄 Atualizar lista", key="btn_refresh"):
            st.rerun()

        runs = persistence.listar_runs()

        if not runs:
            st.info("Nenhuma execução registrada ainda.")
        else:
            for run in runs:
                status = run["status"]
                icone = {"COMPLETED": "✅", "RUNNING": "🔄", "INCOMPLETA": "⚠️", "FAILED": "❌"}.get(status, "❓")
                data = run["started_at"][:16] if run["started_at"] else "—"
                evidencias = run.get("total_evidencias") or 0
                blocos_proc = run.get("blocos_processados") or 0
                total_bl = run.get("total_blocos") or "?"

                with st.expander(f"{icone} {run['nome']}  —  {data}  —  {status}", expanded=False):
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("Status", status)
                    col2.metric("Evidências", evidencias)
                    col3.metric("Blocos", f"{blocos_proc}/{total_bl}")
                    col4.metric("Arquivo", run.get("arquivo_origem") or "—")

                    if run.get("erro_msg"):
                        st.error(f"Erro: {run['erro_msg']}")

                    xlsx_path = get_caminho_excel(run["run_id"])
                    if status == "COMPLETED" and os.path.exists(xlsx_path):
                        with open(xlsx_path, "rb") as f:
                            st.download_button(
                                label="⬇️ Baixar Excel",
                                data=f,
                                file_name=f"evidencias_{run['nome'][:30].replace(' ', '_')}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                key=f"dl_{run['run_id']}",
                            )

                    if status in ("INCOMPLETA", "FAILED", "RUNNING"):
                        st.markdown(
                            '<div class="warn-box">▶️ Para retomar, vá à aba '
                            '<b>Processar</b> e selecione no dropdown de retomada.</div>',
                            unsafe_allow_html=True,
                        )


garantir_diretorios()
main()
