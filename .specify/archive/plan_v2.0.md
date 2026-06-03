# Plano Técnico: P2_mapeamento v2.0

## Decisões Arquiteturais

### 1. Persistência: SQLite com WAL
- **Por quê SQLite?** Projeto local/Docker sem necessidade de servidor. Zero config. Mesma escolha do P1_catalogador (validado em produção).
- **WAL mode**: Evita corrupção em crashes (PRAGMA journal_mode=WAL).
- **Caminho**: `saida/runs.db` (mesma pasta do output Excel, fácil backup).

### 2. Isolamento de Excel por Run
- **Pasta por run**: `saida/runs/{run_id}/evidencias.xlsx`
- **Motivo**: Elimina mistura de processos diferentes. Excel antigo nunca é tocado.
- **Retrocompatibilidade**: `evidencias_extraidas.xlsx` legado pode coexistir (não será deletado).

### 3. Email: best-effort com smtplib (stdlib)
- **Por quê smtplib?** Zero dependências novas. Mesma escolha do P1_catalogador.
- **Factory pattern**: `smtp_factory` injetável para testes unitários.
- **Timeout**: 30s para evitar bloqueio da UI.

### 4. UX de Progresso: Callback pattern
- **Por quê callback?** Desacopla o pipeline da UI. `controlador.py` passa callback recebido de `app.py`.
- **Dados do callback**: `(bloco_id, total_blocos, evidencias_count, status)`
- **ETA**: Calculado em `app.py` com `time.monotonic()`.

### 5. Retomada: Skip por bloco_id
- `persistence.get_processed_block_ids(run_id)` → `set[int]`
- Pipeline verifica `if bloco_id in processed_ids: continue`
- Excel existente da run é carregado (não recriado)

---

## Arquitetura de Módulos

```
P2_mapeamento/
├── app.py                    [ALTERAR] — UI completa v2
├── config.py                 [ALTERAR] — add SMTP_*, CAMINHO_RUNS
├── src/
│   ├── __init__.py           [SEM ALTERAÇÃO]
│   ├── controlador.py        [ALTERAR] — receber run_id + progress_cb
│   ├── gemini_api.py         [SEM ALTERAÇÃO]
│   ├── leitor_txt.py         [SEM ALTERAÇÃO]
│   ├── planilha.py           [ALTERAR] — schema por run + novas colunas
│   ├── persistence.py        [NOVO] — SQLite runs + run_items
│   └── mailer.py             [NOVO] — SMTP best-effort
├── saida/
│   ├── runs.db               [GERADO] — banco SQLite
│   ├── runs/                 [GERADO] — pasta com subpastas por run_id
│   │   └── {run_id}/
│   │       └── evidencias.xlsx
│   └── evidencias_extraidas.xlsx  [LEGADO — não tocar]
├── .env.example              [ALTERAR] — add SMTP vars
└── requirements.txt          [SEM ALTERAÇÃO — smtplib é stdlib]
```

---

## Schema SQLite

```sql
CREATE TABLE IF NOT EXISTS runs (
    run_id        TEXT PRIMARY KEY,
    nome          TEXT NOT NULL,
    arquivo_origem TEXT,
    started_at    TEXT NOT NULL,
    finished_at   TEXT,
    status        TEXT NOT NULL DEFAULT 'RUNNING',
    -- RUNNING | COMPLETED | FAILED | INCOMPLETA
    total_blocos  INTEGER,
    blocos_processados INTEGER DEFAULT 0,
    total_evidencias   INTEGER DEFAULT 0,
    email_destino TEXT,
    erro_msg      TEXT
);

CREATE TABLE IF NOT EXISTS run_items (
    run_id         TEXT NOT NULL,
    bloco_id       INTEGER NOT NULL,
    status         TEXT NOT NULL,
    -- OK | ERRO_LLM | ERRO_PARSE
    evidencias_count INTEGER DEFAULT 0,
    erro_msg       TEXT,
    processed_at   TEXT NOT NULL,
    PRIMARY KEY (run_id, bloco_id)
);

CREATE INDEX IF NOT EXISTS idx_runs_status ON runs(status);
CREATE INDEX IF NOT EXISTS idx_items_run   ON run_items(run_id);
```

---

## Schema Excel (colunas adicionadas)

### Colunas atuais (mantidas):
- Tipo de Evidência, Trecho, Conteúdo, Resumo, Referência

### Novas colunas (adicionadas ao final):
- `Run ID` — UUID da execução
- `Arquivo Origem` — nome do arquivo TXT processado
- `Data Processamento` — ISO timestamp da extração

---

## Fluxo Completo v2

```
app.py: Formulário (nome, email, arquivo, retomar?)
    │
    ▼
persistence.criar_run(nome, email, arquivo) → run_id
    │
    ├─ [se retomar] persistence.get_processed_block_ids(run_id) → skip_set
    │
    ▼
controlador.processar_blocos(run_id, blocos, skip_set, progress_cb)
    │
    ├─ Para cada bloco:
    │   ├─ [se bloco_id in skip_set] → pular
    │   ├─ persistence.atualizar_run_status(RUNNING, blocos_processados)
    │   ├─ gemini_api.enviar_bloco_para_gemini(bloco) → resposta
    │   ├─ controlador.extrair_campos(resposta) → evidencias
    │   ├─ planilha.adicionar_linhas(run_id, evidencias, arquivo_origem)
    │   ├─ persistence.salvar_run_item(run_id, bloco_id, status, count)
    │   └─ progress_cb(bloco_id, total, count_acumulado, status)
    │
    ├─ [sucesso] persistence.finalizar_run(run_id, COMPLETED)
    │   └─ mailer.enviar_resultado(email, run_nome, xlsx_path, resumo)
    │
    └─ [exceção] persistence.finalizar_run(run_id, INCOMPLETA, erro_msg)
```

---

## Interface Streamlit v2 — Estrutura de Abas

```
[Tab 1: Processar]
  ├─ Form: Nome da execução (obrigatório)
  ├─ Form: Email para notificação (opcional)
  ├─ Upload .txt
  ├─ Dropdown: "Retomar execução?" (lista runs INCOMPLETA/FAILED)
  └─ Botão: Iniciar / Retomar

[Tab 2: Progresso] ← aparece durante processamento
  ├─ Progress bar (%)
  ├─ Status: "Bloco X de Y | N evidências extraídas | ETA: Xmin Ys"
  ├─ Lista de blocos com status individual (✅/⚠️/❌)
  └─ Log de evidências em tempo real

[Tab 3: Resultados] ← mostra run atual
  ├─ Métricas: total evidências, tipos únicos, duração
  ├─ Dataframe completo
  ├─ Download Excel
  └─ Gráfico por tipo

[Tab 4: Histórico]
  ├─ Tabela de todas as runs (nome, data, status, evidências)
  ├─ Botão download por run
  └─ Botão "Retomar" para runs incompletas
```

---

## Ordem de Implementação

1. `src/persistence.py` — base de tudo (sem dependências internas)
2. `src/mailer.py` — independente, testável isolado
3. `src/planilha.py` — adicionar suporte a run_id e caminho por run
4. `config.py` — adicionar constantes SMTP e CAMINHO_RUNS
5. `src/controlador.py` — integrar persistence + progress_cb
6. `app.py` — UI completa v2 (usa tudo acima)
7. `.env.example` — documentar variáveis SMTP
