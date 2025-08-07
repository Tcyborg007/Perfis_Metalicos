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
    
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: 'Roboto', sans-serif; line-height: 1.6; color: #333; background-color: #f8f9fa; font-size: 14px; }
    .container { width: 100%; max-width: none; margin: 0; padding: 20px; background-color: white; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); min-height: 100vh; }
    h1, h2, h3, h4, h5 { font-family: 'Roboto Slab', serif; color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 8px; margin: 20px 0 15px 0; page-break-after: avoid; }
    h1 { text-align: center; border: none; font-size: 2.5em; margin-bottom: 30px; color: #1e3a8a; }
    h2 { font-size: 1.8em; margin-top: 40px; } h3 { font-size: 1.5em; margin-top: 30px; } h4 { font-size: 1.3em; margin-top: 25px; }
    h5 { border-bottom: 1px solid #ddd; font-size: 1.1em; margin-top: 20px; color: #34495e; padding-bottom: 5px; }
    .summary-table { width: 100%; border-collapse: collapse; margin: 25px 0; font-size: 0.95em; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
    .summary-table th, .summary-table td { border: 1px solid #ddd; padding: 12px 8px; text-align: center; vertical-align: middle; }
    .summary-table th { background-color: #34495e; color: white; font-weight: 600; font-size: 0.9em; }
    .formula-block { background-color: #f8f9fa; border-left: 4px solid #3498db; padding: 20px; margin: 25px 0; border-radius: 6px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); page-break-inside: avoid; }
    .pass { color: #27ae60; font-weight: bold; } .fail { color: #e74c3c; font-weight: bold; }
    .formula { font-size: 1.1em; text-align: center; margin: 15px 0; word-wrap: break-word; overflow-x: auto; padding: 12px; background-color: #ffffff; border-radius: 6px; border: 1px solid #e9ecef; }
    .final-result { font-weight: bold; color: #2980b9; text-align: center; display: block; margin-top: 20px; font-size: 1.2em; padding: 15px; border: 2px solid #3498db; border-radius: 8px; background-color: #eaf5ff; }
    .final-status { font-size: 1.4em; text-align: center; padding: 15px; border-radius: 8px; margin: 20px 0; font-weight: bold; }
    .final-status.pass { background-color: #d4edda; color: #155724; border: 2px solid #c3e6cb; }
    .final-status.fail { background-color: #f8d7da; color: #721c24; border: 2px solid #f5c6cb; }
    .ref-norma { font-size: 0.85em; color: #6c757d; text-align: right; margin-top: 15px; font-style: italic; }
    p { text-align: justify; margin: 10px 0; line-height: 1.6; }
</style>
"""

st.markdown(HTML_TEMPLATE_CSS, unsafe_allow_html=True)
st.markdown('<script type="text/javascript" async src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.7/MathJax.js?config=TeX-MML-AM_CHTML"></script>', unsafe_allow_html=True)

# ==============================================================================
# 2. FUNÇÕES DE CÁLCULO DE ENGENHARIA
# ==============================================================================

def calcular_esforcos_viga(tipo_viga, L_cm, q_kn_cm=0, p_load=None):
    msd_q, vsd_q, msd_p, vsd_p = 0, 0, 0, 0; L = L_cm
    if q_kn_cm > 0:
        if tipo_viga == 'Bi-apoiada': msd_q, vsd_q = (q_kn_cm * L**2)/8, (q_kn_cm*L)/2
        elif tipo_viga == 'Engastada e Livre (Balanço)': msd_q, vsd_q = (q_kn_cm * L**2)/2, q_kn_cm*L
        elif tipo_viga == 'Bi-engastada': msd_q, vsd_q = (q_kn_cm*L**2)/12, (q_kn_cm*L)/2
        elif tipo_viga == 'Engastada e Apoiada': msd_q, vsd_q = (q_kn_cm*L**2)/8, (5*q_kn_cm*L)/8
    if p_load:
        P, x = p_load; a, b = x, L-a
        if tipo_viga == 'Bi-apoiada': msd_p, vsd_p = (P*a*b)/L, max((P*b)/L, (P*a)/L)
        elif tipo_viga == 'Engastada e Livre (Balanço)': msd_p, vsd_p = P*a, P
        elif tipo_viga == 'Bi-engastada': msd_p,vsd_p = max((P*a*b**2)/L**2, (P*a**2*b)/L**2), max((P*b**2*(3*a+b))/L**3,(P*a**2*(a+3*b))/L**3)
        elif tipo_viga == 'Engastada e Apoiada': msd_p,vsd_p = max((P*b*(L**2-b**2))/(2*L**2),(P*a*(3*L**2-a**2))/(2*L**3)*a),max(P*b*(3*L**2-b**2)/(2*L**3),P*a*(3*L-a)/(2*L**2))
    return msd_q+msd_p, vsd_q+vsd_p

def calcular_flecha_maxima(tipo_viga, L_cm, E, Ix, q_serv_kn_cm=0, p_serv_load=None):
    delta_q, delta_p = 0, 0; L = L_cm
    if q_serv_kn_cm > 0:
        if tipo_viga=='Bi-apoiada': delta_q=(5*q_serv_kn_cm*L**4)/(384*E*Ix)
        elif tipo_viga=='Engastada e Livre (Balanço)': delta_q=(q_serv_kn_cm*L**4)/(8*E*Ix)
        elif tipo_viga=='Bi-engastada': delta_q=(q_serv_kn_cm*L**4)/(384*E*Ix)
        elif tipo_viga=='Engastada e Apoiada': delta_q=(q_serv_kn_cm*L**4)/(185*E*Ix)
    if p_serv_load:
        P, x = p_serv_load; a, b = x, L-a
        if tipo_viga=='Bi-apoiada':
            if a>=L/2: a,b=b,a
            if a<L: delta_p=(P*a*(L**2-a**2)**1.5)/(9*math.sqrt(3)*E*Ix*L)
        elif tipo_viga=='Engastada e Livre (Balanço)': delta_p=(P*a**2*(3*L-a))/(6*E*Ix)
        elif tipo_viga=='Bi-engastada': delta_p=(P*a**3*b**3)/(3*E*Ix*L**3)
        elif tipo_viga=='Engastada e Apoiada':
            if a<b: delta_p=(P*a**2*b**2*(3*L+a))/(12*E*Ix*L**3)
            else: delta_p=(P*b*(L**2-b**2)**1.5)/(9*math.sqrt(3)*E*Ix*L)
    return delta_q+delta_p

def get_profile_properties(profile_series):
    props={"d":profile_series.get('d (mm)'), "bf":profile_series.get('bf (mm)'), "tw":profile_series.get('tw (mm)'), "tf":profile_series.get('tf (mm)'), "h":profile_series.get('h (mm)'), "Area":profile_series.get('Área (cm2)'), "Ix":profile_series.get('Ix (cm4)'), "Wx":profile_series.get('Wx (cm3)'), "rx":profile_series.get('rx (cm)'), "Zx":profile_series.get('Zx (cm3)'), "Iy":profile_series.get('Iy (cm4)'), "Wy":profile_series.get('Wy (cm3)'), "ry":profile_series.get('ry (cm)'), "Zy":profile_series.get('Zy (cm3)'), "J":profile_series.get('It (cm4)'), "Cw":profile_series.get('Cw (cm6)'), "Peso":profile_series.get('Massa Linear (kg/m)', profile_series.get('Peso (kg/m)'))}
    required, profile_name = list(props.keys()), profile_series.get('Bitola (mm x kg/m)', 'Desconhecido')
    for key in required:
        if props[key] is None or pd.isna(props[key]) or props[key]<=0: raise ValueError(f"Propriedade '{key}' inválida em '{profile_name}'.")
    for key in ['d','bf','tw','tf','h']: props[key] /= 10.0
    return props

# ==============================================================================
# 3. GERAÇÃO DO MEMORIAL DE CÁLCULO
# ==============================================================================
def gerar_memorial_completo(perfil_nome, perfil_tipo, resultados):
    html_interno=f"<div class='container'><h1>Memorial de Cálculo Estrutural</h1><h2>Perfil: {perfil_nome} ({perfil_tipo})</h2><p>Norma: {Config.NOME_NORMA}</p>{resultados['resumo_html']}{resultados['passo_a_passo_html']}</div>"
    html_download=f"<!DOCTYPE html><html lang='pt-BR'><head><meta charset='UTF-8'><title>Memorial {perfil_nome}</title>{HTML_TEMPLATE_CSS}<script async src='https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.7/MathJax.js?config=TeX-MML-AM_CHTML'></script></head><body>{html_interno}</body></html>"
    return html_interno, html_download

def _build_verification_block_html(title, solicitante, s_symbol, resistente, r_symbol, eficiencia, status, unit):
    s,c="pass" if status=="APROVADO" else "fail", "≤" if status=="APROVADO" else ">"
    return f"<h4>{title}</h4><div class='formula-block'><p class='formula'>{s_symbol}={solicitante:.2f} {unit}</p><p class='formula'>{r_symbol}={resistente:.2f} {unit}</p><p class='formula'>Eficiência=({solicitante:.2f}/{resistente:.2f})={eficiencia:.1f}%%</p><div class='final-status {s}'>{status} {c} 100%%</div></div>"

# ==============================================================================
# 4. CARREGAMENTO DE DADOS
# ==============================================================================
@st.cache_data
def load_data_from_local_file():
    try: return pd.read_excel('perfis.xlsx', sheet_name=None)
    except FileNotFoundError: st.error("Erro: `perfis.xlsx` não encontrado. Verifique se o arquivo está na pasta raiz do app."); return None
    except Exception as e: st.error(f"Erro ao carregar o arquivo Excel: {e}"); return None

# ==============================================================================
# 5. FUNÇÕES DE CÁLCULO ESTRUTURAL
# ==============================================================================
def _calcular_mrdx_flt(props,Lb,Cb,fy):
    Zx,ry,Iy,Cw,J,Wx=props['Zx'],props['ry'],props['Iy'],props['Cw'],props['J'],props['Wx']
    Mp=Zx*fy; lambda_val=Lb/ry if ry>0 else float('inf'); lambda_p=Config.FATOR_LAMBDA_P_FLT*(Config.E_ACO/fy)**0.5
    d={'Mrdx':0,'Mp':{'d':'Momento Plastificação','v':Mp,'u':'kN.cm'},'λ':{'d':'Esbeltez','v':lambda_val},'λp':{'d':'Esbeltez Limite Plástica','v':lambda_p}}
    if lambda_val <= lambda_p: d['Mrdx']=Mp/Config.GAMMA_A1
    else:
        sigma_r,Mr=(Config.FATOR_SIGMA_R*fy),(fy-Config.FATOR_SIGMA_R*fy)*Wx
        beta1=((fy-sigma_r)*Wx)/(Config.E_ACO*J) if (Config.E_ACO*J)!=0 else 0
        lambda_r=float('inf')
        if ry>0 and beta1>0 and J>0 and Cw>0 and Iy>0:
            t1,t2=1+(27*Cw*(beta1**2)/Iy),0; t2=1+math.sqrt(t1) if t1>=0 else 1; lambda_r=(1.38*(Iy*J)**0.5/(ry*beta1*J))*(t2**0.5)
        d['λr']={'d':'Esbeltez Limite Inelástica','v':lambda_r}
        if lambda_val<=lambda_r:d['Mrdx']=min((Cb/Config.GAMMA_A1)*(Mp-(Mp-Mr)*((lambda_val-lambda_p)/(lambda_r-lambda_p))),Mp/Config.GAMMA_A1)
        else:
            Mcr=0; Lb2=Lb**2
            if Lb2>0 and Iy>0 and Cw>0 and J>0: Mcr=((Cb*(math.pi**2)*Config.E_ACO*Iy)/Lb2)*(((Cw/Iy)*(1+(0.039*J*Lb2/Cw)))**0.5)
            d['Mrdx']=Mcr/Config.GAMMA_A1
    return d

def _calcular_mrdx_flm(props,fy):
    bf,tf,Zx,Wx=props['bf'],props['tf'],props['Zx'],props['Wx']; Mp,l_val=Zx*fy,(bf/2)/tf if tf>0 else float('inf');l_p=Config.FATOR_LAMBDA_P_FLM*(Config.E_ACO/fy)**0.5
    d={'Mrdx':0,'λ':{'d':'Esbeltez Mesa','v':l_val},'λp':{'d':'Esbeltez Limite Plástica','v':l_p}}
    if l_val<=l_p: d['Mrdx']=Mp/Config.GAMMA_A1
    else:
        sigma_r,Mr=(Config.FATOR_SIGMA_R*fy),(fy-Config.FATOR_SIGMA_R*fy)*Wx
        l_r=Config.FATOR_LAMBDA_R_FLM_LAMINADO*(Config.E_ACO/(fy-sigma_r))**0.5 if (fy-sigma_r)>0 else float('inf')
        d['λr']={'d':'Esbeltez Limite Inelástica','v':l_r}
        if l_val<=l_r:d['Mrdx']=(1/Config.GAMMA_A1)*(Mp-(Mp-Mr)*((l_val-l_p)/(l_r-l_p)))
        else:Mcr=(0.69*Config.E_ACO*Wx)/(l_val**2) if l_val>0 else 0; d['Mrdx']=Mcr/Config.GAMMA_A1
    return d

def _calcular_mrdx_fla(props,fy):
    h,tw,Zx,Wx=props['h'],props['tw'],props['Zx'],props['Wx']; Mp,l_val=Zx*fy,h/tw if tw>0 else float('inf'); l_p=Config.FATOR_LAMBDA_P_FLA*(Config.E_ACO/fy)**0.5
    d={'Mrdx':0,'λ':{'d':'Esbeltez Alma','v':l_val},'λp':{'d':'Esbeltez Limite Plástica','v':l_p}}
    if l_val<=l_p:d['Mrdx']=Mp/Config.GAMMA_A1
    else:
        l_r=Config.FATOR_LAMBDA_R_FLA*(Config.E_ACO/fy)**0.5; Mr=fy*Wx
        d['λr']={'d':'Esbeltez Limite Inelástica','v':l_r}
        if l_val<=l_r: d['Mrdx']=(1/Config.GAMMA_A1)*(Mp-(Mp-Mr)*((l_val-l_p)/(l_r-l_p)))
        else:d['Mrdx']=0; d['warn']="Alma esbelta, Anexo H requerido"
    return d

def _calcular_vrd(props,fy):
    d,h,tw=props['d'],props['h'],props['tw']; Vpl=Config.FATOR_VP*d*tw*fy;l_val=h/tw if tw>0 else float('inf');kv=Config.KV_ALMA_SEM_ENRIJECEDORES; l_p=Config.FATOR_LAMBDA_P_VRD*(kv*Config.E_ACO/fy)**0.5
    dets={'Vrd':0,'Vpl':{'d':'Plastificação Cisalhamento','v':Vpl,'u':'kN'},'λ':{'d':'Esbeltez Alma','v':l_val},'λp':{'d':'Esbeltez Limite Plástica','v':l_p}}
    if l_val<=l_p: dets['Vrd']=Vpl/Config.GAMMA_A1
    else:
        l_r=Config.FATOR_LAMBDA_R_VRD*(kv*Config.E_ACO/fy)**0.5
        dets['λr']={'d':'Esbeltez Limite Inelástica','v':l_r}
        if l_val<=l_r: dets['Vrd']=(l_p/l_val)*(Vpl/Config.GAMMA_A1) if l_val>0 else 0
        else: dets['Vrd']=(Config.FATOR_VRD_ELASTICO*(l_p/l_val)**2)*(Vpl/Config.GAMMA_A1) if l_val>0 else 0
    return dets

# ==============================================================================
# 6. FUNÇÕES DE ANÁLISE E VERIFICAÇÃO
# ==============================================================================
def perform_all_checks(props,fy,Lb,Cb,L,Msd,Vsd,q_serv,p_serv,tipo_viga,input_mode,detalhado=False):
    res_flt,res_flm,res_fla,res_vrd=_calcular_mrdx_flt(props,Lb,Cb,fy),_calcular_mrdx_flm(props,fy),_calcular_mrdx_fla(props,fy),_calcular_vrd(props,fy)
    Mrd,Vrd=min(res_flt['Mrdx'],res_flm['Mrdx'],res_fla['Mrdx']),res_vrd['Vrd']
    ef_geral=(Msd/Mrd)*100 if Mrd>0 else float('inf'); stat_f="APROVADO" if ef_geral<=100.1 else "REPROVADO"
    res_f={'Mrd':Mrd,'eficiencia':ef_geral,'status':stat_f,'nota_interacao':"Vsd≤0.5Vrd. Ok." if Vsd<=0.5*Vrd else "Vsd>0.5Vrd. Interação requerida."}
    ef_cis=(Vsd/Vrd)*100 if Vrd>0 else float('inf'); stat_c="APROVADO" if ef_cis<=100.1 else "REPROVADO"
    res_c={'Vrd':Vrd,'eficiencia':ef_cis,'status':stat_c}
    res_d={'status':'N/A'}
    if input_mode=="Calcular a partir de Cargas na Viga":
        dmax=calcular_flecha_maxima(tipo_viga,L,Config.E_ACO,props['Ix'],q_serv,p_serv);dlim=L/Config.LIMITE_FLECHA_TOTAL
        ef_d=(dmax/dlim)*100 if dlim>0 else float('inf'); stat_d="APROVADO" if ef_d<=100.1 else "REPROVADO"
        res_d={'flecha_max':dmax,'flecha_limite':dlim,'eficiencia':ef_d,'status':stat_d}
    passos=build_step_by_step_html(L,Msd,Vsd,res_f,res_c,res_d,res_flt,res_flm,res_fla,res_vrd,input_mode) if detalhado else ""
    return res_f,res_c,res_d,passos

def build_summary_html(Msd,Vsd,res_f,res_c,res_d):
    v=[('Flexão (ELU)',f"{Msd/100:.2f} kNm",f"{res_f['Mrd']/100:.2f} kNm",res_f['eficiencia'],res_f['status']),('Cisalh. (ELU)',f"{Vsd:.2f} kN",f"{res_c['Vrd']:.2f} kN",res_c['eficiencia'],res_c['status'])]
    if res_d['status']!='N/A':v.append(('Flecha (ELS)',f"{res_d['flecha_max']:.2f} cm",f"≤ {res_d['flecha_limite']:.2f} cm",res_d['eficiencia'],res_d['status']))
    rows="".join([f'<tr><td>{n}</td><td>{s}</td><td>{r}</td><td>{e:.1f}%</td><td class="{ "pass" if st=="APROVADO" else "fail"}">{st}</td></tr>' for n,s,r,e,st in v])
    return f'<table class="summary-table"><tr><th>Verificação</th><th>Solicitante</th><th>Resistente/Limite</th><th>Eficiência</th><th>Status</th></tr>{rows}</table><p><b>Nota:</b> {res_f["nota_interacao"]}</p>'

def build_step_by_step_html(L, Msd, Vsd, res_f, res_c, res_d, res_flt, res_flm, res_fla, res_vrd, input_mode):
    html=f'<h2>2. Verificações Detalhadas</h2><h3>3.1 Flexão</h3>'
    html+=_add_verification_details("FLT",res_flt); html+=_add_verification_details("FLM",res_flm); html+=_add_verification_details("FLA",res_fla)
    html+=_build_verification_block_html("Flexão Final", Msd/100, "M<sub>sd</sub>", res_f['Mrd']/100, "M<sub>rd,final</sub>",res_f['eficiencia'], res_f['status'], "kNm")
    html+=f"<h3>3.2 Cisalhamento</h3>"; html+=_add_verification_details("Resistência ao Cisalhamento", res_vrd)
    html+=_build_verification_block_html("Cisalhamento Final", Vsd,"V<sub>sd</sub>", res_c['Vrd'],"V<sub>rd</sub>", res_c['eficiencia'], res_c['status'],"kN")
    if input_mode=="Calcular a partir de Cargas na Viga":
        html+=f"<h3>3.3 Verificação de Serviço (Flecha)</h3>"
        html+=_build_verification_block_html("Flecha",res_d['flecha_max'],"δ<sub>max</sub>",res_d['flecha_limite'],"δ<sub>lim</sub>",res_d['eficiencia'],res_d['status'],"cm")
    return html

def _add_verification_details(title,details):
    html=f"<h4>{title}</h4><div class='formula-block'>"; final_res=0; unit=""
    for k,v in details.items():
        if isinstance(v, dict) and 'd' in v: html+=f"<p>{v['d']}: {v['v']:.2f} {v.get('u','')}</p>"
    if 'Mrdx' in details: final_res, unit = details['Mrdx']/100, "kNm"
    elif 'Vrd' in details: final_res, unit = details['Vrd'], "kN"
    html+=f"<p class='final-result'>Resistência ({title}) = {final_res:.2f} {unit}</p></div>"
    return html

# ==============================================================================
# 7. FUNÇÕES DE ANÁLISE PRINCIPAL
# ==============================================================================
def run_detailed_analysis(df,perfil_nome,perfil_tipo,fy,Lb,Cb,L_cm,Msd,Vsd,q_serv,p_serv,tipo_viga,input_mode):
    try:
        with st.spinner(f"Analisando perfil {perfil_nome}..."):
            perfil_series=df[df['Bitola (mm x kg/m)']==perfil_nome].iloc[0]
            props=get_profile_properties(perfil_series)
            res_f,res_c,res_d,passos=perform_all_checks(props,fy,Lb,Cb,L_cm,Msd,Vsd,q_serv,p_serv,tipo_viga,input_mode,detalhado=True)
            resumo=build_summary_html(Msd,Vsd,res_f,res_c,res_d)
            view_html,download_html=gerar_memorial_completo(perfil_nome,perfil_tipo,{'resumo_html':resumo,'passo_a_passo_html':passos})
        st.success("Análise Concluída com Sucesso!", icon="✅")
        st.markdown(view_html,unsafe_allow_html=True)
        st.download_button("📥 Baixar Memorial Completo (HTML)",download_html.encode('utf-8'),f"Memorial_{perfil_nome.replace(' ','_')}.html","text/html",use_container_width=True)
    except Exception as e:
        st.error(f"Ocorreu um erro durante a análise: {e}",icon="🔥")

# ==============================================================================
# 8. APLICAÇÃO PRINCIPAL
# ==============================================================================
def main():
    st.title("🏛️ Calculadora Estrutural Versátil")
    st.caption(f"Utilizando a norma: {Config.NOME_NORMA}")
    all_sheets=load_data_from_local_file();
    if not all_sheets: st.stop()
    
    with st.sidebar:
        st.header("⚙️ Parâmetros de Entrada")
        st.subheader("1. Modelo da Viga")
        tipo_viga=st.selectbox("Modelo da Viga:", ('Bi-apoiada', 'Engastada e Livre (Balanço)', 'Bi-engastada', 'Engastada e Apoiada'))
        L_cm=st.number_input("Comprimento (L, cm)",min_value=10.0,value=500.0,step=10.0)

        st.subheader("2. Carregamento")
        input_mode=st.radio("Modo de Entrada:",("Calcular a partir de Cargas na Viga","Inserir Esforços Manualmente"),label_visibility="collapsed")
        Msd,Vsd,q_serv,p_serv=0,0,0,None
        if input_mode=="Calcular a partir de Cargas na Viga":
            with st.container(border=True):
                q_serv_knm2=st.number_input("Carga Dist. (serviço, kN/m²)",min_value=0.0,value=4.0,step=0.5)
                larg_inf=st.number_input("Largura de Influência (m)",min_value=0.1,value=5.0,step=0.5); q_serv=(q_serv_knm2*larg_inf)/100.0
                if st.checkbox("Adicionar Carga Pontual"):
                    p_serv_kn=st.number_input("Valor de P (serviço, kN)",min_value=0.0,value=10.0)
                    p_pos_cm=st.number_input("Posição de P (cm)",min_value=0.0,max_value=L_cm,value=L_cm/2); p_serv=(p_serv_kn,p_pos_cm)
                gamma_f=st.number_input(label="Coef. de Majoração (γf)",min_value=1.0,value=1.4,step=0.1)
                q_ult,p_ult=q_serv*gamma_f,(p_serv[0]*gamma_f,p_serv[1]) if p_serv else None; Msd,Vsd=calcular_esforcos_viga(tipo_viga,L_cm,q_ult,p_ult)
        else:
            with st.container(border=True):
                st.warning("Verificação de flecha (ELS) não será realizada.")
                msd_input=st.number_input("Momento Solicitante (Msd, kNm)",min_value=0.0,value=100.0); Msd=msd_input*100
                Vsd=st.number_input("Força Cortante (Vsd, kN)",min_value=0.0,value=50.0)

        st.subheader("3. Parâmetros do Aço")
        fy_aco=st.number_input("fy (kN/cm²)",min_value=20.0,max_value=50.0,value=34.5,step=0.5)
        Lb_projeto=st.number_input("Comp. Destravado (Lb, cm)",min_value=10.0,value=L_cm,step=10.0)
        Cb_projeto=st.number_input("Fator de Modificação (Cb)",min_value=1.0,max_value=3.0,value=1.1,step=0.1)

    st.header("Análise do Perfil Específico")
    c1,c2=st.columns([1,1])
    sheet_disp_name=c1.selectbox("Selecione a Categoria do Perfil",options=list(Config.PROFILE_TYPE_MAP.values()))
    sheet_key=[k for k,v in Config.PROFILE_TYPE_MAP.items() if v==sheet_disp_name][0]
    df_selected=all_sheets[sheet_key]
    perfil_nome=c2.selectbox("Selecione o Perfil",options=df_selected['Bitola (mm x kg/m)'])
    if st.button("Gerar Memorial de Cálculo",type="primary",use_container_width=True):
        run_detailed_analysis(df_selected,perfil_nome,sheet_disp_name,fy_aco,Lb_projeto,Cb_projeto,L_cm,Msd,Vsd,q_serv,p_serv,tipo_viga,input_mode)

if __name__ == '__main__':
    main()