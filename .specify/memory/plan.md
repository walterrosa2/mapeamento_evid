# Plano Técnico: v3.2 — Correções de chunking, parsing e resumo

## Causas-raiz (confirmadas por inspeção)
1. **1 bloco gigante**: `detectar_paginas` criava "página fantasma" (num=0) com o texto inteiro
   quando não havia `[fls.]`, impedindo o fallback. Documento real usa `---Página---`.
2. **Resumo truncado (256 chars)**: thinking de `gemini-2.5-flash` consumia os 2048 tokens de saída.
3. **ERRO_PARSE**: separador Markdown de 24.916 chars concatenado à 1ª linha quebrava o parser.

## Arquivos afetados
| Arquivo | Mudança |
|---|---|
| `config.py` | + `DELIMITADOR_PAGINA_PADRAO`, `MAX_CHARS_BLOCO`, `MAX_TOKENS_RESUMO`; `PROMPT_PADRAO`→JSON; `PROMPT_RESUMIDOR` expandido |
| `src/leitor_txt.py` | `detectar_paginas`/`dividir_por_paginas`/`carregar_blocos` por delimitador literal + teto + fallback |
| `src/gemini_api.py` | resumidor: `max_output_tokens=MAX_TOKENS_RESUMO`, `thinking_budget=0`, log `finish_reason` |
| `src/controlador.py` | `extrair_campos` JSON-first + `_recuperar_objetos_json` + fallback Markdown |
| `app.py` | campo "Delimitador de página"; repassa a `carregar_blocos` |
| `tests/` | `test_leitor_paginas.py`, `test_parser_json.py` |

## Decisões de arquitetura
- **Delimitador configurável por execução** (não fixo): cada TXT OCR traz seu marcador.
- **Teto `MAX_CHARS_BLOCO`** garante blocos pequenos mesmo com poucas páginas grandes — reduz
  respostas gigantes e risco de truncamento de JSON.
- **JSON como formato primário** de extração; `parse_markdown_tabela` mantido só como fallback.
- **`thinking_budget=0`** no resumidor: saída determinística e completa; pode subir para ~512 se necessário.

## Verificação
- `pytest tests/ -q` → 20 testes (10 v3.1 + 10 v3.2).
- Chunking real: 327 págs → 34 blocos (maior 44.745); fallback → 28 blocos.
- Resumo real: 9.107 chars, com DOCUMENTOS-CHAVE (25) e QUESITOS (22).
- Extração real: bloco 0 → 37 evidências em JSON.
- `ruff check` → sem novos erros.
