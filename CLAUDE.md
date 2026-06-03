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
```

<!-- SPECKIT START -->
## Plano Ativo: v3.0 — Chunking Inteligente e Contexto Global

### Objetivo
Melhorar a qualidade da extração de evidências com dois mecanismos ortogonais:
1. **Page-Aware Chunking**: dividir por `[fls. N]` em vez de caracteres
2. **SAC (Summary-Augmented Chunking)**: pipeline de 2 agentes onde o Agente 1
   gera um resumo do processo completo e o Agente 2 usa esse resumo como contexto
   em cada bloco de extração

### Arquivos afetados
| Arquivo | Mudança |
|---|---|
| `config.py` | + `PAGINAS_POR_BLOCO`, `PROMPT_RESUMIDOR`, `MAX_CHARS_RESUMIDOR` |
| `leitor_txt.py` | + `carregar_texto_completo()`, `detectar_paginas()`, `dividir_por_paginas()` |
| `gemini_api.py` | + `gerar_resumo_processo()`, param `contexto_global` em `enviar_bloco_para_gemini()` |
| `controlador.py` | + params `texto_completo`, `usar_sac` em `processar_blocos_run()` |
| `app.py` | + checkbox SAC, progresso 2 fases, ETA só na Fase 2 |

### Ordem de implementação
`config.py` → `leitor_txt.py` → `gemini_api.py` → `controlador.py` → `app.py`

### Spec/Plan/Tasks
- `.specify/memory/specify.md`
- `.specify/memory/plan.md`
- `.specify/memory/tasks.md`
<!-- SPECKIT END -->
