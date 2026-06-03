# CLAUDE.md — P2_mapeamento

## Stack
- Python 3.13 + Streamlit + Google GenAI SDK (`google-genai`)
- Modelo de extração: `gemini-2.5-flash` | max_output_tokens: 32768
- Persistência: SQLite (`saida/runs.db`) + Excel por run (`saida/runs/{run_id}/evidencias.xlsx`)
- Deploy: Docker + Ubuntu VPS (porta 8515)

## Estrutura Principal
```
app.py              — UI Streamlit (abas: Processar, Progresso, Resultados, Histórico)
config.py           — Constantes globais (API key, paths, prompts, chunking)
src/
  leitor_txt.py     — Leitura e chunking do TXT
  gemini_api.py     — Chamadas ao Gemini (extração + resumidor)
  controlador.py    — Pipeline de processamento (run_id, skip_ids, progress_cb)
  planilha.py       — Escrita Excel por run
  persistence.py    — SQLite (runs, run_items)
  mailer.py         — Email best-effort (smtplib)
scripts/
  reenviar_blocos_erro.py  — Diagnóstico: reenvio isolado de blocos com erro
  testar_smtp.py           — Diagnóstico: teste isolado de envio de email (SMTP)
```

<!-- SPECKIT START -->
## Plano Ativo: v3.2 — Correções de chunking, parsing e resumo

### Objetivo
Corrigir três bugs da execução real e enriquecer o resumo para a esteira pericial:
1. **Chunking**: delimitador de página **configurável** na UI (default `---Página---`) + teto de
   tamanho por bloco + fallback char-based (corrige o "1 bloco gigante de 837K chars")
2. **Resumo**: `thinking_budget=0` + `max_output_tokens=8192` (corrige truncamento em 256 chars);
   prompt expandido com **DOCUMENTOS-CHAVE** e **QUESITOS PERICIAIS**
3. **Extração**: saída em **JSON** + parser robusto (corrige `ERRO_PARSE` com tabela Markdown malformada)

### Arquivos afetados
| Arquivo | Mudança |
|---|---|
| `config.py` | + `DELIMITADOR_PAGINA_PADRAO`, `MAX_CHARS_BLOCO`, `MAX_TOKENS_RESUMO`; `PROMPT_PADRAO`→JSON; `PROMPT_RESUMIDOR` expandido |
| `leitor_txt.py` | chunking por delimitador literal + teto `MAX_CHARS_BLOCO` + fallback |
| `gemini_api.py` | resumidor: mais tokens + `thinking_budget=0` + log `finish_reason` |
| `controlador.py` | `extrair_campos` JSON-first + `_recuperar_objetos_json` + fallback Markdown |
| `app.py` | campo "Delimitador de página" repassado a `carregar_blocos` |
| `tests/` | + `test_leitor_paginas.py`, `test_parser_json.py` |

### Validação (API real)
327 págs → 34 blocos · resumo 9.107 chars (25 docs + 22 quesitos) · bloco 0 → 37 evidências JSON · pytest 20/20

### Histórico
- v3.1 (Resumo visível + email), v3.0 (SAC), v2.x: ver `.specify/archive/`

### Spec/Plan/Tasks
- `.specify/memory/specify.md`
- `.specify/memory/plan.md`
- `.specify/memory/tasks.md`
<!-- SPECKIT END -->
