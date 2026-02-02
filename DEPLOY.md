# 🚀 Guia de Deploy - Mapeamento Pericial

Este guia fornece instruções passo a passo para fazer deploy da aplicação **Mapeamento Pericial** no Railway usando Docker Desktop.

## 📋 Pré-requisitos

Antes de começar, certifique-se de ter:

- ✅ **Docker Desktop** instalado e funcionando
- ✅ **Conta no Railway** (plano pago já adquirido)
- ✅ **Chave da API Google Gemini** (GOOGLE_API_KEY)
- ✅ **Git** instalado (opcional, mas recomendado)

---

## 🔧 Parte 1: Teste Local com Docker

### 1.1 Preparar Variável de Ambiente

Crie um arquivo `.env` na raiz do projeto (copie do `.env.example`):

```bash
GOOGLE_API_KEY=sua_chave_api_aqui
```

### 1.2 Build da Imagem Docker

Abra o PowerShell e navegue até o diretório do projeto:

```powershell
cd "c:/Users/walte/OneDrive/Workspace/IA/Cruvinel/Valuation/Projetos/Agente Mapeamento/P2"
```

Execute o build da imagem:

```powershell
docker build -t mapeamento-pericial:latest .
```

⏱️ Este processo pode levar alguns minutos na primeira vez.

### 1.3 Executar Container Localmente

Execute o container com a variável de ambiente:

```powershell
docker run -p 8501:8501 -e GOOGLE_API_KEY="sua_chave_api_aqui" mapeamento-pericial:latest
```

### 1.4 Testar a Aplicação

1. Abra seu navegador em: `http://localhost:8501`
2. Faça upload de um arquivo TXT de teste
3. Clique em "Processar Documento"
4. Verifique se as evidências são extraídas corretamente
5. Baixe a planilha Excel gerada

Se tudo funcionar, pressione `Ctrl+C` no PowerShell para parar o container.

---

## 🚂 Parte 2: Deploy no Railway

### Opção A: Deploy via GitHub (Recomendado)

#### 2.1 Criar Repositório no GitHub

1. Crie um novo repositório no GitHub (pode ser privado)
2. No PowerShell, inicialize o Git no projeto:

```powershell
cd "c:/Users/walte/OneDrive/Workspace/IA/Cruvinel/Valuation/Projetos/Agente Mapeamento/P2"
git init
git add .
git commit -m "Initial commit - Mapeamento Pericial"
```

3. Conecte ao repositório remoto:

```powershell
git remote add origin https://github.com/seu-usuario/seu-repositorio.git
git branch -M main
git push -u origin main
```

#### 2.2 Configurar Projeto no Railway

1. Acesse [railway.app](https://railway.app) e faça login
2. Clique em **"New Project"**
3. Selecione **"Deploy from GitHub repo"**
4. Escolha o repositório que você criou
5. O Railway detectará automaticamente o `Dockerfile`

#### 2.3 Configurar Variáveis de Ambiente

1. No painel do projeto Railway, vá em **"Variables"**
2. Adicione a variável:
   - **Nome**: `GOOGLE_API_KEY`
   - **Valor**: Sua chave da API Gemini
3. Clique em **"Add"**

#### 2.4 Configurar Porta e Domínio

1. Vá em **"Settings"**
2. Em **"Networking"**, clique em **"Generate Domain"**
3. Copie a URL gerada (ex: `mapeamento-pericial-production.up.railway.app`)

#### 2.5 Deploy

1. O Railway iniciará o deploy automaticamente
2. Acompanhe os logs em **"Deployments"**
3. Aguarde até ver a mensagem: `✅ Deployment successful`

### Opção B: Deploy via Docker Image

#### 2.1 Build e Tag da Imagem

```powershell
docker build -t mapeamento-pericial:latest .
docker tag mapeamento-pericial:latest registry.railway.app/seu-projeto-id:latest
```

#### 2.2 Login no Registry do Railway

```powershell
docker login registry.railway.app
```

Use seu token de acesso do Railway quando solicitado.

#### 2.3 Push da Imagem

```powershell
docker push registry.railway.app/seu-projeto-id:latest
```

#### 2.4 Configurar no Railway

Siga os passos 2.3 a 2.5 da Opção A.

---

## ✅ Parte 3: Verificação e Testes

### 3.1 Verificar Deploy

1. Acesse a URL gerada pelo Railway
2. Você deve ver a interface do Mapeamento Pericial
3. Verifique se não há erros no console do navegador

### 3.2 Testar Funcionalidade

1. Faça upload de um arquivo TXT
2. Processe o documento
3. Verifique a extração de evidências
4. Baixe a planilha Excel

### 3.3 Monitorar Logs

No Railway, vá em **"Deployments" → "View Logs"** para acompanhar:
- Requisições à API Gemini
- Processamento de blocos
- Erros (se houver)

---

## 🔍 Troubleshooting

### Problema: "Module not found"

**Solução**: Verifique se todas as dependências estão no `requirements.txt`

```powershell
docker build --no-cache -t mapeamento-pericial:latest .
```

### Problema: "API Key inválida"

**Solução**: 
1. Verifique se a variável `GOOGLE_API_KEY` está configurada no Railway
2. Confirme que a chave é válida no Google AI Studio
3. Redeploy a aplicação

### Problema: Container não inicia

**Solução**: Verifique os logs do Railway:
1. Vá em **"Deployments"**
2. Clique no deploy mais recente
3. Verifique os logs de erro
4. Procure por mensagens de erro do Streamlit ou Python

### Problema: Timeout no processamento

**Solução**: 
- Arquivos muito grandes podem exceder o timeout
- Considere ajustar `TAMANHO_BLOCO` em `config.py`
- Ou divida o arquivo em partes menores

### Problema: Porta incorreta

**Solução**: O Railway define automaticamente a variável `$PORT`. Certifique-se de que o `railway.json` está configurado corretamente.

---

## 🔄 Atualizações Futuras

### Via GitHub (Opção A)

Sempre que fizer alterações no código:

```powershell
git add .
git commit -m "Descrição das alterações"
git push
```

### Métricas Importantes

No Railway, monitore:
- **CPU Usage**: Deve ficar abaixo de 80%
- **Memory Usage**: Depende do tamanho dos arquivos processados
- **Network**: Tráfego de entrada/saída

### Logs Auditáveis

A aplicação usa `loguru` para logs detalhados:
- Todos os blocos enviados são salvos em `logs/bloco_enviado_XXX.txt`
- Todas as respostas da IA são salvas em `logs/resposta_bloco_XXX.txt`

**Nota**: No Railway, estes logs são efêmeros (não persistem entre restarts).

---

## 🔐 Segurança

### Boas Práticas

1. ✅ **Nunca commite** o arquivo `.env` no Git
2. ✅ **Use variáveis de ambiente** para credenciais
3. ✅ **Mantenha** o `.gitignore` atualizado
4. ✅ **Rotacione** a API Key periodicamente
5. ✅ **Monitore** o uso da API para evitar custos inesperados

### Arquivo .gitignore

Certifique-se de que o `.gitignore` inclui:

```
.env
logs/
saida/
entrada/
__pycache__/
```

---

## 💰 Custos Estimados

### Railway
- Plano pago: ~$5-20/mês (dependendo do uso)
- Inclui: 500 horas de execução, 100GB de tráfego

### Google Gemini API
- Gemini 2.0 Flash: Gratuito até certo limite
- Verifique os limites em: [ai.google.dev/pricing](https://ai.google.dev/pricing)

---

## 📞 Suporte

### Recursos Úteis

- **Railway Docs**: https://docs.railway.app
- **Streamlit Docs**: https://docs.streamlit.io
- **Google AI Docs**: https://ai.google.dev/docs

### Comandos Úteis

```powershell
# Ver logs do container local
docker logs <container-id>

# Parar todos os containers
docker stop $(docker ps -q)

# Remover imagens antigas
docker image prune -a

# Verificar uso de espaço
docker system df
```

---

## ✨ Próximos Passos

Após o deploy bem-sucedido:

1. 📧 Configure notificações de erro no Railway
2. 🔄 Configure backup automático (se necessário)
3. 📈 Monitore métricas de uso
4. 🎨 Personalize o tema do Streamlit (`.streamlit/config.toml`)
5. 📱 Teste em diferentes dispositivos

---

**🎉 Parabéns! Sua aplicação está no ar!**
