import streamlit as st
import pandas as pd
import math

# ==============================================================================
# 1. CONFIGURAÇÕES E CONSTANTES GLOBAIS
# ==============================================================================

# A linha mais importante para o layout:
# Garanta que esta seja a PRIMEIRA chamada do Streamlit no seu código.
st.set_page_config(page_title="Calculadora Estrutural - Perfis Metálicos", layout="wide")


class Config:
    NOME_NORMA = 'ABNT NBR 8800:2008'
    GAMMA_A1 = 1.10
    E_ACO = 20000
    FATOR_SIGMA_R = 0.3
    FATOR_LAMBDA_P_FLT = 1.76
    FATOR_LAMBDA_P_FLM = 0.38
    FATOR_LAMBDA_R_FLM_LAMINADO = 0.83
    FATOR_LAMBDA_P_FLA = 3.76
    FATOR_LAMBDA_R_FLA = 5.70
    KV_ALMA_SEM_ENRIJECEDORES = 5.0
    FATOR_VP = 0.60
    FATOR_LAMBDA_P_VRD = 1.10
    FATOR_LAMBDA_R_VRD = 1.37
    FATOR_VRD_ELASTICO = 1.24
    LIMITE_FLECHA_TOTAL = 350

PROFILE_TYPE_MAP = {
    "Laminados": "Perfis Laminados",
    "CS": "Perfis Compactos Soldados",
    "CVS": "Perfil de Seção Variável",
    "VS": "Perfil Soldadas"
}

HTML_TEMPLATE_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&family=Roboto+Slab:wght@400;700&display=swap');
    body { font-family: 'Roboto', sans-serif; line-height: 1.8; color: #333; background-color: #f0f4f8; }
    .container { margin: 20px auto; padding: 1rem; background-color: white; border-radius: 10px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); width: 100%; box-sizing: border-box; }
    h1, h2, h3, h4, h5 { font-family: 'Roboto Slab', serif; color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 5px; margin-top: 30px; }
    h1 { text-align: center; border: none; font-size: 2.2em; }
    h5 { border-bottom: none; font-size: 1.1em; margin-top: 20px; color: #34495e;}
    .summary-table { width: 100%; border-collapse: collapse; margin-bottom: 20px; font-size: 0.9em; }
    .summary-table th, .summary-table td { border: 1px solid #ddd; padding: 8px; text-align: center; vertical-align: middle; }
    .summary-table th { background-color: #34495e; color: white; }
    .formula-block { background-color: #f9fbfc; border-left: 5px solid #3498db; padding: 20px; margin: 20px 0; border-radius: 5px; }
    .verification-block { background-color: #eafaf1; border-left: 5px solid #27ae60; padding: 15px; margin: 20px 0; border-radius: 5px; text-align: left;}
    .pass { color: #27ae60; font-weight: bold; }
    .fail { color: #e74c3c; font-weight: bold; }
    .formula { font-size: 1.2em; text-align: center; margin: 10px 0; word-wrap: break-word; overflow-x: auto; padding: 8px; background-color: #f0f2f5; border-radius: 4px;}
    .final-result { font-weight: bold; color: #3498db; text-align: center; display: block; margin-top: 15px; font-size: 1.2em; padding: 8px; border: 1px solid #3498db; border-radius: 5px; background-color: #eafaf1;}
    .final-status { font-size: 1.5em; text-align: center; padding: 10px; border-radius: 5px; margin-top: 15px; }
    .final-status.pass { background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb;}
    .final-status.fail { background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb;}
    .ref-norma { font-size: 0.8em; color: #7f8c8d; text-align: right; margin-top: 15px; font-style: italic; }
    p { text-align: justify; }
</style>
"""
st.markdown(HTML_TEMPLATE_CSS, unsafe_allow_html=True)

# ==============================================================================
# 2. FUNÇÕES DE CÁLCULO DE ENGENHARIA
# ==============================================================================

def calcular_esforcos_viga(tipo_viga, L_cm, q_kn_cm=0, p_load=None):
    # ... corpo da função ...
    
def calcular_flecha_maxima(tipo_viga, L_cm, E, Ix, q_serv_kn_cm=0, p_serv_load=None):
    # ... corpo da função ...
    
def get_profile_properties(profile_series):
    # ... corpo da função ...

# ==============================================================================
# 3. GERAÇÃO DO MEMORIAL DE CÁLCULO
# ==============================================================================
def gerar_memorial_completo(perfil_nome, perfil_tipo, resultados, input_details):
    # ... corpo da função ...
    
def _build_verification_block_html(title, solicitante, s_symbol, resistente, r_symbol, eficiencia, status, unit):
    # ... corpo da função ...

# ==============================================================================
# 4. APLICAÇÃO PRINCIPAL STREAMLIT
# ==============================================================================
@st.cache_data
def load_data_from_local_file():
    try:
        caminho_arquivo_excel = 'perfis.xlsx'
        return pd.read_excel(caminho_arquivo_excel, sheet_name=None)
    except FileNotFoundError:
        st.error(f"Erro: Arquivo '{caminho_arquivo_excel}' não foi encontrado. Verifique se ele está na mesma pasta que o seu script Python.")
        return None
    except Exception as e:
        st.error(f"Erro ao ler o arquivo Excel: {e}")
        return None

def main():
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = None
    if 'detailed_analysis_html' not in st.session_state:
        st.session_state.detailed_analysis_html = None
    
    # MARCADOR DE VERIFICAÇÃO VISUAL
    st.info("VERSÃO DO CÓDIGO: FINAL - LAYOUT CORRIGIDO")

    st.title("🏛️ Calculadora Estrutural - Perfis Metálicos")
    st.caption(f"Utilizando a norma: {Config.NOME_NORMA}")

    all_sheets = load_data_from_local_file()
    if not all_sheets:
        st.stop()

    display_names = [PROFILE_TYPE_MAP.get(name, name) for name in all_sheets.keys()]
    reverse_name_map = {v: k for k, v in PROFILE_TYPE_MAP.items()}
    
    with st.sidebar:
        st.header("⚙️ Parâmetros de Entrada")
        
        st.header("1. Modelo da Viga")
        tipo_viga = st.selectbox("Tipo de Viga:", ('Bi-apoiada', 'Engastada e Livre (Balanço)', 'Bi-engastada', 'Engastada e Apoiada'), key='tipo_viga')
        L_cm = st.number_input("Comprimento da Viga (L, cm)", 10.0, value=500.0, step=10.0, key='L_cm')

        st.header("2. Modo de Carregamento")
        input_mode = st.radio("Selecione o modo de entrada dos esforços:", ("Calcular a partir de Cargas na Viga", "Inserir Esforços Manualmente"), horizontal=True, label_visibility="collapsed", key='input_mode')

        Msd, Vsd, q_servico_kn_cm, p_load_serv = 0, 0, 0, None
        input_details_html = ""
        detalhes_esforcos = None
        
        if input_mode == "Calcular a partir de Cargas na Viga":
            with st.container(border=True):
                # ... (código de entrada de cargas) ...
        else: # Inserir Esforços Manualmente
            with st.container(border=True):
                # ... (código de entrada manual) ...
        st.header("3. Parâmetros Gerais do Aço")
        fy_aco = st.number_input("Tensão de Escoamento (fy, kN/cm²)", 20.0, 50.0, 34.5, 0.5, key='fy_aco')
        Lb_projeto = st.number_input("Comprimento Destravado (Lb, cm)", 10.0, value=L_cm, step=10.0, key='Lb_projeto')
        Cb_projeto = st.number_input("Fator de Modificação (Cb)", 1.0, 3.0, 1.10, key='Cb_projeto')

    st.header("4. Modo de Análise")
    analysis_mode = st.radio("Selecione o modo de análise:", ("Análise em Lote com Otimização", "Memorial Detalhado de um Perfil"), horizontal=True, label_visibility="collapsed", key='analysis_mode')

    st.session_state.input_parameters = {'tipo_viga': tipo_viga, 'L_cm': L_cm, 'input_mode': input_mode,'Msd': Msd, 'Vsd': Vsd, 'q_servico_kn_cm': q_servico_kn_cm, 'p_load_serv': p_load_serv, 'fy_aco': fy_aco, 'Lb_projeto': Lb_projeto, 'Cb_projeto': Cb_projeto,'input_details_html': input_details_html, 'detalhes_esforcos': detalhes_esforcos}

    if analysis_mode == "Memorial Detalhado de um Perfil":
        left_col, right_col = st.columns([2, 3])

        with left_col:
            st.header("🔍 Seleção do Perfil")
            selected_display_name = st.selectbox("Selecione o Tipo de Perfil:", display_names)
            sheet_name = reverse_name_map.get(selected_display_name, selected_display_name)
            df_selecionado = all_sheets[sheet_name]
            perfil_selecionado_nome = st.selectbox("Selecione o Perfil Específico:", df_selecionado['Bitola (mm x kg/m)'])
            if st.button("Gerar Memorial Completo", type="primary", use_container_width=True):
                run_detailed_analysis(df_selecionado, perfil_selecionado_nome, selected_display_name, st.session_state.input_parameters)
        
        with right_col:
            if st.session_state.detailed_analysis_html:
                st.header("📄 Memorial de Cálculo")
                with st.expander("Clique para expandir ou recolher o memorial", expanded=True):
                    st.components.v1.html(st.session_state.detailed_analysis_html, height=1000, scrolling=True)
                    st.download_button(
                        label="📥 Baixar Memorial HTML",
                        data=st.session_state.detailed_analysis_html.encode('utf-8'),
                        file_name=f"Memorial_{perfil_selecionado_nome.replace(' ', '_')}.html",
                        mime="text/html",
                        use_container_width=True
                    )
            else:
                st.info("⬅️ Preencha os parâmetros, selecione um perfil e clique em 'Gerar Memorial' para ver o resultado aqui.")
    
    elif analysis_mode == "Análise em Lote com Otimização":
        # ... (código da análise em lote) ...

# ==============================================================================
# 5. FUNÇÕES DE ORQUESTRAÇÃO, ANÁLISE E CÁLCULO
# ==============================================================================
# ... (Todas as demais funções, que já estão corretas, vêm aqui) ...

if __name__ == '__main__':
    main()

