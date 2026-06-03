# Feature Specification: P2_mapeamento v3.0 — Chunking Inteligente e Contexto Global

## Contexto
O pipeline atual divide o documento OCR em blocos de tamanho fixo (30k chars) sem respeitar
os limites de página, e envia cada bloco ao Gemini sem nenhum conhecimento sobre o processo
como um todo. Isso causa dois problemas:
1. Evidências que cruzam a fronteira de dois blocos podem ser perdidas ou duplicadas.
2. O modelo classifica evidências sem saber o tipo de ação, as partes ou o período — levando
   a classificações genéricas e menor precisão.

Esta versão resolve ambos com duas melhorias ortogonais que podem ser ativadas
independentemente.

---

## Funcionalidades

### F-01: Page-Aware Chunking
Substituir o corte por caracteres pelo corte nos marcadores `[fls. N]` presentes no texto
OCR, agrupando N páginas por bloco (configurável). Nenhuma evidência será cortada no meio
de uma página.

### F-02: Summary-Augmented Chunking (SAC) — Pipeline de 2 Agentes
**Agente 1 (Resumidor):** recebe o texto completo do processo numa única chamada ao Gemini
e retorna um resumo estruturado: tipo de ação, partes, objeto, período, tipos de documentos.

**Agente 2 (Extrator):** cada bloco enviado ao Gemini recebe o resumo do Agente 1 injetado
no início do prompt como contexto global, melhorando a classificação das evidências.

A ativação do SAC é opcional (toggle na UI e flag no controlador).

---

## User Stories

### US-01: Chunking por Página
Como perito judicial, quero que os blocos de análise respeitem os limites de página do
processo, para que uma NF que aparece entre as páginas 10 e 11 seja analisada completa
em um único bloco.

### US-02: Resumo Automático do Processo
Como perito judicial, quero que o sistema leia o processo completo e gere um resumo das
partes e do objeto da ação antes de iniciar a extração, para que as evidências sejam
classificadas com maior precisão contextual.

### US-03: Contexto Global na Extração
Como perito judicial, quero que o agente extrator "saiba" com antecedência quem são as
partes e qual é o tipo da ação, para evitar que evidências de terceiros sejam classificadas
incorretamente como evidências diretas do processo.

### US-04: Configurabilidade
Como perito judicial, quero poder ajustar o número de páginas por bloco e ativar/desativar
o SAC pela interface, para adaptar o processamento ao tamanho e complexidade do processo.

---

## Acceptance Criteria

### Page-Aware Chunking (F-01)
- [ ] `leitor_txt.py` detecta marcadores `[fls. N]` com regex `\[fls\.\s*\d+\]`
- [ ] Texto é dividido **nos** marcadores `[fls.]`, preservando o marcador no início de cada página
- [ ] Páginas são agrupadas em blocos de `PAGINAS_POR_BLOCO` (padrão: 10)
- [ ] Se o documento não contiver nenhum `[fls.]`, o sistema faz fallback silencioso para o chunking por caracteres atual, com warning no log
- [ ] `config.py` expõe `PAGINAS_POR_BLOCO: int = 10` como constante configurável
- [ ] A função `carregar_blocos()` existente mantém a mesma assinatura externa (retrocompatibilidade com `controlador.py`)
- [ ] Log registra: total de páginas detectadas, total de blocos gerados, páginas por bloco

### SAC — Agente 1: Resumidor (F-02)
- [ ] Nova função `gerar_resumo_processo(texto_completo: str) -> str` em `gemini_api.py`
- [ ] Usa o mesmo modelo (`gemini-2.5-flash`) com `max_output_tokens=2048`
- [ ] Prompt do resumidor retorna SEMPRE o seguinte formato estruturado (mesmo que campos sejam "Não identificado"):
  ```
  TIPO DE AÇÃO: ...
  PARTES:
    - Polo Ativo: ...
    - Polo Passivo: ...
  OBJETO: ...
  PERÍODO RELEVANTE: ...
  TIPOS DE DOCUMENTOS MENCIONADOS: ...
  VALORES EM DISPUTA: ...
  ```
- [ ] Se a chamada falhar (timeout, 503, etc.), retorna string vazia e pipeline continua sem SAC (best-effort)
- [ ] Resumo é salvo em `logs/resumo_processo.txt` para auditoria
- [ ] Log registra: tempo de geração do resumo, tamanho do texto completo enviado

### SAC — Agente 2: Injeção de Contexto (F-02)
- [ ] `enviar_bloco_para_gemini()` aceita parâmetro opcional `contexto_global: str = ""`
- [ ] Quando `contexto_global` não está vazio, é injetado no prompt antes do conteúdo do bloco no formato:
  ```
  [CONTEXTO DO PROCESSO]
  {contexto_global}
  [FIM DO CONTEXTO]
  ```
- [ ] Blocos enviados com contexto são identificados no log: `"Bloco X com contexto global (N chars)"`
- [ ] `bloco_enviado_XXX.txt` de auditoria inclui o contexto injetado

### Pipeline e UI (F-01 + F-02)
- [ ] `controlador.py` aceita `texto_completo: str = ""` e `usar_sac: bool = False` em `processar_blocos_run()`
- [ ] Quando `usar_sac=True` e `texto_completo` não está vazio: gera resumo antes do loop de blocos
- [ ] `app.py` exibe progresso em 2 fases quando SAC ativo: "Fase 1/2: Gerando contexto..." e "Fase 2/2: Extraindo evidências..."
- [ ] Checkbox "Usar contexto global (SAC)" na UI, desativado por padrão
- [ ] ETA da Fase 2 desconsidera o tempo da Fase 1

---

## Edge Cases

### Page-Aware Chunking
- **Documento sem `[fls.]`**: fallback para chunking por caracteres com `logger.warning`
- **Marcador malformado (`[fls.abc]`)**: ignorar e continuar; não contar como página
- **Última página incompleta**: incluída no último bloco normalmente
- **`PAGINAS_POR_BLOCO = 1`**: um bloco por página — válido, cria muitos blocos pequenos
- **Bloco resultante maior que 30k chars**: permitido (o modelo suporta); logar aviso se > 60k chars

### SAC — Resumidor
- **Documento muito grande para o contexto do modelo (> 800k tokens)**: truncar o texto enviado ao resumidor em 600k tokens com aviso no log; a extração ainda usa o texto original completo por bloco
- **Resumo retornado vazio ou malformado**: log de warning, continuar sem SAC (degradação graciosa)
- **Timeout na chamada do resumidor (> 120s)**: capturar, log de error, continuar sem SAC
- **Resumo com PII (CPF, CNPJ)**: aceito — o resumo é interno ao processamento e não é exibido publicamente

### Pipeline
- **SAC ativo mas texto_completo não fornecido**: desativar SAC silenciosamente, log de warning
- **Retomada de execução com SAC**: resumo é regenerado na retomada (não cacheado entre runs)
- **SAC ativo + chunking por caracteres (fallback)**: ambos podem coexistir sem conflito
