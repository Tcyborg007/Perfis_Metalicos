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
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: 'Roboto', sans-serif; line-height: 1.6; color: #333; background-color: #f8f9fa; font-size: 14px; }

    /* Container principal responsivo */
    .container { width: 100%; max-width: none; margin: 0; padding: 20px; background-color: white; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); min-height: 100vh; }

    /* Títulos */
    h1, h2, h3, h4, h5 { font-family: 'Roboto Slab', serif; color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 8px; margin: 20px 0 15px 0; page-break-after: avoid; }
    h1 { text-align: center; border: none; font-size: 2.5em; margin-bottom: 30px; color: #1e3a8a; }
    h2 { font-size: 1.8em; margin-top: 40px; }
    h3 { font-size: 1.5em; margin-top: 30px; }
    h4 { font-size: 1.3em; margin-top: 25px; border-bottom: none; }
    h5 { border-bottom: 1px solid #ddd; font-size: 1.1em; margin-top: 20px; color: #34495e; padding-bottom: 5px; }

    /* Tabela de resumo */
    .summary-table { width: 100%; border-collapse: collapse; margin: 25px 0; font-size: 0.95em; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
    .summary-table th, .summary-table td { border: 1px solid #ddd; padding: 12px 8px; text-align: center; vertical-align: middle; }
    .summary-table th { background-color: #34495e; color: white; font-weight: 600; font-size: 1em; }
    .summary-table tr:nth-child(even) { background-color: #f8f9fa; }
    .summary-table tr:hover { background-color: #e9ecef; }

    /* Blocos de fórmula */
    .formula-block { background-color: #f8f9fa; border-left: 4px solid #3498db; padding: 20px; margin: 25px 0; border-radius: 6px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); page-break-inside: avoid; }
    .pass { color: #27ae60; font-weight: bold; }
    .fail { color: #e74c3c; font-weight: bold; }

    /* Fórmulas e resultados */
    .formula { font-size: 1.1em; text-align: center; margin: 15px 0; word-wrap: break-word; overflow-x: auto; padding: 12px; background-color: #ffffff; border-radius: 6px; border: 1px solid #e9ecef; font-family: 'Courier New', monospace; }
    .final-result { font-weight: bold; color: #2980b9; text-align: center; display: block; margin-top: 20px; font-size: 1.2em; padding: 15px; border: 2px solid #3498db; border-radius: 8px; background-color: #eaf5ff; }

    /* Status final */
    .final-status { font-size: 1.4em; text-align: center; padding: 15px; border-radius: 8px; margin: 20px 0; font-weight: bold; }
    .final-status.pass { background-color: #d4edda; color: #155724; border: 2px solid #c3e6cb; }
    .final-status.fail { background-color: #f8d7da; color: #721c24; border: 2px solid #f5c6cb; }

    /* Misc */
    .ref-norma { font-size: 0.85em; color: #6c757d; text-align: right; margin-top: 15px; font-style: italic; }
    p { text-align: justify; margin: 10px 0; line-height: 1.6; }
    @media (max-width: 768px) {
        .container { padding: 15px; }
        h1 { font-size: 2em; } h2 { font-size: 1.5em; }
        .summary-table { font-size: 0.8em; }
        .summary-table th, .summary-table td { padding: 8px 4px; }
        .formula { font-size: 0.9em; padding: 8px; }
    }
    @media print {
        body { background-color: white; }
        .container { max-width: none; padding: 0; box-shadow: none; border: none; }
        .formula-block, h1, h2, h3, h4, h5 { page-break-inside: avoid; page-break-after: avoid; }
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
    if q_kn_cm > 0:
        if tipo_viga == 'Bi-apoiada': msd_q, vsd_q = (q_kn_cm * L**2)/8, (q_kn_cm*L)/2
        elif tipo_viga == 'Engastada e Livre (Balanço)': msd_q, vsd_q = (q_kn_cm*L**2)/2, q_kn_cm*L
        elif tipo_viga == 'Bi-engastada': msd_q, vsd_q = (q_kn_cm*L**2)/12, (q_kn_cm*L)/2
        elif tipo_viga == 'Engastada e Apoiada': msd_q, vsd_q = (q_kn_cm*L**2)/8, (5*q_kn_cm*L)/8
    if p_load:
        P, x, a, b = p_load[0], p_load[1], p_load[1], L-p_load[1]
        if tipo_viga == 'Bi-apoiada': msd_p, vsd_p = (P*a*b)/L, max((P*b)/L, (P*a)/L)
        elif tipo_viga == 'Engastada e Livre (Balanço)': msd_p, vsd_p = P*a, P
        elif tipo_viga == 'Bi-engastada': msd_p, vsd_p = max((P*a*b**2)/L**2, (P*a**2*b)/L**2), max((P*b**2*(3*a+b))/L**3, (P*a**2*(a+3*b))/L**3)
        elif tipo_viga == 'Engastada e Apoiada': msd_p, vsd_p = max((P*b*(L**2-b**2))/(2*L**2), (P*a*(3*L**2-a**2))/(2*L**3)*a), max(P*b*(3*L**2-b**2)/(2*L**3), P*a*(3*L-a)/(2*L**2))
    return msd_q + msd_p, vsd_q + vsd_p

def calcular_flecha_maxima(tipo_viga, L_cm, E, Ix, q_serv_kn_cm=0, p_serv_load=None):
    """Calcula flecha máxima em vigas"""
    delta_q, delta_p = 0, 0
    L = L_cm
    if q_serv_kn_cm > 0:
        if tipo_viga == 'Bi-apoiada': delta_q = (5 * q_serv_kn_cm * L**4) / (384 * E * Ix)
        elif tipo_viga == 'Engastada e Livre (Balanço)': delta_q = (q_serv_kn_cm * L**4) / (8 * E * Ix)
        elif tipo_viga == 'Bi-engastada': delta_q = (q_serv_kn_cm * L**4) / (384 * E * Ix)
        elif tipo_viga == 'Engastada e Apoiada': delta_q = (q_serv_kn_cm * L**4) / (185 * E * Ix)
    if p_serv_load:
        P, x, a, b = p_serv_load[0], p_serv_load[1], p_serv_load[1], L-p_serv_load[1]
        if tipo_viga == 'Bi-apoiada':
            if a >= L/2: a, b = b, a
            delta_p = (P * a * (L**2 - a**2)**1.5) / (9 * math.sqrt(3) * E * Ix * L) if a < L else 0
        elif tipo_viga == 'Engastada e Livre (Balanço)': delta_p = (P * a**2 * (3*L - a)) / (6 * E * Ix)
        elif tipo_viga == 'Bi-engastada': delta_p = (P * a**3 * b**3) / (3 * E * Ix * L**3)
        elif tipo_viga == 'Engastada e Apoiada':
            if a < b: delta_p = (P * a**2 * b**2 * (3*L+a)) / (12*E*Ix*L**3)
            else: delta_p = (P * b * (L**2 - b**2)**1.5) / (9*math.sqrt(3)*E*Ix*L) if (L**2 - b**2) >=0 else 0
    return delta_q + delta_p

def get_profile_properties(profile_series):
    """Extrai, valida e converte propriedades do perfil da série do pandas"""
    props = {"d": profile_series.get('d (mm)'), "bf": profile_series.get('bf (mm)'), "tw": profile_series.get('tw (mm)'), "tf": profile_series.get('tf (mm)'), "h": profile_series.get('h (mm)'), "Area": profile_series.get('Área (cm2)'), "Ix": profile_series.get('Ix (cm4)'), "Wx": profile_series.get('Wx (cm3)'), "rx": profile_series.get('rx (cm)'), "Zx": profile_series.get('Zx (cm3)'), "Iy": profile_series.get('Iy (cm4)'), "Wy": profile_series.get('Wy (cm3)'), "ry": profile_series.get('ry (cm)'), "Zy": profile_series.get('Zy (cm3)'), "J": profile_series.get('It (cm4)'), "Cw": profile_series.get('Cw (cm6)'), "Peso": profile_series.get('Massa Linear ( kg/m )', profile_series.get('Peso ( kg/m )'))}
    profile_name = profile_series.get('Bitola (mm x kg/m)', 'Perfil Desconhecido')
    for key, value in props.items():
        if value is None or pd.isna(value) or (isinstance(value, (int, float)) and value <= 0): raise ValueError(f"Propriedade essencial '{key}' nula ou inválida no Excel para '{profile_name}'.")
    for key in ['d', 'bf', 'tw', 'tf', 'h']: props[key] /= 10.0
    return props

# ==============================================================================
# 3. GERAÇÃO DO MEMORIAL DE CÁLCULO
# ==============================================================================

def gerar_memorial_completo(perfil_nome, perfil_tipo, resultados):
    """Gera o HTML completo do memorial de cálculo"""
    return f"""<!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Memorial - {perfil_nome}</title>{HTML_TEMPLATE_CSS}<script type="text/javascript" async src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.7/MathJax.js?config=TeX-MML-AM_CHTML"></script></head><body><div class="container"><h1>Memorial de Cálculo Estrutural</h1><h2>Perfil: {perfil_nome} ({perfil_tipo})</h2><p style="text-align:center; font-style:italic;">Norma: <b>{Config.NOME_NORMA}</b></p><h3>1. Resumo das Verificações</h3>{resultados['resumo_html']}{resultados['passo_a_passo_html']}</div></body></html>"""

def _build_verification_block_html(title, solicitante, s_symbol, resistente, r_symbol, eficiencia, status, unit):
    """Constrói bloco HTML reutilizável para verificação"""
    status_class, comp_symbol = ("pass", "≤") if status == "APROVADO" else ("fail", ">")
    return f"""<h4>{title}</h4><div class="formula-block"><p class="formula">{s_symbol} = {solicitante:.2f} {unit}</p><p class="formula">{r_symbol} = {resistente:.2f} {unit}</p><p class="formula">Verificação: {s_symbol} {comp_symbol} {r_symbol}</p><p class="formula">Eficiência = {s_symbol} / {r_symbol} = {solicitante:.2f} / {resistente:.2f} = {eficiencia:.1f}%</p><div class="final-status {status_class}">{status}</div></div>"""

# ==============================================================================
# 4. CARREGAMENTO DE DADOS
# ==============================================================================

@st.cache_data
def load_data_from_local_file():
    """Carrega dados do arquivo 'perfis.xlsx' com cache"""
    try: return pd.read_excel('perfis.xlsx', sheet_name=None)
    except FileNotFoundError: st.error("Erro: 'perfis.xlsx' não encontrado. Verifique se o arquivo está na mesma pasta do app."); return None
    except Exception as e: st.error(f"Erro ao ler o arquivo Excel: {e}"); return None

# ==============================================================================
# 5. FUNÇÕES DE CÁLCULO ESTRUTURAL
# ==============================================================================

def _calcular_mrdx_flt(props, Lb, Cb, fy):
    """Calcula resistência à flambagem lateral com torção"""
    Zx, ry, Iy, Cw, J, Wx = props['Zx'], props['ry'], props['Iy'], props['Cw'], props['J'], props['Wx']
    Mp = Zx * fy
    lambda_val = Lb / ry if ry > 0 else float('inf')
    lambda_p = Config.FATOR_LAMBDA_P_FLT * math.sqrt(Config.E_ACO / fy)
    detalhes = {'Mp': {'desc': 'Momento de Plastificação','symbol': 'M_p','formula': 'M_p = Z_x × f_y','valores': {'Z_x': Zx,'f_y': fy},'valor': Mp,'unidade': 'kN.cm'}, 'lambda': {'desc': 'Índice de Esbeltez','symbol': 'λ','formula': 'λ = L_b / r_y','valores': {'L_b': Lb,'r_y': ry},'valor': lambda_val}, 'lambda_p': {'desc': 'Esbeltez Limite Plástica','symbol': 'λ_p','formula': 'λ_p = 1.76 × √(E/f_y)','valores': {'E': Config.E_ACO,'f_y': fy},'valor': lambda_p,'ref': 'Eq. F-2'}}
    if lambda_val <= lambda_p:
        Mrdx = Mp / Config.GAMMA_A1
        detalhes['Mrdx_calc'] = {'desc': 'Momento Resistente (Plastificação)','symbol': 'M_rd','formula': 'M_rd = M_p / γ_a1','valores': {'M_p': Mp,'γ_a1': Config.GAMMA_A1},'valor': Mrdx,'unidade': 'kN.cm'}
    else:
        sigma_r, Mr, Mrdx = Config.FATOR_SIGMA_R*fy, (fy-Config.FATOR_SIGMA_R*fy)*Wx, 0
        beta1 = ((fy-sigma_r)*Wx)/(Config.E_ACO*J) if Config.E_ACO*J > 0 else 0
        try: lambda_r = (1.38*math.sqrt(Iy*J)/(ry*J*beta1))*math.sqrt(1+math.sqrt(1+27*Cw*(beta1**2)/Iy)) if all(v>0 for v in [ry, J, beta1, Cw, Iy]) else float('inf')
        except (ValueError, ZeroDivisionError): lambda_r = float('inf')
        if lambda_val <= lambda_r:
            Mrdx = min((Cb/Config.GAMMA_A1)*(Mp - (Mp - Mr)*((lambda_val-lambda_p)/(lambda_r-lambda_p))), Mp/Config.GAMMA_A1)
        else:
            try: Mcr = ((Cb*math.pi**2*Config.E_ACO*Iy)/(Lb**2))*math.sqrt((Cw/Iy)*(1+0.039*J*(Lb**2)/Cw)) if all(v>0 for v in [Iy, Cw, J, Lb]) else 0
            except (ValueError, ZeroDivisionError): Mcr = 0
            Mrdx = Mcr / Config.GAMMA_A1
    detalhes['Mrdx'] = Mrdx
    return detalhes

def _calcular_mrdx_flm(props, fy):
    """Calcula resistência à flambagem local da mesa"""
    bf, tf, Zx, Wx = props['bf'], props['tf'], props['Zx'], props['Wx']
    Mp = Zx * fy
    lambda_val = (bf / 2) / tf if tf > 0 else float('inf')
    lambda_p = Config.FATOR_LAMBDA_P_FLM * math.sqrt(Config.E_ACO / fy)
    detalhes = {'lambda': {'desc': 'Esbeltez da Mesa','symbol': 'λ','formula': 'λ = (b_f/2)/t_f','valores': {'b_f':bf,'t_f':tf},'valor':lambda_val}, 'lambda_p':{'desc':'Esbeltez Limite Plástica','symbol':'λ_p','formula':'λ_p=0.38×√(E/f_y)','valores':{'E':Config.E_ACO,'f_y':fy},'valor':lambda_p,'ref':'Tabela F.1'}}
    if lambda_val <= lambda_p:
        Mrdx = Mp / Config.GAMMA_A1
    else:
        sigma_r, Mr = Config.FATOR_SIGMA_R * fy, (fy - Config.FATOR_SIGMA_R * fy) * Wx
        lambda_r = Config.FATOR_LAMBDA_R_FLM_LAMINADO * math.sqrt(Config.E_ACO/(fy-sigma_r)) if (fy-sigma_r) > 0 else float('inf')
        if lambda_val <= lambda_r:
            Mrdx = (1/Config.GAMMA_A1) * (Mp - (Mp - Mr)*((lambda_val - lambda_p)/(lambda_r-lambda_p)))
        else:
            Mrdx = (0.69*Config.E_ACO*Wx/(lambda_val**2))/Config.GAMMA_A1 if lambda_val > 0 else 0
    detalhes['Mrdx'] = Mrdx
    return detalhes

def _calcular_mrdx_fla(props, fy):
    """Calcula resistência à flambagem local da alma"""
    h, tw, Zx, Wx = props['h'], props['tw'], props['Zx'], props['Wx']
    Mp = Zx * fy
    lambda_val = h / tw if tw > 0 else float('inf')
    lambda_p = Config.FATOR_LAMBDA_P_FLA * math.sqrt(Config.E_ACO / fy)
    detalhes = {'lambda': {'desc': 'Esbeltez da Alma','symbol':'λ','formula':'λ=h/t_w','valores':{'h':h,'t_w':tw},'valor':lambda_val}, 'lambda_p':{'desc':'Esbeltez Limite Plástica','symbol':'λ_p','formula':'λ_p=3.76×√(E/f_y)','valores':{'E':Config.E_ACO,'f_y':fy},'valor':lambda_p,'ref':'Tabela F.1'}}
    if lambda_val <= lambda_p:
        Mrdx = Mp / Config.GAMMA_A1
    else:
        lambda_r = Config.FATOR_LAMBDA_R_FLA * math.sqrt(Config.E_ACO / fy)
        Mr = fy * Wx
        if lambda_val <= lambda_r:
            Mrdx = (1/Config.GAMMA_A1) * (Mp - (Mp - Mr) * ((lambda_val - lambda_p) / (lambda_r - lambda_p)))
        else:
            Mrdx = 0  # Alma esbelta, requer Anexo H (simplificado para 0)
    detalhes['Mrdx'] = Mrdx
    return detalhes

def _calcular_vrd(props, fy):
    """Calcula resistência ao cisalhamento"""
    d, h, tw = props['d'], props['h'], props['tw']
    Vpl = Config.FATOR_VP * d * tw * fy
    lambda_val = h / tw if tw > 0 else float('inf')
    kv = Config.KV_ALMA_SEM_ENRIJECEDORES
    lambda_p = Config.FATOR_LAMBDA_P_VRD * math.sqrt((kv * Config.E_ACO) / fy)
    detalhes = {'Vpl': {'desc':'Força Cortante de Plastificação','symbol':'V_pl','formula':'V_pl=0.60×d×t_w×f_y','valores':{'d':d,'t_w':tw,'f_y':fy},'valor':Vpl,'unidade':'kN'}, 'lambda':{'desc':'Esbeltez da Alma (Cisalhamento)','symbol':'λ','formula':'λ=h/t_w','valores':{'h':h,'t_w':tw},'valor':lambda_val}, 'lambda_p':{'desc':'Esbeltez Limite Plástica','symbol':'λ_p','formula':'λ_p=1.10×√(k_v×E/f_y)','valores':{'k_v':kv,'E':Config.E_ACO,'f_y':fy},'valor':lambda_p,'ref':'Eq. 5.25'}}
    if lambda_val <= lambda_p:
        Vrd = Vpl / Config.GAMMA_A1
    else:
        lambda_r = Config.FATOR_LAMBDA_R_VRD * math.sqrt((kv * Config.E_ACO) / fy)
        if lambda_val <= lambda_r:
            Vrd = (lambda_p/lambda_val) * (Vpl/Config.GAMMA_A1) if lambda_val > 0 else 0
        else:
            Vrd = (Config.FATOR_VRD_ELASTICO*(lambda_p/lambda_val)**2)*(Vpl/Config.GAMMA_A1) if lambda_val>0 else 0
    detalhes['Vrd'] = Vrd
    return detalhes

# ==============================================================================
# 6. FUNÇÕES DE ANÁLISE E VERIFICAÇÃO
# ==============================================================================

def perform_all_checks(props, fy, Lb, Cb, L, Msd, Vsd, q_serv_kn_cm, p_serv_load, tipo_viga, input_mode, detalhado=False):
    """Executa todas as verificações estruturais e retorna os resultados"""
    res_flt = _calcular_mrdx_flt(props,Lb,Cb,fy); res_flm = _calcular_mrdx_flm(props,fy); res_fla = _calcular_mrdx_fla(props,fy); res_vrd = _calcular_vrd(props,fy)
    Vrd = res_vrd['Vrd']; Mrd_final = min(res_flt['Mrdx'], res_flm['Mrdx'], res_fla['Mrdx'])
    nota_interacao = "Vsd ≤ 0.5*Vrd. Interação não necessária." if Vsd <= 0.5*Vrd else "Vsd > 0.5*Vrd. Interação deve ser considerada (cálculo não incluso)."
    ef_geral = (Msd/Mrd_final)*100 if Mrd_final > 0 else float('inf')
    res_flexao = {'Mrd':Mrd_final, 'eficiencia':ef_geral, 'status':"APROVADO" if ef_geral <= 100.1 else "REPROVADO", 'nota_interacao':nota_interacao}
    ef_cis = (Vsd/Vrd)*100 if Vrd > 0 else float('inf')
    res_cis = {'Vrd':Vrd, 'eficiencia':ef_cis, 'status':"APROVADO" if ef_cis <= 100.1 else "REPROVADO"}
    res_flecha = {'flecha_max':0, 'flecha_limite':0, 'eficiencia':0, 'status':"N/A"}
    if input_mode == "Calcular a partir de Cargas":
        flecha_max = calcular_flecha_maxima(tipo_viga, L, Config.E_ACO, props['Ix'], q_serv_kn_cm, p_serv_load)
        flecha_lim = L/Config.LIMITE_FLECHA_TOTAL if L > 0 else 0
        ef_flecha = (flecha_max/flecha_lim)*100 if flecha_lim > 0 else float('inf')
        res_flecha.update({'flecha_max':flecha_max, 'flecha_limite':flecha_lim, 'eficiencia':ef_flecha, 'status':"APROVADO" if ef_flecha<=100.1 else "REPROVADO"})
    passo_a_passo = build_step_by_step_html(L, Msd, Vsd, res_flexao, res_cis, res_flecha, res_flt, res_flm, res_fla, res_vrd, input_mode) if detalhado else ""
    return res_flexao, res_cis, res_flecha, passo_a_passo

def build_summary_html(Msd, Vsd, res_flexao, res_cisalhamento, res_flecha):
    """Constrói tabela HTML de resumo das verificações"""
    rows = [( 'Flexão (M) - ELU', f"{Msd/100:.2f} kNm", f"{res_flexao['Mrd']/100:.2f} kNm", res_flexao['eficiencia'], res_flexao['status'] ),
            ( 'Cisalhamento (V) - ELU', f"{Vsd:.2f} kN", f"{res_cisalhamento['Vrd']:.2f} kN", res_cisalhamento['eficiencia'], res_cisalhamento['status'] )]
    if res_flecha['status'] != "N/A":
        rows.append(('Flecha (δ) - ELS', f"{res_flecha['flecha_max']:.2f} cm", f"≤ {res_flecha['flecha_limite']:.2f} cm", res_flecha['eficiencia'], res_flecha['status']))
    rows_html = "".join(f'<tr><td>{n}</td><td>{s}</td><td>{r}</td><td>{e:.1f}%</td><td class="{"pass" if st=="APROVADO" else "fail"}">{st}</td></tr>' for n,s,r,e,st in rows)
    return f'<table class="summary-table"><tr><th>Verificação</th><th>Solicitante/Atuante</th><th>Resistência/Limite</th><th>Eficiência</th><th>Status</th></tr>{rows_html}</table><p><b>Nota:</b> {res_flexao["nota_interacao"]}</p>'

def build_step_by_step_html(L, Msd, Vsd, res_flexao, res_cis, res_flecha, res_flt, res_flm, res_fla, res_vrd, input_mode):
    """Constrói HTML detalhado com o passo a passo dos cálculos"""
    html = f"<h2>2. Esforços de Cálculo</h2><div class='formula-block'><p class='formula'>M<sub>sd</sub> = {Msd/100:.2f} kNm</p><p class='formula'>V<sub>sd</sub> = {Vsd:.2f} kN</p></div><h2>3. Verificações de Resistência (ELU)</h2><h3>3.1. Cálculo da Resistência à Flexão (M<sub>rd</sub>)</h3>"
    html += _add_verification_details("Flambagem Lateral com Torção (FLT)", res_flt)
    html += _add_verification_details("Flambagem Local da Mesa (FLM)", res_flm)
    html += _add_verification_details("Flambagem Local da Alma (FLA)", res_fla)
    html += _build_verification_block_html("Verificação Final à Flexão", Msd/100, "M<sub>sd</sub>", res_flexao['Mrd']/100, "M<sub>rd</sub>", res_flexao['eficiencia'], res_flexao['status'], "kNm")
    html += f"<h3>3.2. Cálculo da Resistência ao Cisalhamento (V<sub>rd</sub>)</h3>"
    html += _add_verification_details("Força Cortante Resistente (VRd)", res_vrd)
    html += _build_verification_block_html("Verificação ao Cisalhamento", Vsd, "V<sub>sd</sub>", res_cis['Vrd'], "V<sub>rd</sub>", res_cis['eficiencia'], res_cis['status'], "kN")
    if input_mode == "Calcular a partir de Cargas":
        html += f"<h2>4. Verificação de Serviço (ELS)</h2><div class='formula-block'><h4>a. Flecha Máxima Atuante (δ<sub>max</sub>)</h4><p class='formula'>δ<sub>max</sub> = {res_flecha['flecha_max']:.2f} cm</p><h4>b. Flecha Limite (δ<sub>lim</sub>)</h4><p class='formula'>δ<sub>lim</sub> = L/{Config.LIMITE_FLECHA_TOTAL} = {L:.2f}/{Config.LIMITE_FLECHA_TOTAL} = {res_flecha['flecha_limite']:.2f} cm</p></div>"
        html += _build_verification_block_html("Verificação da Flecha", res_flecha['flecha_max'], "δ<sub>max</sub>", res_flecha['flecha_limite'], "δ<sub>lim</sub>", res_flecha['eficiencia'], res_flecha['status'], "cm")
    return html

def _add_verification_details(title, details_dict):
    """Adiciona um bloco de detalhes de verificação ao HTML"""
    html = f"<h4>{title}</h4><div class='formula-block'>"
    for value in details_dict.values():
        if isinstance(value, dict) and 'formula' in value:
            formula_valores = value['formula']
            for var, val_num in value.get('valores', {}).items(): formula_valores = formula_valores.replace(var, f"<b>{val_num:.2f}</b>")
            html += f"<h5>{value['desc']} ({value['symbol']})</h5><p class='formula'>{value['formula']}</p><p class='formula'>{formula_valores} = <b>{value['valor']:.2f} {value.get('unidade', '')}</b></p><p class='ref-norma'>{value.get('ref', '')}</p>"
    final_res = details_dict.get('Mrdx', details_dict.get('Vrd', 0))
    unit = 'kNm' if 'Mrdx' in details_dict else 'kN'
    if unit == 'kNm': final_res /= 100
    html += f"<h5>Resultado da Resistência</h5><p class='final-result'>{title.split('(')[0].strip()} = {final_res:.2f} {unit}</p></div>"
    return html

# ==============================================================================
# 7. FUNÇÕES DE INTERFACE E EXECUÇÃO
# ==============================================================================

def run_detailed_analysis(df, perfil_nome, perfil_tipo_display, fy, Lb, Cb, L, Msd, Vsd, q_serv_kn_cm, p_serv_load, tipo_viga, input_mode):
    """Executa e exibe a análise detalhada de um perfil"""
    with st.spinner(f"Gerando análise completa para {perfil_nome}..."):
        try:
            perfil_series = df[df['Bitola (mm x kg/m)'] == perfil_nome].iloc[0]
            props = get_profile_properties(perfil_series)
            res_flexao, res_cis, res_flecha, passo_a_passo = perform_all_checks(props, fy, Lb, Cb, L, Msd, Vsd, q_serv_kn_cm, p_serv_load, tipo_viga, input_mode, detalhado=True)
            resumo_html = build_summary_html(Msd, Vsd, res_flexao, res_cis, res_flecha)
            html_content = gerar_memorial_completo(perfil_nome, perfil_tipo_display, {'resumo_html': resumo_html, 'passo_a_passo_html': passo_a_passo})
            st.success("Análise concluída!")
            st.components.v1.html(html_content, height=800, scrolling=True)
            st.download_button("📥 Baixar Memorial HTML", html_content.encode('utf-8'), f"Memorial_{perfil_nome.replace(' ','_')}.html", "text/html", use_container_width=True)
        except (ValueError, KeyError) as e: st.error(f"❌ Erro nos Dados: {e}")
        except Exception as e: st.error(f"❌ Erro Inesperado: {e}", icon="🚨")

def run_batch_analysis(all_sheets, fy, Lb, Cb, L, Msd, Vsd, q_serv_kn_cm, p_serv_load, tipo_viga, input_mode):
    """Executa análise em lote para todos os perfis"""
    results, total = [], sum(len(df) for df in all_sheets.values()); bar = st.progress(0, "Iniciando análise...")
    with st.spinner(f"Analisando {total} perfis..."):
        for i, (sheet, df) in enumerate(all_sheets.items()):
            for _, row in df.iterrows():
                try:
                    props = get_profile_properties(row)
                    res_flexao, res_cis, res_flecha, _ = perform_all_checks(props, fy, Lb, Cb, L, Msd, Vsd, q_serv_kn_cm, p_serv_load, tipo_viga, input_mode)
                    status = "APROVADO" if max(res_flexao['eficiencia'], res_cis['eficiencia'], res_flecha.get('eficiencia',0)) <= 100.1 else "REPROVADO"
                    results.append({'Tipo':sheet,'Perfil':row['Bitola (mm x kg/m)'],'Peso(kg/m)':props['Peso'],'Status':status,'Ef.Flexão(%)':res_flexao['eficiencia'],'Ef.Cisal.(%)':res_cis['eficiencia'],'Ef.Flecha(%)':res_flecha.get('eficiencia',pd.NA)})
                except (ValueError, KeyError): continue
            bar.progress((i + 1) / len(all_sheets), f"Analisando: {Config.PROFILE_TYPE_MAP.get(sheet, sheet)}")
    bar.empty(); st.success(f"{len(results)} perfis analisados.")
    df_results = pd.DataFrame(results)
    tabs = st.tabs([Config.PROFILE_TYPE_MAP.get(name, name) for name in all_sheets.keys()])
    for i, sheet_name in enumerate(all_sheets.keys()):
        with tabs[i]:
            df_type = df_results[df_results['Tipo'] == sheet_name].drop(columns=['Tipo'])
            aprovados = df_type[df_type['Status'] == 'APROVADO'].sort_values('Peso(kg/m)')
            if not aprovados.empty:
                st.subheader("🏆 Perfil Mais Leve Aprovado"); st.dataframe(aprovados.head(1).style.format('{:.1f}', subset=[c for c in aprovados if '%' in c]), use_container_width=True)
                with st.expander("Ver todos aprovados"): st.dataframe(aprovados.style.format('{:.1f}', subset=[c for c in aprovados if '%' in c]), use_container_width=True)
            else: st.info("Nenhum perfil foi aprovado nesta categoria.")
            if not (reprovados := df_type[df_type['Status'] == 'REPROVADO']).empty:
                with st.expander("Ver perfis reprovados"): st.dataframe(reprovados.style.format('{:.1f}', subset=[c for c in reprovados if '%' in c]), use_container_width=True)

# ==============================================================================
# 8. APLICAÇÃO PRINCIPAL
# ==============================================================================

def main():
    st.title("🏛️ Calculadora Estrutural Versátil"); st.caption(f"Utilizando a norma: {Config.NOME_NORMA}")
    all_sheets = load_data_from_local_file()
    if not all_sheets: st.stop()

    with st.sidebar:
        st.header("⚙️ Parâmetros de Entrada")
        st.header("1. Modelo da Viga"); tipo_viga = st.selectbox("Tipo de Viga:", ('Bi-apoiada', 'Engastada e Livre (Balanço)', 'Bi-engastada', 'Engastada e Apoiada'))
        L_cm = st.number_input("Comprimento da Viga (L, cm)", 10.0, 5000.0, 500.0, 10.0)
        st.header("2. Carregamento"); input_mode = st.radio("Entrada",("Calcular a partir de Cargas", "Inserir Esforços Manualmente"),label_visibility="collapsed", horizontal=True)
        Msd, Vsd, q_serv_kn_cm, p_load_serv = 0,0,0,None
        if input_mode == "Calcular a partir de Cargas":
            with st.container(border=True):
                st.subheader("Carga Distribuída (q)"); carga_area=st.number_input("Serviço (kN/m²)",0.0,value=4.0,step=0.5); larg_inf=st.number_input("Larg. Influência (m)",0.0,value=5.0,step=0.5)
                st.subheader("Carga Pontual (P)")
                if st.checkbox("Adicionar Carga Pontual"):
                    p_serv=st.number_input("Serviço (kN)",0.0,10.0); p_pos=st.number_input("Posição (cm)",0.0,L_cm,L_cm/2); p_load_serv=(p_serv,p_pos)
                gamma_f = st.number_input("Coef. Majoração (γf)", 1.0, 2.0, 1.4, 0.1)
                q_serv_kn_cm = (carga_area*larg_inf)/100; Msd,Vsd = calcular_esforcos_viga(tipo_viga, L_cm, q_serv_kn_cm*gamma_f, (p_load_serv[0]*gamma_f,p_load_serv[1]) if p_load_serv else None)
        else:
            with st.container(border=True):
                st.warning("Verificação de flecha (ELS) não realizada no modo manual."); msd_input=st.number_input("Msd (kNm)",0.0,100.0); Vsd=st.number_input("Vsd (kN)",0.0,50.0); Msd=msd_input*100
        st.header("3. Aço"); fy_aco=st.number_input("fy (kN/cm²)",20.0,50.0,34.5,0.5)
        Lb_projeto=st.number_input("Comp. Destravado Lb (cm)",10.0,L_cm,L_cm,10.0); Cb_projeto=st.number_input("Fator Cb",1.0,3.0,1.1,0.1)
        st.header("4. Análise"); analysis_mode = st.radio("Análise",("Memorial Detalhado", "Análise Otimizada"),label_visibility="collapsed",horizontal=True)

    if analysis_mode == "Memorial Detalhado":
        st.header("🔍 Memorial de Cálculo Detalhado")
        col1, col2 = st.columns(2)
        with col1: selected_name=st.selectbox("Tipo de Perfil", [Config.PROFILE_TYPE_MAP.get(n,n) for n in all_sheets.keys()])
        sheet_name = [k for k, v in Config.PROFILE_TYPE_MAP.items() if v == selected_name][0]
        with col2: perfil_nome = st.selectbox("Perfil Específico", all_sheets[sheet_name]['Bitola (mm x kg/m)'])
        if st.button("Gerar Memorial Completo",type="primary",use_container_width=True):
            run_detailed_analysis(all_sheets[sheet_name], perfil_nome, selected_name, fy_aco, Lb_projeto, Cb_projeto, L_cm, Msd, Vsd, q_serv_kn_cm, p_load_serv, tipo_viga, input_mode)
    else:
        st.header("📊 Análise Otimizada em Lote")
        if st.button("Iniciar Análise Otimizada",type="primary",use_container_width=True):
            run_batch_analysis(all_sheets, fy_aco, Lb_projeto, Cb_projeto, L_cm, Msd, Vsd, q_serv_kn_cm, p_load_serv, tipo_viga, input_mode)

if __name__ == '__main__':
    main()