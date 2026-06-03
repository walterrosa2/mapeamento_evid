# Plano Técnico: v3.1 — Resumo SAC visível e confirmação de email

## Arquivos afetados

| Arquivo | Mudança |
|---|---|
| `src/persistence.py` | + coluna `resumo_processo` no DDL; `_migrar_schema()` idempotente; `salvar_resumo_run()` |
| `src/planilha.py` | substitui `salvar_resumo_final()` (órfã) por `escrever_resumo_primeira_aba()`; + `ler_evidencias_df()`; `_parsear_resumo()`; `NOME_ABA_RESUMO` |
| `src/controlador.py` | `processar_blocos_run()` retorna tupla `(evidencias, resumo)`; persiste resumo na Fase 1; grava aba no fim |
| `app.py` | captura tupla; expander de resumo em Processar; resumo + status de email persistentes em Resultados; usa `ler_evidencias_df`; remove `import pandas` ocioso |
| `scripts/testar_smtp.py` | novo — diagnóstico/teste isolado de SMTP (reusa `enviar_resultado`) |
| `tests/` | novo — `test_persistence_resumo.py`, `test_planilha_resumo.py`, `test_mailer.py`, `conftest.py` |

## Decisões de arquitetura
- **Aba Resumo escrita por último**: `adicionar_linhas_excel` faz `df.to_excel(caminho)` que
  reescreve o arquivo inteiro, apagando abas extras. Por isso `escrever_resumo_primeira_aba`
  roda no fim de `processar_blocos_run`, via openpyxl (`create_sheet("Resumo", 0)`).
- **Leitura resiliente**: `ler_evidencias_df()` escolhe a primeira aba que não seja "Resumo",
  mantendo compatibilidade com Excels antigos (aba única).
- **Persistência no banco**: coluna `resumo_processo` permite exibir o resumo de qualquer run
  (inclusive em sessões futuras) sem depender de arquivo de log global.
- **Email**: a lógica de envio já estava correta (STARTTLS/587). O problema era UX — confirmação
  efêmera dentro de `if submitted:`. Solução: persistir status em `session_state` e exibir em
  Resultados; e fornecer script de teste isolado.

## Ordem de implementação
`persistence.py` → `planilha.py` → `controlador.py` → `app.py` → `scripts/testar_smtp.py` → `tests/`

## Verificação
- `pytest tests/ -q` → 10 testes passando
- `ruff check` → sem novos erros (apenas F541/E741 pré-existentes)
- `py scripts/testar_smtp.py <email>` → envio real confirmado
- App: ativar SAC, processar, verificar expander + aba Resumo (1ª) + persistência ao trocar de aba
