"""
Catalogador Pericial - Interface Streamlit
Aplicação para extração automatizada de evidências jurídicas
"""

import streamlit as st
import os
import sys
import pandas as pd
from pathlib import Path
import tempfile
from loguru import logger

# Configurar logger
logger.remove()
logger.add(sys.stdout, format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>")

# Importar módulos da aplicação
from src.controlador import processar_todos_os_blocos
from src.leitor_txt import carregar_blocos
from src.gemini_api import enviar_bloco_para_gemini
from src.planilha import inicializar_planilha, adicionar_linha_excel
from src.controlador import extrair_campos, limpar_linha_vazia
from config import CAMINHO_ENTRADA, CAMINHO_SAIDA, ARQUIVO_PADRAO_TXT

# Configuração da página
st.set_page_config(
    page_title="Catalogador Pericial",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #64748B;
        text-align: center;
        margin-bottom: 2rem;
    }
    .stProgress > div > div > div > div {
        background-color: #1E3A8A;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #D1FAE5;
        border-left: 4px solid #10B981;
        margin: 1rem 0;
    }
    .info-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #DBEAFE;
        border-left: 4px solid #3B82F6;
        margin: 1rem 0;
    }
    </style>
""", unsafe_allow_html=True)

def garantir_diretorios():
    """Garante que os diretórios necessários existam"""
    for dir_path in [CAMINHO_ENTRADA, CAMINHO_SAIDA, os.path.join(os.path.dirname(__file__), "logs")]:
        os.makedirs(dir_path, exist_ok=True)

def processar_arquivo_upload(uploaded_file):
    """Processa o arquivo enviado pelo usuário"""
    # Garantir que diretórios existam
    garantir_diretorios()
    
    # Salvar arquivo temporariamente
    arquivo_path = os.path.join(CAMINHO_ENTRADA, ARQUIVO_PADRAO_TXT)
    with open(arquivo_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    return arquivo_path

def main():
    # Header
    st.markdown('<div class="main-header">⚖️ Catalogador Pericial</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Extração Automatizada de Evidências Jurídicas</div>', unsafe_allow_html=True)
    
    # Sidebar com informações
    with st.sidebar:
        st.header("ℹ️ Sobre")
        st.markdown("""
        Esta aplicação utiliza IA para extrair e catalogar evidências de processos jurídicos.
        
        **Como usar:**
        1. Faça upload do arquivo TXT (extraído via OCR)
        2. Clique em "Processar Documento"
        3. Aguarde o processamento
        4. Baixe a planilha com as evidências
        
        **Tipos de Evidências:**
        - Notas Fiscais
        - Contratos
        - Pagamentos
        - Multas Contratuais
        - Apontamentos (OSs)
        - Base de Cálculo
        - Oscilações de Despesas
        - Perdas Diretas/Indiretas
        - Reembolsos e Despesas
        """)
        
        st.divider()
        st.caption("🤖 Powered by Google Gemini AI")
    
    # Área principal
    tab1, tab2 = st.tabs(["📤 Upload e Processamento", "📊 Resultados"])
    
    with tab1:
        st.markdown('<div class="info-box">📥 <b>Passo 1:</b> Faça upload do arquivo TXT contendo o processo extraído via OCR</div>', unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader(
            "Selecione o arquivo TXT do processo",
            type=['txt'],
            help="Arquivo de texto extraído via OCR contendo o processo jurídico"
        )
        
        if uploaded_file is not None:
            # Mostrar informações do arquivo
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📄 Nome do Arquivo", uploaded_file.name)
            with col2:
                file_size_kb = uploaded_file.size / 1024
                st.metric("📊 Tamanho", f"{file_size_kb:.2f} KB")
            with col3:
                st.metric("✅ Status", "Pronto")
            
            st.divider()
            
            # Botão de processamento
            if st.button("🚀 Processar Documento", type="primary", use_container_width=True):
                try:
                    # Salvar arquivo
                    with st.spinner("Salvando arquivo..."):
                        arquivo_path = processar_arquivo_upload(uploaded_file)
                        st.success(f"✅ Arquivo salvo: {uploaded_file.name}")
                    
                    # Carregar blocos
                    with st.spinner("Analisando documento e dividindo em blocos..."):
                        blocos = carregar_blocos(ARQUIVO_PADRAO_TXT)
                        total_blocos = len(blocos)
                        st.info(f"📚 Documento dividido em {total_blocos} blocos para processamento")
                    
                    # Inicializar planilha
                    inicializar_planilha()
                    
                    # Processar blocos
                    st.markdown("### 🔄 Processamento em Andamento")
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    log_container = st.container()
                    
                    total_evidencias = 0
                    
                    for i, bloco in enumerate(blocos):
                        # Atualizar progresso
                        progresso = (i + 1) / total_blocos
                        progress_bar.progress(progresso)
                        status_text.text(f"Processando bloco {i+1} de {total_blocos}...")
                        
                        with log_container:
                            with st.expander(f"📝 Bloco {i+1}/{total_blocos}", expanded=(i == len(blocos)-1)):
                                st.text(f"🔍 Enviando para análise de IA...")
                                
                                # Enviar para Gemini
                                resposta = enviar_bloco_para_gemini(bloco, bloco_id=i)
                                
                                if not resposta:
                                    st.error("❌ Erro: nenhum retorno recebido da IA")
                                    continue
                                
                                st.text(f"✅ Resposta recebida")
                                
                                # Extrair evidências
                                evidencias = extrair_campos(resposta)
                                
                                if not evidencias:
                                    st.warning("⚠️ Nenhuma evidência encontrada neste bloco")
                                    continue
                                
                                # Salvar evidências
                                linhas_validas = 0
                                for evidencia in evidencias:
                                    evidencia_limpa = limpar_linha_vazia(evidencia)
                                    if evidencia_limpa:
                                        adicionar_linha_excel(evidencia_limpa)
                                        linhas_validas += 1
                                        total_evidencias += 1
                                
                                st.success(f"✅ {linhas_validas} evidência(s) extraída(s)")
                    
                    # Finalização
                    progress_bar.progress(1.0)
                    status_text.empty()
                    
                    st.markdown(f'<div class="success-box">🎉 <b>Processamento Concluído!</b><br>Total de evidências extraídas: {total_evidencias}</div>', unsafe_allow_html=True)
                    
                    # Armazenar flag de sucesso
                    st.session_state['processamento_concluido'] = True
                    st.session_state['total_evidencias'] = total_evidencias
                    
                except Exception as e:
                    st.error(f"❌ Erro durante o processamento: {str(e)}")
                    logger.error(f"Erro no processamento: {e}")
    
    with tab2:
        st.markdown("### 📊 Resultados da Análise")
        
        # Verificar se existe arquivo de saída
        arquivo_excel = os.path.join(CAMINHO_SAIDA, "evidencias_extraidas.xlsx")
        
        if os.path.exists(arquivo_excel):
            try:
                # Ler planilha
                df = pd.read_excel(arquivo_excel)
                
                if not df.empty:
                    # Métricas
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("📋 Total de Evidências", len(df))
                    with col2:
                        tipos_unicos = df['Tipo de Evidência'].nunique() if 'Tipo de Evidência' in df.columns else 0
                        st.metric("🏷️ Tipos Diferentes", tipos_unicos)
                    with col3:
                        st.metric("📄 Status", "Disponível")
                    
                    st.divider()
                    
                    # Exibir tabela
                    st.dataframe(
                        df,
                        use_container_width=True,
                        hide_index=True,
                        height=400
                    )
                    
                    # Botão de download
                    with open(arquivo_excel, "rb") as file:
                        st.download_button(
                            label="📥 Baixar Planilha Excel",
                            data=file,
                            file_name="evidencias_extraidas.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            type="primary",
                            use_container_width=True
                        )
                    
                    # Distribuição por tipo
                    if 'Tipo de Evidência' in df.columns:
                        st.divider()
                        st.markdown("### 📈 Distribuição por Tipo de Evidência")
                        tipo_counts = df['Tipo de Evidência'].value_counts()
                        st.bar_chart(tipo_counts)
                else:
                    st.info("ℹ️ A planilha existe mas está vazia. Processe um documento primeiro.")
            
            except Exception as e:
                st.error(f"❌ Erro ao ler a planilha: {str(e)}")
        else:
            st.info("ℹ️ Nenhum resultado disponível ainda. Faça upload e processe um documento primeiro.")

if __name__ == "__main__":
    # Garantir diretórios no início
    garantir_diretorios()
    main()
