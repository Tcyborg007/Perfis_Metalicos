import streamlit as st
import pandas as pd
import math
import plotly.graph_objects as go
from datetime import datetime

# ==============================================================================
# 1. CONFIGURAÇÕES E CONSTANTES GLOBAIS
# ==============================================================================

st.set_page_config(
    page_title="🏗️ Calculadora Estrutural Pro - Perfis Metálicos",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://www.abnt.org.br',
        'Report a bug': None,
        'About': "# Calculadora Estrutural Pro\nCálculos baseados na ABNT NBR 8800:2008"
    }
)

class Config:
    NOME_NORMA = 'ABNT NBR 8800:2008'
    GAMMA_A1 = 1.10
    E_ACO = 20000  # kN/cm²
    FATOR_SIGMA_R = 0.3
    FATOR_LAMBDA_P_FLT = 1.76
    FATOR_LAMBDA_P_FLM = 0.38
    FATOR_LAMBDA_R_FLM_LAMINADO = 0.83
    FATOR_LAMBDA_R_FLM_SOLDADO = 0.95
    FATOR_LAMBDA_P_FLA = 3.76
    FATOR_LAMBDA_R_FLA = 5.70
    KV_ALMA_SEM_ENRIJECEDORES = 5.0
    FATOR_VP = 0.60
    FATOR_LAMBDA_P_VRD = 1.10
    FATOR_LAMBDA_R_VRD = 1.37
    FATOR_VRD_ELASTICO = 1.24

PROFILE_TYPE_MAP = {
    "Laminados": "Perfis Laminados",
    "CS": "Perfis Compactos Soldados",
    "CVS": "Perfil de Seção Variável",
    "VS": "Perfis Soldados"
}

HTML_TEMPLATE_CSS_PRO = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
    
    :root {
        --primary-color: #1e40af;
        --secondary-color: #3b82f6;
        --accent-color: #60a5fa;
        --success-color: #10b981;
        --warning-color: #f59e0b;
        --error-color: #ef4444;
        --background: #f8fafc;
        --surface: #ffffff;
        --text-primary: #1f2937;
        --text-secondary: #6b7280;
        --border: #e5e7eb;
    }
    
    body { 
        font-family: 'Inter', sans-serif; 
        line-height: 1.6; 
        color: var(--text-primary); 
        background: var(--background);
    }
    
    .pro-header {
        background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
        color: white;
        padding: 3rem 2rem;
        border-radius: 16px;
        text-align: center;
        margin-bottom: 2rem;
        position: relative;
        overflow: hidden;
    }
    
    .pro-header h1 {
        font-size: 3rem;
        font-weight: 700;
        margin: 0;
        position: relative;
        z-index: 1;
    }
    
    .pro-header p {
        font-size: 1.25rem;
        margin: 0.5rem 0 0;
        opacity: 0.9;
        position: relative;
        z-index: 1;
    }
</style>
"""

# ==============================================================================
# 2. FUNÇÕES DE CÁLCULO E UTILITÁRIAS
# ==============================================================================

@st.cache_data
def load_data_from_local_file():
    """Carrega os dados da planilha de perfis."""
    try:
        caminho_arquivo_excel = 'perfis.xlsx'
        return pd.read_excel(caminho_arquivo_excel, sheet_name=None)
    except FileNotFoundError:
        st.error(f"Erro: Arquivo '{caminho_arquivo_excel}' não foi encontrado. Verifique se ele está na mesma pasta que o seu script Python.")
        return None
    except Exception as e:
        st.error(f"Erro ao ler o arquivo Excel: {e}")
        return None

def calcular_esforcos_viga(tipo_viga, L_cm, q_kn_cm=0, p_load=None):
    msd_q, vsd_q, msd_p, vsd_p = 0, 0, 0, 0
    L = L_cm
    detalhes_esforcos = {'Msd_q': {'valor': 0, 'formula_simbolica': "", 'formula_numerica': "", 'unidade': 'kN.cm'},'Vsd_q': {'valor': 0, 'formula_simbolica': "", 'formula_numerica': "", 'unidade': 'kN'},'Msd_p': {'valor': 0, 'formula_simbolica': "", 'formula_numerica': "", 'unidade': 'kN.cm'},'Vsd_p': {'valor': 0, 'formula_simbolica': "", 'formula_numerica': "", 'unidade': 'kN'}}
    if q_kn_cm > 0:
        if tipo_viga == 'Bi-apoiada':
            msd_q = (q_kn_cm * L**2) / 8
            vsd_q = (q_kn_cm * L) / 2
            detalhes_esforcos['Msd_q']['formula_simbolica'] = f"M_{{sd, q}} = \\frac{{q_{{última}} \\times L^2}}{{8}}"
            detalhes_esforcos['Msd_q']['formula_numerica'] = f"\\frac{{ \\mathbf{{{q_kn_cm*100:.2f}}} \\, kN/m \\times (\\mathbf{{{L_cm/100:.2f}}} \\, m)^2}}{{8}}"
            detalhes_esforcos['Vsd_q']['formula_simbolica'] = f"V_{{sd, q}} = \\frac{{q_{{última}} \\times L}}{{2}}"
            detalhes_esforcos['Vsd_q']['formula_numerica'] = f"\\frac{{ \\mathbf{{{q_kn_cm*100:.2f}}} \\, kN/m \\times \\mathbf{{{L_cm/100:.2f}}} \\, m}}{{2}}"
        elif tipo_viga == 'Engastada e Livre (Balanço)':
            msd_q = (q_kn_cm * L**2) / 2
            vsd_q = q_kn_cm * L
            detalhes_esforcos['Msd_q']['formula_simbolica'] = f"M_{{sd, q}} = \\frac{{q_{{última}} \\times L^2}}{{2}}"
            detalhes_esforcos['Msd_q']['formula_numerica'] = f"\\frac{{ \\mathbf{{{q_kn_cm*100:.2f}}} \\, kN/m \\times (\\mathbf{{{L_cm/100:.2f}}} \\, m)^2}}{{2}}"
            detalhes_esforcos['Vsd_q']['formula_simbolica'] = f"V_{{sd, q}} = q_{{última}} \\times L"
            detalhes_esforcos['Vsd_q']['formula_numerica'] = f"\\mathbf{{{q_kn_cm*100:.2f}}} \\, kN/m \\times \\mathbf{{{L_cm/100:.2f}}} \\, m"
        elif tipo_viga == 'Bi-engastada':
            msd_q = (q_kn_cm * L**2) / 12
            vsd_q = (q_kn_cm * L) / 2
            detalhes_esforcos['Msd_q']['formula_simbolica'] = f"M_{{sd, q}} = \\frac{{q_{{última}} \\times L^2}}{{12}}"
            detalhes_esforcos['Msd_q']['formula_numerica'] = f"\\frac{{ \\mathbf{{{q_kn_cm*100:.2f}}} \\, kN/m \\times (\\mathbf{{{L_cm/100:.2f}}} \\, m)^2}}{{12}}"
            detalhes_esforcos['Vsd_q']['formula_simbolica'] = f"V_{{sd, q}} = \\frac{{q_{{última}} \\times L}}{{2}}"
            detalhes_esforcos['Vsd_q']['formula_numerica'] = f"\\frac{{ \\mathbf{{{q_kn_cm*100:.2f}}} \\, kN/m \\times \\mathbf{{{L_cm/100:.2f}}} \\, m}}{{2}}"
        elif tipo_viga == 'Engastada e Apoiada':
            msd_q = (q_kn_cm * L**2) / 8
            vsd_q = (5 * q_kn_cm * L) / 8
            detalhes_esforcos['Msd_q']['formula_simbolica'] = f"M_{{sd, q}} = \\frac{{q_{{última}} \\times L^2}}{{8}}"
            detalhes_esforcos['Msd_q']['formula_numerica'] = f"\\frac{{ \\mathbf{{{q_kn_cm*100:.2f}}} \\, kN/m \\times (\\mathbf{{{L_cm/100:.2f}}} \\, m)^2}}{{8}}"
            detalhes_esforcos['Vsd_q']['formula_simbolica'] = f"V_{{sd, q}} = \\frac{{5 \\times q_{{última}} \\times L}}{{8}}"
            detalhes_esforcos['Vsd_q']['formula_numerica'] = f"\\frac{{5 \\times \\mathbf{{{q_kn_cm*100:.2f}}} \\, kN/m \\times \\mathbf{{{L_cm/100:.2f}}} \\, m}}{{8}}"
    if p_load:
        P, x = p_load
        P_kn = P
        L_m = L / 100.0
        x_m = x / 100.0
        a = x_m
        b = L_m - a
        if tipo_viga == 'Bi-apoiada':
            msd_p = (P_kn * a * b) / L_m
            vsd_p = max((P_kn * b) / L_m, (P_kn * a) / L_m)
            detalhes_esforcos['Msd_p']['formula_simbolica'] = f"M_{{sd, P}} = \\frac{{P_{{última}} \\times a \\times b}}{{L}}"
            detalhes_esforcos['Msd_p']['formula_numerica'] = f"\\frac{{ \\mathbf{{{P_kn:.2f}}} \\, kN \\times \\mathbf{{{a:.2f}}} \\, m \\times \\mathbf{{{b:.2f}}} \\, m}}{{\\mathbf{{{L_m:.2f}}} \\, m}}"
            detalhes_esforcos['Vsd_p']['formula_simbolica'] = f"V_{{sd, P}} = \\max(\\frac{{P_{{última}} \\times b}}{{L}}, \\frac{{P_{{última}} \\times a}}{{L}})"
            detalhes_esforcos['Vsd_p']['formula_numerica'] = f"\\max(\\frac{{ \\mathbf{{{P_kn:.2f}}} \\times \\mathbf{{{b:.2f}}} }}{{\\mathbf{{{L_m:.2f}}}}}, \\frac{{ \\mathbf{{{P_kn:.2f}}} \\times \\mathbf{{{a:.2f}}} }}{{\\mathbf{{{L_m:.2f}}}}} )"
        elif tipo_viga == 'Engastada e Livre (Balanço)':
            msd_p = P_kn * a
            vsd_p = P_kn
            detalhes_esforcos['Msd_p']['formula_simbolica'] = f"M_{{sd, P}} = P_{{última}} \\times a"
            detalhes_esforcos['Msd_p']['formula_numerica'] = f"\\mathbf{{{P_kn:.2f}}} \\, kN \\times \\mathbf{{{a:.2f}}} \\, m"
            detalhes_esforcos['Vsd_p']['formula_simbolica'] = f"V_{{sd, P}} = P_{{última}}"
            detalhes_esforcos['Vsd_p']['formula_numerica'] = f"\\mathbf{{{P_kn:.2f}}} \\, kN"
        msd_p *= 100
    detalhes_esforcos['Msd_q']['valor'] = msd_q
    detalhes_esforcos['Vsd_q']['valor'] = vsd_q
    detalhes_esforcos['Msd_p']['valor'] = msd_p
    detalhes_esforcos['Vsd_p']['valor'] = vsd_p
    msd_total = msd_q + msd_p
    vsd_total = vsd_q + vsd_p
    return msd_total, vsd_total, detalhes_esforcos

def calcular_flecha_maxima(tipo_viga, L_cm, E, Ix, q_serv_kn_cm=0, p_serv_load=None):
    delta_q, delta_p = 0, 0
    L = L_cm
    
    detalhes = {
        'delta_q': {'formula_simbolica': '', 'formula_numerica': '', 'valor': 0, 'unidade': 'cm'},
        'delta_p': {'formula_simbolica': '', 'formula_numerica': '', 'valor': 0, 'unidade': 'cm'},
        'delta_total': 0
    }

    if q_serv_kn_cm > 0:
        q_serv_val = q_serv_kn_cm
        if tipo_viga == 'Bi-apoiada':
            delta_q = (5 * q_serv_val * L**4) / (384 * E * Ix)
            detalhes['delta_q']['formula_simbolica'] = "\\delta_q = \\frac{5 \\times q_{serv} \\times L^4}{384 \\times E \\times I_x}"
            detalhes['delta_q']['formula_numerica'] = f"\\frac{{5 \\times \\mathbf{{{q_serv_val:.4f}}} \\times \\mathbf{{{L:.2f}}}^4}}{{384 \\times \\mathbf{{{E:.0f}}} \\times \\mathbf{{{Ix:.2f}}}}}"
        elif tipo_viga == 'Engastada e Livre (Balanço)':
            delta_q = (q_serv_val * L**4) / (8 * E * Ix)
            detalhes['delta_q']['formula_simbolica'] = "\\delta_q = \\frac{q_{serv} \\times L^4}{8 \\times E \\times I_x}"
            detalhes['delta_q']['formula_numerica'] = f"\\frac{{\\mathbf{{{q_serv_val:.4f}}} \\times \\mathbf{{{L:.2f}}}^4}}{{8 \\times \\mathbf{{{E:.0f}}} \\times \\mathbf{{{Ix:.2f}}}}}"
        elif tipo_viga == 'Bi-engastada':
            delta_q = (q_serv_val * L**4) / (384 * E * Ix)
            detalhes['delta_q']['formula_simbolica'] = "\\delta_q = \\frac{q_{serv} \\times L^4}{384 \\times E \\times I_x}"
            detalhes['delta_q']['formula_numerica'] = f"\\frac{{\\mathbf{{{q_serv_val:.4f}}} \\times \\mathbf{{{L:.2f}}}^4}}{{384 \\times \\mathbf{{{E:.0f}}} \\times \\mathbf{{{Ix:.2f}}}}}"
        elif tipo_viga == 'Engastada e Apoiada':
            delta_q = (q_serv_val * L**4) / (185 * E * Ix)
            detalhes['delta_q']['formula_simbolica'] = "\\delta_q = \\frac{q_{serv} \\times L^4}{185 \\times E \\times I_x}"
            detalhes['delta_q']['formula_numerica'] = f"\\frac{{\\mathbf{{{q_serv_val:.4f}}} \\times \\mathbf{{{L:.2f}}}^4}}{{185 \\times \\mathbf{{{E:.0f}}} \\times \\mathbf{{{Ix:.2f}}}}}"
        detalhes['delta_q']['valor'] = delta_q

    if p_serv_load:
        P, x = p_serv_load
        a = x
        b = L - a
        if tipo_viga == 'Bi-apoiada':
            delta_p = (P * a**2 * b**2) / (3 * E * Ix * L)
            detalhes['delta_p']['formula_simbolica'] = "\\delta_p = \\frac{P_{serv} \\times a^2 \\times b^2}{3 \\times E \\times I_x \\times L}"
            detalhes['delta_p']['formula_numerica'] = f"\\frac{{\\mathbf{{{P:.2f}}} \\times \\mathbf{{{a:.2f}}}^2 \\times \\mathbf{{{b:.2f}}}^2}}{{3 \\times \\mathbf{{{E:.0f}}} \\times \\mathbf{{{Ix:.2f}}} \\times \\mathbf{{{L:.2f}}}}}"
        elif tipo_viga == 'Engastada e Livre (Balanço)':
            delta_p = (P * a**3) / (3 * E * Ix)
            detalhes['delta_p']['formula_simbolica'] = "\\delta_p = \\frac{P_{serv} \\times a^3}{3 \\times E \\times I_x}"
            detalhes['delta_p']['formula_numerica'] = f"\\frac{{\\mathbf{{{P:.2f}}} \\times \\mathbf{{{a:.2f}}}^3}}{{3 \\times \\mathbf{{{E:.0f}}} \\times \\mathbf{{{Ix:.2f}}}}}"
        elif tipo_viga == 'Bi-engastada':
            delta_p = (P * a**3 * b**3) / (3 * E * Ix * L**3)
            detalhes['delta_p']['formula_simbolica'] = "\\delta_p = \\frac{P_{serv} \\times a^3 \\times b^3}{3 \\times E \\times I_x \\times L^3}"
            detalhes['delta_p']['formula_numerica'] = f"\\frac{{\\mathbf{{{P:.2f}}} \\times \\mathbf{{{a:.2f}}}^3 \\times \\mathbf{{{b:.2f}}}^3}}{{3 \\times \\mathbf{{{E:.0f}}} \\times \\mathbf{{{Ix:.2f}}} \\times \\mathbf{{{L:.2f}}}^3}}"
        elif tipo_viga == 'Engastada e Apoiada':
            delta_p = (P * a**3 * b**2) / (12 * E * Ix * L**3) * (a + 2*L)
            detalhes['delta_p']['formula_simbolica'] = "\\delta_p = \\frac{P_{serv} \\times a^3 \\times b^2 \\times (a + 2L)}{12 \\times E \\times I_x \\times L^3}"
            detalhes['delta_p']['formula_numerica'] = f"\\frac{{\\mathbf{{{P:.2f}}} \\times \\mathbf{{{a:.2f}}}^3 \\times \\mathbf{{{b:.2f}}}^2 \\times (\\mathbf{{{a:.2f}}} + 2 \\times \\mathbf{{{L:.2f}}})}}{{12 \\times \\mathbf{{{E:.0f}}} \\times \\mathbf{{{Ix:.2f}}} \\times \\mathbf{{{L:.2f}}}^3}}"
    
        detalhes['delta_p']['valor'] = delta_p
    
    detalhes['delta_total'] = delta_q + delta_p
    return detalhes

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

def _calcular_mrdx_flt(props, Lb, Cb, fy):
    Zx, ry, Iy, Cw, J, Wx = props['Zx'], props['ry'], props['Iy'], props['Cw'], props['J'], props['Wx']
    Mp = Zx * fy
    lambda_val = Lb / ry if ry > 0 else float('inf')
    lambda_p = Config.FATOR_LAMBDA_P_FLT * math.sqrt(Config.E_ACO / fy)
    detalhes = {'Mp': {'desc': 'Momento de Plastificação', 'formula': 'M_p = Z_x \\times f_y', 'valores': {'Z_x': Zx, 'f_y': fy}, 'valor': Mp, 'unidade': 'kN.cm'},'lambda': {'desc': 'Índice de Esbeltez (Lb/ry)', 'formula': '\\lambda = \\frac{{L_b}}{{r_y}}', 'valores': {'L_b': Lb, 'r_y': ry}, 'valor': lambda_val},'lambda_p': {'desc': 'Esbeltez Limite (Plástica)', 'formula': '\\lambda_p = 1.76 \\sqrt{\\frac{{E}}{{f_y}}}', 'valores': {'E': Config.E_ACO, 'f_y': fy}, 'valor': lambda_p}}
    verificacao_texto = ""
    if lambda_val <= lambda_p:
        verificacao_texto = f"""O índice de esbeltez (λ = {lambda_val:.2f}) é **menor ou igual** ao limite para plastificação (λp = {lambda_p:.2f}).
        **Conclusão:** Ocorre plastificação total da seção."""
        Mrdx = Mp / Config.GAMMA_A1
        detalhes['Mrdx_calc'] = {'desc': 'Momento Resistente (Plastificação)', 'formula': 'M_{rd} = \\frac{{M_p}}{{\\gamma_{{a1}}}}', 'valores': {'M_p': Mp, '\\gamma_{{a1}}': Config.GAMMA_A1}, 'valor': Mrdx, 'unidade': 'kN.cm', 'ref': 'Eq. F-1'}
    else:
        sigma_r = Config.FATOR_SIGMA_R * fy
        detalhes['sigma_r'] = {'desc': 'Tensão Residual (σr)', 'formula': '\\sigma_r = 0,3 \\times f_y', 'valores': {'f_y': fy}, 'valor': sigma_r, 'unidade': 'kN/cm²'}
        Mr = (fy - sigma_r) * Wx
        detalhes['Mr_calc'] = {'desc': 'Momento de Escoamento Residual (Mr)', 'formula': 'M_r = (f_y - \\sigma_r) \\times W_x', 'valores': {'f_y': fy, '\\sigma_r': sigma_r, 'W_x': Wx}, 'valor': Mr, 'unidade': 'kN.cm'}
        beta1 = ((fy - sigma_r) * Wx) / (Config.E_ACO * J) if Config.E_ACO * J != 0 else 0
        detalhes['beta_1'] = {'desc': 'Parâmetro β1', 'formula': '\\beta_1 = \\frac{(f_y - \\sigma_r) \\times W_x}{E \\times J}', 'valores': {'f_y': fy, '\\sigma_r': sigma_r, 'W_x': Wx, 'E': Config.E_ACO, 'J': J}, 'valor': beta1, 'unidade': ''}
        lambda_r = float('inf')
        if ry > 0 and beta1 > 0 and J > 0 and Cw > 0 and Iy > 0:
            termo_sqrt1 = 1 + (27 * Cw * (beta1**2) / Iy)
            termo_sqrt2 = 1 + math.sqrt(termo_sqrt1) if termo_sqrt1 >= 0 else 1
            lambda_r = (1.38 * math.sqrt(Iy * J) / (ry * beta1 * J)) * math.sqrt(termo_sqrt2)
        detalhes['lambda_r'] = {'desc': 'Esbeltez Limite (Inelástica)', 'formula': '\\lambda_r = 1.38 \\frac{\\sqrt{I_y \\times J}}{r_y \\times \\beta_1 \\times J} \\sqrt{1 + \\sqrt{1+\\frac{27 \\times C_w \\times \\beta_1^2}{I_y}}}', 'valores': {'I_y': Iy, 'J': J, 'r_y': ry, '\\beta_1': beta1, 'C_w': Cw}, 'valor': lambda_r}
        if lambda_val <= lambda_r:
            verificacao_texto = f"""O índice de esbeltez (λ = {lambda_val:.2f}) está **entre os limites** plástico (λp = {lambda_p:.2f}) e inelástico (λr = {lambda_r:.2f}).
            **Conclusão:** Ocorre flambagem no regime inelástico."""
            Mrdx_calc = (Cb / Config.GAMMA_A1) * (Mp - (Mp - Mr) * ((lambda_val - lambda_p) / (lambda_r - lambda_p)))
            Mp_gamma = Mp / Config.GAMMA_A1
            Mrdx = min(Mrdx_calc, Mp_gamma)
            detalhes['Mrdx_calc'] = {'desc': 'Cálculo do Momento Resistente (Regime Inelástico)', 'formula': 'M_{rd,calc} = \\frac{{C_b}}{{\\gamma_{{a1}}}} [M_p - (M_p - M_r) (\\frac{{\\lambda - \\lambda_p}}{{\\lambda_r - \\lambda_p}})]', 'valores': {'C_b': Cb, '\\gamma_{{a1}}': Config.GAMMA_A1, 'M_p': Mp, 'M_r': Mr, '\\lambda': lambda_val, '\\lambda_p': lambda_p, '\\lambda_r': lambda_r}, 'valor': Mrdx_calc, 'unidade': 'kN.cm', 'ref': 'Eq. F-1'}
            detalhes['verificacao_limite'] = {
                'desc': 'Verificação do Limite de Plastificação',
                'texto': f"""A norma exige que a resistência no regime inelástico seja limitada pela resistência plástica.
                $$M_{{rd,calc}} = {Mrdx_calc/100:.2f} \\, kNm$$
                $$M_{{p,rd}} = \\frac{{M_p}}{{\\gamma_{{a1}}}} = \\frac{{{Mp:.2f}}}{{{Config.GAMMA_A1:.2f}}} = {Mp_gamma/100:.2f} \\, kNm$$
                Adota-se o menor valor: $$M_{{rd}} = \\min(M_{{rd,calc}}; M_{{p,rd}}) = \\min({Mrdx_calc/100:.2f}; {Mp_gamma/100:.2f}) = \\mathbf{{{Mrdx/100:.2f}}} \\, kNm$$"""
            }
        else:
            verificacao_texto = f"""O índice de esbeltez (λ = {lambda_val:.2f}) é **maior** que o limite inelástico (λr = {lambda_r:.2f}).
            **Conclusão:** Ocorre flambagem no regime elástico."""
            Mcr = 0
            if Lb**2 > 0 and Iy > 0 and Cw > 0 and J > 0:
                Mcr = ((Cb * (math.pi**2) * Config.E_ACO * Iy) / (Lb**2)) * math.sqrt((Cw/Iy) * (1 + (0.039 * J * (Lb**2) / Cw)))
            Mrdx = Mcr / Config.GAMMA_A1
            detalhes['Mcr'] = {'desc': 'Momento Crítico Elástico', 'formula': 'M_{cr} = \\frac{{C_b \\times \\pi^2 \\times E \\times I_y}}{{L_b^2}} \\sqrt{{\\frac{{C_w}}{{I_y}}(1 + 0.039 \\times \\frac{{J \\times L_b^2}}{{C_w}})}}', 'valores': {'C_b': Cb, '\\pi^2': math.pi**2, 'E': Config.E_ACO, 'I_y': Iy, 'L_b': Lb, 'C_w': Cw, 'J': J}, 'valor': Mcr, 'unidade': 'kN.cm', 'ref': 'Eq. F-4'}
            detalhes['Mrdx_calc'] = {'desc': 'Momento Resistente (Regime Elástico)', 'formula': 'M_{rd} = \\frac{{M_{{cr}}}}{{\\gamma_{{a1}}}}', 'valores': {'M_{{cr}}': Mcr, '\\gamma_{{a1}}': Config.GAMMA_A1}, 'valor': Mrdx, 'unidade': 'kN.cm', 'ref': 'Eq. F-1'}
    detalhes['verificacao_classificacao'] = {'desc': 'Classificação do Regime de Flambagem Lateral', 'texto': verificacao_texto}
    detalhes['Mrdx'] = Mrdx
    return detalhes

def _calcular_mrdx_flm(props, fy, tipo_fabricacao):
    bf, tf, Zx, Wx, h, tw = props['bf'], props['tf'], props['Zx'], props['Wx'], props['h'], props['tw']
    Mp = Zx * fy
    lambda_val = (bf / 2) / tf if tf > 0 else float('inf')
    lambda_p = Config.FATOR_LAMBDA_P_FLM * math.sqrt(Config.E_ACO / fy)
    detalhes = {'Mp': {'desc': 'Momento de Plastificação', 'formula': 'M_p = Z_x \\times f_y', 'valores': {'Z_x': Zx, 'f_y': fy}, 'valor': Mp, 'unidade': 'kN.cm'}, 'lambda': {'desc': 'Esbeltez da Mesa (bf/2tf)', 'formula': '\\lambda = \\frac{{b_f/2}}{{t_f}}', 'valores': {'b_f': bf, 't_f': tf}, 'valor': lambda_val},'lambda_p': {'desc': 'Esbeltez Limite (Plástica)', 'formula': '\\lambda_p = 0,38 \\sqrt{{\\frac{{E}}{{f_y}}}}', 'valores': {'E': Config.E_ACO, 'f_y': fy}, 'valor': lambda_p, 'ref': 'Tabela F.1'}}
    verificacao_texto = ""
    if lambda_val <= lambda_p:
        verificacao_texto = f"""A esbeltez da mesa (λ = {lambda_val:.2f}) é **menor ou igual** à esbeltez limite plástica (λp = {lambda_p:.2f}).
        **Conclusão:** A mesa é classificada como **COMPACTA**."""
        Mrdx = Mp / Config.GAMMA_A1
        detalhes['Mrdx_calc'] = {'desc': 'Momento Resistente (Mesa Compacta)', 'formula': 'M_{rd} = \\frac{{M_p}}{{\\gamma_{{a1}}}}', 'valores': {'M_p': Mp, '\\gamma_{{a1}}': Config.GAMMA_A1}, 'valor': Mrdx, 'unidade': 'kN.cm'}
    else:
        sigma_r = Config.FATOR_SIGMA_R * fy
        detalhes['sigma_r'] = {'desc': 'Tensão Residual (σr)', 'formula': '\\sigma_r = 0,3 \\times f_y', 'valores': {'f_y': fy}, 'valor': sigma_r, 'unidade': 'kN/cm²'}
        Mr = (fy - sigma_r) * Wx
        detalhes['Mr_calc'] = {'desc': 'Momento de Escoamento Residual (Mr)', 'formula': 'M_r = (f_y - \\sigma_r) \\times W_x', 'valores': {'f_y': fy, '\\sigma_r': sigma_r, 'W_x': Wx}, 'valor': Mr, 'unidade': 'kN.cm'}
    
        if tipo_fabricacao == "Laminado":
            lambda_r = Config.FATOR_LAMBDA_R_FLM_LAMINADO * math.sqrt(Config.E_ACO / (fy - sigma_r)) if (fy - sigma_r) > 0 else float('inf')
            detalhes['lambda_r'] = {'desc': 'Esbeltez Limite (Semicompacta)', 'formula': '\\lambda_r = 0,83 \\sqrt{{\\frac{{E}}{{f_y - \\sigma_r}}}}', 'valores': {'E': Config.E_ACO, 'f_y': fy, '\\sigma_r': sigma_r}, 'valor': lambda_r, 'ref': 'Tabela F.1'}
        else: # Soldado
            kc = 4 / math.sqrt(h/tw) if (h/tw) > 0 else float('inf')
            if kc < 0.35: kc = 0.35
            if kc > 0.76: kc = 0.76
            detalhes['kc'] = {'desc': 'Parâmetro kc', 'formula': 'k_c = \\frac{4}{\\sqrt{h/t_w}} \\, (0,35 \\le k_c \\le 0,76)', 'valores': {'h': h, 't_w': tw}, 'valor': kc, 'unidade': ''}
            lambda_r = Config.FATOR_LAMBDA_R_FLM_SOLDADO * math.sqrt(Config.E_ACO / ((fy - sigma_r)/kc) ) if (fy - sigma_r) > 0 and kc > 0 else float('inf')
            detalhes['lambda_r'] = {'desc': 'Esbeltez Limite (Semicompacta)', 'formula': '\\lambda_r = 0,95 \\sqrt{{\\frac{E \\times k_c}{{f_y - \\sigma_r}}}}', 'valores': {'E': Config.E_ACO, 'k_c': kc, 'f_y': fy, '\\sigma_r': sigma_r}, 'valor': lambda_r, 'ref': 'Tabela F.1'}

        if lambda_val <= lambda_r:
            verificacao_texto = f"""A esbeltez da mesa (λ = {lambda_val:.2f}) está **entre os limites** plástico (λp = {lambda_p:.2f}) e semicompacto (λr = {lambda_r:.2f}).
            **Conclusão:** A mesa é classificada como **SEMICOMPACTA**."""
            Mrdx = (1 / Config.GAMMA_A1) * (Mp - (Mp - Mr) * ((lambda_val - lambda_p) / (lambda_r - lambda_p)))
            detalhes['Mrdx_calc'] = {'desc': 'Momento Resistente (Mesa Semicompacta)', 'formula': 'M_{rd} = \\frac{{1}}{{\\gamma_{{a1}}}} [M_p - (M_p - M_r) (\\frac{{\\lambda - \\lambda_p}}{{\\lambda_r - \\lambda_p}})]', 'valores': {'\\gamma_{{a1}}': Config.GAMMA_A1, 'M_p': Mp, 'M_r': Mr, '\\lambda': lambda_val, '\\lambda_p': lambda_p, '\\lambda_r': lambda_r}, 'valor': Mrdx, 'unidade': 'kN.cm'}
        else:
            verificacao_texto = f"""A esbeltez da mesa (λ = {lambda_val:.2f}) é **maior** que a esbeltez limite semicompacta (λr = {lambda_r:.2f}).
            **Conclusão:** A mesa é classificada como **ESBELTA**. O cálculo para almas esbeltas à flexão não é coberto por este aplicativo (ver Anexo H da NBR 8800)."""
            if tipo_fabricacao == "Laminado":
                Mcr = (0.69 * Config.E_ACO * Wx) / (lambda_val**2) if lambda_val > 0 else 0
                detalhes['Mcr'] = {'desc': 'Momento Crítico (Mcr)', 'formula': 'M_{cr} = \\frac{0,69 \\times E \\times W_x}{\\lambda^2}', 'valores': {'E': Config.E_ACO, 'W_x': Wx, '\\lambda': lambda_val}, 'valor': Mcr, 'unidade': 'kN.cm'}
            else: # Soldado
                Mcr = (0.90 * Config.E_ACO * kc * Wx) / (lambda_val**2) if lambda_val > 0 else 0
                detalhes['Mcr'] = {'desc': 'Momento Crítico (Mcr)', 'formula': 'M_{cr} = \\frac{0,90 \\times E \\times k_c \\times W_x}{\\lambda^2}', 'valores': {'E': Config.E_ACO, 'k_c': kc, 'W_x': Wx, '\\lambda': lambda_val}, 'valor': Mcr, 'unidade': 'kN.cm'}
            Mrdx = Mcr / Config.GAMMA_A1
            detalhes['Mrdx_calc'] = {'desc': 'Momento Resistente (Mesa Esbelta)', 'formula': 'M_{rd} = \\frac{M_{cr}}{\\gamma_{a1}}', 'valores': {'M_{cr}': Mcr, '\\gamma_{a1}': Config.GAMMA_A1}, 'valor': Mrdx, 'unidade': 'kN.cm'}
    
    detalhes['verificacao_classificacao'] = {'desc': 'Classificação da Mesa quanto à Flambagem Local', 'texto': verificacao_texto}
    detalhes['Mrdx'] = Mrdx
    return detalhes

def _calcular_mrdx_fla(props, fy):
    h, tw, Zx, Wx = props['h'], props['tw'], props['Zx'], props['Wx']
    Mp = Zx * fy
    lambda_val = h / tw if tw > 0 else float('inf')
    lambda_p = Config.FATOR_LAMBDA_P_FLA * math.sqrt(Config.E_ACO / fy)
    detalhes = {'Mp': {'desc': 'Momento de Plastificação', 'formula': 'M_p = Z_x \\times f_y', 'valores': {'Z_x': Zx, 'f_y': fy}, 'valor': Mp, 'unidade': 'kN.cm'}, 'lambda': {'desc': 'Esbeltez da Alma (h/tw)', 'formula': '\\lambda = \\frac{{h}}{{t_w}}', 'valores': {'h': h, 't_w': tw}, 'valor': lambda_val},'lambda_p': {'desc': 'Esbeltez Limite (Plástica)', 'formula': '\\lambda_p = 3,76 \\sqrt{{\\frac{{E}}{{f_y}}}}', 'valores': {'E': Config.E_ACO, 'f_y': fy}, 'valor': lambda_p, 'ref': 'Tabela F.1'}}
    verificacao_texto = ""
    if lambda_val <= lambda_p:
        verificacao_texto = f"""A esbeltez da alma (λ = {lambda_val:.2f}) é **menor ou igual** à esbeltez limite plástica (λp = {lambda_p:.2f}).
        **Conclusão:** A alma é classificada como **COMPACTA**."""
        Mrdx = Mp / Config.GAMMA_A1
        detalhes['Mrdx_calc'] = {'desc': 'Momento Resistente (Alma Compacta)', 'formula': 'M_{rd} = \\frac{{M_p}}{{\\gamma_{{a1}}}}', 'valores': {'M_p': Mp, '\\gamma_{{a1}}': Config.GAMMA_A1}, 'valor': Mrdx, 'unidade': 'kN.cm'}
    else:
        lambda_r = Config.FATOR_LAMBDA_R_FLA * math.sqrt(Config.E_ACO / fy)
        detalhes['lambda_r'] = {'desc': 'Esbeltez Limite (Semicompacta)', 'formula': '\\lambda_r = 5,70 \\sqrt{{\\frac{{E}}{{f_y}}}}', 'valores': {'E': Config.E_ACO, 'f_y': fy}, 'valor': lambda_r, 'ref': 'Tabela F.1'}
        Mr = fy * Wx
        detalhes['Mr_calc'] = {'desc': 'Momento de Escoamento (Mr)', 'formula': 'M_r = f_y \\times W_x', 'valores': {'f_y': fy, 'W_x': Wx}, 'valor': Mr, 'unidade': 'kN.cm'}
        if lambda_val <= lambda_r:
            verificacao_texto = f"""A esbeltez da alma (λ = {lambda_val:.2f}) está **entre os limites** plástico (λp = {lambda_p:.2f}) e semicompacto (λr = {lambda_r:.2f}).
            **Conclusão:** A alma é classificada como **SEMICOMPACTA**."""
            Mrdx = (1 / Config.GAMMA_A1) * (Mp - (Mp - Mr) * ((lambda_val - lambda_p) / (lambda_r - lambda_p)))
            detalhes['Mrdx_calc'] = {'desc': 'Momento Resistente (Alma Semicompacta)', 'formula': 'M_{rd} = \\frac{{1}}{{\\gamma_{{a1}}}} [M_p - (M_p - M_r) (\\frac{{\\lambda - \\lambda_p}}{{\\lambda_r - \\lambda_p}})]', 'valores': {'\\gamma_{{a1}}': Config.GAMMA_A1, 'M_p': Mp, 'M_r': Mr, '\\lambda': lambda_val, '\\lambda_p': lambda_p, '\\lambda_r': lambda_r}, 'valor': Mrdx, 'unidade': 'kN.cm'}
        else:
            verificacao_texto = f"""A esbeltez da alma (λ = {lambda_val:.2f}) é **maior** que a esbeltez limite semicompacta (λr = {lambda_r:.2f}).
            **Conclusão:** A alma é classificada como **ESBELTA**. O cálculo para almas esbeltas à flexão não é coberto por este aplicativo (ver Anexo H da NBR 8800)."""
            Mrdx = 0
            detalhes['Mrdx_calc'] = {'desc': 'Momento Resistente (Alma Esbelta)', 'formula': 'N/A', 'valores': {}, 'valor': Mrdx, 'unidade': 'kN.cm', 'ref': 'Perfil com alma esbelta. Ver Anexo H.'}
    detalhes['verificacao_classificacao'] = {'desc': 'Classificação da Alma quanto à Flambagem Local', 'texto': verificacao_texto}
    detalhes['Mrdx'] = Mrdx
    return detalhes

def _calcular_vrd(props, fy, usa_enrijecedores, a_enr):
    d, h, tw = props['d'], props['h'], props['tw']
    Vpl = Config.FATOR_VP * d * tw * fy
    lambda_val = h / tw if tw > 0 else float('inf')
    
    detalhes = {'Vpl': {'desc': 'Força Cortante de Plastificação', 'formula': 'V_{pl} = 0,60 \\times d \\times t_{w} \\times f_{y}', 'valores': {'d': d, 't_{w}': tw, 'f_{y}': fy}, 'valor': Vpl, 'unidade': 'kN'}, 'lambda': {'desc': 'Esbeltez da Alma (Cisalhamento)', 'formula': '\\lambda = \\frac{{h}}{{t_w}}', 'valores': {'h': h, 't_w': tw}, 'valor': lambda_val}}

    kv = Config.KV_ALMA_SEM_ENRIJECEDORES
    kv_formula = "k_v = 5"
    kv_desc = "Fator de Flambagem (kv) - para almas sem enrijecedores"
    kv_valores = {}

    if usa_enrijecedores and a_enr > 0 and h > 0:
        a_h_ratio = a_enr / h
        if a_h_ratio < 3:
            kv = 5 + (5 / (a_h_ratio**2))
            kv_formula = "k_v = 5 + \\frac{5}{(a/h)^2}"
            kv_desc = "Fator de Flambagem (kv) - com enrijecedores"
            kv_valores = {'a': a_enr, 'h': h}
    
    detalhes['kv_calc'] = {'desc': kv_desc, 'formula': kv_formula, 'valores': kv_valores, 'valor': kv, 'unidade': ''}
    
    lambda_p = Config.FATOR_LAMBDA_P_VRD * math.sqrt((kv * Config.E_ACO) / fy)
    detalhes['lambda_p'] = {'desc': 'Esbeltez Limite (Plástica)', 'formula': '\\lambda_p = 1,10 \\sqrt{{\\frac{{k_v \\times E}}{{f_y}}}}', 'valores': {'k_v': kv, 'E': Config.E_ACO, 'f_y': fy}, 'valor': lambda_p}

    verificacao_texto = ""
    if lambda_val <= lambda_p:
        verificacao_texto = f"""A esbeltez da alma (λ = {lambda_val:.2f}) é **menor ou igual** ao limite de plastificação (λp = {lambda_p:.2f}).
        **Conclusão:** A resistência é governada pelo escoamento da alma por cisalhamento."""
        Vrd = Vpl / Config.GAMMA_A1
        detalhes['Vrd_calc'] = {'desc': 'Cortante Resistente (Escoamento)', 'formula': 'V_{rd} = \\frac{{V_{{pl}}}}{{\\gamma_{{a1}}}}', 'valores': {'V_{{pl}}': Vpl, '\\gamma_{{a1}}': Config.GAMMA_A1}, 'valor': Vrd, 'unidade': 'kN'}
    else:
        lambda_r = Config.FATOR_LAMBDA_R_VRD * math.sqrt((kv * Config.E_ACO) / fy)
        detalhes['lambda_r'] = {'desc': 'Esbeltez Limite (Inelástica)', 'formula': '\\lambda_r = 1,37 \\sqrt{{\\frac{{k_v \\times E}}{{f_y}}}}', 'valores': {'k_v': kv, 'E': Config.E_ACO, 'f_y': fy}, 'valor': lambda_r}
        if lambda_val <= lambda_r:
            verificacao_texto = f"""A esbeltez da alma (λ = {lambda_val:.2f}) está **entre o regime** plástico (λp = {lambda_p:.2f}) e o elástico (λr = {lambda_r:.2f}).
            **Conclusão:** Ocorre flambagem por cisalhamento no regime inelástico."""
            Vrd = (lambda_p / lambda_val) * (Vpl / Config.GAMMA_A1) if lambda_val > 0 else 0
            detalhes['Vrd_calc'] = {'desc': 'Cortante Resistente (Inelástico)', 'formula': 'V_{rd} = \\frac{{\\lambda_p}}{{\\lambda}} \\times \\frac{{V_{{pl}}}}{{\\gamma_{{a1}}}}', 'valores': {'\\lambda_p': lambda_p, '\\lambda': lambda_val, 'V_{{pl}}': Vpl, '\\gamma_{{a1}}': Config.GAMMA_A1}, 'valor': Vrd, 'unidade': 'kN'}
        else:
            verificacao_texto = f"""A esbeltez da alma (λ = {lambda_val:.2f}) é **maior** que o limite para flambagem inelástica (λr = {lambda_r:.2f}).
            **Conclusão:** Ocorre flambagem por cisalhamento no regime elástico."""
            Vrd = (Config.FATOR_VRD_ELASTICO * (lambda_p / lambda_val)**2) * (Vpl / Config.GAMMA_A1) if lambda_val > 0 else 0
            detalhes['Vrd_calc'] = {'desc': 'Cortante Resistente (Elástico)', 'formula': 'V_{rd} = 1,24 (\\frac{{\\lambda_p}}{{\\lambda}})^2 \\times \\frac{{V_{{pl}}}}{{\\gamma_{{a1}}}}', 'valores': {'\\lambda_p': lambda_p, '\\lambda': lambda_val, 'V_{{pl}}': Vpl, '\\gamma_{{a1}}': Config.GAMMA_A1}, 'valor': Vrd, 'unidade': 'kN'}
    detalhes['verificacao_classificacao'] = {'desc': 'Classificação da Alma quanto ao Cisalhamento', 'texto': verificacao_texto}
    detalhes['Vrd'] = Vrd
    return detalhes

# ==============================================================================
# 3. FUNÇÕES DE GERAÇÃO DE INTERFACE E GRÁFICOS
# ==============================================================================

def create_professional_header():
    st.markdown("""
    <div class="pro-header">
        <h1>🏗️ Calculadora Estrutural Pro</h1>
        <p>Análise Avançada de Perfis Metálicos | NBR 8800:2008</p>
    </div>
    """, unsafe_allow_html=True)

def create_metrics_dashboard(input_params):
    st.markdown("### 📊 Parâmetros do Projeto")
    
    msd_value = input_params.get('Msd', 0)
    vsd_value = input_params.get('Vsd', 0)

    col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
    
    with col1:
        st.metric(label="📐 Norma", value="NBR 8800")
    with col2:
        st.metric(label="⚡ Módulo E", value="20.000 kN/cm²")
    with col3:
        st.metric(label="🛡️ γa1", value="1,10")
    with col4:
        st.metric(label="📏 Vão", value=f"{input_params['L_cm']/100:.2f} m")
    with col5:
        st.metric(label="🔥 fy", value=f"{input_params['fy_aco']:.1f} kN/cm²")
    
    with col6:
        st.metric(
            label=" Msd (Momento)",
            value=f"{msd_value/100:.2f} kNm" if msd_value > 0 else "-",
            help="Momento Fletor Solicitante de Cálculo"
        )
    with col7:
        st.metric(
            label=" Vsd (Cortante)",
            value=f"{vsd_value:.2f} kN" if vsd_value > 0 else "-",
            help="Força Cortante Solicitante de Cálculo"
        )

def style_classic_dataframe(df):
    def color_efficiency(val):
        if pd.isna(val) or not isinstance(val, (int, float)): return ''
        if val > 100:   color = '#f8d7da' # Red
        elif val > 95:  color = '#ffeeba' # Yellow
        elif val > 80:  color = '#fff3cd' # Light Yellow
        else:           color = '#d4edda' # Green
        return f'background-color: {color}'

    def style_status(val):
        if val == 'APROVADO':
            return 'background-color: #d4edda; font-weight: bold; color: #155724;'
        elif val == 'REPROVADO':
            return 'background-color: #f8d7da; font-weight: bold; color: #721c24;'
        return ''

    efficiency_cols = [col for col in df.columns if '%' in col]
    
    styled_df = df.style.applymap(color_efficiency, subset=efficiency_cols)
    
    if 'Status' in df.columns:
        styled_df = styled_df.applymap(style_status, subset=['Status'])
        
    format_dict = {"Peso (kg/m)": "{:.2f}", **{col: "{:.1f}" for col in efficiency_cols}}
    return styled_df.format(format_dict)

def create_top_profiles_chart(df_approved, top_n=10):
    if df_approved.empty: return None
    df_top = df_approved.head(top_n).sort_values(by='Peso (kg/m)', ascending=False)
    fig = go.Figure(go.Bar(
        y=df_top['Perfil'], x=df_top['Peso (kg/m)'], orientation='h',
        text=[f'{w:.2f} kg/m' for w in df_top['Peso (kg/m)']], textposition='auto',
        marker=dict(color=df_top['Peso (kg/m)'], colorscale='Blues_r', colorbar=dict(title="Peso")),
        hovertemplate='<b>%{y}</b><br>Peso: %{x:.2f} kg/m<extra></extra>'
    ))
    fig.update_layout(
        title={'text': f'🏆 Top {top_n} Perfis Mais Leves (Aprovados)', 'x': 0.5},
        xaxis_title='Peso (kg/m)', yaxis_title='Perfil', template='plotly_white', height=500, margin=dict(l=150)
    )
    return fig

# Funções para renderizar o memorial de cálculo usando componentes nativos
def render_verification_step(title, details_dict, solicitante):
    """Renderiza um passo de verificação com fórmulas e detalhes."""
    st.markdown(f"#### {title}")
    
    with st.expander("Ver cálculo detalhado", expanded=True):
        # Classificação do regime de flambagem
        if 'verificacao_classificacao' in details_dict:
            st.markdown(f"##### {details_dict['verificacao_classificacao']['desc']}")
            st.info(details_dict['verificacao_classificacao']['texto'])

        # Detalhes das fórmulas intermediárias
        for key, value in details_dict.items():
            if isinstance(value, dict) and 'formula' in value:
                if key not in ['Mrdx_calc', 'Vrd_calc', 'verificacao_classificacao', 'verificacao_limite']:
                    st.markdown(f"##### {value['desc']}")
                    st.latex(value['formula'])
                    formula_numerica = value['formula']
                    for var, val_num in value['valores'].items():
                        formula_numerica = formula_numerica.replace(var, f"\\mathbf{{{val_num:.2f}}}")
                    st.latex(f"{formula_numerica} = {value['valor']:.4f} \\, {value.get('unidade', '')}")

        # Cálculo da resistência final
        st.markdown(f"##### Cálculo da Resistência Final")
        resistente_key = 'Mrdx_calc' if 'Mrdx_calc' in details_dict else 'Vrd_calc'
        
        if resistente_key in details_dict:
            res_details = details_dict[resistente_key]
            st.latex(res_details['formula'])
            valor_final = res_details['valor']
            
            unit = res_details.get('unidade', '')
            if 'Mrd' in resistente_key:
                valor_final /= 100.0
                unit = 'kNm'

            st.latex(f"= {valor_final:.2f} \\, {unit}")
            st.caption(f"Referência: {res_details.get('ref', '')}")

        # Verificação de limite (exclusivo para FLT inelástica)
        if 'verificacao_limite' in details_dict:
            st.markdown(f"##### {details_dict['verificacao_limite']['desc']}")
            st.markdown(details_dict['verificacao_limite']['texto'])
    
    # Eficiência e status
    st.markdown(f"##### Verificação Final")
    resistente = details_dict.get('Mrdx', details_dict.get('Vrd', 0))
    eficiencia = (solicitante / resistente) * 100 if resistente > 0 else float('inf')
    status = "APROVADO" if eficiencia <= 100.1 else "REPROVADO"
    
    comp_symbol = "\\le" if status == "APROVADO" else ">"
    sol_symbol = 'M_{sd}' if 'Mrd' in resistente_key else 'V_{sd}'
    res_symbol = 'M_{rd}' if 'Mrd' in resistente_key else 'V_{rd}'
    unit = 'kN.cm' if 'Mrd' in resistente_key else 'kN'
    
    st.latex(f"\\text{{Solicitante: }} {solicitante:.2f} \\, {unit}")
    st.latex(f"\\text{{Resistente: }} {resistente:.2f} \\, {unit}")
    st.markdown(f"**Verificação:** ${sol_symbol} {comp_symbol} {res_symbol}$")
    st.latex(f"\\text{{Eficiência}} = \\frac{{{solicitante:.2f}}}{{{resistente:.2f}}} = {eficiencia:.1f}\\%")
    
    if status == "APROVADO":
        st.success(f"Status: **{status}** 🎉")
    else:
        st.error(f"Status: **{status}** ⛔")
    st.markdown("---")


def render_final_check(check_name, solicitante, s_symbol, resistente, r_symbol, unit, eficiencia, status):
    """Renderiza o bloco de verificação final de maneira clara."""
    st.markdown(f"#### Verificação Final de {check_name}")
    st.latex(f"\\text{{Solicitante: }} {s_symbol} = {solicitante:.2f} \\, {unit}")
    st.latex(f"\\text{{Resistente: }} {r_symbol} = {resistente:.2f} \\, {unit}")

    comp_symbol = "\\le" if status == "APROVADO" else ">"
    st.markdown(f"**Verificação:** ${s_symbol} {comp_symbol} {r_symbol}$")
    st.latex(f"\\text{{Eficiência}} = \\frac{{{solicitante:.2f}}}{{{resistente:.2f}}} = {eficiencia:.1f}\\%")

    if status == "APROVADO":
        st.success(f"**Status:** {status} 🎉")
    else:
        st.error(f"**Status:** {status} ⛔")

def render_detailed_memorial_streamlit(perfil_nome, perfil_tipo, resultados, input_params, props):
    """
    Renderiza o memorial de cálculo detalhado usando apenas componentes nativos do Streamlit.
    """
    st.header(f"📋 Memorial de Cálculo Estrutural")
    st.subheader(f"Perfil: {perfil_nome} ({perfil_tipo})")

    # Informações do Projeto
    st.markdown("### 📋 Identificação do Projeto")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.write(f"**Projeto:** {input_params['projeto_info']['nome']}")
    with col2:
        st.write(f"**Engenheiro:** {input_params['projeto_info']['engenheiro']}")
    with col3:
        st.write(f"**Data:** {input_params['projeto_info']['data']}")
    with col4:
        st.write(f"**Revisão:** {input_params['projeto_info']['revisao']}")

    # Resumo Executivo
    st.markdown("---")
    st.header("1. Resumo Executivo")
    st.dataframe(resultados['resumo_df'].style.applymap(lambda x: 'background-color: #d4edda' if 'APROVADO' in str(x) else 'background-color: #f8d7da', subset=['Status']), use_container_width=True)

    # Detalhes do Perfil e Entradas
    st.markdown("---")
    st.header("2. Parâmetros de Entrada e Propriedades do Perfil")
    
    st.subheader("2.1 Propriedades Geométricas do Perfil")
    profile_props_df = pd.DataFrame({
        'Propriedade': ['d (cm)', 'bf (cm)', 'tw (cm)', 'tf (cm)', 'h (cm)', 'Ix (cm⁴)', 'Wx (cm³)', 'Zx (cm³)', 'Peso (kg/m)'],
        'Valor': [props['d'], props['bf'], props['tw'], props['tf'], props['h'], props['Ix'], props['Wx'], props['Zx'], props['Peso']]
    })
    st.table(profile_props_df.set_index('Propriedade').style.format("{:.2f}"))

    st.subheader("2.2 Esforços Solicitantes")
    Msd_total, Vsd_total, detalhes_esforcos = calcular_esforcos_viga(
        input_params['tipo_viga'], 
        input_params['L_cm'], 
        input_params['q_serv_kn_cm'] * input_params['gamma_f'], 
        (input_params['p_load_serv'][0] * input_params['gamma_f'], input_params['p_load_serv'][1]) if input_params['p_load_serv'] else None
    )

    st.markdown(f"**Tipo de Viga:** {input_params['tipo_viga']} | **Comprimento:** {input_params['L_cm']/100:.2f} m")
    
    col_esf1, col_esf2 = st.columns(2)
    with col_esf1:
        st.markdown("#### Momento Fletor (Msd)")
        if detalhes_esforcos['Msd_q']['valor'] > 0:
            st.latex(f"M_{{sd,q}} = {detalhes_esforcos['Msd_q']['formula_numerica']} = {detalhes_esforcos['Msd_q']['valor']:.2f} \\, kN.cm")
        if detalhes_esforcos['Msd_p']['valor'] > 0:
            st.latex(f"M_{{sd,P}} = {detalhes_esforcos['Msd_p']['formula_numerica']} = {detalhes_esforcos['Msd_p']['valor']:.2f} \\, kN.cm")
        st.latex(f"M_{{sd,total}} = {Msd_total:.2f} \\, kN.cm")
    
    with col_esf2:
        st.markdown("#### Força Cortante (Vsd)")
        if detalhes_esforcos['Vsd_q']['valor'] > 0:
            st.latex(f"V_{{sd,q}} = {detalhes_esforcos['Vsd_q']['formula_numerica']} = {detalhes_esforcos['Vsd_q']['valor']:.2f} \\, kN")
        if detalhes_esforcos['Vsd_p']['valor'] > 0:
            st.latex(f"V_{{sd,P}} = {detalhes_esforcos['Vsd_p']['formula_numerica']} = {detalhes_esforcos['Vsd_p']['valor']:.2f} \\, kN")
        st.latex(f"V_{{sd,total}} = {Vsd_total:.2f} \\, kN")

    # Verificações de Resistência (ELU)
    st.markdown("---")
    st.header("3. Verificações de Resistência (ELU)")
    
    st.subheader("3.1. Resistência à Flexão (Mrd)")
    render_verification_step("Flambagem Lateral com Torção (FLT)", resultados['flt'], input_params['Msd'])
    render_verification_step("Flambagem Local da Mesa (FLM)", resultados['flm'], input_params['Msd'])
    render_verification_step("Flambagem Local da Alma (FLA)", resultados['fla'], input_params['Msd'])

    st.markdown("---")
    st.subheader("Verificação Final à Flexão")
    Mrd_final = min(resultados['flt']['Mrdx'], resultados['flm']['Mrdx'], resultados['fla']['Mrdx'])
    ef_geral = (input_params['Msd'] / Mrd_final) * 100 if Mrd_final > 0 else float('inf')
    status_flexao = "APROVADO" if ef_geral <= 100.1 else "REPROVADO"
    render_final_check(
        'Flexão', 
        input_params['Msd'], 
        'M_{sd}', 
        Mrd_final, 
        'M_{rd}', 
        'kN.cm', 
        ef_geral, 
        status_flexao
    )

    # Cisalhamento
    st.subheader("3.2. Resistência ao Cisalhamento (Vrd)")
    render_verification_step("Resistência ao Cisalhamento (Vrd)", resultados['cis'], input_params['Vsd'])
    render_final_check(
        'Cisalhamento', 
        input_params['Vsd'], 
        'V_{sd}', 
        resultados['cis']['Vrd'], 
        'V_{rd}', 
        'kN', 
        resultados['cis']['eficiencia'], 
        resultados['cis']['status']
    )

    # Verificação de Serviço (ELS)
    if input_params['input_mode'] == "Calcular a partir de Cargas na Viga":
        st.markdown("---")
        st.header("4. Verificação de Serviço (ELS)")
        
        st.subheader("4.1. Flecha Máxima Atuante (δ_max)")
        detalhes_flecha = resultados['flecha']['detalhes']
        delta_q_details = detalhes_flecha.get('delta_q', {})
        delta_p_details = detalhes_flecha.get('delta_p', {})
        
        if delta_q_details.get('valor', 0) > 0:
            st.markdown("##### Flecha devido à Carga Distribuída (δ_q)")
            st.latex(delta_q_details['formula_simbolica'])
            st.latex(f"= {delta_q_details['valor']:.4f} \\, cm")
        
        if delta_p_details.get('valor', 0) > 0:
            st.markdown("##### Flecha devido à Carga Pontual (δ_p)")
            st.latex(delta_p_details['formula_simbolica'])
            st.latex(f"= {delta_p_details['valor']:.4f} \\, cm")

        st.markdown("##### Flecha Total")
        st.latex(f"\\delta_{{max}} = \\delta_q + \\delta_p = {detalhes_flecha['delta_total']:.4f} \\, cm")

        st.subheader("4.2. Flecha Limite (δ_lim)")
        st.latex(f"\\delta_{{lim}} = \\frac{{L}}{{{resultados['flecha']['divisor']}}} = \\frac{{{input_params['L_cm']:.2f}}}{{{resultados['flecha']['divisor']}}} = {resultados['flecha']['flecha_limite']:.2f} \\, cm")

        st.subheader("4.3. Verificação Final da Flecha")
        render_final_check(
            'Flecha', 
            resultados['flecha']['flecha_max'], 
            '\\delta_{max}', 
            resultados['flecha']['flecha_limite'], 
            '\\delta_{lim}', 
            'cm', 
            resultados['flecha']['eficiencia'], 
            resultados['flecha']['status']
        )
    
    st.markdown("---")
    st.info(f"Memorial gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}")

# ==============================================================================
# 4. FUNÇÕES DE ORQUESTRAÇÃO E ANÁLISE
# ==============================================================================

def perform_all_checks(props, fy_aco, Lb_projeto, Cb_projeto, L_cm, Msd, Vsd, q_serv_kn_cm, p_load_serv, tipo_viga, input_mode, tipo_fabricacao, usa_enrijecedores, a_enr, limite_flecha_divisor, projeto_info, detalhado=False, **kwargs):
    res_flt = _calcular_mrdx_flt(props, Lb_projeto, Cb_projeto, fy_aco)
    res_flm = _calcular_mrdx_flm(props, fy_aco, tipo_fabricacao)
    res_fla = _calcular_mrdx_fla(props, fy_aco)
    res_vrd = _calcular_vrd(props, fy_aco, usa_enrijecedores, a_enr)
    
    if res_flt['Mrdx'] > 0: res_flt['eficiencia'] = (Msd / res_flt['Mrdx']) * 100
    else: res_flt['eficiencia'] = float('inf')
    if res_flm['Mrdx'] > 0: res_flm['eficiencia'] = (Msd / res_flm['Mrdx']) * 100
    else: res_flm['eficiencia'] = float('inf')
    if res_fla['Mrdx'] > 0: res_fla['eficiencia'] = (Msd / res_fla['Mrdx']) * 100
    else: res_fla['eficiencia'] = float('inf')
    
    Vrd = res_vrd['Vrd']
    if Vrd > 0: res_cis = {'Vrd': Vrd, 'eficiencia': (Vsd / Vrd) * 100, 'status': "APROVADO" if (Vsd / Vrd) * 100 <= 100.1 else "REPROVADO"}
    else: res_cis = {'Vrd': Vrd, 'eficiencia': float('inf'), 'status': "REPROVADO"}
    
    flecha_max, flecha_limite, eficiencia_flecha, status_flecha = 0, 0, 0, "N/A"
    detalhes_flecha = {}
    if input_mode == "Calcular a partir de Cargas na Viga":
        detalhes_flecha = calcular_flecha_maxima(tipo_viga, L_cm, Config.E_ACO, props['Ix'], q_serv_kn_cm, p_load_serv)
        flecha_max = detalhes_flecha['delta_total']
        flecha_limite = L_cm / limite_flecha_divisor if L_cm > 0 else 0
        eficiencia_flecha = (flecha_max / flecha_limite) * 100 if flecha_limite > 0 else float('inf')
        status_flecha = "APROVADO" if eficiencia_flecha <= 100.1 else "REPROVADO"
    else:
        status_flecha = "N/A"

    res_flecha = {'flecha_max': flecha_max, 'flecha_limite': flecha_limite, 'eficiencia': eficiencia_flecha, 'status': status_flecha, 'Ix': props['Ix'], 'detalhes': detalhes_flecha, 'divisor': limite_flecha_divisor}
    
    return res_flt, res_flm, res_fla, res_cis, res_flecha, res_vrd

# ==============================================================================
# 5. APLICAÇÃO PRINCIPAL STREAMLIT
# ==============================================================================

def main():
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = None
    if 'analysis_mode' not in st.session_state:
        st.session_state.analysis_mode = "batch"
    if 'detailed_analysis_results' not in st.session_state:
        st.session_state.detailed_analysis_results = None
    if 'generated_memorial' not in st.session_state:
        st.session_state.generated_memorial = False

    all_sheets = load_data_from_local_file()
    if not all_sheets:
        st.stop()
    
    st.markdown(HTML_TEMPLATE_CSS_PRO, unsafe_allow_html=True)
    create_professional_header()

    with st.sidebar:
        st.markdown("## ⚙️ Configuração do Projeto")
        with st.expander("📋 Identificação do Projeto", expanded=False):
            projeto_nome = st.text_input("Nome do Projeto", "Análise Estrutural")
            engenheiro = st.text_input("Engenheiro Responsável", " ")
            data_projeto = st.date_input("Data", datetime.now())
            revisao = st.text_input("Revisão", "00")
        
        st.markdown("---")
        st.markdown("### 🏗️ Modelo Estrutural")
        tipo_viga = st.selectbox("🔗 Tipo de Viga:", ('Bi-apoiada', 'Engastada e Livre (Balanço)', 'Bi-engastada', 'Engastada e Apoiada'), key='tipo_viga')
        L_cm = st.number_input("📏 Comprimento (L, cm)", 10.0, value=500.0, step=10.0, key='L_cm')
        
        st.markdown("---")
        st.markdown("### ⚖️ Carregamento")
        input_mode = st.radio("Método de entrada:", ("Calcular a partir de Cargas na Viga", "Inserir Esforços Manualmente"), key='input_mode')

        Msd, Vsd, q_serv_kn_cm, p_load_serv = 0, 0, 0, None
        gamma_f = 1.4
        if input_mode == "Calcular a partir de Cargas na Viga":
            with st.container(border=True):
                st.subheader("Carga Distribuída (q)")
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
                gamma_f = st.number_input("Coeficiente de Majoração de Cargas (γf)", 1.0, value=1.4, step=0.1, key='gamma_f')
                q_servico_kn_m = (carga_area * larg_inf_total_m)
                q_serv_kn_cm = q_servico_kn_m / 100.0
                q_ult_kn_cm = q_serv_kn_cm * gamma_f
                p_load_ult = (p_load_serv[0] * gamma_f, p_load_serv[1]) if p_load_serv else None
                Msd, Vsd, _ = calcular_esforcos_viga(tipo_viga, L_cm, q_ult_kn_cm, p_load_ult)
        else:
            with st.container(border=True):
                st.warning("No modo manual, a verificação de flecha (ELS) não é realizada.")
                msd_input = st.number_input("Momento Solicitante de Cálculo (Msd, kNm)", min_value=0.0, value=100.0, key='msd_input')
                Msd = msd_input * 100
                Vsd = st.number_input("Força Cortante Solicitante de Cálculo (Vsd, kN)", min_value=0.0, value=50.0, key='vsd_input')
        
        st.markdown("---")
        st.markdown("### 🔩 Parâmetros do Aço e Viga")
        fy_aco = st.number_input("Tensão de Escoamento (fy, kN/cm²)", 20.0, 50.0, 34.5, 0.5, key='fy_aco')
        Lb_projeto = st.number_input("Comprimento Destravado (Lb, cm)", 10.0, value=L_cm, step=10.0, key='Lb_projeto')
        Cb_projeto = st.number_input("Fator de Modificação (Cb)", 1.0, 3.0, 1.10, key='Cb_projeto')
        
        with st.container(border=True):
            st.subheader("Enrijecedores de Alma")
            usa_enrijecedores = st.checkbox("Utilizar enrijecedores transversais?", key='usa_enrijecedores')
            a_enr = 0
            if usa_enrijecedores:
                a_enr = st.number_input("Distância entre enrijecedores (a, cm)", min_value=1.0, value=100.0, step=1.0, key='a_enr')

        st.markdown("---")
        st.markdown("### 📐 Verificação de Serviço (ELS)")
        limite_flecha_divisor = st.selectbox("Limite de Flecha (L/x)", (180, 250, 350, 500), index=2, key='limite_flecha_divisor')

    projeto_info = {'nome': projeto_nome, 'engenheiro': engenheiro, 'data': data_projeto.strftime('%d/%m/%Y'), 'revisao': revisao}
    input_params = {'tipo_viga': tipo_viga, 'L_cm': L_cm, 'input_mode': input_mode,'Msd': Msd, 'Vsd': Vsd, 'q_serv_kn_cm': q_serv_kn_cm, 'p_load_serv': p_load_serv, 'fy_aco': fy_aco, 'Lb_projeto': Lb_projeto, 'Cb_projeto': Cb_projeto,'usa_enrijecedores': usa_enrijecedores, 'a_enr': a_enr, 'limite_flecha_divisor': limite_flecha_divisor, 'projeto_info': projeto_info, 'gamma_f': gamma_f}

    create_metrics_dashboard(input_params)

    st.markdown("### 🎯 Modo de Análise")
    col1, col2 = st.columns(2)
    if col1.button("📊 Análise em Lote e Otimização", use_container_width=True):
        st.session_state.analysis_mode = "batch"
        st.session_state.generated_memorial = False
    if col2.button("📋 Memorial Detalhado de Perfil", use_container_width=True):
        st.session_state.analysis_mode = "detailed"
        st.session_state.generated_memorial = False

    if st.session_state.analysis_mode == "batch":
        st.header("📊 Análise em Lote")
        if st.button("🚀 Iniciar Análise Otimizada", type="primary", use_container_width=True):
            run_batch_analysis(all_sheets, input_params)
            
        if st.session_state.analysis_results is not None:
            df_all_results = st.session_state.analysis_results
            tabs = st.tabs([PROFILE_TYPE_MAP.get(name, name) for name in all_sheets.keys()])
            for i, sheet_name in enumerate(all_sheets.keys()):
                with tabs[i]:
                    df_type = df_all_results[df_all_results['Tipo'] == sheet_name].drop(columns=['Tipo'])
                    df_aprovados_cat = df_type[df_type['Status'] == 'APROVADO'].copy().sort_values(by='Peso (kg/m)')
                    df_reprovados_cat = df_type[df_type['Status'] == 'REPROVADO'].copy().sort_values(by='Peso (kg/m)')

                    if not df_aprovados_cat.empty:
                        st.plotly_chart(create_top_profiles_chart(df_aprovados_cat), use_container_width=True)
                        with st.expander(f"Ver todos os {len(df_aprovados_cat)} perfis aprovados"):
                            st.dataframe(style_classic_dataframe(df_aprovados_cat), use_container_width=True)
                    else:
                        st.info("Nenhum perfil aprovado nesta categoria.")

                    if not df_reprovados_cat.empty:
                        with st.expander(f"Ver os {len(df_reprovados_cat)} perfis reprovados"):
                            st.dataframe(style_classic_dataframe(df_reprovados_cat), use_container_width=True)

    elif st.session_state.analysis_mode == "detailed":
        st.header("📋 Memorial Detalhado")
        display_names = [PROFILE_TYPE_MAP.get(name, name) for name in all_sheets.keys()]
        reverse_name_map = {v: k for k, v in PROFILE_TYPE_MAP.items()}
        
        col1, col2 = st.columns(2)
        selected_display_name = col1.selectbox("Selecione o Tipo de Perfil:", display_names)
        sheet_name = reverse_name_map.get(selected_display_name, selected_display_name)
        df_selecionado = all_sheets[sheet_name]
        perfil_selecionado_nome = col2.selectbox("Selecione o Perfil Específico:", df_selecionado['Bitola (mm x kg/m)'])
        
        if st.button("📄 Gerar Memorial Completo", type="primary", use_container_width=True):
            run_detailed_analysis(df_selecionado, perfil_selecionado_nome, selected_display_name, input_params)
            st.session_state.generated_memorial = True
        
        if st.session_state.generated_memorial and st.session_state.get('detailed_analysis_results'):
            st.markdown("---")
            render_detailed_memorial_streamlit(
                st.session_state.detailed_analysis_results['perfil_nome'],
                st.session_state.detailed_analysis_results['perfil_tipo'],
                st.session_state.detailed_analysis_results['resultados'],
                st.session_state.detailed_analysis_results['input_params'],
                st.session_state.detailed_analysis_results['props']
            )

def run_detailed_analysis(df, perfil_nome, perfil_tipo_display, input_params):
    with st.spinner(f"Gerando análise completa para {perfil_nome}..."):
        try:
            perfil_series = df[df['Bitola (mm x kg/m)'] == perfil_nome].iloc[0]
            props = get_profile_properties(perfil_series)
            tipo_fabricacao = "Soldado" if "Soldado" in perfil_tipo_display else "Laminado"
            
            res_flt, res_flm, res_fla, res_cis, res_flecha, res_vrd = perform_all_checks(
                props=props, detalhado=False, tipo_fabricacao=tipo_fabricacao, **input_params
            )
            
            resumo_df = pd.DataFrame({
                'Verificação': ['Flexão (FLT)', 'Flexão (FLM)', 'Flexão (FLA)', 'Cisalhamento', 'Flecha (ELS)'],
                'Solicitante': [f"{input_params['Msd']:.2f} kN.cm"]*3 + [f"{input_params['Vsd']:.2f} kN", f"{res_flecha['flecha_max']:.2f} cm"],
                'Resistente': [f"{res_flt['Mrdx']:.2f} kN.cm", f"{res_flm['Mrdx']:.2f} kN.cm", f"{res_fla['Mrdx']:.2f} kN.cm", f"{res_cis['Vrd']:.2f} kN", f"≤ {res_flecha['flecha_limite']:.2f} cm"],
                'Eficiência (%)': [res_flt['eficiencia'], res_flm['eficiencia'], res_fla['eficiencia'], res_cis['eficiencia'], res_flecha['eficiencia']],
                'Status': ["APROVADO" if res_flt['eficiencia'] <= 100.1 else "REPROVADO",
                           "APROVADO" if res_flm['eficiencia'] <= 100.1 else "REPROVADO",
                           "APROVADO" if res_fla['eficiencia'] <= 100.1 else "REPROVADO",
                           res_cis['status'], res_flecha['status']]
            })

            resultados = {
                'resumo_df': resumo_df,
                'flt': res_flt,
                'flm': res_flm,
                'fla': res_fla,
                'cis': res_cis,
                'flecha': res_flecha,
                'vrd': res_vrd
            }
            
            st.session_state.detailed_analysis_results = {'perfil_nome': perfil_nome, 'perfil_tipo': perfil_tipo_display, 'resultados': resultados, 'input_params': input_params, 'props': props}
        
        except Exception as e:
            st.error(f"❌ Ocorreu um erro: {e}")

def run_batch_analysis(all_sheets, input_params):
    all_results = []
    progress_bar = st.progress(0, text="Analisando perfis...")
    total_perfis = sum(len(df) for df in all_sheets.values())
    perfis_processados = 0
    
    for sheet_name, df in all_sheets.items():
        display_name = PROFILE_TYPE_MAP.get(sheet_name, sheet_name)
        tipo_fabricacao_auto = "Soldado" if "Soldado" in display_name else "Laminado"
        
        for _, row in df.iterrows():
            perfis_processados += 1
            progress_bar.progress(perfis_processados / total_perfis, text=f"Analisando: {row['Bitola (mm x kg/m)']}")
            try:
                props = get_profile_properties(row)
                res_flt, res_flm, res_fla, res_cis, res_flecha, _ = perform_all_checks(
                    props=props, tipo_fabricacao=tipo_fabricacao_auto, **input_params
                )
                
                status_geral = "APROVADO"
                if any(res['eficiencia'] > 100.1 for res in [res_flt, res_flm, res_fla, res_cis, res_flecha]):
                    status_geral = "REPROVADO"
                
                all_results.append({
                    'Tipo': sheet_name, 'Perfil': row['Bitola (mm x kg/m)'],
                    'Peso (kg/m)': props.get('Peso', 0), 'Status': status_geral,
                    'Ef. FLT (%)': res_flt['eficiencia'], 'Ef. FLM (%)': res_flm['eficiencia'],
                    'Ef. FLA (%)': res_fla['eficiencia'], 'Ef. Cisalhamento (%)': res_cis['eficiencia'],
                    'Ef. Flecha (%)': res_flecha['eficiencia']
                })
            except (ValueError, KeyError):
                continue
    progress_bar.empty()
    st.session_state.analysis_results = pd.DataFrame(all_results) if all_results else pd.DataFrame()


if __name__ == '__main__':
    main()