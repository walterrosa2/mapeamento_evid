# Feature Specification: P2_mapeamento v2.0 — Persistência, Email e UX

## Contexto
O agente de mapeamento pericial processa documentos OCR (TXT) extraindo evidências via
Google Gemini e salva em Excel. A versão atual possui um arquivo Excel acumulativo sem
isolamento por execução, sem banco de dados, sem email e sem capacidade de retomada.

---

## User Stories

### US-01: Isolamento por Execução
Como perito judicial, quero que cada processamento gere seu próprio arquivo de evidências
para que processos diferentes nunca se misturem no mesmo Excel.

### US-02: Persistência de Execuções
Como perito judicial, quero que o sistema registre cada execução no banco de dados (mesmo
as incompletas) para que eu tenha histórico e rastreabilidade de tudo que foi processado.

### US-03: Retomada de Execução Incompleta
Como perito judicial, quero poder retomar uma execução que falhou ou foi interrompida a
partir do último bloco processado com sucesso, para não precisar reprocessar o documento
do zero caso haja queda de conexão ou erro de API.

### US-04: Notificação por Email
Como perito judicial, quero receber o Excel de evidências por email ao final do
processamento, para que eu possa iniciar o processamento e deixar a máquina trabalhar sem
precisar monitorar a tela.

### US-05: UX de Progresso em Tempo Real
Como perito judicial, quero ver em tempo real: quantos blocos foram processados, quantas
evidências foram extraídas até agora e uma estimativa de tempo restante, para ter
visibilidade do andamento mesmo em documentos grandes (50+ blocos).

### US-06: Histórico de Execuções
Como perito judicial, quero ver uma lista das execuções anteriores com status e poder
baixar o Excel de qualquer execução passada diretamente na interface.

---

## Acceptance Criteria

### Isolamento (US-01)
- [ ] Cada execução cria pasta `saida/runs/{run_id}/` com `evidencias.xlsx` exclusivo
- [ ] Excel de uma execução nunca contém linhas de outra execução
- [ ] Excel contém colunas adicionais: `run_id`, `arquivo_origem`, `data_processamento`
- [ ] Execuções antigas não são alteradas ao iniciar uma nova

### Persistência SQLite (US-02)
- [ ] Banco `saida/runs.db` criado automaticamente na primeira execução
- [ ] Tabela `runs` registra: run_id, nome, started_at, finished_at, status, total_blocos, blocos_processados, email_destino, arquivo_origem, erro_msg
- [ ] Tabela `run_items` registra: run_id, bloco_id, status (OK/ERRO_LLM/ERRO_PARSE), evidencias_count, erro_msg, processed_at
- [ ] Status INCOMPLETA é gravado se o processo for interrompido antes de finalizar
- [ ] Status COMPLETED é gravado ao finalizar com sucesso

### Retomada (US-03)
- [ ] UI oferece dropdown com execuções com status INCOMPLETA ou FAILED
- [ ] Ao retomar, blocos com status OK são pulados automaticamente
- [ ] Ao retomar, o Excel existente é reutilizado (novos blocos são adicionados)
- [ ] Contagem de progresso reflete apenas os blocos ainda pendentes

### Email (US-04)
- [ ] Campo de email opcional no formulário de início
- [ ] Ao finalizar com sucesso, envia email com Excel em anexo (best-effort)
- [ ] Falha no envio de email NÃO falha a execução (apenas warning na UI)
- [ ] Email contém: nome da execução, total de evidências extraídas, arquivo Excel anexado
- [ ] Configuração via .env: SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, SMTP_TLS

### UX de Progresso (US-05)
- [ ] Progress bar atualiza em tempo real (0-100%) baseado em blocos processados
- [ ] Contador "Bloco X de Y" atualizado a cada bloco
- [ ] Contador de evidências extraídas cumulativo atualizado a cada bloco
- [ ] ETA calculado como `(tempo_médio_por_bloco × blocos_restantes)`
- [ ] Cada bloco recebe indicador visual: ✅ OK, ⚠️ sem evidências, ❌ erro

### Histórico (US-06)
- [ ] Aba "Histórico" lista todas as execuções com: nome, data, status, total evidências
- [ ] Botão de download do Excel disponível para cada execução COMPLETED
- [ ] Execuções INCOMPLETA/FAILED exibem botão "Retomar" que pré-seleciona no formulário

---

## Edge Cases

### Processamento
- **Documento com 0 blocos**: Registrar run com status FAILED imediatamente, não iniciar loop
- **Todos os blocos retornam vazio**: Status COMPLETED com 0 evidências; email enviado com planilha vazia
- **Erro no bloco N (não de cota)**: Salvar bloco como ERRO_PARSE no run_items, continuar com próximo bloco
- **Erro 429 (cota Gemini)**: Retry exponencial já implementado em gemini_api.py, comportamento inalterado
- **Falha no meio do processamento**: run.status = INCOMPLETA, last checkpoint = último bloco OK

### Retomada
- **Run sem nenhum bloco OK**: Retomar equivale a iniciar do zero
- **Run com todos os blocos OK**: Retomar detecta que está COMPLETED, avisa usuário
- **Arquivo TXT original deletado**: Não é possível retomar (avisar ao usuário)
- **run_id inválido**: Ignorar e tratar como nova execução

### Email
- **Email não configurado (.env vazio)**: Pular envio silenciosamente (sem erro)
- **Email inválido**: Capturar exceção smtplib, registrar warning, NÃO falhar run
- **Anexo Excel > 25MB**: Enviar email sem anexo com aviso no corpo
- **Timeout SMTP**: 30s máximo, capturar exception, NÃO falhar run

### Banco de Dados
- **Banco corrompido**: Recriar banco, log de aviso, NÃO impedir processamento
- **Migração de schema**: Se tabelas não existem, criá-las (idempotente)
- **Runs RUNNING órfãs** (app fechou abruptamente): Tratar como INCOMPLETA ao listar histórico
