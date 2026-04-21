# PRD - Mapeamento Pericial

## Objetivo
Automatizar a extração de evidências em processos jurídicos utilizando Inteligência Artificial (Google Gemini). A aplicação visa reduzir o tempo de análise manual de grandes documentos (OCR) e gerar uma planilha estruturada para peritos e advogados.

## Usuários
- Peritos judiciais
- Advogados
- Auditores jurídicos

## Requisitos
- Upload de arquivos TXT (extraídos via OCR).
- Divisão inteligente do documento em blocos para respeitar limites de tokens.
- Extração de campos específicos: Tipo de Evidência, Trecho, Conteúdo, Resumo, Referência.
- Geração de planilha Excel (.xlsx) com os resultados.
- Interface visual moderna via Streamlit.

## Limitações
- Dependência de chave de API Google Gemini.
- Qualidade da extração depende da qualidade do OCR original.
- Limite de caracteres por bloco configurado em `config.py`.

## Dados Sensíveis/PII
- Processos jurídicos podem conter dados sensíveis. O processamento é feito via API da Google. Recomenda-se anonimização prévia se necessário.
