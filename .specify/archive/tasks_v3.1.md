# Tasks: P2_mapeamento v3.1 — Resumo SAC visível e confirmação de email

## Status Global: ✅ Implementado e validado (pytest 10/10, ruff limpo, SMTP confirmado)

---

## Bloco 1: persistence.py — persistir resumo
- [x] T01 — Adicionar coluna `resumo_processo TEXT` ao `_DDL`
- [x] T02 — `_migrar_schema(con)`: `PRAGMA table_info(runs)` + `ALTER TABLE ... ADD COLUMN` idempotente
- [x] T03 — Chamar `_migrar_schema` em `init_db()` após `executescript`
- [x] T04 — `salvar_resumo_run(run_id, resumo)` (UPDATE)

## Bloco 2: planilha.py — aba Resumo (1ª)
- [x] T05 — `NOME_ABA_RESUMO = "Resumo"` + `_parsear_resumo()` (Campo|Valor)
- [x] T06 — `escrever_resumo_primeira_aba(run_id, resumo)` via openpyxl `create_sheet(.., 0)` (best-effort)
- [x] T07 — `ler_evidencias_df(caminho)`: lê a primeira aba que não seja "Resumo" (compat. Excel antigo)
- [x] T08 — Remover função órfã `salvar_resumo_final()`

## Bloco 3: controlador.py — retorno e gravação
- [x] T09 — Importar `escrever_resumo_primeira_aba`
- [x] T10 — Persistir resumo via `persistence.salvar_resumo_run` na Fase 1
- [x] T11 — Gravar aba Resumo no fim (após o loop), só se houver resumo
- [x] T12 — Retornar tupla `(evidencias_acumuladas, contexto_global)`

## Bloco 4: app.py — UI
- [x] T13 — Capturar tupla e salvar `st.session_state["resumo_processo"]`
- [x] T14 — Expander de resumo na aba Processar (pós-conclusão)
- [x] T15 — Resumo persistente na aba Resultados (lido do banco via `get_run`)
- [x] T16 — Status de email em `session_state["email_status"]` exibido em Resultados
- [x] T17 — Trocar `pd.read_excel` por `ler_evidencias_df`; remover import pandas ocioso

## Bloco 5: scripts/testar_smtp.py
- [x] T18 — Script de diagnóstico/envio de teste (reusa `enviar_resultado`); stdout UTF-8

## Bloco 6: tests/
- [x] T19 — `conftest.py` (sys.path raiz)
- [x] T20 — `test_persistence_resumo.py` (migração + salvar/ler + banco legado)
- [x] T21 — `test_planilha_resumo.py` (aba Resumo é 1ª; evidências intactas; parser)
- [x] T22 — `test_mailer.py` (factory mock; sem destino; sem config; exceção)

## Bloco 7: Validação
- [x] T23 — `pytest tests/ -q` → 10 passed
- [x] T24 — `ruff check` → sem novos erros
- [x] T25 — `scripts/testar_smtp.py` → email enviado com sucesso (Gmail/587/STARTTLS)
