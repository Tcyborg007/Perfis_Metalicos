import streamlit as st
import pandas as pd
import math

# ==============================================================================
# 1. CONFIGURAÇÕES E CONSTANTES GLOBAIS
# ==============================================================================

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

st.set_page_config(page_title="Calculadora Estrutural - Perfis Metálicos", layout="wide")

HTML_TEMPLATE_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&family=Roboto+Slab:wght@400;700&display=swap');
    body { font-family: 'Roboto', sans-serif; line-height: 1.8; color: #333; background-color: #f0f4f8; }
    .container { margin: 20px auto; padding: 1rem; background-color: white; border-radius: 10px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); width: 100%; box-sizing: border-box; }
    h1, h2, h3, h4, h5 { font-family: 'Roboto Slab', serif; color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 5px; margin-top: 30px; }
    h1 { text-align: center; border: none; font-size: 2.2em; }
    h5 { border-bottom: none; font-size: 1em; margin-top: 15px; color: #34495e;}
    .summary-table { width: 100%; border-collapse: collapse; margin-bottom: 20px; font-size: 0.9em; }
    .summary-table th, .summary-table td { border: 1px solid #ddd; padding: 8px; text-align: center; vertical-align: middle; }
    .summary-table th { background-color: #34495e; color: white; }
    .formula-block { background-color: #f9fbfc; border-left: 5px solid #3498db; padding: 20px; margin: 20px 0; border-radius: 5px; }
    .pass { color: #27ae60; font-weight: bold; }
    .fail { color: #e74c3c; font-weight: bold; }
    .formula { font-size: 1.2em; text-align: center; margin: 10px 0; word-wrap: break-word; overflow-x: auto; padding: 8px; background-color: #f0f2f5; border-radius: 4px;}
    .final-result { font-weight: bold; color: #3498db; text-align: center; display: block; margin-top: 15px; font-size: 1.2em; padding: 8px; border: 1px solid #3498db; border-radius: 5px; background-color: #eafaf1;}
    .final-status { font-size: 1.5em; text-align: center; padding: 10px; border-radius: 5px; margin-top: 15px; }
    .final-status.pass { background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb;}
    .final-status.fail { background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb;}
    .ref-norma { font-size: 0.8em; color: #7f8c8d; text-align: right; margin-top: 15px; font-style: italic; }
    p { text-align: justify; }
    
    @media (max-width: 600px) {
        .container {
            padding: 10px;
        }
        h1 { font-size: 1.8em; }
        .summary-table, .summary-table th, .summary-table td {
            font-size: 0.8em;
            display: block;
            width: 100%;
            box-sizing: border-box;
        }
        .summary-table thead, .summary-table tbody, .summary-table tr, .summary-table th, .summary-table td {
            display: block;
        }
        .summary-table tr {
            margin-bottom: 15px;
            border: 1px solid #ddd;
        }
        .summary-table td {
            text-align: right;
            padding-left: 50%;
            position: relative;
            word-wrap: break-word;
        }
        .summary-table td::before {
            content: attr(data-label);
            position: absolute;
            left: 6px;
            width: 45%;
            padding-right: 10px;
            white-space: nowrap;
            text-align: left;
            font-weight: bold;
        }
    }
    
    /* Regras de impressão para formatar como A4 */
    @media print {
        body {
            background-color: white;
            font-size: 12pt;
        }
        .container {
            max-width: 8.5in;
            margin: 0;
            padding: 0.75in;
            box-shadow: none;
            border-radius: 0;
        }
        .streamlit-container {
            display: none; /* Esconde a interface do Streamlit ao imprimir */
        }
    }
</style>
"""
st.markdown(HTML_TEMPLATE_CSS, unsafe_allow_html=True)

# ==============================================================================
# 2. FUNÇÕES DE CÁLCULO DE ENGENHARIA
# ==============================================================================

def calcular_esforcos_viga(tipo_viga, L_cm, q_kn_cm=0, p_load=None):
    msd_q, vsd_q, msd_p, vsd_p = 0, 0, 0, 0
    L = L_cm
    
    msd_q_formula, vsd_q_formula = "", ""
    msd_p_formula, vsd_p_formula = "", ""
    
    # Parte da carga distribuída (q)
    if q_kn_cm > 0:
        if tipo_viga == 'Bi-apoiada':
            msd_q = (q_kn_cm * L**2) / 8
            vsd_q = (q_kn_cm * L) / 2
            msd_q_formula = f"M_{{sd, q}} = \\frac{{q_{{última}} \\cdot L^2}}{8}"
            vsd_q_formula = f"V_{{sd, q}} = \\frac{{q_{{última}} \\cdot L}}{2}"
        elif tipo_viga == 'Engastada e Livre (Balanço)':
            msd_q = (q_kn_cm * L**2) / 2
            vsd_q = q_kn_cm * L
            msd_q_formula = f"M_{{sd, q}} = \\frac{{q_{{última}} \\cdot L^2}}{2}"
            vsd_q_formula = f"V_{{sd, q}} = q_{{última}} \\cdot L"
        elif tipo_viga == 'Bi-engastada':
            msd_q = (q_kn_cm * L**2) / 12 # Momento no engaste
            vsd_q = (q_kn_cm * L) / 2
            msd_q_formula = f"M_{{sd, q}} = \\frac{{q_{{última}} \\cdot L^2}}{12}"
            vsd_q_formula = f"V_{{sd, q}} = \\frac{{q_{{última}} \\cdot L}}{2}"
        elif tipo_viga == 'Engastada e Apoiada':
            msd_q = (q_kn_cm * L**2) / 8
            vsd_q = (5 * q_kn_cm * L) / 8
            msd_q_formula = f"M_{{sd, q}} = \\frac{{q_{{última}} \\cdot L^2}}{8}"
            vsd_q_formula = f"V_{{sd, q}} = \\frac{{5 \\cdot q_{{última}} \\cdot L}}{8}"
            
    # Parte da carga pontual (P)
    if p_load:
        P, x = p_load # P em kN, x em cm
        a = x
        b = L - a
        if tipo_viga == 'Bi-apoiada':
            msd_p = (P * a * b) / L
            vsd_p = max((P * b) / L, (P * a) / L)
            msd_p_formula = f"M_{{sd, P}} = \\frac{{P_{{última}} \\cdot a \\cdot b}}{L}"
            vsd_p_formula = f"V_{{sd, P}} = \\max(\\frac{{P_{{última}} \\cdot b}}{L}, \\frac{{P_{{última}} \\cdot a}}{L})"
        elif tipo_viga == 'Engastada e Livre (Balanço)':
            msd_p = P * a # Momento no engaste
            vsd_p = P
            msd_p_formula = f"M_{{sd, P}} = P_{{última}} \\cdot a"
            vsd_p_formula = f"V_{{sd, P}} = P_{{última}}"
        # Simplificando para tipos de viga complexos, como no código original
        # para evitar cálculos excessivamente complexos no memorial
        
    msd_total = msd_q + msd_p
    vsd_total = vsd_q + vsd_p
    
    detalhes_esforcos = {
        'Msd_q': {'valor': msd_q, 'formula': msd_q_formula, 'unidade': 'kN.cm'},
        'Vsd_q': {'valor': vsd_q, 'formula': vsd_q_formula, 'unidade': 'kN'},
        'Msd_p': {'valor': msd_p, 'formula': msd_p_formula, 'unidade': 'kN.cm'},
        'Vsd_p': {'valor': vsd_p, 'formula': vsd_p_formula, 'unidade': 'kN'}
    }
    
    return msd_total, vsd_total, detalhes_esforcos

def calcular_flecha_maxima(tipo_viga, L_cm, E, Ix, q_serv_kn_cm=0, p_serv_load=None):
    delta_q, delta_p = 0, 0
    L = L_cm
    
    if q_serv_kn_cm > 0:
        if tipo_viga == 'Bi-apoiada':
            delta_q = (5 * q_serv_kn_cm * L**4) / (384 * E * Ix)
        elif tipo_viga == 'Engastada e Livre (Balanço)':
            delta_q = (q_serv_kn_cm * L**4) / (8 * E * Ix)
        elif tipo_viga == 'Bi-engastada':
            delta_q = (q_serv_kn_cm * L**4) / (384 * E * Ix)
        elif tipo_viga == 'Engastada e Apoiada':
            delta_q = (q_serv_kn_cm * L**4) / (185 * E * Ix)
            
    if p_serv_load:
        P, x = p_serv_load
        a = x
        b = L-a
        if tipo_viga == 'Bi-apoiada':
            if a >= L/2: a,b = b,a
            delta_p = (P * a * (L**2 - a**2)**1.5) / (9 * math.sqrt(3) * E * Ix * L) if a < L else 0
        elif tipo_viga == 'Engastada e Livre (Balanço)':
            delta_p = (P * a**2 * (3*L - a)) / (6 * E * Ix)
        elif tipo_viga == 'Bi-engastada':
            delta_p = (P * a**3 * b**3) / (3 * E * Ix * L**3)
        elif tipo_viga == 'Engastada e Apoiada':
            if a < b: delta_p = (P * a**2 * b**2 * (3*L+a))/(12*E*Ix*L**3)
            else: delta_p = (P * b * (L**2 - b**2)**1.5)/(9*math.sqrt(3)*E*Ix*L)

    return delta_q + delta_p

def get_profile_properties(profile_series):
    props = {"d": profile_series.get('d (mm)'),"bf": profile_series.get('bf (mm)'),"tw": profile_series.get('tw (mm)'),"tf": profile_series.get('tf (mm)'),"h": profile_series.get('h (mm)'),"Area": profile_series.get('Área (cm2)'),"Ix": profile_series.get('Ix (cm4)'),"Wx": profile_series.get('Wx (cm3)'),"rx": profile_series.get('rx (cm)'),"Zx": profile_series.get('Zx (cm3)'),"Iy": profile_series.get('Iy (cm4)'),"Wy": profile_series.get('Wy (cm3)'),"ry": profile_series.get('ry (cm)'),"Zy": profile_series.get('Zy (cm3)'),"J": profile_series.get('It (cm4)'),"Cw": profile_series.get('Cw (cm6)'),"Peso": profile_series.get('Massa Linear (kg/m)', profile_series.get('Peso (kg/m)'))}
    required_keys = ["d", "bf", "tw", "tf", "h", "Area", "Ix", "Wx", "rx", "Zx", "Iy", "ry", "J", "Cw", "Peso"]
    profile_name = profile_series.get('Bitola (mm x kg/m)', 'Perfil Desconhecido')
    for key in required_keys:
        value = props.get(key)
        if value is None or pd.isna(value) or (isinstance(value, (int, float)) and value <= 0):
            raise ValueError(f"Propriedade ESSENCIAL '{key}' inválida ou nula no Excel para '{profile_name}'. Verifique a planilha.")
    for key in ['d', 'bf', 'tw', 'tf', 'h']: props[key] /= 10.0
    return props

# ==============================================================================
# 3. GERAÇÃO DO MEMORIAL DE CÁLCULO
# ==============================================================================
def gerar_memorial_completo(perfil_nome, perfil_tipo, resultados, input_details):
    # Removido o botão de download daqui
    html = f"""
    <!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8"><title>Memorial de Cálculo - {perfil_nome}</title>{HTML_TEMPLATE_CSS}<script type="text/javascript" async src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.7/MathJax.js?config=TeX-MML-AM_CHTML"></script></head><body><div class="container"><h1>Memorial de Cálculo Estrutural</h1><h2>Perfil Metálico: {perfil_nome} ({perfil_tipo})</h2><p style="text-align:center; font-style:italic;">Cálculos baseados na norma: <b>{Config.NOME_NORMA}</b></p><h3>1. Resumo Final das Verificações</h3>{resultados['resumo_html']}{input_details}{resultados['passo_a_passo_html']}</div></body></html>"""
    return html

def _build_verification_block_html(title, solicitante, s_symbol, resistente, r_symbol, eficiencia, status, unit):
    status_class = "pass" if status == "APROVADO" else "fail"
    comp_symbol = "\\le" if status == "APROVADO" else ">"
    return f"""<h4>{title}</h4><div class="formula-block"><p class="formula">$$ {s_symbol} = {solicitante:.2f} \\, {unit} $$</p><p class="formula">$$ {r_symbol} = {resistente:.2f} \\, {unit} $$</p><p class="formula">$$ \\text{{Verificação: }} {s_symbol} {comp_symbol} {r_symbol} $$</p><p class="formula">$$ \\text{{Eficiência}} = \\frac{{{s_symbol}}}{{{r_symbol}}} = \\frac{{{solicitante:.2f}}}{{{resistente:.2f}}} = {eficiencia:.1f}\% $$</p><div class="final-status {status_class}">{status}</div></div>"""

# ==============================================================================
# 4. APLICAÇÃO PRINCIPAL STREAMLIT (COM AS ALTERAÇÕES)
# ==============================================================================

# NOVA FUNÇÃO DE CARREGAMENTO AUTOMÁTICO
@st.cache_data
def load_data_from_local_file():
    """
    Esta função carrega os dados diretamente do arquivo 'perfis.xlsx'
    que está na mesma pasta do projeto.
    """
    try:
        # O nome do arquivo Excel deve ser exatamente este
        caminho_arquivo_excel = 'perfis.xlsx'
        return pd.read_excel(caminho_arquivo_excel, sheet_name=None)
    except FileNotFoundError:
        st.error(f"Erro: Arquivo '{caminho_arquivo_excel}' não foi encontrado. Verifique se ele está no mesmo repositório do GitHub que o arquivo 'app.py'.")
        return None
    except Exception as e:
        st.error(f"Erro ao ler o arquivo Excel: {e}")
        return None

def main():
    # Inicializa o estado da sessão para armazenar os resultados
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = None
    if 'detailed_analysis_html' not in st.session_state:
        st.session_state.detailed_analysis_html = None
    
    st.title("🏛️ Calculadora Estrutural - Perfis Metálicos")
    st.caption(f"Utilizando a norma: {Config.NOME_NORMA}")

    # CARREGAMENTO AUTOMÁTICO DOS DADOS
    all_sheets = load_data_from_local_file()

    # Para a aplicação se os dados não puderem ser carregados
    if not all_sheets:
        st.stop()

    # Mapeamento dos nomes das abas (necessário no início da main)
    display_names = [PROFILE_TYPE_MAP.get(name, name) for name in all_sheets.keys()]
    reverse_name_map = {v: k for k, v in PROFILE_TYPE_MAP.items()}
    
    # --- ENTRADA DE DADOS NA SIDEBAR ---
    with st.sidebar:
        st.header("⚙️ Parâmetros de Entrada")
        
        st.header("1. Modelo da Viga")
        # st.selectbox agora tem um key para identificar a mudança e limpar a sessão
        tipo_viga = st.selectbox("Tipo de Viga:", ('Bi-apoiada', 'Engastada e Livre (Balanço)', 'Bi-engastada', 'Engastada e Apoiada'), key='tipo_viga')
        L_cm = st.number_input("Comprimento da Viga (L, cm)", 10.0, value=500.0, step=10.0, key='L_cm')

        st.header("2. Modo de Carregamento")
        input_mode = st.radio("Selecione o modo de entrada dos esforços:", ("Calcular a partir de Cargas na Viga", "Inserir Esforços Manualmente"), horizontal=True, label_visibility="collapsed", key='input_mode')

        Msd, Vsd, q_servico_kn_cm, p_load_serv = 0, 0, 0, None
        
        input_details_html = "" # Para o memorial
        detalhes_esforcos = None
        
        if input_mode == "Calcular a partir de Cargas na Viga":
            with st.container(border=True):
                st.subheader("Carga Distribuída (q)")
                st.markdown("##### Definição da Área de Influência")
                larg_esq_cm = st.number_input("Largura da laje à esquerda (cm)", 0.0, value=200.0, step=10.0, key='larg_esq_cm')
                larg_dir_cm = st.number_input("Largura da laje à direita (cm)", 0.0, value=200.0, step=10.0, key='larg_dir_cm')

                larg_inf_total_m = (larg_esq_cm / 100.0 / 2) + (larg_dir_cm / 100.0 / 2)
                st.info(f"Largura de Influência Total (B) = {larg_inf_total_m:.2f} m")

                carga_area = st.number_input("Carga Distribuída (serviço, kN/m²)", 0.0, value=4.0, step=0.5, key='carga_area')

                st.subheader("Carga Pontual (P)")
                add_p_load = st.checkbox("Adicionar Carga Pontual (ex: parede)", key='add_p_load')
                if add_p_load:
                    p_serv_kn = st.number_input("Valor da Carga P (serviço, kN)", min_value=0.0, value=10.0, key='p_serv_kn')
                    p_pos_cm = st.number_input("Posição da Carga P (x, cm do apoio esquerdo)", min_value=0.0, max_value=L_cm, value=L_cm/2, key='p_pos_cm')
                    p_load_serv = (p_serv_kn, p_pos_cm)
                else:
                    p_serv_kn = 0
                    p_pos_cm = 0

                gamma_f = st.number_input("Coeficiente de Majoração de Cargas (γf)", 1.0, value=1.4, step=0.1, key='gamma_f')
                
                q_servico_kn_m = (carga_area * larg_inf_total_m)
                q_servico_kn_cm = q_servico_kn_m / 100.0
                q_ult_kn_cm = q_servico_kn_cm * gamma_f
                p_load_ult = (p_load_serv[0] * gamma_f, p_load_serv[1]) if p_load_serv else None
                
                Msd, Vsd, detalhes_esforcos = calcular_esforcos_viga(tipo_viga, L_cm, q_ult_kn_cm, p_load_ult)

                input_details_html = f"""
                <h2>2. Cálculo dos Esforços Solicitantes</h2>
                <h3>2.1 Carga Distribuída</h3>
                <div class="formula-block">
                    <h4>a. Determinação da Área de Influência</h4>
                    <p class="formula">$$ \\text{{Área de Influência}} (B) = \\frac{{Laje_{{esq}}}}{2} + \\frac{{Laje_{{dir}}}}{2} $$</p>
                    <p class="formula">$$ B = \\frac{{{larg_esq_cm:.2f}}}{2} + \\frac{{{larg_dir_cm:.2f}}}{2} = {larg_inf_total_m * 100:.2f} \\, cm = {larg_inf_total_m:.2f} \\, m $$</p>
                    <h4>b. Carga Distribuída por metro linear (q)</h4>
                    <p class="formula">$$ q_{{serviço}} = \\text{{Carga}} \\times B = {carga_area:.2f} \\, kN/m^2 \\times {larg_inf_total_m:.2f} \\, m = {q_servico_kn_m:.2f} \\, kN/m $$</p>
                    <p class="formula">$$ q_{{última}} = q_{{serviço}} \\times \\gamma_f = {q_servico_kn_m:.2f} \\, kN/m \\times {gamma_f:.2f} = {q_ult_kn_cm * 100:.2f} \\, kN/m $$</p>
                </div>
                """
                if add_p_load:
                    input_details_html += f"""
                    <h3>2.2 Carga Pontual</h3>
                    <div class="formula-block">
                        <p class="formula">$$ P_{{serviço}} = {p_serv_kn:.2f} \\, kN $$</p>
                        <p class="formula">$$ P_{{última}} = P_{{serviço}} \\times \\gamma_f = {p_serv_kn:.2f} \\times {gamma_f:.2f} = {p_load_ult[0]:.2f} \\, kN $$</p>
                        <p class="formula">$$ x = {p_pos_cm:.2f} \\, cm $$</p>
                    </div>
                    """
                
                input_details_html += f"""
                <h3>2.3 Cálculo dos Esforços Finais na Viga</h3>
                <div class="formula-block">
                    <h4>Momento Fletor Solicitante de Cálculo (Msd) </h4>
                    <p class="formula">$$ M_{{sd}} = M_{{sd, q}} + M_{{sd, P}} $$</p>
                    <p class="formula">$$ \\text{{Para carga distribuída: }} {detalhes_esforcos['Msd_q']['formula']} = \\frac{{{q_ult_kn_cm * 100:.2f} \\, kN/m \\times ({L_cm/100:.2f} \\, m)^2}}{8} = {detalhes_esforcos['Msd_q']['valor']/100:.2f} \\, kNm $$</p>
                    {"<p class='formula'>$$ \\text{{Para carga pontual: }} " + detalhes_esforcos['Msd_p']['formula'] + f" = {detalhes_esforcos['Msd_p']['valor']/100:.2f} \\, kNm $$</p>" if add_p_load and detalhes_esforcos['Msd_p']['formula'] else ""}
                    <p class="formula">$$ M_{{sd}} = {Msd/100:.2f} \\, kNm $$</p>
                    <h4>Força Cortante Solicitante de Cálculo (Vsd) </h4>
                    <p class="formula">$$ V_{{sd}} = V_{{sd, q}} + V_{{sd, P}} $$</p>
                    <p class="formula">$$ \\text{{Para carga distribuída: }} {detalhes_esforcos['Vsd_q']['formula']} = \\frac{{{q_ult_kn_cm * 100:.2f} \\, kN/m \\times {L_cm/100:.2f} \\, m}}{2} = {detalhes_esforcos['Vsd_q']['valor']:.2f} \\, kN $$</p>
                    {"<p class='formula'>$$ \\text{{Para carga pontual: }} " + detalhes_esforcos['Vsd_p']['formula'] + f" = {detalhes_esforcos['Vsd_p']['valor']:.2f} \\, kN $$</p>" if add_p_load and detalhes_esforcos['Vsd_p']['formula'] else ""}
                    <p class="formula">$$ V_{{sd}} = {Vsd:.2f} \\, kN $$</p>
                </div>
                """
        else: # Inserir Esforços Manualmente
            with st.container(border=True):
                st.warning("No modo manual, a verificação de flecha (ELS) não é realizada.")
                msd_input = st.number_input("Momento Solicitante de Cálculo (Msd, kNm)", min_value=0.0, value=100.0, key='msd_input')
                Msd = msd_input * 100 # Convertendo para kN.cm
                Vsd = st.number_input("Força Cortante Solicitante de Cálculo (Vsd, kN)", min_value=0.0, value=50.0, key='vsd_input')
                input_details_html = f"""
                <h2>2. Cálculo dos Esforços Solicitantes</h2>
                <p>Neste modo, os esforços solicitantes foram inseridos diretamente pelo usuário.</p>
                <div class="formula-block">
                    <p class="formula">$$ M_{{sd}} = {Msd/100:.2f} \\, kNm $$</p>
                    <p class="formula">$$ V_{{sd}} = {Vsd:.2f} \\, kN $$</p>
                </div>
                """
                q_servico_kn_cm = 0 # Reiniciar para a verificação de flecha não ser executada
                p_load_serv = None

        st.header("3. Parâmetros Gerais do Aço")
        fy_aco = st.number_input("Tensão de Escoamento (fy, kN/cm²)", 20.0, 50.0, 34.5, 0.5, key='fy_aco')
        Lb_projeto = st.number_input("Comprimento Destravado (Lb, cm)", 10.0, value=L_cm, step=10.0, key='Lb_projeto')
        Cb_projeto = st.number_input("Fator de Modificação (Cb)", 1.0, 3.0, 1.10, key='Cb_projeto')
    
    # --- MODO DE ANÁLISE NA INTERFACE PRINCIPAL ---
    st.header("4. Modo de Análise")
    analysis_mode = st.radio("Selecione o modo de análise:", ("Análise em Lote com Otimização", "Memorial Detalhado de um Perfil"), horizontal=True, label_visibility="collapsed", key='analysis_mode')

    # Salva os parâmetros de entrada no estado da sessão
    st.session_state.input_parameters = {
        'tipo_viga': tipo_viga, 'L_cm': L_cm, 'input_mode': input_mode,
        'Msd': Msd, 'Vsd': Vsd, 'q_servico_kn_cm': q_servico_kn_cm, 
        'p_load_serv': p_load_serv, 'fy_aco': fy_aco, 
        'Lb_projeto': Lb_projeto, 'Cb_projeto': Cb_projeto,
        'input_details_html': input_details_html, 'detalhes_esforcos': detalhes_esforcos
    }

    if analysis_mode == "Memorial Detalhado de um Perfil":
        st.header("🔍 Memorial de Cálculo Detalhado")
        selected_display_name = st.selectbox("Selecione o Tipo de Perfil:", display_names)
        sheet_name = reverse_name_map.get(selected_display_name, selected_display_name)
        df_selecionado = all_sheets[sheet_name]
        perfil_selecionado_nome = st.selectbox("Selecione o Perfil Específico:", df_selecionado['Bitola (mm x kg/m)'])
        if st.button("Gerar Memorial Completo", type="primary", use_container_width=True):
            run_detailed_analysis(df_selecionado, perfil_selecionado_nome, selected_display_name, st.session_state.input_parameters)

        if st.session_state.detailed_analysis_html:
            st.components.v1.html(st.session_state.detailed_analysis_html, height=1000, scrolling=True)
            st.download_button(label="📥 Baixar Memorial HTML", data=st.session_state.detailed_analysis_html.encode('utf-8'), file_name=f"Memorial_{perfil_selecionado_nome.replace(' ', '_')}.html", mime="text/html")


    elif analysis_mode == "Análise em Lote com Otimização":
        st.header("📊 Pré-dimensionamento e Análise por Categoria")
        st.info("Analisa todos os perfis e organiza os resultados em abas por tipo, destacando os 5 perfis mais leves de cada categoria.")
        
        st.subheader("Esforços Solicitantes para a Análise em Lote")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Momento Solicitante de Cálculo (Msd)", f"{Msd/100:.2f} kNm")
        with col2:
            st.metric("Força Cortante Solicitante de Cálculo (Vsd)", f"{Vsd:.2f} kN")
            
        if st.button("Iniciar Análise Otimizada", type="primary", use_container_width=True):
            run_batch_analysis(all_sheets, st.session_state.input_parameters)

        # Se houver resultados armazenados, exibe-os
        if st.session_state.analysis_results is not None:
            df_all_results = st.session_state.analysis_results
            st.success(f"{len(df_all_results)} perfis analisados.")
            tab_names = [PROFILE_TYPE_MAP.get(name, name) for name in all_sheets.keys()]
            tabs = st.tabs(tab_names)
            def style_dataframe(df):
                def color_efficiency(val):
                    if pd.isna(val) or not isinstance(val, (int, float)): return ''
                    if val > 100:   color = '#f8d7da'
                    elif val > 95:  color = '#ffeeba'
                    elif val > 80:  color = '#fff3cd'
                    else:           color = '#d4edda'
                    return f'background-color: {color}'
                efficiency_cols = [col for col in df.columns if '%' in col]
                return df.style.applymap(color_efficiency, subset=efficiency_cols).format(
                    {"Peso (kg/m)": "{:.2f}"}
                ).format("{:.1f}", subset=efficiency_cols)
            for i, sheet_name in enumerate(all_sheets.keys()):
                with tabs[i]:
                    df_type = df_all_results[df_all_results['Tipo'] == sheet_name].drop(columns=['Tipo'])
                    if df_type.empty:
                        st.write("Nenhum perfil desta categoria foi analisado.")
                        continue
                    aprovados = df_type[df_type['Status'] == 'APROVADO'].copy()
                    reprovados = df_type[df_type['Status'] == 'REPROVADO'].copy()
                    
                    st.subheader("🔍 Dados de Análise em Lote")
                    st.markdown(f"""
                    <div style="background-color: #f0f2f5; padding: 10px; border-radius: 5px; margin-bottom: 20px;">
                        <p><b>Parâmetros utilizados na análise:</b></p>
                        <ul>
                            <li>Momento Solicitante (Msd): <b>{st.session_state.input_parameters['Msd']/100:.2f} kNm</b></li>
                            <li>Força Cortante (Vsd): <b>{st.session_state.input_parameters['Vsd']:.2f} kN</b></li>
                            <li>Comprimento da Viga (L): <b>{st.session_state.input_parameters['L_cm']:.2f} cm</b></li>
                            <li>Tensão de Escoamento (fy): <b>{st.session_state.input_parameters['fy_aco']:.2f} kN/cm²</b></li>
                        </ul>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if not aprovados.empty:
                        aprovados.sort_values(by='Peso (kg/m)', inplace=True)
                        st.subheader("🏆 5 Perfis Mais Leves Aprovados (Otimizados)")
                        st.dataframe(style_dataframe(aprovados.head(5)), use_container_width=True)
                        with st.expander("Ver todos os perfis aprovados desta categoria"):
                            st.dataframe(style_dataframe(aprovados), use_container_width=True)
                    else: st.info("Nenhum perfil desta categoria foi aprovado.")
                    if not reprovados.empty:
                        with st.expander("Ver perfis reprovados desta categoria"):
                            st.dataframe(style_dataframe(reprovados), use_container_width=True)


# ==============================================================================
# 5. FUNÇÕES DE ORQUESTRAÇÃO E ANÁLISE
# ==============================================================================

def run_detailed_analysis(df, perfil_nome, perfil_tipo_display, input_params):
    with st.spinner(f"Gerando análise completa para {perfil_nome}..."):
        try:
            perfil_series = df[df['Bitola (mm x kg/m)'] == perfil_nome].iloc[0]
            props = get_profile_properties(perfil_series)
            # Desempacota as 6 variáveis retornadas
            res_flt, res_flm, res_fla, res_cis, res_flecha, passo_a_passo = perform_all_checks(props, input_params['fy_aco'], input_params['Lb_projeto'], input_params['Cb_projeto'], input_params['L_cm'], input_params['Msd'], input_params['Vsd'], input_params['q_servico_kn_cm'], input_params['p_load_serv'], input_params['tipo_viga'], input_params['input_mode'], detalhado=True)
            
            # Recria o dicionário res_flexao para a função build_summary_html
            Mrd_final = min(res_flt['Mrdx'], res_flm['Mrdx'], res_fla['Mrdx'])
            ef_geral = (input_params['Msd'] / Mrd_final) * 100 if Mrd_final > 0 else float('inf')
            status_flexao = "APROVADO" if ef_geral <= 100.1 else "REPROVADO"
            res_flexao = {'Mrd': Mrd_final, 'eficiencia': ef_geral, 'status': status_flexao, 'ef_flt': res_flt['eficiencia'], 'ef_flm': res_flm['eficiencia'], 'ef_fla': res_fla['eficiencia']}
            
            # Passa os dicionários de resultados diretamente para a função build_summary_html
            resumo_html = build_summary_html(input_params['Msd'], input_params['Vsd'], res_flt, res_flm, res_fla, res_cis, res_flecha)
            resultados = {'resumo_html': resumo_html, 'passo_a_passo_html': passo_a_passo}
            html_content = gerar_memorial_completo(perfil_nome, perfil_tipo_display, resultados, input_params['input_details_html'])
            
            st.session_state.detailed_analysis_html = html_content
            st.success("Análise concluída!")

        except (ValueError, KeyError) as e: st.error(f"❌ Erro nos Dados de Entrada: {e}")
        except Exception as e: st.error(f"❌ Ocorreu um erro inesperado: {e}")

def run_batch_analysis(all_sheets, input_params):
    all_results = []
    progress_bar = st.progress(0, text="Analisando perfis...")
    total_perfis = sum(len(df) for df in all_sheets.values())
    perfis_processados = 0
    with st.spinner("Processando todos os perfis..."):
        for sheet_name, df in all_sheets.items():
            for _, row in df.iterrows():
                perfis_processados += 1
                progress_bar.progress(perfis_processados / total_perfis)
                try:
                    props = get_profile_properties(row)
                    # Desempacota as 6 variáveis retornadas
                    res_flt, res_flm, res_fla, res_cis, res_flecha, _ = perform_all_checks(props, input_params['fy_aco'], input_params['Lb_projeto'], input_params['Cb_projeto'], input_params['L_cm'], input_params['Msd'], input_params['Vsd'], input_params['q_servico_kn_cm'], input_params['p_load_serv'], input_params['tipo_viga'], input_params['input_mode'])
                    
                    status_geral = "APROVADO"
                    if res_flt['eficiencia'] > 100.1 or res_flm['eficiencia'] > 100.1 or res_fla['eficiencia'] > 100.1 or res_cis['eficiencia'] > 100.1 or res_flecha['eficiencia'] > 100.1:
                        status_geral = "REPROVADO"
                    
                    all_results.append({
                        'Tipo': sheet_name, 
                        'Perfil': row['Bitola (mm x kg/m)'], 
                        'Peso (kg/m)': props.get('Peso', 0), 
                        'Status': status_geral, 
                        'Ef. FLT (%)': res_flt['eficiencia'],
                        'Ef. FLM (%)': res_flm['eficiencia'],
                        'Ef. FLA (%)': res_fla['eficiencia'],
                        'Ef. Cisalhamento (%)': res_cis['eficiencia'], 
                        'Ef. Flecha (%)': res_flecha['eficiencia']
                    })
                except (ValueError, KeyError): 
                    continue
    progress_bar.empty()
    if not all_results:
        st.error("Não foi possível analisar nenhum perfil.")
        st.session_state.analysis_results = None
        return
    df_all_results = pd.DataFrame(all_results)
    st.session_state.analysis_results = df_all_results
    st.success(f"{len(df_all_results)} perfis analisados.")

def perform_all_checks(props, fy, Lb, Cb, L, Msd, Vsd, q_serv_kn_cm, p_serv_load, tipo_viga, input_mode, detalhado=False):
    res_flt = _calcular_mrdx_flt(props, Lb, Cb, fy)
    res_flm = _calcular_mrdx_flm(props, fy)
    res_fla = _calcular_mrdx_fla(props, fy)
    res_vrd = _calcular_vrd(props, fy)
    
    # ======================================================================
    # Ajuste na lógica para calcular a eficiência aqui e adicionar aos dicionários
    # ======================================================================
    if res_flt['Mrdx'] > 0:
        res_flt['eficiencia'] = (Msd / res_flt['Mrdx']) * 100
    else:
        res_flt['eficiencia'] = float('inf')

    if res_flm['Mrdx'] > 0:
        res_flm['eficiencia'] = (Msd / res_flm['Mrdx']) * 100
    else:
        res_flm['eficiencia'] = float('inf')

    if res_fla['Mrdx'] > 0:
        res_fla['eficiencia'] = (Msd / res_fla['Mrdx']) * 100
    else:
        res_fla['eficiencia'] = float('inf')

    Vrd = res_vrd['Vrd']
    if Vrd > 0:
        res_cis = {'Vrd': Vrd, 'eficiencia': (Vsd / Vrd) * 100, 'status': "APROVADO" if (Vsd / Vrd) * 100 <= 100.1 else "REPROVADO"}
    else:
        res_cis = {'Vrd': Vrd, 'eficiencia': float('inf'), 'status': "REPROVADO"}

    flecha_max, flecha_limite, eficiencia_flecha, status_flecha = 0, 0, 0, "N/A"
    if input_mode == "Calcular a partir de Cargas na Viga":
        flecha_max = calcular_flecha_maxima(tipo_viga, L, Config.E_ACO, props['Ix'], q_serv_kn_cm, p_serv_load)
        flecha_limite = L / Config.LIMITE_FLECHA_TOTAL if L > 0 else 0
        eficiencia_flecha = (flecha_max / flecha_limite) * 100 if flecha_limite > 0 else float('inf')
        status_flecha = "APROVADO" if eficiencia_flecha <= 100.1 else "REPROVADO"
    else: # Modo manual
        status_flecha = "N/A"
    
    res_flecha = {'flecha_max': flecha_max, 'flecha_limite': flecha_limite, 'eficiencia': eficiencia_flecha, 'status': status_flecha, 'Ix': props['Ix']}

    # Resumo da flexão geral para o memorial
    Mrd_final = min(res_flt['Mrdx'], res_flm['Mrdx'], res_fla['Mrdx'])
    ef_geral = (Msd / Mrd_final) * 100 if Mrd_final > 0 else float('inf')
    status_flexao = "APROVADO" if ef_geral <= 100.1 else "REPROVADO"
    res_flexao = {'Mrd': Mrd_final, 'eficiencia': ef_geral, 'status': status_flexao}
    
    passo_a_passo_html = ""
    if detalhado:
        # A função build_step_by_step_html precisa dos dicionários de resultados completos
        passo_a_passo_html = build_step_by_step_html(L, Msd, Vsd, res_flexao, res_cis, res_flecha, res_flt, res_flm, res_fla, res_vrd, input_mode)
    
    # Retorna os dicionários completos para as funções de orquestração
    return res_flt, res_flm, res_fla, res_cis, res_flecha, passo_a_passo_html

def build_summary_html(Msd, Vsd, res_flt, res_flm, res_fla, res_cisalhamento, res_flecha):
    verificacoes = [
        ('Flexão (FLT) - ELU', f"{Msd/100:.2f} kNm", f"{res_flt['Mrdx']/100:.2f} kNm", res_flt['eficiencia'], "APROVADO" if res_flt['eficiencia'] <= 100.1 else "REPROVADO"),
        ('Flexão (FLM) - ELU', f"{Msd/100:.2f} kNm", f"{res_flm['Mrdx']/100:.2f} kNm", res_flm['eficiencia'], "APROVADO" if res_flm['eficiencia'] <= 100.1 else "REPROVADO"),
        ('Flexão (FLA) - ELU', f"{Msd/100:.2f} kNm", f"{res_fla['Mrdx']/100:.2f} kNm", res_fla['eficiencia'], "APROVADO" if res_fla['eficiencia'] <= 100.1 else "REPROVADO"),
        ('Cisalhamento (V) - ELU', f"{Vsd:.2f} kN", f"{res_cisalhamento['Vrd']:.2f} kN", res_cisalhamento['eficiencia'], res_cisalhamento['status']),
        ('Flecha (δ) - ELS', f"{res_flecha['flecha_max']:.2f} cm" if res_flecha['status'] != "N/A" else "N/A", f"≤ {res_flecha['flecha_limite']:.2f} cm" if res_flecha['status'] != "N/A" else "N/A", res_flecha['eficiencia'], res_flecha['status'])
    ]
    rows_html = ""
    for nome, sol, res, efic, status in verificacoes:
        status_class = "pass" if status == "APROVADO" else "fail"
        rows_html += f"""<tr><td data-label="Verificação">{nome}</td><td data-label="Solicitante / Atuante">{sol}</td><td data-label="Resistência / Limite">{res}</td><td data-label="Eficiência">{efic:.1f}%</td><td data-label="Status" class="{status_class}">{status}</td></tr>"""
    # A nota sobre interação M-V precisa ser calculada separadamente
    Vrd = res_cisalhamento['Vrd']
    nota_interacao = "Vsd ≤ 0.5*Vrd. Interação desconsiderada."
    if Vrd > 0 and Vsd > 0.5 * Vrd: nota_interacao = "Vsd > 0.5 * Vrd. Interação deve ser considerada."
    return f"""<table class="summary-table"><thead><tr><th>Verificação</th><th>Solicitante / Atuante</th><th>Resistência / Limite</th><th>Eficiência</th><th>Status</th></tr></thead><tbody>{rows_html}</tbody></table><p style="text-align:justify; font-size:0.9em;"><b>Nota sobre Interação M-V:</b> {nota_interacao}</p>"""

def build_step_by_step_html(L, Msd, Vsd, res_flexao, res_cisalhamento, res_flecha, res_flt, res_flm, res_fla, res_vrd, input_mode):
    # O passo a passo dos esforços agora é gerado em main() e passado para a função
    html = """""" # Agora os esforços são gerados no input_details_html
    html += """<h2>3. Verificações de Resistência (ELU)</h2><h3>3.1 Cálculo da Resistência à Flexão (Mrd)</h3>"""
    
    # Adicionando a verificação detalhada com eficiência para cada tipo de flambagem
    html += _add_verification_details_with_efficiency("Flambagem Lateral com Torção (FLT)", Msd, res_flt)
    html += _add_verification_details_with_efficiency("Flambagem Local da Mesa (FLM)", Msd, res_flm)
    html += _add_verification_details_with_efficiency("Flambagem Local da Alma (FLA)", Msd, res_fla)
    
    html += _build_verification_block_html("Verificação Final à Flexão", Msd/100, "M_{{sd}}", res_flexao['Mrd']/100, "M_{{rd}}", res_flexao['eficiencia'], res_flexao['status'], "kNm")
    html += f"<h3>3.2 Cálculo da Resistência ao Cisalhamento (Vrd)</h3>"
    html += _add_verification_details("Força Cortante (VRd)", res_vrd)
    # A função _build_verification_block_html precisa do dicionário de cisalhamento completo, não apenas do resultado de _calcular_vrd
    html += _build_verification_block_html("Verificação ao Cisalhamento", Vsd, "V_{{sd}}", res_cisalhamento['Vrd'], "V_{{rd}}", res_cisalhamento['eficiencia'], res_cisalhamento['status'], "kN")
    if input_mode == "Calcular a partir de Cargas na Viga":
        html += f"""<h2>4. Verificação de Serviço (ELS)</h2><div class="formula-block"><h4>a. Flecha Máxima Atuante (δ_max)</h4><p class="formula">$$ \\delta_{{max}} = {res_flecha['flecha_max']:.2f} \\, cm $$</p><h4>b. Flecha Limite (δ_lim)</h4><p class="formula">$$ \\delta_{{lim}} = \\frac{{L}}{{{Config.LIMITE_FLECHA_TOTAL}}} = \\frac{{{L:.2f}}}{{{Config.LIMITE_FLECHA_TOTAL}}} = {res_flecha['flecha_limite']:.2f} \\, cm $$</p></div>"""
        html += _build_verification_block_html("Verificação da Flecha", res_flecha['flecha_max'], "\\delta_{{max}}", res_flecha['flecha_limite'], "\\delta_{{lim}}", res_flecha['eficiencia'], res_flecha['status'], "cm")
    return html

def _add_verification_details(title, details_dict):
    html = f"<h4>{title}</h4><div class='formula-block'>"
    for key, value in details_dict.items():
        if isinstance(value, dict) and 'formula' in value:
            formula_valores = value['formula']
            for var, val_num in value['valores'].items():
                formula_valores = formula_valores.replace(var, f"\\mathbf{{{val_num:.2f}}}")
            html += f"""<h5>{value['desc']}</h5><p class="formula">$$ {value['formula']} $$</p><p class="formula">$$ {formula_valores} = \\mathbf{{{value['valor']:.2f} {value.get('unidade', '')}}} $$</p><p class="ref-norma">{value.get('ref', '')}</p>"""
    final_resistance = details_dict.get('Mrdx', details_dict.get('Vrd', 0))
    unit = 'kNm' if 'Mrdx' in details_dict else 'kN'
    if unit == 'kNm': final_resistance /= 100
    html += f"<h5>Resultado da Resistência</h5><p class='final-result'>{title.split('(')[0].strip()} Resistente = {final_resistance:.2f} {unit}</p></div>"
    return html

def _add_verification_details_with_efficiency(title, Msd, details_dict):
    html = f"<h4>{title}</h4><div class='formula-block'>"
    for key, value in details_dict.items():
        if isinstance(value, dict) and 'formula' in value:
            formula_valores = value['formula']
            # Substitui as variáveis pelos valores numéricos no texto da fórmula
            formula_calculada = value['formula']
            for var, val_num in value['valores'].items():
                formula_calculada = formula_calculada.replace(var, f"\\mathbf{{{val_num:.2f}}}")
            html += f"""<h5>{value['desc']}</h5><p class="formula">$$ {value['formula']} $$</p><p class="formula">$$ {formula_calculada} = \\mathbf{{{value['valor']:.2f} {value.get('unidade', '')}}} $$</p><p class="ref-norma">{value.get('ref', '')}</p>"""
    
    final_resistance = details_dict.get('Mrdx', 0)
    unit = 'kN.cm'
    
    if final_resistance > 0:
        eficiencia = (Msd / final_resistance) * 100
        status = "APROVADO" if eficiencia <= 100.1 else "REPROVADO"
        status_class = "pass" if status == "APROVADO" else "fail"
        comp_symbol = "\\le" if status == "APROVADO" else ">"
        
        if 'Mrdx_calc' in details_dict:
            formula_final_latex = details_dict.get('Mrdx_calc')['formula']
            formula_final_latex = formula_final_latex.replace("\\frac{1}{\\gamma_{a1}}", f"\\frac{{1}}{{{Config.GAMMA_A1:.2f}}}")
            formula_final_latex = formula_final_latex.replace("\\frac{C_b}{\\gamma_{a1}}", f"\\frac{{{details_dict.get('Mrdx_calc')['valores'].get('C_b', 0):.2f}}}{{{Config.GAMMA_A1:.2f}}}")
            formula_final_latex = formula_final_latex.replace("\\frac{M_{cr}}{\\gamma_{a1}}", f"\\frac{{{details_dict.get('Mrdx_calc')['valores'].get('M_{cr}', 0):.2f}}}{{{Config.GAMMA_A1:.2f}}}")
            formula_final_latex = formula_final_latex.replace("\\frac{M_p}{\\gamma_{a1}}", f"\\frac{{{details_dict.get('Mrdx_calc')['valores'].get('M_p', 0):.2f}}}{{{Config.GAMMA_A1:.2f}}}")
            
            formula_calculada_final = formula_final_latex
            for var, val_num in details_dict.get('Mrdx_calc')['valores'].items():
                formula_calculada_final = formula_calculada_final.replace(var, f"\\mathbf{{{val_num:.2f}}}")
            
            html += f"""<h5>Cálculo do Momento Resistente</h5><p class="formula">$$ {details_dict.get('Mrdx_calc')['formula']} $$</p><p class="formula">$$ {formula_calculada_final} = \\mathbf{{{details_dict.get('Mrdx_calc')['valor']:.2f} \\, kNm}} $$</p><p class="ref-norma">{details_dict.get('Mrdx_calc').get('ref', '')}</p>"""

    
    final_resistance_knm = final_resistance / 100.0 if unit == 'kN.cm' else final_resistance
    
    if final_resistance > 0:
        eficiencia = (Msd / final_resistance) * 100
        status = "APROVADO" if eficiencia <= 100.1 else "REPROVADO"
        status_class = "pass" if status == "APROVADO" else "fail"
        comp_symbol = "\\le" if status == "APROVADO" else ">"
        
        html += f"""
        <hr style="border: 1px solid #ddd; margin: 15px 0;">
        <h5>Verificação de Eficiência</h5>
        <p class="formula">$$ M_{{sd}} = {Msd/100:.2f} \\, kNm $$</p>
        <p class="formula">$$ M_{{rd}} = {final_resistance/100:.2f} \\, kNm $$</p>
        <p class="formula">$$ \\text{{Verificação: }} M_{{sd}} {comp_symbol} M_{{rd}} $$</p>
        <p class="formula">$$ \\text{{Eficiência}} = \\frac{{M_{{sd}}}}{{{details_dict.get('Mrdx_calc')['symbol']}}} = \\frac{{{Msd/100:.2f}}}{{{final_resistance/100:.2f}}} = {eficiencia:.1f}\% $$</p>
        <div class="final-status {status_class}">{status}</div>
        """
    else:
        html += f"""
        <hr style="border: 1px solid #ddd; margin: 15px 0;">
        <h5>Verificação de Eficiência</h5>
        <div class="final-status fail">REPROVADO</div>
        <p>Não foi possível calcular a resistência para este modo de falha.</p>
        """

    html += f"</div>"
    return html

def _calcular_mrdx_flt(props, Lb, Cb, fy):
    Zx, ry, Iy, Cw, J, Wx = props['Zx'], props['ry'], props['Iy'], props['Cw'], props['J'], props['Wx']
    Mp = Zx * fy
    lambda_val = Lb / ry if ry > 0 else float('inf')
    lambda_p = Config.FATOR_LAMBDA_P_FLT * math.sqrt(Config.E_ACO / fy)
    detalhes = {'Mp': {'desc': 'Momento de Plastificação', 'symbol': 'M_p', 'formula': 'M_p = Z_x \\cdot f_y', 'valores': {'Z_x': Zx, 'f_y': fy}, 'valor': Mp, 'unidade': 'kN.cm', 'ref': 'Item F.1.1(a)'},'lambda': {'desc': 'Índice de Esbeltez', 'symbol': '\\lambda', 'formula': '\\lambda = \\frac{L_b}{r_y}', 'valores': {'L_b': Lb, 'r_y': ry}, 'valor': lambda_val},'lambda_p': {'desc': 'Esbeltez Limite (Plástica)', 'symbol': '\\lambda_p', 'formula': '\\lambda_p = 1.76 \\sqrt{\\frac{E}{f_y}}', 'valores': {'E': Config.E_ACO, 'f_y': fy}, 'valor': lambda_p, 'ref': 'Eq. F-2'}}
    if lambda_val <= lambda_p:
        Mrdx = Mp / Config.GAMMA_A1
        detalhes['Mrdx_calc'] = {'desc': 'Momento Resistente (Plastificação)', 'symbol': 'M_{rd}', 'formula': 'M_{rd} = \\frac{M_p}{\\gamma_{a1}}', 'valores': {'M_p': Mp, '\\gamma_{a1}': Config.GAMMA_A1}, 'valor': Mrdx, 'unidade': 'kN.cm', 'ref': 'Eq. F-1'}
    else:
        sigma_r = Config.FATOR_SIGMA_R * fy
        Mr = (fy - sigma_r) * Wx
        beta1 = ((fy - sigma_r) * Wx) / (Config.E_ACO * J) if Config.E_ACO * J != 0 else 0
        lambda_r = float('inf')
        if ry > 0 and beta1 > 0 and J > 0 and Cw > 0 and Iy > 0:
            termo_sqrt1 = 1 + (27 * Cw * (beta1**2) / Iy)
            termo_sqrt2 = 1 + math.sqrt(termo_sqrt1) if termo_sqrt1 >= 0 else 1
            lambda_r = (1.38 * math.sqrt(Iy * J) / (ry * beta1 * J)) * math.sqrt(termo_sqrt2)
        detalhes['lambda_r'] = {'desc': 'Esbeltez Limite (Inelástica)', 'symbol': '\\lambda_r', 'formula': '\\lambda_r = 1.38 \\sqrt{\\frac{I_y \\cdot J}{r_y^2 \\cdot (f_y-f_r)}} \\cdot \\sqrt{1 + \\sqrt{1 + \\frac{27 \\cdot C_w \\cdot (f_y-f_r)^2 \\cdot I_y}{E^2 \\cdot J^2}}}', 'valores': {'I_y': Iy, 'J': J, 'r_y': ry, '\\beta_1': beta1, 'C_w': Cw, 'f_y': fy, 'f_r': sigma_r, 'E': Config.E_ACO}, 'valor': lambda_r, 'ref': 'Eq. F-3 (Simplificada)'}
        if lambda_val <= lambda_r:
            termo_interp = (Mp - Mr) * ((lambda_val - lambda_p) / (lambda_r - lambda_p))
            Mrdx_calc = (Cb / Config.GAMMA_A1) * (Mp - termo_interp)
            Mrdx = min(Mrdx_calc, Mp / Config.GAMMA_A1)
            detalhes['Mrdx_calc'] = {'desc': 'Momento Resistente (Inelástico)', 'symbol': 'M_{rd}', 'formula': 'M_{rd} = \\frac{C_b}{\\gamma_{a1}} [M_p - (M_p - M_r) (\\frac{\\lambda - \\lambda_p}{\\lambda_r - \\lambda_p})] \\le \\frac{M_p}{\\gamma_{a1}}', 'valores': {'C_b': Cb, 'M_p': Mp, 'M_r': Mr, '\\lambda': lambda_val, '\\lambda_p': lambda_p, '\\lambda_r': lambda_r, '\\gamma_{a1}': Config.GAMMA_A1}, 'valor': Mrdx, 'unidade': 'kN.cm', 'ref': 'Eq. F-1'}
        else:
            Mcr = 0
            if Lb**2 > 0 and Iy > 0 and Cw > 0 and J > 0:
                Mcr_termo1 = (Cb * (math.pi**2) * Config.E_ACO * Iy) / (Lb**2)
                Mcr_termo2 = math.sqrt((Cw/Iy) * (1 + (0.039 * J * (Lb**2) / Cw)))
                Mcr = Mcr_termo1 * Mcr_termo2
            Mrdx = Mcr / Config.GAMMA_A1
            detalhes['Mcr'] = {'desc': 'Momento Crítico Elástico', 'symbol': 'M_{cr}', 'formula': 'M_{cr} = \\frac{C_b \\pi^2 E I_y}{L_b^2} \\sqrt{\\frac{C_w}{I_y}(1 + 0.039 \\frac{J L_b^2}{C_w})}', 'valores': {'C_b': Cb, 'E': Config.E_ACO, 'I_y': Iy, 'L_b': Lb, 'C_w': Cw, 'J': J}, 'valor': Mcr, 'unidade': 'kN.cm', 'ref': 'Eq. F-4'}
            detalhes['Mrdx_calc'] = {'desc': 'Momento Resistente (Elástico)', 'symbol': 'M_{rd}', 'formula': 'M_{rd} = \\frac{M_{cr}}{\\gamma_{a1}}', 'valores': {'M_{cr}': Mcr, '\\gamma_{a1}': Config.GAMMA_A1}, 'valor': Mrdx, 'unidade': 'kN.cm', 'ref': 'Eq. F-1'}
    detalhes['Mrdx'] = Mrdx
    return detalhes

def _calcular_mrdx_flm(props, fy):
    bf, tf, Zx, Wx = props['bf'], props['tf'], props['Zx'], props['Wx']
    Mp = Zx * fy
    lambda_val = (bf / 2) / tf if tf > 0 else float('inf')
    lambda_p = Config.FATOR_LAMBDA_P_FLM * math.sqrt(Config.E_ACO / fy)
    detalhes = {'lambda': {'desc': 'Esbeltez da Mesa', 'symbol': '\\lambda', 'formula': '\\lambda = \\frac{b_f/2}{t_f}', 'valores': {'b_f': bf, 't_f': tf}, 'valor': lambda_val},'lambda_p': {'desc': 'Esbeltez Limite (Plástica)', 'symbol': '\\lambda_p', 'formula': '\\lambda_p = 0.38 \\sqrt{\\frac{E}{f_y}}', 'valores': {'E': Config.E_ACO, 'f_y': fy}, 'valor': lambda_p, 'ref': 'Tabela F.1'}}
    if lambda_val <= lambda_p:
        Mrdx = Mp / Config.GAMMA_A1
        detalhes['Mrdx_calc'] = {'desc': 'Momento Resistente (Mesa Compacta)', 'symbol': 'M_{rd}', 'formula': 'M_{rd} = \\frac{M_p}{\\gamma_{a1}}', 'valores': {'M_p': Mp, '\\gamma_{a1}': Config.GAMMA_A1}, 'valor': Mrdx, 'unidade': 'kN.cm'}
    else:
        sigma_r = Config.FATOR_SIGMA_R * fy
        lambda_r = Config.FATOR_LAMBDA_R_FLM_LAMINADO * math.sqrt(Config.E_ACO / (fy - sigma_r)) if (fy - sigma_r) > 0 else float('inf')
        Mr = (fy - sigma_r) * Wx
        detalhes['lambda_r'] = {'desc': 'Esbeltez Limite (Inelástica)', 'symbol': '\\lambda_r', 'formula': '\\lambda_r = 0.83 \\sqrt{\\frac{E}{f_y - f_r}}', 'valores': {'E': Config.E_ACO, 'f_y': fy, 'f_r': sigma_r}, 'valor': lambda_r, 'ref': 'Tabela F.1'}
        if lambda_val <= lambda_r:
            termo_interp = (Mp - Mr) * ((lambda_val - lambda_p) / (lambda_r - lambda_p))
            Mrdx = (1 / Config.GAMMA_A1) * (Mp - termo_interp)
            detalhes['Mrdx_calc'] = {'desc': 'Momento Resistente (Mesa Semicompacta)', 'symbol': 'M_{rd}', 'formula': 'M_{rd} = \\frac{1}{\\gamma_{a1}} [M_p - (M_p - M_r) (\\frac{\\lambda - \\lambda_p}{\\lambda_r - \\lambda_p})]', 'valores': {'M_p': Mp, 'M_r': Mr, '\\lambda': lambda_val, '\\lambda_p': lambda_p, '\\lambda_r': lambda_r, '\\gamma_{a1}': Config.GAMMA_A1}, 'valor': Mrdx, 'unidade': 'kN.cm'}
        else:
            Mcr = (0.69 * Config.E_ACO * Wx) / (lambda_val**2) if lambda_val > 0 else 0
            Mrdx = Mcr / Config.GAMMA_A1
            detalhes['Mrdx_calc'] = {'desc': 'Momento Resistente (Mesa Esbelta)', 'symbol': 'M_{rd}', 'formula': 'M_{rd} = \\frac{0.69 E W_x}{\\lambda^2 \\gamma_{a1}}', 'valores': {'E': Config.E_ACO, 'W_x': Wx, '\\lambda': lambda_val, '\\gamma_{a1}': Config.GAMMA_A1}, 'valor': Mrdx, 'unidade': 'kN.cm'}
    detalhes['Mrdx'] = Mrdx
    return detalhes

def _calcular_mrdx_fla(props, fy):
    h, tw, Zx, Wx = props['h'], props['tw'], props['Zx'], props['Wx']
    Mp = Zx * fy
    lambda_val = h / tw if tw > 0 else float('inf')
    lambda_p = Config.FATOR_LAMBDA_P_FLA * math.sqrt(Config.E_ACO / fy)
    detalhes = {'lambda': {'desc': 'Esbeltez da Alma', 'symbol': '\\lambda', 'formula': '\\lambda = \\frac{h}{t_w}', 'valores': {'h': h, 't_w': tw}, 'valor': lambda_val},'lambda_p': {'desc': 'Esbeltez Limite (Plástica)', 'symbol': '\\lambda_p', 'formula': '\\lambda_p = 3.76 \\sqrt{\\frac{E}{f_y}}', 'valores': {'E': Config.E_ACO, 'f_y': fy}, 'valor': lambda_p, 'ref': 'Tabela F.1'}}
    if lambda_val <= lambda_p:
        Mrdx = Mp / Config.GAMMA_A1
        detalhes['Mrdx_calc'] = {'desc': 'Momento Resistente (Alma Compacta)', 'symbol': 'M_{rd}', 'formula': 'M_{rd} = \\frac{M_p}{\\gamma_{a1}}', 'valores': {'M_p': Mp, '\\gamma_{a1}': Config.GAMMA_A1}, 'valor': Mrdx, 'unidade': 'kN.cm'}
    else:
        lambda_r = Config.FATOR_LAMBDA_R_FLA * math.sqrt(Config.E_ACO / fy)
        Mr = fy * Wx
        detalhes['lambda_r'] = {'desc': 'Esbeltez Limite (Inelástica)', 'symbol': '\\lambda_r', 'formula': '\\lambda_r = 5.70 \\sqrt{\\frac{E}{f_y}}', 'valores': {'E': Config.E_ACO, 'f_y': fy}, 'valor': lambda_r, 'ref': 'Tabela F.1'}
        if lambda_val <= lambda_r:
            termo_interp = (Mp - Mr) * ((lambda_val - lambda_p) / (lambda_r - lambda_p))
            Mrdx = (1 / Config.GAMMA_A1) * (Mp - termo_interp)
            detalhes['Mrdx_calc'] = {'desc': 'Momento Resistente (Alma Semicompacta)', 'symbol': 'M_{rd}', 'formula': 'M_{rd} = \\frac{1}{\\gamma_{a1}} [M_p - (M_p - M_r) (\\frac{\\lambda - \\lambda_p}{\\lambda_r - \\lambda_p})]', 'valores': {'M_p': Mp, 'M_r': Mr, '\\lambda': lambda_val, '\\lambda_p': lambda_p, '\\lambda_r': lambda_r, '\\gamma_{a1}': Config.GAMMA_A1}, 'valor': Mrdx, 'unidade': 'kN.cm'}
        else:
            Mrdx = 0
            detalhes['Mrdx_calc'] = {'desc': 'Momento Resistente (Alma Esbelta)', 'symbol': 'M_{rd}', 'formula': 'N/A', 'valores': {}, 'valor': Mrdx, 'unidade': 'kN.cm', 'ref': 'Perfil com alma esbelta. Ver Anexo H.'}
    detalhes['Mrdx'] = Mrdx
    return detalhes

def _calcular_vrd(props, fy):
    d, h, tw = props['d'], props['h'], props['tw']
    Vpl = Config.FATOR_VP * d * tw * fy
    lambda_val = h / tw if tw > 0 else float('inf')
    kv = Config.KV_ALMA_SEM_ENRIJECEDORES
    lambda_p = Config.FATOR_LAMBDA_P_VRD * math.sqrt((kv * Config.E_ACO) / fy)
    detalhes = {'Vpl': {'desc': 'Força Cortante de Plastificação', 'symbol': 'V_{pl}', 'formula': 'V_{pl} = 0.60 \\cdot d_{perfil} \\cdot t_{w,alma} \\cdot f_{y,aco}', 'valores': {'d_{perfil}': d, 't_{w,alma}': tw, 'f_{y,aco}': fy}, 'valor': Vpl, 'unidade': 'kN', 'ref': 'Eq. 5.23 / G.2.1(a)'}, 'lambda': {'desc': 'Esbeltez da Alma (Cisalhamento)', 'symbol': '\\lambda', 'formula': '\\lambda = \\frac{h}{t_w}', 'valores': {'h': h, 't_w': tw}, 'valor': lambda_val},'lambda_p': {'desc': 'Esbeltez Limite (Plástica)', 'symbol': '\\lambda_p', 'formula': '\\lambda_p = 1.10 \\sqrt{\\frac{k_v \\cdot E}{f_y}}', 'valores': {'k_v': kv, 'E': Config.E_ACO, 'f_y': fy}, 'valor': lambda_p, 'ref': 'Eq. 5.25 / G-4'}}
    if lambda_val <= lambda_p:
        Vrd = Vpl / Config.GAMMA_A1
        detalhes['Vrd_calc'] = {'desc': 'Cortante Resistente (Escoamento)', 'symbol': 'V_{rd}', 'formula': 'V_{rd} = \\frac{V_{pl}}{\\gamma_{a1}}', 'valores': {'V_{pl}': Vpl, '\\gamma_{a1}': Config.GAMMA_A1}, 'valor': Vrd, 'unidade': 'kN', 'ref': 'Eq. 5.24 / G-3a'}
    else:
        lambda_r = Config.FATOR_LAMBDA_R_VRD * math.sqrt((kv * Config.E_ACO) / fy)
        detalhes['lambda_r'] = {'desc': 'Esbeltez Limite (Inelástica)', 'symbol': '\\lambda_r', 'formula': '\\lambda_r = 1.37 \\sqrt{\\frac{k_v \\cdot E}{f_y}}', 'valores': {'k_v': kv, 'E': Config.E_ACO, 'f_y': fy}, 'valor': lambda_r, 'ref': 'Eq. 5.27 / G-4'}
        if lambda_val <= lambda_r:
            Vrd = (lambda_p / lambda_val) * (Vpl / Config.GAMMA_A1) if lambda_val > 0 else 0
            detalhes['Vrd_calc'] = {'desc': 'Cortante Resistente (Inelástico)', 'symbol': 'V_{rd}', 'formula': 'V_{rd} = \\frac{\\lambda_p}{\\lambda} \\frac{V_{pl}}{\\gamma_{a1}}', 'valores': {'\\lambda_p': lambda_p, '\\lambda': lambda_val, 'V_{pl}': Vpl, '\\gamma_{a1}': Config.GAMMA_A1}, 'valor': Vrd, 'unidade': 'kN', 'ref': 'Eq. 5.26 / G-3b'}
        else:
            Vrd = (Config.FATOR_VRD_ELASTICO * (lambda_p / lambda_val)**2) * (Vpl / Config.GAMMA_A1) if lambda_val > 0 else 0
            detalhes['Vrd_calc'] = {'desc': 'Cortante Resistente (Elástico)', 'symbol': 'V_{rd}', 'formula': 'V_{rd} = 1.24 (\\frac{\\lambda_p}{\\lambda})^2 \\frac{V_{pl}}{\\gamma_{a1}}', 'valores': {'\\lambda_p': lambda_p, '\\lambda': lambda_val, 'V_{pl}': Vpl, '\\gamma_{a1}': Config.GAMMA_A1}, 'valor': Vrd, 'unidade': 'kN', 'ref': 'Eq. 5.28 / G-3c'}
    detalhes['Vrd'] = Vrd
    return detalhes

if __name__ == '__main__':
    main()
