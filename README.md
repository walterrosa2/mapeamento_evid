# ⚖️ Mapeamento Pericial (P2)

Esta aplicação web desenvolvida em Streamlit e Python é o motor de inteligência artificial de primeiro nível responsável pela extração massiva e mapeamento sistemático de provas.

## 🎯 Objetivo

Analisar a totalidade de arquivos textuais de processos judiciais de grande volume (convertidos anteriormente via OCR), aplicando modelos de IA para varrer e encontrar de forma automatizada trechos relativos a 9 tipos de evidências financeiras e jurídicas que fundamentam laudos de assistência pericial.

## 📅 Última Alteração de Código
*   **Data estimada**: 21 de abril de 2026

## ✨ Principais Funcionalidades

*   **Portal Web Streamlit**: Interface web intuitiva para carregamento do arquivo texto bruto do processo judiciário (`.txt`).
*   **Processamento Inteligente por Lotes**: Algoritmo que quebra o processo em blocos e orquestra chamadas sequenciais para os modelos de IA do Gemini (`gemini-1.5-pro` ou `gemini-1.5-flash`), mantendo a integridade de contexto do processo.
*   **Mapeamento de 9 Tipos de Evidências Periciais**: Identificação inteligente dos seguintes eventos críticos:
    1.  **Notas Fiscais**: Faturas e comprovantes de prestação de serviços/vendas.
    2.  **Contratos**: Cláusulas contratuais, aditivos, termos de distrato ou parcerias.
    3.  **Comprovantes de Pagamentos**: Transações financeiras (TEDs, PIX, boletos, recibos).
    4.  **Multas Contratuais**: Encargos, penalidades de atraso ou quebras contratuais.
    5.  **Apontamentos e OSs**: Ordens de serviço e relatórios de atividades técnicas executadas.
    6.  **Base de Cálculo (Horas)**: Timesheets, relatórios de cronogramas e horas trabalhadas.
    7.  **Oscilações de Despesas**: Anormalidades e picos atípicos nas despesas societárias.
    8.  **Perdas Diretas ou Indiretas**: Lucros cessantes, multas governamentais ou prejuízos operacionais.
    9.  **Reembolsos e Viagens**: Prestação de contas de deslocamentos de negócios.
*   **Geração Automatizada de Planilha**: Geração da planilha Excel de saída estruturada (`evidencias_extraidas_mapeamento.xlsx`) mapeando o Tipo de Evidência, Trecho e Referência de Página encontrada.
*   **Infraestrutura Dockerizada**: Contêineres prontos via `Dockerfile` e `docker-compose.yml` para deployment integrado em servidores locais ou na nuvem Railway (`railway.json`).
*   **Automação Multiplataforma**: Scripts de inicialização prontos para Windows (`_start.ps1`, `_start.bat`) e Linux (`_start_linux.sh`).
