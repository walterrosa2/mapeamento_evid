# Tasks: P2_mapeamento v3.2 — Correções de chunking, parsing e resumo

## Status Global: ✅ Implementado e validado (pytest 20/20; chunking/resumo/extração confirmados via API)

---

## Bloco 1: config.py
- [x] T01 — `DELIMITADOR_PAGINA_PADRAO = "---Página---"`
- [x] T02 — `MAX_CHARS_BLOCO = 45000` (teto de bloco)
- [x] T03 — `MAX_TOKENS_RESUMO = 8192`
- [x] T04 — `PROMPT_PADRAO`: seção de formato Markdown → **JSON** (regras de validação mantidas)
- [x] T05 — `PROMPT_RESUMIDOR`: + DOCUMENTOS-CHAVE e QUESITOS PERICIAIS

## Bloco 2: leitor_txt.py
- [x] T06 — `detectar_paginas(texto, delimitador)` por split literal; `[]` se ausente
- [x] T07 — `dividir_por_paginas` agrupa + subdivide acima de `MAX_CHARS_BLOCO`
- [x] T08 — `carregar_blocos(nome, delimitador)` com fallback char-based
- [x] T09 — log: "N páginas detectadas (delim) → M blocos"

## Bloco 3: gemini_api.py
- [x] T10 — resumidor: `max_output_tokens=MAX_TOKENS_RESUMO` + `thinking_config(thinking_budget=0)`
- [x] T11 — logar `finish_reason` do resumo

## Bloco 4: controlador.py
- [x] T12 — `extrair_campos`: isola array JSON (1º `[` / último `]`), parseia
- [x] T13 — `_recuperar_objetos_json`: recupera objetos de JSON truncado
- [x] T14 — fallback `parse_markdown_tabela` mantido

## Bloco 5: app.py
- [x] T15 — campo "Delimitador de página" (default `---Página---`)
- [x] T16 — repassar delimitador a `carregar_blocos`

## Bloco 6: tests/
- [x] T17 — `test_leitor_paginas.py` (detecção, fallback, teto)
- [x] T18 — `test_parser_json.py` (JSON puro, cercas, truncado, normalização, fallback MD)

## Bloco 7: Validação
- [x] T19 — `pytest tests/ -q` → 20 passed
- [x] T20 — Chunking real: 34 blocos (sem gigantes); fallback 28 blocos
- [x] T21 — Resumo real: 9.107 chars com documentos-chave + quesitos
- [x] T22 — Extração real: bloco 0 → 37 evidências (era ERRO_PARSE)
- [x] T23 — `ruff check` sem novos erros
