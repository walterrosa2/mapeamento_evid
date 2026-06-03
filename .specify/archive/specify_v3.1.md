# Feature Specification: P2_mapeamento v3.1 — Resumo SAC visível e confirmação de email

## Contexto
A v3.0 introduziu o SAC (Summary-Augmented Chunking): o Gemini gera um resumo do processo
(Agente 1) que é injetado como contexto em cada bloco de extração (Agente 2). Esse resumo,
porém, só era salvo num log global e nunca chegava ao usuário nem ao Excel. Além disso, o
envio de email ao final não era confirmado de forma confiável na tela (a mensagem sumia ao
trocar de aba do Streamlit).

Esta versão torna o resumo visível e auditável, e confirma/diagnostica o envio de email.

---

## User Stories

### US-01: Resumo visível na tela
Como perito, quero ver o resumo do processo (gerado pelo SAC) na interface após o
processamento e ao revisitar os resultados, para validar o contexto que orientou a extração.

### US-02: Resumo no Excel
Como perito, quero que o Excel final tenha o resumo do processo como **primeira aba**, para
que quem abrir o arquivo entenda o contexto antes de ver as evidências.

### US-03: Confirmação de envio de email
Como perito, quero saber com clareza se o email com o resultado foi enviado (ou por que
falhou), inclusive ao navegar entre as abas, e quero uma forma de testar o SMTP isoladamente.

---

## Acceptance Criteria

### Resumo na tela (US-01)
- [x] `processar_blocos_run()` retorna `(total_evidencias, resumo_processo)`
- [x] Resumo persistido na coluna `resumo_processo` da tabela `runs` (migração idempotente)
- [x] Aba Processar exibe o resumo num expander após a conclusão (quando SAC gerou resumo)
- [x] Aba Resultados exibe o resumo persistente (lido do banco), sobrevivendo à troca de abas

### Resumo no Excel (US-02)
- [x] Aba "Resumo" é a **primeira** aba do arquivo (`wb.sheetnames[0] == "Resumo"`)
- [x] Formato Campo | Valor; linhas `CHAVE: valor` viram duas colunas
- [x] A aba de evidências permanece intacta; leitura resiliente via `ler_evidencias_df()`
- [x] Aba Resumo escrita APÓS as evidências (para não ser apagada pela reescrita do arquivo)

### Email (US-03)
- [x] `scripts/testar_smtp.py` envia email de teste e reporta erro exato
- [x] Status do envio guardado em `st.session_state["email_status"]` e exibido na aba Resultados
- [x] SMTP confirmado funcional (Gmail/587/STARTTLS) via teste real

---

## Edge Cases
- **SAC desativado / resumo vazio**: nenhuma aba "Resumo" criada; coluna fica NULL; UI não mostra resumo.
- **Excel antigo (aba única 'Sheet1')**: `ler_evidencias_df()` continua lendo corretamente.
- **Banco runs.db legado sem a coluna**: migração idempotente adiciona a coluna sem perder dados.
- **Falha ao escrever aba Resumo**: best-effort, apenas warning no log; pipeline não é interrompido.
- **Falha de envio de email**: retorna False; UI mostra aviso persistente apontando para o script de teste.
