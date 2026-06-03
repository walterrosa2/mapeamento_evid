# Tasks: P2_mapeamento v3.0 — Chunking Inteligente e Contexto Global

## Status Global: 📋 Aguardando Implementação

---

## Bloco 1: config.py — Novas Constantes
> Estimativa: 15min | Risco: Mínimo | Sem dependências

- [ ] T01 — Adicionar `PAGINAS_POR_BLOCO: int = 10` com comentário explicativo
- [ ] T02 — Adicionar `PROMPT_RESUMIDOR` com o prompt estruturado do Agente 1 (ver plan.md)
- [ ] T03 — Adicionar `MAX_CHARS_RESUMIDOR: int = 2_400_000` (limite de truncagem ~600k tokens)

**Done quando:** `from config import PAGINAS_POR_BLOCO, PROMPT_RESUMIDOR` importa sem erro.

---

## Bloco 2: leitor_txt.py — Page-Aware Chunking
> Estimativa: 1h | Risco: Baixo | Depende de: T01

- [ ] T04 — Adicionar `carregar_texto_completo(nome_arquivo) -> str`: lê e retorna o texto bruto sem nenhum chunking nem limpeza (para uso pelo Agente 1)
- [ ] T05 — Adicionar `detectar_paginas(texto: str) -> list[tuple[int, str]]`: usa `re.split(r'(\[fls\.\s*\d+\])', texto)` para retornar lista de `(num_pagina, texto_pagina)`; ignora segmentos que não são `[fls. N]`
- [ ] T06 — Adicionar `dividir_por_paginas(texto: str, paginas_por_bloco: int) -> list[str]`: chama `detectar_paginas()`, agrupa N páginas por bloco, aplica `limpar_texto()` dentro de cada bloco
- [ ] T07 — Refatorar `carregar_blocos(nome_arquivo)` para: (1) chamar `detectar_paginas()`, (2) se páginas > 0 usar `dividir_por_paginas()`, (3) senão `logger.warning` + fallback para `dividir_em_blocos()` atual
- [ ] T08 — Garantir que log registra: `"Documento: X páginas detectadas → Y blocos de Z páginas"`
- [ ] T09 — Garantir fallback: se `detectar_paginas()` retornar lista vazia, log `"⚠️ Nenhum marcador [fls.] detectado — usando chunking por caracteres"` e chamar `dividir_em_blocos()`

**Done quando:** `carregar_blocos("processo.txt")` retorna blocos respeitando páginas; `carregar_texto_completo()` retorna texto bruto.

---

## Bloco 3: gemini_api.py — Resumidor + Contexto
> Estimativa: 45min | Risco: Baixo | Depende de: T02, T03

- [ ] T10 — Adicionar parâmetro `contexto_global: str = ""` à assinatura de `enviar_bloco_para_gemini()`
- [ ] T11 — Modificar montagem do `prompt_final` em `enviar_bloco_para_gemini()`: quando `contexto_global` não está vazio, inserir bloco `[CONTEXTO DO PROCESSO]\n{contexto_global}\n[FIM DO CONTEXTO]\n\n` entre `PROMPT_PADRAO` e `texto_bloco`
- [ ] T12 — Atualizar `salvar_bloco_enviado()` para que o arquivo de auditoria inclua o contexto quando presente (já está implícito via `prompt_final`, verificar)
- [ ] T13 — Adicionar `logger.info` quando contexto é injetado: `"Bloco {id} com contexto global ({N} chars)"`
- [ ] T14 — Implementar `gerar_resumo_processo(texto_completo: str) -> str` com:
  - Truncagem: se `len(texto_completo) > MAX_CHARS_RESUMIDOR`, truncar e logar warning
  - Usar `PROMPT_RESUMIDOR` de `config.py`
  - `max_output_tokens=2048` no `GenerateContentConfig`
  - Mesmo retry pattern de `enviar_bloco_para_gemini()` (max 3 tentativas)
  - Em caso de falha: retornar `""` (best-effort)
  - Salvar resultado em `logs/resumo_processo.txt`
  - Log: `"✅ Resumo gerado em {t:.1f}s ({N} chars)"` ou `"⚠️ Falha ao gerar resumo — SAC desativado"`

**Done quando:** chamada manual de `gerar_resumo_processo(texto)` retorna string estruturada com campos TIPO DE AÇÃO, PARTES, etc.

---

## Bloco 4: controlador.py — Orquestração 2 Fases
> Estimativa: 30min | Risco: Médio | Depende de: T10-T14

- [ ] T15 — Adicionar imports: `from src.gemini_api import gerar_resumo_processo` e `from src.leitor_txt import carregar_texto_completo`
- [ ] T16 — Adicionar parâmetros à assinatura de `processar_blocos_run()`: `texto_completo: str = ""` e `usar_sac: bool = False`
- [ ] T17 — Implementar Fase 1 no início de `processar_blocos_run()`: se `usar_sac and texto_completo`, chamar `gerar_resumo_processo(texto_completo)` e armazenar em `contexto_global`; chamar `progress_cb(-1, total_blocos, 0, "resumindo")` antes da chamada
- [ ] T18 — Passar `contexto_global` para cada chamada de `enviar_bloco_para_gemini()` no loop
- [ ] T19 — Garantir que `processar_todos_os_blocos()` (wrapper legado) não é alterado e continua funcional

**Done quando:** `processar_blocos_run(..., usar_sac=True, texto_completo=txt)` executa Fase 1 antes do loop.

---

## Bloco 5: app.py — UI e Progresso 2 Fases
> Estimativa: 1h | Risco: Baixo | Depende de: T15-T18

- [ ] T20 — Adicionar `usar_sac = st.checkbox("🧠 Usar contexto global (SAC)", value=False, help="Gera um resumo do processo antes da extração para melhorar a classificação das evidências.")` no formulário da Tab 1
- [ ] T21 — Ao fazer upload do arquivo, chamar `carregar_texto_completo()` e salvar em `st.session_state["texto_completo"]`
- [ ] T22 — Passar `texto_completo=st.session_state.get("texto_completo", "")` e `usar_sac=usar_sac` para `processar_blocos_run()`
- [ ] T23 — Atualizar `_progress_cb` para tratar `bloco_id == -1` como sinal de Fase 1: exibir `st.status("🔍 Fase 1/2: Gerando contexto do processo...")` e não atualizar progress bar nem ETA
- [ ] T24 — Quando SAC ativo e Fase 1 concluída, exibir `st.success("✅ Contexto gerado. Iniciando extração...")` antes da Fase 2
- [ ] T25 — ETA deve ser calculado apenas a partir do primeiro bloco real (bloco_id >= 0), ignorando tempo da Fase 1
- [ ] T26 — Se `usar_sac=True` e resumo falhou (best-effort), exibir `st.warning("⚠️ Contexto global não disponível — extração continua sem SAC.")` e prosseguir normalmente

**Done quando:** checkbox SAC aparece na UI; quando ativado, UI mostra "Fase 1/2" antes da progress bar normal.

---

## Bloco 6: Validação
> Estimativa: 30min | Depende de: todos os blocos anteriores

- [ ] T27 — Smoke test F-01: processar documento com `[fls.]` → verificar no log "X páginas detectadas → Y blocos"
- [ ] T28 — Smoke test F-01 fallback: processar documento sem `[fls.]` → verificar warning no log e chunking por caracteres
- [ ] T29 — Smoke test F-02: ativar SAC → verificar `logs/resumo_processo.txt` gerado e campos estruturados presentes
- [ ] T30 — Smoke test F-02 injeção: verificar `logs/bloco_enviado_001.txt` contém `[CONTEXTO DO PROCESSO]`
- [ ] T31 — Smoke test integração: run completa com SAC ativo → comparar número de evidências com run sem SAC no mesmo documento
- [ ] T32 — Testar fallback SAC: simular falha do resumidor (desconectar API temporariamente) → verificar que extração continua e warning é exibido na UI
