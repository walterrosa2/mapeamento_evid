# Walkthrough - Mapeamento Pericial

## O que foi feito
A aplicação foi configurada e inicializada seguindo os padrões "Production-Minded":
1.  **Estrutura de Módulos**: Adicionado `src/__init__.py` para garantir importações corretas.
2.  **Scripts de Execução**: Criados `_start.ps1` e `_start.bat` para facilitar a inicialização.
3.  **Ambiente Virtual**: Corrigido problema de caminhos absolutos no `.venv` através da recriação do ambiente.
4.  **Configuração**: Garantido que `.env` existe e está carregado corretamente via `python-dotenv`.
5.  **Execução**: Servidor Streamlit iniciado em `http://localhost:8515`.

## Onde no código
- `app.py`: Interface principal e lógica de fluxo.
- `src/controlador.py`: Coordenação do processamento de blocos.
- `config.py`: Definições globais e prompt da IA.
- `_start.ps1`: Script mestre de automação (configurado para porta 8515).

## Como validar
1.  Acesse `http://localhost:8515`.
2.  Faça upload de um arquivo `.txt` de teste (pode usar um pequeno trecho de processo).
3.  Clique em "Processar Documento".
4.  Verifique na aba "Resultados" se a tabela e o gráfico de distribuição são gerados.
5.  Baixe a planilha Excel.
