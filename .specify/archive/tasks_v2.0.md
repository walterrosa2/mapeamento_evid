# Tasks: P2_mapeamento v2.0

## Status Global: 🔄 Em Implementação

---

## Bloco 1: src/persistence.py (NOVO)
- [ ] T01 — Criar `src/persistence.py` com `init_db()`: abre/cria `saida/runs.db` com WAL, cria tabelas `runs` e `run_items` + índices
- [ ] T02 — Implementar `criar_run(nome, arquivo_origem, email_destino) -> str`: insere run com status RUNNING, retorna run_id (UUID)
- [ ] T03 — Implementar `atualizar_progresso_run(run_id, blocos_processados, total_evidencias)`: UPDATE parcial da run
- [ ] T04 — Implementar `finalizar_run(run_id, status, erro_msg=None)`: SET finished_at + status (COMPLETED/FAILED/INCOMPLETA)
- [ ] T05 — Implementar `salvar_run_item(run_id, bloco_id, status, evidencias_count, erro_msg=None)`: INSERT OR REPLACE run_items
- [ ] T06 — Implementar `get_processed_block_ids(run_id) -> set[int]`: retorna IDs de blocos com status OK
- [ ] T07 — Implementar `listar_runs() -> list[dict]`: retorna todas as runs ordenadas por started_at DESC
- [ ] T08 — Implementar `listar_runs_incompletas() -> list[dict]`: filtra status IN (RUNNING, INCOMPLETA, FAILED)
- [ ] T09 — Implementar `get_run(run_id) -> dict | None`: busca run por ID
- [ ] T10 — Tratar runs RUNNING órfãs em `listar_runs_incompletas()`: status RUNNING com finished_at NULL → tratar como INCOMPLETA

## Bloco 2: src/mailer.py (NOVO)
- [ ] T11 — Criar `src/mailer.py` com função `smtp_configurado() -> bool`: verifica se SMTP_HOST, SMTP_USER, SMTP_PASS estão no .env
- [ ] T12 — Implementar `_build_message(destino, run_nome, resumo, xlsx_path) -> MIMEMultipart`: monta email com assunto, corpo texto e anexo XLSX (se existir e < 25MB)
- [ ] T13 — Implementar `enviar_resultado(destino, run_nome, xlsx_path, resumo, smtp_factory=None) -> bool`: conecta SMTP TLS, autentica, envia; captura todas as exceções; retorna bool
- [ ] T14 — Garantir best-effort: qualquer exceção em `enviar_resultado` retorna False sem propagar

## Bloco 3: src/planilha.py (ALTERAÇÃO)
- [ ] T15 — Atualizar `COLUNAS_PADRAO` para incluir `Run ID`, `Arquivo Origem`, `Data Processamento` ao final
- [ ] T16 — Refatorar `inicializar_planilha(run_id)`: criar arquivo em `saida/runs/{run_id}/evidencias.xlsx` (criar pasta se necessário)
- [ ] T17 — Refatorar `adicionar_linha_excel(dados_linha, run_id, arquivo_origem)`: preencher automaticamente as 3 novas colunas com valores passados
- [ ] T18 — Adicionar função `get_caminho_excel(run_id) -> str`: retorna caminho padronizado do Excel da run
- [ ] T19 — Manter função `salvar_resumo_final()` sem alteração (retrocompatibilidade)

## Bloco 4: config.py (ALTERAÇÃO)
- [ ] T20 — Adicionar constantes SMTP: `SMTP_HOST`, `SMTP_PORT` (int, default 587), `SMTP_USER`, `SMTP_PASS`, `SMTP_TLS` (bool, default True)
- [ ] T21 — Adicionar constante `CAMINHO_RUNS = os.path.join(CAMINHO_SAIDA, "runs")`
- [ ] T22 — Adicionar constante `CAMINHO_DB = os.path.join(CAMINHO_SAIDA, "runs.db")`

## Bloco 5: src/controlador.py (ALTERAÇÃO)
- [ ] T23 — Adicionar `import` de `persistence` e alterar assinatura de `processar_todos_os_blocos()` para `processar_blocos_run(run_id, blocos, skip_ids=None, progress_cb=None)`
- [ ] T24 — No loop, checar `if i in skip_ids: continue` e chamar `progress_cb` após cada bloco com assinatura `(bloco_id, total, evidencias_acumuladas, status_bloco)`
- [ ] T25 — Chamar `persistence.salvar_run_item()` após cada bloco (OK, ERRO_LLM ou ERRO_PARSE)
- [ ] T26 — Chamar `persistence.atualizar_progresso_run()` após cada bloco
- [ ] T27 — Manter `processar_todos_os_blocos()` original como wrapper para retrocompatibilidade do `main.py`

## Bloco 6: app.py (ALTERAÇÃO MAIOR)
- [ ] T28 — Substituir cabeçalho CSS para refletir v2.0 (manter paleta azul existente)
- [ ] T29 — Refatorar Tab 1 ("Upload e Processamento") para incluir: campo `nome_run`, campo `email`, dropdown de retomada (runs incompletas)
- [ ] T30 — Implementar lógica de retomada: se run selecionada → carregar run_id existente + skip_ids; se nova → criar run via persistence
- [ ] T31 — Implementar progress callback `_progress_cb(bloco_id, total, evidencias_acumuladas, status_bloco)` que atualiza progress_bar, status_text e lista de status por bloco
- [ ] T32 — Implementar cálculo de ETA: `elapsed = time.monotonic() - t0; eta = (elapsed / processados) * restantes`
- [ ] T33 — Implementar formatação de ETA: `_fmt_eta(segundos) -> str` (ex: "3min 25s", "< 1min")
- [ ] T34 — Após finalizar: chamar `mailer.enviar_resultado()` e exibir `st.success` ou `st.warning` conforme resultado
- [ ] T35 — Refatorar Tab 3 ("Resultados") para ler Excel por `run_id` atual via `planilha.get_caminho_excel(run_id)`
- [ ] T36 — Criar Tab 4 ("Histórico"): chamar `persistence.listar_runs()`, exibir tabela, botão download por run, botão "Retomar" para incompletas
- [ ] T37 — Proteger app de runs sem arquivo TXT disponível para retomada (exibir aviso claro)
- [ ] T38 — Garantir que `st.session_state` armazena: `run_id`, `processamento_concluido`, `total_evidencias`

## Bloco 7: Arquivos de configuração
- [ ] T39 — Atualizar `.env.example` com bloco SMTP documentado
- [ ] T40 — Verificar `requirements.txt`: confirmar que não precisa de novas dependências

## Bloco 8: Validação
- [ ] T41 — Smoke test: iniciar app, processar arquivo pequeno, verificar banco, Excel por run, email (se configurado)
- [ ] T42 — Testar retomada: interromper no meio, reiniciar, confirmar que blocos OK são pulados
- [ ] T43 — Testar histórico: verificar Tab 4 lista execuções corretamente com botões funcionais
