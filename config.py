# config.py

import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente do arquivo .env (se existir)
load_dotenv()

# === RAIZ ABSOLUTA DO PROJETO ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# === CHAVE DA API GEMINI ===
# Prioriza variável de ambiente, com fallback para chave local (desenvolvimento)
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "AIzaSyBnB53v9E0fVo-DOfxqRe14-I_SzTeyGDg")

# === TAMANHO DO BLOCO EM CARACTERES (ajuste se necessário) ===
TAMANHO_BLOCO = 80000  # Aproximadamente 10k caracteres por bloco

# === CAMINHOS PADRÃO USANDO BASE ABSOLUTA ===
CAMINHO_ENTRADA = os.path.join(BASE_DIR, "entrada")
CAMINHO_SAIDA = os.path.join(BASE_DIR, "saida")
CAMINHO_LOGS = os.path.join(BASE_DIR, "logs")

# === ARQUIVO DE ENTRADA PADRÃO ===
ARQUIVO_PADRAO_TXT = "processo.txt"

# === PROMPT PADRÃO APLICADO A CADA BLOCO ===
PROMPT_PADRAO = """
Instruções de Análise:

Divisão do Documento:
Analise o documento em blocos. Forneça os seguintes detalhes para cada bloco, seu objetivo principal é identificar as evidencias <tipo_eviencias>:
- Tipo de Evidência: Classifique todas as evidencias localizadas cujo conteúdo refere-se aos tipos de evidencias <tipo_eviencias>.
- Trecho: Como a paginação do arquivo pode conter inconsistências, será necessário trazer trechos, exatamente iguais aos caracteres/palavras do processo lido (entrada), de forma que facilite a identificação da página. 
- Conteúdo: Descreva o conteúdo brevemente com base no contexto fornecido.
- Resumo: Ofereça um resumo objetivo do que a evidência aborda e sua relevância para o caso.
- Referência: Identifique no arquivo o trecho <pagina>. Todas as paginas do arquivo de entrada possuem a expressão <pagina> que caracteriza a página.

<tipo_evidencias>
NOTAS FISCAIS - Podendo ser notas fiscais de produto e serviço
CONTRATOS (PROPRIA OU TERCEIROS) - Podendo ser contratos entre as partes do processo ou terceiros
PAGAMENTOS (ted, pix, boletos, etc) - Qualquer comprovante de pagamentos
MULTAS CONTRATUAIS - Clausulas relacionadas a multas contratuais
APONTAMENTOS (OSs) - Evidencias de apontamentos relacionados a produtividade, seja como resumo ou analitico (detalhado)
BASE DE CALCULO (HORAS INTERNAS COLABORADORES) - Relação de horas gastas/aplicadas e que são parte das evidencias do processo
OSCILAÇÕES DE DESPESAS/GASTOS - Relatos sobre gastos e/ou despesas incorridas e que fazem parte do processo
PERDAS DIRETAS OU INDIRETAS - Relatos sobre perdas e/ou gastos/despesas incorridas e que fazem parte do processo
REEMBOLSO E DESPESAS VIAGENS - Relatos sobre reembolso e despesas viagens incorridas e que fazem parte do processo
</tipo_evidencias>

<pagina>
Identifique o trecho [fls.] e a numeração na sequência corresponde a numeração da página.
</pagina>



Formato de Resposta (OBRIGATÓRIO):
IMPORTANTE:
- Responda **exclusivamente** em formato de tabela Markdown, conforme o exemplo.
- **Nunca** utilize JSON ou outro formato, mesmo que o texto seja extenso.
Responda exclusivamente no formato de tabela abaixo. Não inclua explicações ou texto fora da tabela.

| Tipo de Evidência | Trecho                                             | Conteúdo                              | Resumo                         | Referência       | 
|-------------------|---------------------------------------------------|---------------------------------------|--------------------------------|------------------|
| Contrato          | "conforme previu contrato na página 4, artigo 1°" | Contrato de Cloud Services com Oracle | Contrato firmado em 22/01/2015 | Pág. 10          |

Cada linha deve representar uma evidência encontrada no bloco. Mesmo que haja apenas uma evidência, a resposta deve manter o formato de tabela.

Validação de Evidências:
Certifique-se de:
- Validar se os documentos citados são provas diretas ou contextuais.
- Relacionar as evidências com os pontos principais do caso descritos no processo.
- Toda nova linha de evidência precisa OBRIGATORIAMENTE gerar todos os pontos: Tipo de Evidência, Trecho, Conteúdo, Resumo, Referência.
- Todo retorno deverá conter o "Trecho" obrigatório e sempre contido no documento entrada origem, ou seja, nunca inventar, inferir ou autocompletar.
- Ignore narrativas jurídicas, exposições de fatos, fundamentos legais, citações de jurisprudência e pedidos. Analise SOMENTE trechos que tenham natureza documental (comprovantes, notas, tabelas, quadros, extratos, recibos, contratos, notificações, OS, relatórios, anexos etc.)
- Só classifique como evidência aquilo que seja um documento, anexo, prova objetiva ou elemento mensurável. Nunca classifique trechos descritivos, justificativas, reclamações ou explicações como evidência.

"""
