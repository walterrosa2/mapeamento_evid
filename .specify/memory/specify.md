# Feature Specification: P2_mapeamento v3.2 — Correções de chunking, parsing e resumo

## Contexto
A execução `GRITTI_0306_V1` (v3.1) expôs três bugs: (1) documento dividido em 1 bloco gigante,
(2) resumo SAC truncado em 256 chars, (3) `ERRO_PARSE` no bloco 0 mesmo com a resposta cheia de
evidências. Todos diagnosticados na origem e corrigidos nesta versão. Além disso, o resumo passa
a ser mais completo (documentos-chave + quesitos) para alimentar as próximas etapas da esteira
de auditoria pericial.

---

## User Stories

### US-01: Delimitador de página configurável
Como perito, quero informar o marcador de página do meu TXT OCR (ex.: `---Página---`), para que
o documento seja dividido corretamente em blocos por página — sem virar um único bloco gigante.

### US-02: Resumo completo e útil
Como perito, quero um resumo do processo completo e estruturado (overview + documentos-chave +
quesitos periciais), que sirva de insumo para as etapas seguintes da auditoria.

### US-03: Extração robusta
Como perito, quero que a extração de evidências não falhe por formatação, para que nenhum bloco
com evidências retorne "0 evidências" por erro de parsing.

---

## Acceptance Criteria

### Chunking (US-01)
- [x] `detectar_paginas(texto, delimitador)` divide pelo delimitador literal configurável
- [x] Sem o delimitador no texto → retorna `[]` e o chamador usa fallback por caracteres (corrige a "página fantasma")
- [x] `dividir_por_paginas` subdivide blocos que excedam `MAX_CHARS_BLOCO` (teto 45.000)
- [x] UI tem campo "Delimitador de página" (default `---Página---`) repassado a `carregar_blocos`
- [x] Validado: 327 páginas → 34 blocos (maior 44.745 chars); fallback → 28 blocos

### Resumo (US-02)
- [x] `max_output_tokens=8192` e `thinking_config(thinking_budget=0)` no resumidor (corrige truncamento)
- [x] `PROMPT_RESUMIDOR` com TIPO DE AÇÃO, PARTES, OBJETO, PERÍODO, VALORES, **DOCUMENTOS-CHAVE**, **QUESITOS PERICIAIS**
- [x] `finish_reason` logado para diagnóstico
- [x] Validado: resumo real com 9.107 chars (antes 256), 25 documentos e 22 quesitos

### Extração (US-03)
- [x] `PROMPT_PADRAO` pede saída em **JSON** (array de objetos)
- [x] `extrair_campos` robusto: isola array, recupera objetos de JSON truncado, fallback Markdown
- [x] Validado: bloco 0 → 37 evidências (antes 0 / ERRO_PARSE)

---

## Edge Cases
- **Delimitador ausente / vazio**: fallback por caracteres (`dividir_em_blocos`).
- **Página única gigante**: subdividida pelo teto `MAX_CHARS_BLOCO`.
- **JSON truncado por limite de tokens**: `_recuperar_objetos_json` recupera os objetos completos.
- **Modelo responde com cercas ```json ou texto extra**: isolado pelo 1º `[` / último `]`.
- **Delimitador que começa com "página"**: `limpar_texto` só remove linhas iniciadas por "página";
  `---Página---` começa com `---`, então é preservado.
