# config.py

import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente do arquivo .env (se existir)
load_dotenv(override=True)

# === RAIZ ABSOLUTA DO PROJETO ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# === CHAVE DA API GEMINI ===
# Prioriza variável de ambiente, com fallback para chave local (desenvolvimento)
_CHAVE_FALLBACK = "AIzaSyBnB53v9E0fVo-DOfxqRe14-I_SzTeyGDg"
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", _CHAVE_FALLBACK)

from loguru import logger
if GOOGLE_API_KEY == _CHAVE_FALLBACK:
    logger.warning("⚠️ Usando API Key de FALLBACK (Memória). Verifique seu .env!")
else:
    # Mostra apenas o final para auditoria sem vazar a chave
    logger.success(f"🔑 API Key carregada com sucesso do .env (Final: ...{GOOGLE_API_KEY[-4:]})")

# === TAMANHO DO BLOCO EM CARACTERES (ajuste se necessário) ===
TAMANHO_BLOCO = 30000  # ~7.5k tokens de documento — deixa margem suficiente para resposta

# === PAGE-AWARE CHUNKING v3.0 ===
PAGINAS_POR_BLOCO = 10  # Agrupar N páginas por bloco; ajuste para adaptar tamanho

# === DELIMITADOR DE PÁGINA (v3.2) ===
# Marcador que separa as páginas no TXT OCR. Cada processo pode ter o seu;
# este é apenas o valor inicial sugerido na UI.
DELIMITADOR_PAGINA_PADRAO = "---Página---"

# Teto de segurança: se um grupo de páginas exceder este tamanho, é subdividido
# por caracteres para evitar blocos gigantes (e respostas truncadas do modelo).
MAX_CHARS_BLOCO = 45000

# === CAMINHOS PADRÃO USANDO BASE ABSOLUTA ===
CAMINHO_ENTRADA = os.path.join(BASE_DIR, "entrada")
CAMINHO_SAIDA = os.path.join(BASE_DIR, "saida")
CAMINHO_LOGS = os.path.join(BASE_DIR, "logs")

# === ARQUIVO DE ENTRADA PADRÃO ===
ARQUIVO_PADRAO_TXT = "processo.txt"

# === CAMINHOS v2.0 ===
CAMINHO_RUNS = os.path.join(CAMINHO_SAIDA, "runs")
CAMINHO_DB   = os.path.join(CAMINHO_SAIDA, "runs.db")

# === SMTP (email best-effort) ===
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
SMTP_TLS  = os.getenv("SMTP_TLS", "true").lower() == "true"

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
- Responda **exclusivamente** em formato JSON: um array de objetos, conforme o exemplo.
- **Nunca** inclua texto, explicações ou marcações fora do array JSON.
- Use exatamente estas chaves em cada objeto: "Tipo de Evidência", "Trecho", "Conteúdo", "Resumo", "Referência".
- Escape corretamente aspas internas; não use quebras de linha dentro dos valores.

Exemplo de resposta:
[
  {
    "Tipo de Evidência": "Contrato",
    "Trecho": "conforme previu contrato na página 4, artigo 1°",
    "Conteúdo": "Contrato de Cloud Services com Oracle",
    "Resumo": "Contrato firmado em 22/01/2015",
    "Referência": "Pág. 10"
  }
]

Cada objeto deve representar uma evidência encontrada no bloco. Mesmo que haja apenas uma evidência, a resposta deve ser um array JSON. Se nenhuma evidência for encontrada, responda apenas: []

Validação de Evidências:
Certifique-se de:
- Validar se os documentos citados são provas diretas ou contextuais.
- Relacionar as evidências com os pontos principais do caso descritos no processo.
- Toda nova linha de evidência precisa OBRIGATORIAMENTE gerar todos os pontos: Tipo de Evidência, Trecho, Conteúdo, Resumo, Referência.
- Todo retorno deverá conter o "Trecho" obrigatório e sempre contido no documento entrada origem, ou seja, nunca inventar, inferir ou autocompletar.
- Ignore narrativas jurídicas, exposições de fatos, fundamentos legais, citações de jurisprudência e pedidos. Analise SOMENTE trechos que tenham natureza documental (comprovantes, notas, tabelas, quadros, extratos, recibos, contratos, notificações, OS, relatórios, anexos etc.)
- Só classifique como evidência aquilo que seja um documento, anexo, prova objetiva ou elemento mensurável. Nunca classifique trechos descritivos, justificativas, reclamações ou explicações como evidência.

"""

# === SAC v3.0 — RESUMIDOR (AGENTE 1) ===
MAX_CHARS_RESUMIDOR = 2_400_000  # ~600k tokens — truncar texto muito grande antes de enviar
MAX_TOKENS_RESUMO = 8192  # v3.2: orçamento de saída do resumidor (antes 2048 truncava)

PROMPT_RESUMIDOR = """
Você é um assistente jurídico-pericial especializado em análise de processos judiciais.

TAREFA: Analise o processo judicial completo abaixo e produza um RESUMO ESTRUTURADO E COMPLETO,
que servirá de contexto para as próximas etapas de uma auditoria pericial. Seja detalhado nos
campos de DOCUMENTOS-CHAVE e QUESITOS PERICIAIS. Retorne EXCLUSIVAMENTE o resumo abaixo, sem
nenhum texto introdutório ou final.

TIPO DE AÇÃO: [ex: Reclamação Trabalhista, Ação de Indenização, Procedimento Comum Cível, etc.]
PARTES:
  - Polo Ativo: [Nome/Razão Social do reclamante ou autor]
  - Polo Passivo: [Nome/Razão Social do réu ou demandado]
OBJETO: [3-5 linhas descrevendo o pedido principal, a pretensão e a controvérsia central]
PERÍODO RELEVANTE: [datas de início e fim do período discutido no processo]
VALORES EM DISPUTA: [valores monetários identificados; caso contrário: Não identificado]
DOCUMENTOS-CHAVE: [liste, um por linha iniciado por "- ", os principais documentos/provas
  mencionados no processo (notas fiscais, contratos, laudos, comprovantes, ARTs, recibos, etc.),
  indicando tipo e, quando houver, número/data/página de referência]
QUESITOS PERICIAIS: [liste, um por linha iniciado por "- ", os quesitos formulados às partes ou
  ao perito; se não houver quesitos no processo, escreva: Não identificado]

REGRA IMPORTANTE: Se algum campo não puder ser identificado com certeza no texto, escreva:
Não identificado. Não invente informações que não estejam no processo.
"""
