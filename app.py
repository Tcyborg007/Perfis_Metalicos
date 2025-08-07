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
    "Laminados": "Perfis Laminados", "CS": "Perfis Compactos Soldados",
    "CVS": "Vigas de Seção Variável", "VS": "Vigas Soldadas"
}

HTML_GLOBAL_STYLE = """
<style>
    iframe { width: 100%; }
    .container {
        width: 100%; padding: 20px; background-color: white; border-radius: 10px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1); font-family: 'Roboto', sans-serif;
        line-height: 1.8; color: #333;
    }
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
</style>
"""

# ==============================================================================
# 2. TODAS AS FUNÇÕES DE BACKEND (AGORA PRESENTES, SEM CORTES)
# ==============================================================================

# ---- FUNÇÃO DE CARREGAMENTO DE DADOS ----
@st.cache_data
def load_data_from_local_file():
    try:
        return pd.read_excel('perfis.xlsx', sheet_name=None)
    except FileNotFoundError:
        st.error("Erro Crítico: Arquivo 'perfis.xlsx' não encontrado. Verifique se ele está no repositório GitHub.")
        return None
    except Exception as e:
        st.error(f"Erro ao ler o arquivo Excel: {e}")
        return None

# ---- FUNÇÕES DE CÁLCULO DE ENGENHARIA ----
def calcular_esforcos_viga(tipo_viga, L_cm, q_kn_cm=0, p_load=None):
    msd_q, vsd_q, msd_p, vsd_p = 0, 0, 0, 0; L = L_cm
    if q_kn_cm > 0:
        if tipo_viga == 'Bi-apoiada': msd_q, vsd_q = (q_kn_cm * L**2)/8, (q_kn_cm * L)/2
        elif tipo_viga == 'Engastada e Livre (Balanço)': msd_q, vsd_q = (q_kn_cm * L**2)/2, q_kn_cm * L
        elif tipo_viga == 'Bi-engastada': msd_q, vsd_q = (q_kn_cm * L**2)/12, (q_kn_cm * L)/2
        elif tipo_viga == 'Engastada e Apoiada': msd_q, vsd_q = (q_kn_cm * L**2)/8, (5 * q_kn_cm * L)/8
    if p_load:
        P, x = p_load; a, b = x, L - x
        if tipo_viga == 'Bi-apoiada': msd_p, vsd_p = (P*a*b)/L, max((P*b)/L, (P*a)/L)
        elif tipo_viga == 'Engastada e Livre (Balanço)': msd_p, vsd_p = P*a, P
        elif tipo_viga == 'Bi-engastada': msd_p, vsd_p = max((P*a*b**2)/L**2, (P*a**2*b)/L**2), max((P*b**2*(3*a+b))/L**3, (P*a**2*(a+3*b))/L**3)
        elif tipo_viga == 'Engastada e Apoiada': msd_p, vsd_p = max((P*b*(L**2-b**2))/(2*L**2), (P*a*(3*L**2-a**2))/(2*L**3)*a), max(P*b*(3*L**2-b**2)/(2*L**3), P*a*(3*L-a)/(2*L**2))
    return msd_q + msd_p, vsd_q + vsd_p

def calcular_flecha_maxima(tipo_viga, L_cm, E, Ix, q_serv_kn_cm=0, p_serv_load=None):
    delta_q, delta_p = 0, 0; L = L_cm
    if q_serv_kn_cm > 0:
        if tipo_viga == 'Bi-apoiada': delta_q = (5*q_serv_kn_cm*L**4)/(384*E*Ix)
        elif tipo_viga == 'Engastada e Livre (Balanço)': delta_q = (q_serv_kn_cm*L**4)/(8*E*Ix)
        elif tipo_viga == 'Bi-engastada': delta_q = (q_serv_kn_cm*L**4)/(384*E*Ix)
        elif tipo_viga == 'Engastada e Apoiada': delta_q = (q_serv_kn_cm*L**4)/(185*E*Ix)
    if p_serv_load:
        P, x = p_serv_load; a, b = x, L-a
        if tipo_viga == 'Bi-apoiada':
            if a >= L/2: a,b = b,a
            delta_p = (P*a*(L**2-a**2)**1.5)/(9*math.sqrt(3)*E*Ix*L) if a < L else 0
        elif tipo_viga == 'Engastada e Livre (Balanço)': delta_p = (P*a**2*(3*L-a))/(6*E*Ix)
        elif tipo_viga == 'Bi-engastada': delta_p = (P*a**3*b**3)/(3*E*Ix*L**3)
        elif tipo_viga == 'Engastada e Apoiada':
            if a < b: delta_p = (P*a**2*b**2*(3*L+a))/(12*E*Ix*L**3)
            else: delta_p = (P*b*(L**2-b**2)**1.5)/(9*math.sqrt(3)*E*Ix*L)
    return delta_q + delta_p

def get_profile_properties(profile_series):
    props = {k: profile_series.get(v) for k,v in {
        "d": "d (mm)", "bf": "bf (mm)", "tw": "tw (mm)", "tf": "tf (mm)", "h": "h (mm)",
        "Area": "Área (cm2)", "Ix": "Ix (cm4)", "Wx": "Wx (cm3)", "rx": "rx (cm)", "Zx": "Zx (cm3)",
        "Iy": "Iy (cm4)", "Wy": "Wy (cm3)", "ry": "ry (cm)", "Zy": "Zy (cm3)",
        "J": "It (cm4)", "Cw": "Cw (cm6)",
        "Peso": profile_series.get('Massa Linear (kg/m)', profile_series.get('Peso (kg/m)'))}.items()}
    profile_name = profile_series.get('Bitola (mm x kg/m)', 'Perfil Desconhecido')
    for key in props.keys():
        if props[key] is None or pd.isna(props[key]) or (isinstance(props[key], (int, float)) and props[key] <= 0):
             raise ValueError(f"Propriedade ESSENCIAL '{key}' inválida ou nula para '{profile_name}'. Verifique a planilha.")
    for key in ['d', 'bf', 'tw', 'tf', 'h']: props[key] /= 10.0
    return props

# ---- FUNÇÕES DE GERAÇÃO DE HTML E MEMORIAL ----
def gerar_memorial_completo(perfil_nome, perfil_tipo, resultados):
    html_body = f"""<div class="container"><h1>Memorial de Cálculo Estrutural</h1><h2>Perfil Metálico: {perfil_nome} ({perfil_tipo})</h2><p style="text-align:center; font-style:italic;">Cálculos baseados na norma: <b>{Config.NOME_NORMA}</b></p><h3>1. Resumo Final das Verificações</h3>{resultados['resumo_html']}{resultados['passo_a_passo_html']}</div>"""
    return f"""<!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8"><title>Memorial - {perfil_nome}</title><script type="text/javascript" async src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.7/MathJax.js?config=TeX-MML-AM_CHTML"></script></head><body>{html_body}</body></html>"""

def _build_verification_block_html(title, solicitante, s_symbol, resistente, r_symbol, eficiencia, status, unit):
    status_class, comp_symbol = ("pass", "\\le") if status == "APROVADO" else ("fail", ">")
    return f"""<h4>{title}</h4><div class="formula-block"><p class="formula">$$ {s_symbol} = {solicitante:.2f} \\, {unit} $$</p><p class="formula">$$ {r_symbol} = {resistente:.2f} \\, {unit} $$</p><p class="formula">$$ \\text{{Verificação: }} {s_symbol} {comp_symbol} {r_symbol} $$</p><p class="formula">$$ \\text{{Eficiência}} = \\frac{{{s_symbol}}}{{{r_symbol}}} = \\frac{{{solicitante:.2f}}}{{{resistente:.2f}}} = {eficiencia:.1f}\% $$</p><div class="final-status {status_class}">{status}</div></div>"""

def build_summary_html(Msd, Vsd, res_flexao, res_cis, res_flecha):
    verificacoes = [('Flexão (M) - ELU', f"{Msd/100:.2f} kNm", f"{res_flexao['Mrd']/100:.2f} kNm", res_flexao['eficiencia'], res_flexao['status']),
                    ('Cisalhamento (V) - ELU', f"{Vsd:.2f} kN", f"{res_cis['Vrd']:.2f} kN", res_cis['eficiencia'], res_cis['status']),
                    ('Flecha (δ) - ELS', f"{res_flecha['flecha_max']:.2f} cm" if res_flecha['status'] != "N/A" else "N/A", f"≤ {res_flecha['flecha_limite']:.2f} cm" if res_flecha['status'] != "N/A" else "N/A", res_flecha['eficiencia'], res_flecha['status'])]
    rows_html = "".join([f'<tr><td>{n}</td><td>{s}</td><td>{r}</td><td>{e:.1f}%</td><td class="{"pass" if st == "APROVADO" else "fail"}">{st}</td></tr>' for n, s, r, e, st in verificacoes])
    return f"""<table class="summary-table"><tr><th>Verificação</th><th>Solicitante</th><th>Resistência/Limite</th><th>Eficiência</th><th>Status</th></tr>{rows_html}</table><p style="text-align:justify; font-size:0.9em;"><b>Nota Interação M-V:</b> {res_flexao['nota_interacao']}</p>"""

def build_step_by_step_html(L, Msd, Vsd, res_flexao, res_cis, res_flecha, res_flt, res_flm, res_fla, res_vrd, input_mode):
    html = f"""<h2>2. Esforços de Cálculo</h2><div class="formula-block"><p class="formula">$$ M_{{sd}} = {Msd/100:.2f} \\, kNm $$</p><p class="formula">$$ V_{{sd}} = {Vsd:.2f} \\, kN $$</p></div><h2>3. Verificações de Resistência (ELU)</h2><h3>3.1 Resistência à Flexão (Mrd)</h3>"""
    html += _add_verification_details("Flambagem Lateral com Torção (FLT)", res_flt)
    html += _add_verification_details("Flambagem Local da Mesa (FLM)", res_flm)
    html += _add_verification_details("Flambagem Local da Alma (FLA)", res_fla)
    html += _build_verification_block_html("Verificação Final à Flexão", Msd/100, "M_{sd}", res_flexao['Mrd']/100, "M_{rd}", res_flexao['eficiencia'], res_flexao['status'], "kNm")
    html += f"<h3>3.2 Resistência ao Cisalhamento (Vrd)</h3>"
    html += _add_verification_details("Força Cortante (VRd)", res_vrd)
    html += _build_verification_block_html("Verificação ao Cisalhamento", Vsd, "V_{sd}", res_cis['Vrd'], "V_{rd}", res_cis['eficiencia'], res_cis['status'], "kN")
    if input_mode == "Calcular a partir de Cargas na Viga":
        html += f"""<h2>4. Verificação de Serviço (ELS)</h2><div class="formula-block"><h4>Flecha Atuante (δ_max)</h4><p class="formula">$$ \\delta_{{max}} = {res_flecha['flecha_max']:.2f} \\, cm $$</p><h4>Flecha Limite (δ_lim)</h4><p class="formula">$$ \\delta_{{lim}} = \\frac{{L}}{{{Config.LIMITE_FLECHA_TOTAL}}} = \\frac{{{L:.2f}}}{{{Config.LIMITE_FLECHA_TOTAL}}} = {res_flecha['flecha_limite']:.2f} \\, cm $$</p></div>"""
        html += _build_verification_block_html("Verificação da Flecha", res_flecha['flecha_max'], "\\delta_{max}", res_flecha['flecha_limite'], "\\delta_{lim}", res_flecha['eficiencia'], res_flecha['status'], "cm")
    return html

def _add_verification_details(title, details_dict):
    html = f"<h4>{title}</h4><div class='formula-block'>"
    for value in details_dict.values():
        if isinstance(value, dict) and 'formula' in value:
            formula_valores = value['formula']
            for var, val_num in value.get('valores', {}).items(): formula_valores = formula_valores.replace(var, f"\\mathbf{{{val_num:.2f}}}")
            html += f"""<h5>{value['desc']}</h5><p class="formula">$$ {value['formula']} $$</p><p class="formula">$$ {formula_valores} = \\mathbf{{{value['valor']:.2f} {value.get('unidade', '')}}} $$</p><p class="ref-norma">{value.get('ref', '')}</p>"""
    final_resistance = details_dict.get('Mrdx', details_dict.get('Vrd', 0))
    unit = 'kNm' if 'Mrdx' in details_dict else 'kN'
    if unit == 'kNm': final_resistance /= 100
    html += f"<h5>Resultado da Resistência</h5><p class='final-result'>{title.split('(')[0].strip()} Resistente = {final_resistance:.2f} {unit}</p></div>"
    return html

# ---- FUNÇÕES DE CÁLCULO ESPECÍFICAS (PERFIS) ----
def _calcular_mrdx_flt(props, Lb, Cb, fy):
    Zx, ry, Iy, Cw, J, Wx = props.values()
    Mp = Zx * fy; lambda_val = Lb / ry if ry > 0 else float('inf'); lambda_p = Config.FATOR_LAMBDA_P_FLT * math.sqrt(Config.E_ACO / fy)
    detalhes = {'Mp': {'desc': 'Momento de Plastificação', 'formula': 'M_p=Z_x\\cdot f_y', 'valores': {'Z_x':Zx,'f_y':fy}, 'valor': Mp, 'unidade': 'kN.cm', 'ref':'Item F.1.1(a)'}, 'lambda':{'desc':'Índice de Esbeltez', 'formula':'\\lambda=\\frac{L_b}{r_y}', 'valores':{'L_b':Lb,'r_y':ry}, 'valor':lambda_val}, 'lambda_p':{'desc':'Esbeltez Limite (Plástica)', 'formula':'\\lambda_p=1.76\\sqrt{\\frac{E}{f_y}}', 'valores':{'E':Config.E_ACO, 'f_y':fy}, 'valor':lambda_p, 'ref':'Eq. F-2'}}
    if lambda_val <= lambda_p:
        Mrdx = Mp / Config.GAMMA_A1; detalhes['Mrdx_calc'] = {'desc':'Momento Resistente (Plastificação)', 'formula':'M_{rd}=\\frac{M_p}{\\gamma_{a1}}', 'valores':{'M_p':Mp, '\\gamma_{a1}':Config.GAMMA_A1}, 'valor':Mrdx, 'unidade':'kN.cm', 'ref':'Eq. F-1'}
    else:
        sigma_r = Config.FATOR_SIGMA_R*fy; Mr = (fy - sigma_r)*Wx; beta1 = ((fy - sigma_r)*Wx)/(Config.E_ACO*J) if Config.E_ACO*J != 0 else 0
        lambda_r = float('inf')
        if all(x > 0 for x in [ry, beta1, J, Cw, Iy]):
            termo_sqrt1 = 1+(27*Cw*(beta1**2)/Iy); termo_sqrt2 = 1+math.sqrt(termo_sqrt1) if termo_sqrt1 >= 0 else 1
            lambda_r = (1.38*math.sqrt(Iy*J)/(ry*beta1*J))*math.sqrt(termo_sqrt2)
        detalhes['lambda_r'] = {'desc':'Esbeltez Limite (Inelástica)', 'formula':'\\lambda_r=\\frac{1.38\\sqrt{I_y \\cdot J}}{r_y J \\beta_1}\\sqrt{1+\\sqrt{1+\\frac{27 C_w \\beta_1^2}{I_y}}}', 'valores':{'I_y':Iy, 'J':J, 'r_y':ry, '\\beta_1':beta1, 'C_w':Cw}, 'valor':lambda_r, 'ref':'Eq. F-3'}
        if lambda_r > lambda_p and lambda_val <= lambda_r:
            Mrdx_calc = (Cb/Config.GAMMA_A1)*(Mp - (Mp - Mr)*((lambda_val-lambda_p)/(lambda_r-lambda_p))); Mrdx = min(Mrdx_calc, Mp/Config.GAMMA_A1)
            detalhes['Mrdx_calc'] = {'desc':'Momento Resistente (Inelástico)', 'formula':'M_{rd}=\\frac{C_b}{\\gamma_{a1}}[M_p-(M_p-M_r)(\\frac{\\lambda-\\lambda_p}{\\lambda_r-\\lambda_p})] \\le \\frac{M_p}{\\gamma_{a1}}', 'valores':{'C_b':Cb, 'M_p':Mp, 'M_r':Mr, '\\lambda':lambda_val, '\\lambda_p':lambda_p, '\\lambda_r':lambda_r}, 'valor':Mrdx, 'unidade':'kN.cm', 'ref':'Eq. F-1'}
        else:
            Mcr = ((Cb*(math.pi**2)*Config.E_ACO*Iy)/(Lb**2))*math.sqrt((Cw/Iy)*(1+(0.039*J*(Lb**2)/Cw))) if all(x>0 for x in [Lb, Iy, Cw, J]) else 0
            Mrdx = Mcr / Config.GAMMA_A1
            detalhes['Mcr'] = {'desc':'Momento Crítico Elástico', 'symbol':'M_{cr}', 'formula':'M_{cr}=\\frac{C_b\\pi^2 EI_y}{L_b^2}\\sqrt{\\frac{C_w}{I_y}(1+0.039\\frac{JL_b^2}{C_w})}', 'valores':{'C_b':Cb, 'E':Config.E_ACO, 'I_y':Iy, 'L_b':Lb, 'C_w':Cw, 'J':J}, 'valor':Mcr, 'unidade':'kN.cm', 'ref':'Eq. F-4'}
            detalhes['Mrdx_calc'] = {'desc':'Momento Resistente (Elástico)', 'formula':'M_{rd}=\\frac{M_{cr}}{\\gamma_{a1}}', 'valores':{'M_{cr}':Mcr, '\\gamma_{a1}':Config.GAMMA_A1}, 'valor':Mrdx, 'unidade':'kN.cm', 'ref':'Eq. F-1'}
    detalhes['Mrdx'] = Mrdx
    return detalhes

def _calcular_mrdx_flm(props, fy):
    Zx, Wx, bf, tf = props['Zx'], props['Wx'], props['bf'], props['tf']
    Mp = Zx*fy; lambda_val = (bf/2)/tf if tf>0 else float('inf'); lambda_p = Config.FATOR_LAMBDA_P_FLM*math.sqrt(Config.E_ACO/fy)
    detalhes = {'lambda':{'desc':'Esbeltez da Mesa','formula':'\\lambda=\\frac{b_f/2}{t_f}','valores':{'b_f':bf,'t_f':tf},'valor':lambda_val}, 'lambda_p':{'desc':'Esbeltez Limite (Plástica)','formula':'\\lambda_p=0.38\\sqrt{\\frac{E}{f_y}}','valores':{'E':Config.E_ACO,'f_y':fy},'valor':lambda_p, 'ref':'Tabela F.1'}}
    if lambda_val <= lambda_p:
        Mrdx = Mp/Config.GAMMA_A1; detalhes['Mrdx_calc'] = {'desc':'Momento Resistente (Mesa Compacta)','formula':'M_{rd}=\\frac{M_p}{\\gamma_{a1}}','valores':{'M_p':Mp,'\\gamma_{a1}':Config.GAMMA_A1},'valor':Mrdx,'unidade':'kN.cm'}
    else:
        sigma_r = Config.FATOR_SIGMA_R*fy; lambda_r = Config.FATOR_LAMBDA_R_FLM_LAMINADO*math.sqrt(Config.E_ACO/(fy-sigma_r)) if (fy-sigma_r)>0 else float('inf'); Mr = (fy-sigma_r)*Wx
        detalhes['lambda_r'] = {'desc':'Esbeltez Limite (Inelástica)','formula':'\\lambda_r=0.83\\sqrt{\\frac{E}{f_y-f_r}}','valores':{'E':Config.E_ACO,'f_y':fy,'f_r':sigma_r},'valor':lambda_r,'ref':'Tabela F.1'}
        if lambda_r > lambda_p and lambda_val <= lambda_r:
            Mrdx = (1/Config.GAMMA_A1)*(Mp - ((Mp - Mr) * ((lambda_val - lambda_p)/(lambda_r-lambda_p))))
            detalhes['Mrdx_calc'] = {'desc':'Momento Resistente (Mesa Semicompacta)','formula':'M_{rd}=\\frac{1}{\\gamma_{a1}}[M_p-(M_p-M_r)(\\frac{\\lambda-\\lambda_p}{\\lambda_r-\\lambda_p})]','valores':{'M_p':Mp,'M_r':Mr,'\\lambda':lambda_val,'\\lambda_p':lambda_p,'\\lambda_r':lambda_r},'valor':Mrdx,'unidade':'kN.cm'}
        else:
            Mrdx = ((0.69*Config.E_ACO*Wx)/(lambda_val**2))/Config.GAMMA_A1 if lambda_val > 0 else 0
            detalhes['Mrdx_calc'] = {'desc':'Momento Resistente (Mesa Esbelta)','formula':'M_{rd}=\\frac{0.69EW_x}{\\lambda^2\\gamma_{a1}}','valores':{'E':Config.E_ACO,'W_x':Wx,'\\lambda':lambda_val,'\\gamma_{a1}':Config.GAMMA_A1},'valor':Mrdx,'unidade':'kN.cm'}
    detalhes['Mrdx'] = Mrdx
    return detalhes

def _calcular_mrdx_fla(props, fy):
    Zx, Wx, h, tw = props['Zx'], props['Wx'], props['h'], props['tw']
    Mp = Zx * fy; lambda_val = h / tw if tw > 0 else float('inf'); lambda_p = Config.FATOR_LAMBDA_P_FLA * math.sqrt(Config.E_ACO/fy)
    detalhes = {'lambda':{'desc':'Esbeltez da Alma','formula':'\\lambda=\\frac{h}{t_w}','valores':{'h':h,'t_w':tw},'valor':lambda_val}, 'lambda_p':{'desc':'Esbeltez Limite (Plástica)','formula':'\\lambda_p=3.76\\sqrt{\\frac{E}{f_y}}','valores':{'E':Config.E_ACO,'f_y':fy},'valor':lambda_p, 'ref':'Tabela F.1'}}
    if lambda_val <= lambda_p:
        Mrdx = Mp/Config.GAMMA_A1; detalhes['Mrdx_calc'] = {'desc':'Momento Resistente (Alma Compacta)','formula':'M_{rd}=\\frac{M_p}{\\gamma_{a1}}','valores':{'M_p':Mp,'\\gamma_{a1}':Config.GAMMA_A1},'valor':Mrdx,'unidade':'kN.cm'}
    else:
        lambda_r = Config.FATOR_LAMBDA_R_FLA*math.sqrt(Config.E_ACO/fy); Mr = fy*Wx
        detalhes['lambda_r'] = {'desc':'Esbeltez Limite (Inelástica)','formula':'\\lambda_r=5.70\\sqrt{\\frac{E}{f_y}}','valores':{'E':Config.E_ACO,'f_y':fy},'valor':lambda_r, 'ref':'Tabela F.1'}
        if lambda_r > lambda_p and lambda_val <= lambda_r:
            Mrdx = (1/Config.GAMMA_A1)*(Mp - (Mp-Mr)*((lambda_val-lambda_p)/(lambda_r-lambda_p)))
            detalhes['Mrdx_calc'] = {'desc':'Momento Resistente (Alma Semicompacta)','formula':'M_{rd}=\\frac{1}{\\gamma_{a1}}[M_p-(M_p-M_r)(\\frac{\\lambda-\\lambda_p}{\\lambda_r-\\lambda_p})]','valores':{'M_p':Mp,'M_r':Mr,'\\lambda':lambda_val,'\\lambda_p':lambda_p,'\\lambda_r':lambda_r},'valor':Mrdx,'unidade':'kN.cm'}
        else:
            Mrdx = 0; detalhes['Mrdx_calc'] = {'desc':'Momento Resistente (Alma Esbelta)','formula':'N/A','valores':{},'valor':Mrdx,'unidade':'kN.cm','ref':'Perfil com alma esbelta. Ver Anexo H.'}
    detalhes['Mrdx'] = Mrdx
    return detalhes

def _calcular_vrd(props, fy):
    d, h, tw = props['d'], props['h'], props['tw']
    Vpl = Config.FATOR_VP*d*tw*fy; lambda_val = h/tw if tw>0 else float('inf'); kv = Config.KV_ALMA_SEM_ENRIJECEDORES; lambda_p = Config.FATOR_LAMBDA_P_VRD*math.sqrt((kv*Config.E_ACO)/fy)
    detalhes = {'Vpl':{'desc':'Força Cortante de Plastificação','formula':'V_{pl}=0.60d t_w f_y','valores':{'d':d,'t_w':tw,'f_y':fy},'valor':Vpl,'unidade':'kN','ref':'Eq. 5.23/G.2.1(a)'}, 'lambda':{'desc':'Esbeltez da Alma (Cisalhamento)','formula':'\\lambda=\\frac{h}{t_w}','valores':{'h':h,'t_w':tw},'valor':lambda_val}, 'lambda_p':{'desc':'Esbeltez Limite (Plástica)','formula':'\\lambda_p=1.10\\sqrt{\\frac{k_v E}{f_y}}','valores':{'k_v':kv,'E':Config.E_ACO,'f_y':fy},'valor':lambda_p, 'ref':'Eq. 5.25/G-4'}}
    if lambda_val <= lambda_p:
        Vrd = Vpl/Config.GAMMA_A1; detalhes['Vrd_calc'] = {'desc':'Cortante Resistente (Escoamento)','formula':'V_{rd}=\\frac{V_{pl}}{\\gamma_{a1}}','valores':{'V_{pl}':Vpl,'\\gamma_{a1}':Config.GAMMA_A1},'valor':Vrd,'unidade':'kN','ref':'Eq. 5.24/G-3a'}
    else:
        lambda_r = Config.FATOR_LAMBDA_R_VRD*math.sqrt((kv*Config.E_ACO)/fy)
        detalhes['lambda_r'] = {'desc':'Esbeltez Limite (Inelástica)','formula':'\\lambda_r=1.37\\sqrt{\\frac{k_v E}{f_y}}','valores':{'k_v':kv,'E':Config.E_ACO,'f_y':fy},'valor':lambda_r,'ref':'Eq. 5.27/G-4'}
        if lambda_r > lambda_p and lambda_val <= lambda_r:
            Vrd = (lambda_p/lambda_val)*(Vpl/Config.GAMMA_A1) if lambda_val>0 else 0
            detalhes['Vrd_calc'] = {'desc':'Cortante Resistente (Inelástico)','formula':'V_{rd}=\\frac{\\lambda_p}{\\lambda}\\frac{V_{pl}}{\\gamma_{a1}}','valores':{'\\lambda_p':lambda_p,'\\lambda':lambda_val,'V_{pl}':Vpl,'\\gamma_{a1}':Config.GAMMA_A1},'valor':Vrd,'unidade':'kN','ref':'Eq. 5.26/G-3b'}
        else:
            Vrd = (Config.FATOR_VRD_ELASTICO*((lambda_p/lambda_val)**2))*(Vpl/Config.GAMMA_A1) if lambda_val>0 else 0
            detalhes['Vrd_calc'] = {'desc':'Cortante Resistente (Elástico)','formula':'V_{rd}=1.24(\\frac{\\lambda_p}{\\lambda})^2\\frac{V_{pl}}{\\gamma_{a1}}','valores':{'\\lambda_p':lambda_p,'\\lambda':lambda_val,'V_{pl}':Vpl,'\\gamma_{a1}':Config.GAMMA_A1},'valor':Vrd,'unidade':'kN','ref':'Eq. 5.28/G-3c'}
    detalhes['Vrd'] = Vrd
    return detalhes

# ---- FUNÇÕES DE ORQUESTRAÇÃO ----
def perform_all_checks(props, fy, Lb, Cb, L, Msd, Vsd, q_serv_kn_cm, p_serv_load, tipo_viga, detalhado=False):
    res_flt = _calcular_mrdx_flt(props.values(), Lb, Cb, fy)
    res_flm = _calcular_mrdx_flm({k:props[k] for k in ['Zx','Wx','bf','tf']}, fy)
    res_fla = _calcular_mrdx_fla({k:props[k] for k in ['Zx','Wx','h','tw']}, fy)
    res_vrd = _calcular_vrd({k:props[k] for k in ['d','h','tw']}, fy)
    Vrd, Mrd_final = res_vrd['Vrd'], min(res_flt['Mrdx'], res_flm['Mrdx'], res_fla['Mrdx'])
    nota_interacao = "Vsd ≤ 0.5*Vrd. Interação desconsiderada." if Vrd<=0 or Vsd<=0.5*Vrd else "Vsd > 0.5*Vrd. Interação deve ser considerada."
    ef_geral = (Msd/Mrd_final)*100 if Mrd_final>0 else float('inf')
    status_flexao = "APROVADO" if ef_geral <= 100.1 else "REPROVADO"
    res_flexao = {'Mrd':Mrd_final, 'eficiencia':ef_geral, 'status':status_flexao,
                  'ef_flt':(Msd/res_flt['Mrdx'])*100 if res_flt['Mrdx']>0 else float('inf'),
                  'ef_flm':(Msd/res_flm['Mrdx'])*100 if res_flm['Mrdx']>0 else float('inf'),
                  'ef_fla':(Msd/res_fla['Mrdx'])*100 if res_fla['Mrdx']>0 else float('inf'), 'nota_interacao':nota_interacao}
    ef_cis = (Vsd/Vrd)*100 if Vrd>0 else float('inf'); status_cis = "APROVADO" if ef_cis<=100.1 else "REPROVADO"
    res_cis = {'Vrd':Vrd, 'eficiencia':ef_cis, 'status':status_cis}
    flecha_max, flecha_lim, ef_flecha, status_flecha = 0,0,0,"N/A"
    if tipo_viga == "Calcular a partir de Cargas na Viga":
        flecha_max = calcular_flecha_maxima(tipo_viga, L, Config.E_ACO, props['Ix'], q_serv_kn_cm, p_serv_load)
        flecha_lim = L/Config.LIMITE_FLECHA_TOTAL if L>0 else 0
        ef_flecha = (flecha_max/flecha_lim)*100 if flecha_lim>0 else float('inf')
        status_flecha = "APROVADO" if ef_flecha<=100.1 else "REPROVADO"
    res_flecha = {'flecha_max':flecha_max, 'flecha_limite':flecha_lim, 'eficiencia':ef_flecha, 'status':status_flecha, 'Ix':props['Ix']}
    passo_a_passo = build_step_by_step_html(L, Msd, Vsd, res_flexao, res_cis, res_flecha, res_flt, res_flm, res_fla, res_vrd, tipo_viga) if detalhado else ""
    return res_flexao, res_cis, res_flecha, passo_a_passo

# ==============================================================================
# 3. APLICAÇÃO PRINCIPAL
# ==============================================================================
def main():
    st.set_page_config(page_title="Calculadora Estrutural Versátil", layout="wide")
    st.markdown(HTML_GLOBAL_STYLE, unsafe_allow_html=True)
    st.title("🏛️ Calculadora Estrutural Versátil")
    st.caption(f"Utilizando a norma: {Config.NOME_NORMA}")
    
    all_sheets = load_data_from_local_file()
    if not all_sheets: st.stop()
    
    with st.sidebar:
        st.header("⚙️ Parâmetros de Entrada")
        st.header("1. Modelo da Viga"); tipo_viga = st.selectbox("Tipo de Viga:", ('Bi-apoiada', 'Engastada e Livre (Balanço)', 'Bi-engastada', 'Engastada e Apoiada')); L_cm = st.number_input("Comprimento (L, cm)", 10.0, value=500.0, step=10.0)
        st.header("2. Carregamento"); input_mode = st.radio("Selecione:", ("Calcular a partir de Cargas", "Inserir Esforços"), horizontal=True, label_visibility="collapsed")
        Msd,Vsd,q_servico_kn_cm,p_load_serv = 0,0,0,None
        if input_mode == "Calcular a partir de Cargas":
            with st.container(border=True):
                st.subheader("Carga Distribuída (q)"); carga_area = st.number_input("Carga (serviço, kN/m²)",0.0,value=4.0,step=0.5); larg_inf = st.number_input("Largura Influência (m)",0.0,value=5.0,step=0.5)
                st.subheader("Carga Pontual (P)"); add_p_load = st.checkbox("Adicionar Carga Pontual")
                if add_p_load: p_serv_kn = st.number_input("Valor P (serviço, kN)",0.0,value=10.0); p_pos_cm = st.number_input("Posição (x, cm)",0.0,max_value=L_cm,value=L_cm/2); p_load_serv = (p_serv_kn, p_pos_cm)
                gamma_f = st.number_input("Coef. Majoração (γf)",1.0,value=1.4,step=0.1)
                q_servico_kn_cm = (carga_area*larg_inf)/100.0; p_load_ult = (p_load_serv[0]*gamma_f, p_load_serv[1]) if p_load_serv else None
                Msd, Vsd = calcular_esforcos_viga(tipo_viga, L_cm, q_servico_kn_cm*gamma_f, p_load_ult)
        else:
             with st.container(border=True):
                st.warning("ELS de flecha não será verificado no modo manual."); Msd = st.number_input("Momento (Msd, kNm)",0.0,value=100.0)*100; Vsd = st.number_input("Cortante (Vsd, kN)",0.0,value=50.0)
        st.header("3. Parâmetros do Aço"); fy_aco = st.number_input("fy (kN/cm²)",20.0,50.0,34.5,0.5); Lb_projeto = st.number_input("Destravamento (Lb, cm)",10.0,value=L_cm,step=10.0); Cb_projeto = st.number_input("Fator Modificação (Cb)",1.0,3.0,1.10)
    
    tab1, tab2 = st.tabs(["📊 Análise em Lote", "🔍 Memorial Detalhado"])
    with tab1:
        st.header("Análise Otimizada de Todos os Perfis")
        st.info("Esta ferramenta analisa todos os perfis sob os esforços definidos, destacando a opção mais leve e econômica de cada categoria.")
        if st.button("Iniciar Análise Otimizada",type="primary",use_container_width=True,key="btn_lote"): run_batch_analysis(all_sheets, fy_aco, Lb_projeto, Cb_projeto, L_cm, Msd, Vsd, q_servico_kn_cm, p_load_serv, tipo_viga, input_mode)
    with tab2:
        st.header("Análise Detalhada de um Único Perfil")
        st.info("Selecione um perfil para gerar um memorial de cálculo completo, mostrando todas as etapas de verificação.")
        display_names = [PROFILE_TYPE_MAP.get(name,name) for name in all_sheets.keys()]; reverse_name_map = {v:k for k,v in PROFILE_TYPE_MAP.items()}
        col1,col2 = st.columns(2)
        with col1: selected_display_name = st.selectbox("Selecione o Tipo de Perfil:",display_names,key="tipo_perfil_memorial")
        sheet_name = reverse_name_map.get(selected_display_name, selected_display_name); df_selecionado = all_sheets[sheet_name]
        with col2: perfil_selecionado_nome = st.selectbox("Selecione o Perfil Específico:",df_selecionado['Bitola (mm x kg/m)'],key="nome_perfil_memorial")
        if st.button("Gerar Memorial Completo",type="primary",use_container_width=True,key="btn_memorial"): run_detailed_analysis(df_selecionado,perfil_selecionado_nome,selected_display_name,fy_aco,Lb_projeto,Cb_projeto,L_cm,Msd,Vsd,q_servico_kn_cm,p_load_serv,tipo_viga,input_mode)

if __name__ == '__main__':
    main()