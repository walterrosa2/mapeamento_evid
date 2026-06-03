# Plano Técnico: P2_mapeamento v3.0 — Chunking Inteligente e Contexto Global

## Estado de Entrada (baseline v2.x)
- `generation_config` com `max_output_tokens=32768` ✅ já implementado
- `gemini-2.5-flash` como modelo de extração ✅ já implementado
- `TAMANHO_BLOCO = 30000` chars ✅ já ajustado
- Pipeline v2: run_id, SQLite, mailer, progress_cb ✅ já implementado

---

## Decisões Arquiteturais

### 1. Page-Aware Chunking — Estratégia de Split

**Abordagem escolhida:** Split-by-marker com agrupamento.

O texto OCR contém marcadores `[fls. N]` (ex: `[fls. 97]`). A estratégia:
1. Preservar o texto bruto **sem** o `limpar_texto()` colapsado — manter quebras de linha para não perder posição dos marcadores.
2. Usar `re.split(r'(\[fls\.\s*\d+\])', texto)` para extrair segmentos indexados por página.
3. Agrupar `PAGINAS_POR_BLOCO` segmentos consecutivos em cada bloco.
4. Manter `limpar_texto()` aplicado **dentro** de cada bloco (não no texto global).

**Por que não alterar `carregar_blocos()` internamente apenas?**
A assinatura pública `carregar_blocos(nome_arquivo)` é chamada em `controlador.py` e `app.py`. Ela se mantém — internamente passa a chamar `dividir_por_paginas()` se houver marcadores, ou `dividir_em_blocos()` como fallback.

**Novo parâmetro `texto_completo`:**
`carregar_blocos()` retornará também o texto completo (não chunked) via função separada `carregar_texto_completo()` para uso pelo Agente 1 (SAC).

### 2. SAC — Agente 1: Resumidor

**Fluxo:**
```
texto_completo → truncar se > 600k tokens (~2.4M chars) → prompt_resumidor → gemini-2.5-flash → resumo estruturado
```

**Por que mesmo modelo (`gemini-2.5-flash`) e não `flash-lite`?**
O resumidor recebe o documento COMPLETO (potencialmente 200k-500k chars). O `flash-lite` teve problemas de MAX_TOKENS nesta mesma carga. `gemini-2.5-flash` com 1M de contexto de entrada e foco numa saída curta (2048 tokens) é a escolha segura.

**Prompt do Resumidor** (separado do `PROMPT_PADRAO`):
```
Você é um assistente jurídico especializado. Analise o processo judicial completo abaixo
e retorne EXCLUSIVAMENTE o seguinte resumo estruturado, sem texto adicional:

TIPO DE AÇÃO: [ex: Reclamação Trabalhista, Ação de Indenização, etc.]
PARTES:
  - Polo Ativo: [Nome / Razão Social]
  - Polo Passivo: [Nome / Razão Social / CNPJ]
OBJETO: [2-3 linhas descrevendo o pedido principal]
PERÍODO RELEVANTE: [datas de início e fim do período discutido]
TIPOS DE DOCUMENTOS MENCIONADOS: [lista separada por vírgula]
VALORES EM DISPUTA: [se identificados, caso contrário: Não identificado]

Se algum campo não puder ser identificado, escreva: Não identificado.
```

**Saída salva em** `logs/resumo_processo.txt` (auditoria).

### 3. SAC — Agente 2: Injeção de Contexto

O contexto é injetado **entre** o `PROMPT_PADRAO` e o conteúdo do bloco:

```
{PROMPT_PADRAO}

[CONTEXTO DO PROCESSO]
{resumo}
[FIM DO CONTEXTO]

{texto_do_bloco}
```

Isso garante que o modelo lê as instruções de extração, depois o contexto global, depois o bloco — ordem cognitiva correta.

### 4. Controlador — Orquestração das 2 Fases

```python
def processar_blocos_run(
    run_id, blocos, arquivo_origem="",
    skip_ids=None, progress_cb=None,
    texto_completo="", usar_sac=False      # ← novos params
):
    contexto_global = ""
    if usar_sac and texto_completo:
        # Fase 1
        progress_cb(-1, total, 0, "resumindo")  # sinal especial para UI
        contexto_global = gerar_resumo_processo(texto_completo)

    # Fase 2 — loop existente (recebe contexto_global)
    for i, bloco in enumerate(blocos):
        resposta = enviar_bloco_para_gemini(bloco, bloco_id=i,
                                            contexto_global=contexto_global)
        ...
```

O `bloco_id=-1` é o sinal para a UI entrar no modo "Fase 1".

### 5. App — Progresso em 2 Fases

Quando SAC está ativo:
- Fase 1: `st.status("🔍 Fase 1/2: Gerando contexto do processo...")` com spinner
- Fase 2: progress bar normal (0–100% sobre os blocos)
- ETA começa a ser calculado apenas na Fase 2

---

## Arquitetura de Módulos v3.0

```
leitor_txt.py      [REFACTOR]
  ├── ler_arquivo_txt()              → sem alteração
  ├── limpar_texto()                 → sem alteração
  ├── carregar_texto_completo()      → NOVA: retorna texto bruto sem chunking
  ├── detectar_paginas()             → NOVA: split por [fls. N], retorna list[tuple(num, texto)]
  ├── dividir_por_paginas()          → NOVA: agrupa N páginas por bloco
  ├── dividir_em_blocos()            → sem alteração (fallback)
  └── carregar_blocos()              → REFACTOR interno: tenta page-aware, fallback char-based

gemini_api.py      [ADDITIVE]
  ├── enviar_bloco_para_gemini()     → adicionar param contexto_global=""
  └── gerar_resumo_processo()        → NOVA função

config.py          [ADDITIVE]
  ├── PAGINAS_POR_BLOCO = 10         → NOVA constante
  └── PROMPT_RESUMIDOR               → NOVA constante (prompt do agente 1)

controlador.py     [EXTEND]
  └── processar_blocos_run()         → adicionar params texto_completo, usar_sac

app.py             [EXTEND]
  ├── Checkbox SAC na Tab 1          → NOVA
  ├── Progress Fase 1/Fase 2         → NOVA lógica no callback
  └── carregar_texto_completo()      → chamar ao fazer upload
```

---

## Ordem de Implementação

```
1. config.py          → constantes novas (sem dependências)
2. leitor_txt.py      → refactor de chunking (sem dependências externas)
3. gemini_api.py      → gerar_resumo_processo() + param contexto_global
4. controlador.py     → orquestração 2 fases
5. app.py             → UI: checkbox SAC + progresso 2 fases
```

---

## Riscos e Mitigações

| Risco | Probabilidade | Mitigação |
|---|---|---|
| Documento sem `[fls.]` quebra chunking | Baixa | Fallback automático para char-based com warning |
| Resumidor timeout em docs muito grandes | Média | Timeout 120s + best-effort (continua sem SAC) |
| Contexto injetado aumenta prompt e estoura 32k de saída | Baixa | Resumo é < 500 chars; impacto mínimo no budget de saída |
| Retomada de run SAC gera resumo diferente | Baixa | Aceito — resumo é regenerado, mas extração será consistente |
| `[fls.]` malformado (`[fls.abc]`) rompe regex | Baixa | Regex só captura `\d+`; malformados são ignorados |
