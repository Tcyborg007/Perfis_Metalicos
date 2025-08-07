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
        "CVS": "Vigas de Seção Variável",
        "VS": "Vigas Soldadas"
    }

# Configuração da página com layout wide
st.set_page_config(
    page_title="Calculadora Estrutural Versátil", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS otimizado para visualização em tela cheia
HTML_TEMPLATE_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&family=Roboto+Slab:wght@400;700&display=swap');
    
    /* Reset e configurações base */
    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }
    
    body { 
        font-family: 'Roboto', sans-serif; 
        line-height: 1.6; 
        color: #333; 
        background-color: #f8f9fa;
        font-size: 14px;
    }
    
    /* Container principal responsivo */
    .container { 
        width: 100%;
        max-width: none;
        margin: 0;
        padding: 20px;
        background-color: white; 
        border-radius: 8px; 
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        min-height: 100vh;
    }
    
    /* Títulos */
    h1, h2, h3, h4, h5 { 
        font-family: 'Roboto Slab', serif; 
        color: #2c3e50; 
        border-bottom: 2px solid #3498db; 
        padding-bottom: 8px; 
        margin: 20px 0 15px 0;
        page-break-after: avoid;
    }
    
    h1 { 
        text-align: center; 
        border: none; 
        font-size: 2.5em; 
        margin-bottom: 30px;
        color: #1e3a8a;
    }
    
    h2 { 
        font-size: 1.8em; 
        margin-top: 40px;
    }
    
    h3 { 
        font-size: 1.5em; 
        margin-top: 30px;
    }
    
    h4 { 
        font-size: 1.3em; 
        margin-top: 25px;
    }
    
    h5 { 
        border-bottom: 1px solid #ddd; 
        font-size: 1.1em; 
        margin-top: 20px; 
        color: #34495e;
        padding-bottom: 5px;
    }
    
    /* Tabela de resumo */
    .summary-table { 
        width: 100%; 
        border-collapse: collapse; 
        margin: 25px 0; 
        font-size: 0.95em;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    .summary-table th, .summary-table td { 
        border: 1px solid #ddd; 
        padding: 12px 8px; 
        text-align: center; 
        vertical-align: middle; 
    }
    
    .summary-table th { 
        background-color: #34495e; 
        color: white; 
        font-weight: 600;
        font-size: 0.9em;
    }
    
    .summary-table tr:nth-child(even) {
        background-color: #f8f9fa;
    }
    
    .summary-table tr:hover {
        background-color: #e9ecef;
    }
    
    /* Blocos de fórmula */
    .formula-block { 
        background-color: #f8f9fa; 
        border-left: 4px solid #3498db; 
        padding: 20px; 
        margin: 25px 0; 
        border-radius: 6px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        page-break-inside: avoid;
    }
    
    /* Status de aprovação/reprovação */
    .pass { 
        color: #27ae60; 
        font-weight: bold; 
    }
    
    .fail { 
        color: #e74c3c; 
        font-weight: bold; 
    }
    
    /* Fórmulas matemáticas */
    .formula { 
        font-size: 1.1em; 
        text-align: center; 
        margin: 15px 0; 
        word-wrap: break-word; 
        overflow-x: auto; 
        padding: 12px; 
        background-color: #ffffff; 
        border-radius: 6px;
        border: 1px solid #e9ecef;
        font-family: 'Courier New', monospace;
    }
    
    /* Resultado final */
    .final-result { 
        font-weight: bold; 
        color: #2980b9; 
        text-align: center; 
        display: block; 
        margin-top: 20px; 
        font-size: 1.2em; 
        padding: 15px; 
        border: 2px solid #3498db; 
        border-radius: 8px; 
        background-color: #eaf5ff;
    }
    
    /* Status final */
    .final-status { 
        font-size: 1.4em; 
        text-align: center; 
        padding: 15px; 
        border-radius: 8px; 
        margin: 20px 0; 
        font-weight: bold;
    }
    
    .final-status.pass { 
        background-color: #d4edda; 
        color: #155724; 
        border: 2px solid #c3e6cb;
    }
    
    .final-status.fail { 
        background-color: #f8d7da; 
        color: #721c24; 
        border: 2px solid #f5c6cb;
    }
    
    /* Referência da norma */
    .ref-norma { 
        font-size: 0.85em; 
        color: #6c757d; 
        text-align: right; 
        margin-top: 15px; 
        font-style: italic; 
    }
    
    /* Parágrafos */
    p { 
        text-align: justify; 
        margin: 10px 0;
        line-height: 1.6;
    }
    
    /* Responsividade para dispositivos móveis */
    @media (max-width: 768px) {
        .container {
            padding: 15px;
        }
        
        h1 {
            font-size: 2em;
        }
        
        h2 {
            font-size: 1.5em;
        }
        
        .summary-table {
            font-size: 0.8em;
        }
        
        .summary-table th, .summary-table td {
            padding: 8px 4px;
        }
        
        .formula {
            font-size: 0.9em;
            padding: 8px;
        }
    }
    
    /* Configurações de impressão */
    @media print {
        .container {
            max-width: none;
            padding: 0;
            box-shadow: none;
        }
        
        .formula-block {
            break-inside: avoid;
        }
        
        h1, h2, h3, h4, h5 {
            break-after: avoid;
        }
    }
</style>
"""

st.markdown(HTML_TEMPLATE_CSS, unsafe_allow_html=True)

# ==============================================================================
# 2. FUNÇÕES DE CÁLCULO DE ENGENHARIA
# ==============================================================================

def calcular_esforcos_viga(tipo_viga, L_cm, q_kn_cm=0, p_load=None):
    """Calcula esforços solicitantes em vigas"""
    msd_q, vsd_q, msd_p, vsd_p = 0, 0, 0, 0
    L = L_cm

    # Parte da carga distribuída (q)
    if q_kn_cm > 0:
        if tipo_viga == 'Bi-apoiada':
            msd_q = (q_kn_cm * L**2) / 8
            vsd_q = (q_kn_cm * L) / 2
        elif tipo_viga == 'Engastada e Livre (Balanço)':
            msd_q = (q_kn_cm * L**2) / 2
            vsd_q = q_kn_cm * L
        elif tipo_viga == 'Bi-engastada':
            msd_q = (q_kn_cm * L**2) / 12
            vsd_q = (q_kn_cm * L) / 2
        elif tipo_viga == 'Engastada e Apoiada':
            msd_q = (q_kn_cm * L**2) / 8
            vsd_q = (5 * q_kn_cm * L) / 8
            
    # Parte da carga pontual (P)
    if p_load:
        P, x = p_load
        a = x
        b = L - a
        if tipo_viga == 'Bi-apoiada':
            msd_p = (P * a * b) / L
            vsd_p = max((P * b) / L, (P * a) / L)
        elif tipo_viga == 'Engastada e Livre (Balanço)':
            msd_p = P * a
            vsd_p = P
        elif tipo_viga == 'Bi-engastada':
            msd_p = max((P * a * b**2) / L**2, (P * a**2 * b) / L**2)
            vsd_p = max((P * b**2 * (3*a + b)) / L**3, (P * a**2 * (a + 3*b)) / L**3)
        elif tipo_viga == 'Engastada e Apoiada':
            msd_p = max((P*b*(L**2 - b**2))/(2*L**2), (P*a*(3*L**2 - a**2))/(2*L**3)*a)
            vsd_p = max(P*b*(3*L**2-b**2)/(2*L**3), P*a*(3*L-a)/(2*L**2))

    msd_total = msd_q + msd_p
    vsd_total = vsd_q + vsd_p

    return msd_total, vsd_total

def calcular_flecha_maxima(tipo_viga, L_cm, E, Ix, q_serv_kn_cm=0, p_serv_load=None):
    """Calcula flecha máxima em vigas"""
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
    """Extrai propriedades do perfil da série do pandas"""
    props = {
        "d": profile_series.get('d (mm)'),
        "bf": profile_series.get('bf (mm)'),
        "tw": profile_series.get('tw (mm)'),
        "tf": profile_series.get('tf (mm)'),
        "h": profile_series.get('h (mm)'),
        "Area": profile_series.get('Área (cm2)'),
        "Ix": profile_series.get('Ix (cm4)'),
        "Wx": profile_series.get('Wx (cm3)'),
        "rx": profile_series.get('rx (cm)'),
        "Zx": profile_series.get('Zx (cm3)'),
        "Iy": profile_series.get('Iy (cm4)'),
        "Wy": profile_series.get('Wy (cm3)'),
        "ry": profile_series.get('ry (cm)'),
        "Zy": profile_series.get('Zy (cm3)'),
        "J": profile_series.get('It (cm4)'),
        "Cw": profile_series.get('Cw (cm6)'),
        "Peso": profile_series.get('Massa Linear (kg/m)', profile_series.get('Peso (kg/m)'))
    }
    
    required_keys = ["d", "bf", "tw", "tf", "h", "Area", "Ix", "Wx", "rx", "Zx", "Iy", "ry", "J", "Cw", "Peso"]
    # Corrigindo os possíveis nomes das colunas de Perfil e Peso para corresponder ao seu código.
    profile_name = profile_series.get('Bitola (mm x kg/m)', 'Perfil Desconhecido')
    
    for key in required_keys:
        value = props.get(key)
        if value is None or pd.isna(value) or (isinstance(value, (int, float)) and value <= 0):
            raise ValueError(f"Propriedade ESSENCIAL '{key}' inválida ou nula no Excel para '{profile_name}'. Verifique a planilha.")
    
    # Converter de mm para cm
    for key in ['d', 'bf', 'tw', 'tf', 'h']: 
        props[key] /= 10.0
    
    return props

# ==============================================================================
# 3. GERAÇÃO DO MEMORIAL DE CÁLCULO
# ==============================================================================

def gerar_memorial_completo(perfil_nome, perfil_tipo, resultados):
    """Gera o HTML completo do memorial de cálculo"""
    html_content_interno = f"""
    <div class="container">
        <h1>Memorial de Cálculo Estrutural</h1>
        <h2>Perfil Metálico: {perfil_nome} ({perfil_tipo})</h2>
        <p style="text-align:center; font-style:italic;">Cálculos baseados na norma: <b>{Config.NOME_NORMA}</b></p>
        
        <h3>1. Resumo Final das Verificações</h3>
        {resultados['resumo_html']}
        
        {resultados['passo_a_passo_html']}
    </div>
    """
    
    # Para o download, cria-se um documento completo
    html_para_download = f"""
    <!DOCTYPE html><html lang="pt-BR">
    <head>
        <meta charset="UTF-8"><title>Memorial de Cálculo - {perfil_nome}</title>{HTML_TEMPLATE_CSS}
        <script type="text/javascript" async src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.7/MathJax.js?config=TeX-MML-AM_CHTML"></script>
    </head><body>{html_content_interno}</body></html>
    """

    # Para a visualização, usamos só o conteúdo interno injetado com st.markdown
    html_para_visualizacao = f"<div id='memorial-render'>{html_content_interno}</div>"

    return html_para_visualizacao, html_para_download

def _build_verification_block_html(title, solicitante, s_symbol, resistente, r_symbol, eficiencia, status, unit):
    """Constrói bloco HTML para verificação"""
    status_class = "pass" if status == "APROVADO" else "fail"
    comp_symbol = "≤" if status == "APROVADO" else ">"
    # Escapando o % para a f-string
    return f"""
    <h4>{title}</h4>
    <div class="formula-block">
        <p class="formula">
            {s_symbol} = {solicitante:.2f} {unit}
        </p>
        <p class="formula">
            {r_symbol} = {resistente:.2f} {unit}
        </p>
        <p class="formula">
            Verificação: {s_symbol} {comp_symbol} {r_symbol}
        </p>
        <p class="formula">
            Eficiência = ({s_symbol} / {r_symbol}) = ({solicitante:.2f} / {resistente:.2f}) = {eficiencia:.1f}%%
        </p>
        <div class="final-status {status_class}">{status}</div>
    </div>
    """

# ==============================================================================
# 4. CARREGAMENTO DE DADOS
# ==============================================================================

@st.cache_data
def load_data_from_local_file():
    """Carrega os dados diretamente do arquivo 'perfis.xlsx'"""
    try:
        caminho_arquivo_excel = 'perfis.xlsx'
        return pd.read_excel(caminho_arquivo_excel, sheet_name=None)
    except FileNotFoundError:
        st.error(f"Erro: Arquivo '{caminho_arquivo_excel}' não foi encontrado. Verifique se ele está na mesma pasta do seu `app.py`.")
        return None
    except Exception as e:
        st.error(f"Erro ao ler o arquivo Excel: {e}")
        return None

# ==============================================================================
# 5. FUNÇÕES DE CÁLCULO ESTRUTURAL
# ==============================================================================
# (As funções _calcular_mrdx_flt, _calcular_mrdx_flm e _calcular_vrd estão corretas, vou manter)
def _calcular_mrdx_flt(props, Lb, Cb, fy):
    Zx, ry, Iy, Cw, J, Wx = props['Zx'], props['ry'], props['Iy'], props['Cw'], props['J'], props['Wx']
    Mp = Zx * fy
    lambda_val = Lb / ry if ry > 0 else float('inf')
    lambda_p = Config.FATOR_LAMBDA_P_FLT * math.sqrt(Config.E_ACO / fy)
    detalhes = {'Mrdx': 0, 'Mp':{ 'desc':'Momento de Plastificação', 'valor':Mp, 'unidade':'kN.cm'}, 'lambda':{'desc':'Índice de Esbeltez', 'valor':lambda_val}, 'lambda_p':{'desc':'Esbeltez Limite (Plástica)', 'valor':lambda_p}}
    if lambda_val <= lambda_p:
        Mrdx = Mp / Config.GAMMA_A1
    else:
        sigma_r, Mr = Config.FATOR_SIGMA_R * fy, (fy - Config.FATOR_SIGMA_R * fy) * Wx
        beta1 = ((fy-sigma_r) * Wx) / (Config.E_ACO*J) if (Config.E_ACO*J)!=0 else 0
        lambda_r = float('inf')
        if ry>0 and beta1>0 and J>0 and Cw>0 and Iy>0:
            ts1 = 1+(27*Cw*(beta1**2)/Iy)
            ts2 = 1+math.sqrt(ts1) if ts1>=0 else 1
            lambda_r = (1.38 * math.sqrt(Iy*J) / (ry*beta1*J)) * math.sqrt(ts2)
        detalhes['lambda_r']={'desc':'Esbeltez Limite (Inelástica)', 'valor':lambda_r}
        if lambda_val <= lambda_r:
            Mrdx = min((Cb/Config.GAMMA_A1)*(Mp - (Mp-Mr)*((lambda_val-lambda_p)/(lambda_r-lambda_p))), Mp/Config.GAMMA_A1)
        else:
            Mcr=0
            if Lb**2>0 and Iy>0 and Cw>0 and J>0: Mcr = ((Cb*(math.pi**2)*Config.E_ACO*Iy)/(Lb**2))*math.sqrt((Cw/Iy)*(1+(0.039*J*(Lb**2)/Cw)))
            Mrdx = Mcr/Config.GAMMA_A1
    detalhes['Mrdx'] = Mrdx
    return detalhes

def _calcular_mrdx_flm(props, fy):
    bf,tf,Zx,Wx = props['bf'],props['tf'],props['Zx'],props['Wx']
    Mp, lambda_val = Zx*fy, (bf/2)/tf if tf>0 else float('inf')
    lambda_p = Config.FATOR_LAMBDA_P_FLM*math.sqrt(Config.E_ACO/fy)
    detalhes = {'Mrdx': 0, 'lambda':{'desc':'Esbeltez da Mesa','valor':lambda_val}, 'lambda_p':{'desc':'Esbeltez Limite (Plástica)','valor':lambda_p}}
    if lambda_val <= lambda_p:
        Mrdx = Mp / Config.GAMMA_A1
    else:
        sigma_r = Config.FATOR_SIGMA_R*fy
        Mr = (fy-sigma_r)*Wx
        lambda_r = Config.FATOR_LAMBDA_R_FLM_LAMINADO * math.sqrt(Config.E_ACO/(fy-sigma_r)) if (fy-sigma_r)>0 else float('inf')
        detalhes['lambda_r']={'desc':'Esbeltez Limite (Inelástica)','valor':lambda_r}
        if lambda_val <= lambda_r:
            Mrdx = (1/Config.GAMMA_A1)*(Mp - (Mp-Mr)*((lambda_val-lambda_p)/(lambda_r-lambda_p)))
        else:
            Mcr = (0.69*Config.E_ACO*Wx)/(lambda_val**2) if lambda_val>0 else 0
            Mrdx = Mcr / Config.GAMMA_A1
    detalhes['Mrdx'] = Mrdx
    return detalhes

def _calcular_mrdx_fla(props, fy):
    """Calcula resistência à flambagem local da alma"""
    h, tw, Zx, Wx = props['h'], props['tw'], props['Zx'], props['Wx']
    Mp = Zx * fy
    lambda_val = h / tw if tw > 0 else float('inf')
    lambda_p = Config.FATOR_LAMBDA_P_FLA * math.sqrt(Config.E_ACO / fy)
    
    detalhes = { 'Mrdx':0, 'lambda':{'desc':'Esbeltez da Alma','valor':lambda_val}, 'lambda_p':{'desc':'Esbeltez Limite (Plástica)','valor':lambda_p}}

    if lambda_val <= lambda_p:
        Mrdx = Mp / Config.GAMMA_A1
    else:
        lambda_r = Config.FATOR_LAMBDA_R_FLA * math.sqrt(Config.E_ACO / fy)
        Mr = fy * Wx
        detalhes['lambda_r'] = {'desc':'Esbeltez Limite (Inelástica)', 'valor':lambda_r}

        if lambda_val <= lambda_r:
            termo_interp = (Mp - Mr) * ((lambda_val - lambda_p) / (lambda_r - lambda_p))
            Mrdx = (1 / Config.GAMMA_A1) * (Mp - termo_interp)
        else: # Alma esbelta
            Mrdx = 0
            detalhes['aviso'] = "Perfil com alma esbelta, necessita de análise específica (Anexo H) não implementada."

    detalhes['Mrdx'] = Mrdx
    return detalhes

def _calcular_vrd(props, fy):
    d, h, tw = props['d'], props['h'], props['tw']
    Vpl = Config.FATOR_VP * d * tw * fy
    lambda_val = h / tw if tw > 0 else float('inf')
    kv = Config.KV_ALMA_SEM_ENRIJECEDORES
    lambda_p = Config.FATOR_LAMBDA_P_VRD * math.sqrt((kv * Config.E_ACO) / fy)
    detalhes = {'Vrd':0, 'Vpl':{'desc':'Força Cortante de Plastificação','valor':Vpl, 'unidade':'kN'}, 'lambda':{'desc':'Esbeltez da Alma (Cisalhamento)','valor':lambda_val}, 'lambda_p':{'desc':'Esbeltez Limite (Plástica)','valor':lambda_p}}

    if lambda_val <= lambda_p:
        Vrd = Vpl / Config.GAMMA_A1
    else:
        lambda_r = Config.FATOR_LAMBDA_R_VRD * math.sqrt((kv * Config.E_ACO) / fy)
        detalhes['lambda_r'] = {'desc':'Esbeltez Limite (Inelástica)', 'valor':lambda_r}

        if lambda_val <= lambda_r:
            Vrd = (lambda_p / lambda_val) * (Vpl / Config.GAMMA_A1) if lambda_val > 0 else 0
        else: # Regime elástico
            Vrd = (Config.FATOR_VRD_ELASTICO * (lambda_p / lambda_val)**2) * (Vpl / Config.GAMMA_A1) if lambda_val > 0 else 0

    detalhes['Vrd'] = Vrd
    return detalhes


# ==============================================================================
# 6. FUNÇÕES DE ANÁLISE E VERIFICAÇÃO
# ==============================================================================

def perform_all_checks(props, fy, Lb, Cb, L, Msd, Vsd, q_serv_kn_cm, p_serv_load, tipo_viga, input_mode, detalhado=False):
    res_flt=_calcular_mrdx_flt(props,Lb,Cb,fy); res_flm=_calcular_mrdx_flm(props,fy); res_fla=_calcular_mrdx_fla(props,fy); res_vrd=_calcular_vrd(props,fy)
    Vrd=res_vrd['Vrd']; Mrd_final=min(res_flt['Mrdx'], res_flm['Mrdx'], res_fla['Mrdx'])
    nota_interacao="Vsd≤0.5*Vrd. Interação não necessária." if Vsd<=0.5*Vrd else "Vsd>0.5*Vrd. Interação deve ser considerada."
    ef_geral=(Msd/Mrd_final)*100 if Mrd_final>0 else float('inf'); status_flexao="APROVADO" if ef_geral<=100.1 else "REPROVADO"
    res_flexao={'Mrd':Mrd_final, 'eficiencia':ef_geral,'status':status_flexao,'nota_interacao':nota_interacao}
    
    eficiencia_cis=(Vsd/Vrd)*100 if Vrd>0 else float('inf'); status_cis="APROVADO" if eficiencia_cis<=100.1 else "REPROVADO"
    res_cis={'Vrd':Vrd, 'eficiencia':eficiencia_cis, 'status':status_cis}

    res_flecha={'status':'N/A'}
    if input_mode == "Calcular a partir de Cargas na Viga":
        flecha_max = calcular_flecha_maxima(tipo_viga,L,Config.E_ACO,props['Ix'],q_serv_kn_cm,p_serv_load)
        flecha_limite = L / Config.LIMITE_FLECHA_TOTAL
        ef_flecha = (flecha_max/flecha_limite)*100 if flecha_limite>0 else float('inf')
        res_flecha={'flecha_max':flecha_max,'flecha_limite':flecha_limite,'eficiencia':ef_flecha,'status':"APROVADO" if ef_flecha<=100.1 else "REPROVADO"}

    passo_a_passo = build_step_by_step_html(L, Msd, Vsd, res_flexao, res_cis, res_flecha,res_flt,res_flm,res_fla,res_vrd,input_mode) if detalhado else ""
    return res_flexao,res_cis,res_flecha,passo_a_passo

def build_summary_html(Msd, Vsd, res_flexao, res_cis, res_flecha):
    verificacoes = [('Flexão', f"{Msd/100:.2f} kNm", f"{res_flexao['Mrd']/100:.2f} kNm", res_flexao['eficiencia'], res_flexao['status']),('Cisalh.', f"{Vsd:.2f} kN", f"{res_cis['Vrd']:.2f} kN", res_cis['eficiencia'], res_cis['status'])]
    if res_flecha['status'] != 'N/A':
        verificacoes.append(('Flecha',f"{res_flecha['flecha_max']:.2f} cm",f"≤ {res_flecha['flecha_limite']:.2f} cm",res_flecha['eficiencia'], res_flecha['status']))
    rows = "".join([f'<tr><td>{n}</td><td>{s}</td><td>{r}</td><td>{e:.1f}%</td><td class="{"pass" if st=="APROVADO" else "fail"}">{st}</td></tr>' for n,s,r,e,st in verificacoes])
    return f'<table class="summary-table"><tr><th>Verificação</th><th>Solicitante</th><th>Resistente/Limite</th><th>Eficiência</th><th>Status</th></tr>{rows}</table><p><b>Nota Interação M-V:</b> {res_flexao["nota_interacao"]}</p>'

def build_step_by_step_html(L, Msd, Vsd, res_flexao, res_cis, res_flecha, res_flt, res_flm, res_fla, res_vrd, input_mode):
    html=f'<h2>2. Esforços de Cálculo</h2><div class="formula-block"><p class="formula">M<sub>sd</sub>={Msd/100:.2f} kNm</p><p class="formula">V<sub>sd</sub>={Vsd:.2f} kN</p></div><h2>3. Verificações de Resistência (ELU)</h2><h3>3.1 Resistência à Flexão (M<sub>rd</sub>)</h3>'
    html += _add_verification_details("Flambagem Lateral com Torção (FLT)", res_flt); html += _add_verification_details("Flambagem Local da Mesa (FLM)", res_flm); html += _add_verification_details("Flambagem Local da Alma (FLA)", res_fla)
    html += _build_verification_block_html("Flexão Final", Msd/100,"M<sub>sd</sub>", res_flexao['Mrd']/100, "M<sub>rd,final</sub>", res_flexao['eficiencia'], res_flexao['status'], "kNm")
    html += f"<h3>3.2 Resistência ao Cisalhamento (V<sub>rd</sub>)</h3>"; html += _add_verification_details("Força Cortante", res_vrd)
    html += _build_verification_block_html("Cisalhamento Final", Vsd, "V<sub>sd</sub>", res_cis['Vrd'], "V<sub>rd</sub>", res_cis['eficiencia'], res_cis['status'], "kN")
    if input_mode == "Calcular a partir de Cargas na Viga":
        html += f'<h2>4. Verificação de Serviço (ELS)</h2><div class="formula-block"><h4>Flecha Atuante</h4><p class="formula">δ<sub>max</sub>={res_flecha["flecha_max"]:.2f} cm</p><h4>Flecha Limite</h4><p class="formula">δ<sub>lim</sub>=L/{Config.LIMITE_FLECHA_TOTAL}={L:.2f}/{Config.LIMITE_FLECHA_TOTAL}={res_flecha["flecha_limite"]:.2f} cm</p></div>'
        html += _build_verification_block_html("Flecha Final",res_flecha['flecha_max'],"δ<sub>max</sub>", res_flecha['flecha_limite'], "δ<sub>lim</sub>", res_flecha['eficiencia'],res_flecha['status'],"cm")
    return html

def _add_verification_details(title, details_dict):
    html = f"<h4>{title}</h4><div class='formula-block'>"
    for key, value in details_dict.items():
        if isinstance(value, dict) and 'desc' in value:
            html += f"<h5>{value['desc']}: <b>{value['valor']:.2f} {value.get('unidade','')}</b></h5>"
    final_res = details_dict.get('Mrdx', details_dict.get('Vrd',0)); unit = 'kNm' if 'Mrdx' in details_dict else 'kN'
    if unit == 'kNm': final_res /= 100
    html += f"<p class='final-result'>{title.split('(')[0].strip()} Resistente = {final_res:.2f} {unit}</p></div>"
    return html

# ==============================================================================
# 7. FUNÇÕES DE ANÁLISE PRINCIPAL
# ==============================================================================
def run_detailed_analysis(df, perfil_nome, perfil_tipo, fy, Lb, Cb, L_cm, Msd, Vsd, q_serv_kn_cm, p_load_serv, tipo_viga, input_mode):
    with st.spinner(f"Gerando análise completa para {perfil_nome}..."):
        try:
            perfil_series = df[df['Bitola (mm x kg/m)'] == perfil_nome].iloc[0]
            props = get_profile_properties(perfil_series)
            res_flexao, res_cis, res_flecha, passo_a_passo = perform_all_checks(props,fy,Lb,Cb,L_cm,Msd,Vsd,q_serv_kn_cm,p_load_serv,tipo_viga,input_mode,detalhado=True)
            resumo_html = build_summary_html(Msd,Vsd,res_flexao,res_cis,res_flecha)
            html_view, html_download = gerar_memorial_completo(perfil_nome,perfil_tipo,{'resumo_html':resumo_html,'passo_a_passo_html':passo_a_passo})
            
            st.success("Análise concluída!")
            st.markdown(html_view, unsafe_allow_html=True) # Usa st.markdown para renderizar
            st.download_button("📥 Baixar Memorial HTML", html_download.encode('utf-8'), f"Memorial_{perfil_nome.replace(' ', '_')}.html", "text/html", use_container_width=True)
        except Exception as e:
            st.error(f"❌ Erro na análise: {e}")

def run_batch_analysis(all_sheets, fy, Lb, Cb, L, Msd, Vsd, q_serv_kn_cm, p_load_serv, tipo_viga, input_mode):
    all_results, total = [], sum(len(df) for df in all_sheets.values()); bar = st.progress(0)
    for i, (sheet_name, df) in enumerate(all_sheets.items()):
        for _, row in df.iterrows():
            bar.progress( (i*len(df)+_)/total )
            try:
                props=get_profile_properties(row); res_f,res_c,res_d,_ = perform_all_checks(props,fy,Lb,Cb,L,Msd,Vsd,q_serv_kn_cm,p_load_serv,tipo_viga,input_mode)
                status="APROVADO" if max(res_f['eficiencia'],res_c['eficiencia'],res_d.get('eficiencia',0)) <=100.1 else "REPROVADO"
                all_results.append({'Tipo':sheet_name,'Perfil':row['Bitola (mm x kg/m)'],'Peso':props['Peso'],'Status':status,'Ef. Flexão':res_f['eficiencia'],'Ef. Cis.':res_c['eficiencia'],'Ef. Flecha':res_d.get('eficiencia')})
            except Exception: continue
    bar.empty(); df_res=pd.DataFrame(all_results); tabs=st.tabs(list(Config.PROFILE_TYPE_MAP.values()));
    def style_df(df_in):
        cols = [c for c in df_in.columns if 'Ef.' in c]
        return df_in.style.format("{:.1f}",subset=cols).background_gradient(cmap='RdYlGn_r',subset=cols,vmin=0,vmax=120)
    for i, tab in enumerate(tabs):
        with tab:
            df_type = df_res[df_res['Tipo'] == list(Config.PROFILE_TYPE_MAP.keys())[i]].drop(columns='Tipo')
            aprovados = df_type[df_type.Status=='APROVADO'].sort_values('Peso').reset_index(drop=True)
            if not aprovados.empty: st.dataframe(style_df(aprovados),use_container_width=True)
            else: st.info("Nenhum perfil aprovado.")

# ==============================================================================
# 8. APLICAÇÃO PRINCIPAL
# ==============================================================================
def main():
    st.title("🏛️ Calculadora Estrutural Versátil")
    st.caption(f"Utilizando a norma: {Config.NOME_NORMA}")
    all_sheets = load_data_from_local_file()
    if not all_sheets: st.stop()

    with st.sidebar:
        st.header("⚙️ Parâmetros de Entrada"); st.header("1. Modelo da Viga")
        tipo_viga=st.selectbox("Viga:", ('Bi-apoiada', 'Engastada e Livre (Balanço)'))
        L_cm=st.number_input("Comprimento (L, cm)",10.0,500.0,step=10.0)
        st.header("2. Carregamento"); input_mode=st.radio("Modo:", ("Calcular a partir de Cargas na Viga","Inserir Esforços Manualmente"), label_visibility='collapsed', horizontal=True)
        Msd,Vsd,q_serv,p_serv=0,0,0,None
        if input_mode == "Calcular a partir de Cargas na Viga":
            with st.container(border=True):
                q_serv_knm2 = st.number_input("Carga Dist. (kN/m²)",0.0,4.0,step=0.5); larg_inf=st.number_input("Larg. Influência (m)",0.1,5.0,step=0.5); q_serv=(q_serv_knm2*larg_inf)/100.0
                if st.checkbox("Adicionar Carga Pontual"): p_serv_kn=st.number_input("Carga P (kN)",0.0,10.0); p_pos_cm=st.number_input("Posição x (cm)",0.0,L_cm,L_cm/2); p_serv=(p_serv_kn, p_pos_cm)
                gamma_f=st.number_input("γf",1.0,1.4,0.1); q_ult=q_serv*gamma_f; p_ult=(p_serv[0]*gamma_f,p_serv[1]) if p_serv else None; Msd,Vsd=calcular_esforcos_viga(tipo_viga,L_cm,q_ult,p_ult)
        else: 
            with st.container(border=True): st.warning("Flecha (ELS) não verificada.");Msd,Vsd=st.number_input("Msd (kNm)",0.0,100.0)*100,st.number_input("Vsd (kN)",0.0,50.0)
        st.header("3. Aço"); fy=st.number_input("fy (kN/cm²)",20.0,34.5,0.5);Lb=st.number_input("Lb (cm)",10.0,L_cm,L_cm);Cb=st.number_input("Cb",1.0,1.1)
        st.header("4. Análise"); analysis_mode=st.radio("Modo:",("Análise em Lote","Memorial Detalhado"), label_visibility='collapsed',horizontal=True)

    if analysis_mode == "Memorial Detalhado":
        st.header("🔍 Memorial de Cálculo")
        c1,c2 = st.columns(2)
        sheet = c1.selectbox("Tipo de Perfil:",list(Config.PROFILE_TYPE_MAP.values()))
        sheet_name=list(Config.PROFILE_TYPE_MAP.keys())[list(Config.PROFILE_TYPE_MAP.values()).index(sheet)]
        df=all_sheets[sheet_name]; perfil_nome=c2.selectbox("Perfil Específico:", df['Bitola (mm x kg/m)'])
        if st.button("Gerar Memorial", type='primary',use_container_width=True):
            run_detailed_analysis(df,perfil_nome,sheet,fy,Lb,Cb,L_cm,Msd,Vsd,q_serv,p_serv,tipo_viga,input_mode)
    else:
        st.header("📊 Análise em Lote")
        if st.button("Iniciar Análise",type='primary',use_container_width=True):
            run_batch_analysis(all_sheets,fy,Lb,Cb,L_cm,Msd,Vsd,q_serv,p_serv,tipo_viga,input_mode)

if __name__ == '__main__':
    main()