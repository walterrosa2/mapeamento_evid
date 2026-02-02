# Catalogador Pericial ⚖️

Aplicação de extração automatizada de evidências jurídicas usando IA (Google Gemini).

## 🎯 Funcionalidades

- Upload de arquivos TXT (processos extraídos via OCR)
- Análise automática com IA para identificar evidências
- Extração de 9 tipos de evidências jurídicas
- Geração de planilha Excel organizada
- Interface web amigável com Streamlit

## 🚀 Início Rápido

### Desenvolvimento Local

1. Clone o repositório
2. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure a API Key:
   ```bash
   cp .env.example .env
   # Edite .env e adicione sua GOOGLE_API_KEY
   ```
4. Execute a aplicação:
   ```bash
   streamlit run app.py
   ```

### Deploy no Railway

Consulte o arquivo [DEPLOY.md](DEPLOY.md) para instruções completas de deploy.

## 📦 Tipos de Evidências Extraídas

1. Notas Fiscais
2. Contratos
3. Pagamentos (TED, PIX, Boletos)
4. Multas Contratuais
5. Apontamentos (OSs)
6. Base de Cálculo (Horas)
7. Oscilações de Despesas
8. Perdas Diretas/Indiretas
9. Reembolsos e Despesas de Viagens

## 🛠️ Tecnologias

- **Python 3.11**
- **Streamlit** - Interface web
- **Google Gemini AI** - Análise de documentos
- **Pandas** - Manipulação de dados
- **Docker** - Containerização

## 📄 Licença

Uso interno - Cruvinel Valuation

## 👨‍💻 Autor

Desenvolvido para análise pericial jurídica
