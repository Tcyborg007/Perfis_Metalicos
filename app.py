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

st.set_page_config(page_title="Calculadora Estrutural Versátil", layout="wide")

# ALTERAÇÃO 1: CSS foi ajustado para ser responsivo e ocupar a largura total.
# A propriedade `max-width` foi mudada de um valor fixo para `100%`.
HTML_TEMPLATE_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&family=Roboto+Slab:wght@400;700&display=swap');
    body { font-family: 'Roboto', sans-serif; line-height: 1.8; color: #333; background-color: #f0f4f8; }
    .container {
        max-width: 100%; /* ALTERADO DE 8.5in para 100% para ocupar o espaço disponível */
        margin: 20px auto;
        padding: 2rem; /* Usando unidade relativa para melhor responsividade */
        background-color: white;
        border-radius: 10px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        box-sizing: border-box; /* Garante que padding não adicione largura extra */
    }
    h1, h2, h3, h4, h5 { font-family: 'Roboto Slab', serif; color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 5px; margin-top: 30px; }
    h1 { text-align: center; border: none; font-size: 2.2em; }
    h5 { border-bottom: none; font-size: 1em; margin-top: 15px; color: #34495e;}
    .summary-table { width: 100%; border-collapse: collapse; margin-bottom: 20px; font-size: 0.9em; }
    .summary-table th, .summary-table td { border: 1px solid #ddd; padding: 8px; text-align: center; vertical-align: middle; }
    .summary-table th { background-color: #34495e; color: white; }
    .formula-block { background-color: #f9fbfc; border-left: 5px solid #3498db; padding: 20px; margin: 20px 0; border-radius: 5px; overflow-x: auto; }
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

# ALTERAÇÃO 2: Injetar o script de renderização de fórmulas matemáticas globalmente.
st.markdown('<script type="text/javascript" async src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.7/MathJax.js?config=TeX-MML-AM_CHTML"></script>', unsafe_allow_html=True)


# ==============================================================================
# 2. FUNÇÕES DE CÁLCULO DE ENGENHARIA (SEM ALTERAÇÕES)
# ==============================================================================

def calcular_esforcos_viga(tipo_viga, L_cm, q_kn_cm=0, p_load=None):
    msd_q, vsd_q, msd_p, vsd_p = 0, 0, 0, 0
    L = L_cm
    if q_kn_cm > 0:
        if tipo_viga == 'Bi-apoiada': msd_q, vsd_q = (q_kn_cm * L**2) / 8, (q_kn_cm * L) / 2
        elif tipo_viga == 'Engastada e Livre (Balanço)': msd_q, vsd_q = (q_kn_cm * L**2) / 2, q_kn_cm * L
        elif tipo_viga == 'Bi-engastada': msd_q, vsd_q = (q_kn_cm * L**2) / 12, (q_kn_cm * L) / 2
        elif tipo_viga == 'Engastada e Apoiada': msd_q, vsd_q = (q_kn_cm * L**2) / 8, (5 * q_kn_cm * L) / 8
    if p_load:
        P, x = p_load; a, b = x, L - x
        if tipo_viga == 'Bi-apoiada': msd_p, vsd_p = (P * a * b) / L, max((P * b) / L, (P * a) / L)
        elif tipo_viga == 'Engastada e Livre (Balanço)': msd_p, vsd_p = P * a, P
        elif tipo_viga == 'Bi-engastada': msd_p, vsd_p = max((P * a * b**2) / L**2, (P * a**2 * b) / L**2), max((P * b**2 * (3*a + b)) / L**3, (P * a**2 * (a + 3*b)) / L**3)
        elif tipo_viga == 'Engastada e Apoiada': msd_p, vsd_p = max((P*b*(L**2 - b**2))/(2*L**2), (P*a*(3*L**2 - a**2))/(2*L**3)*a), max(P*b*(3*L**2-b**2)/(2*L**3), P*a*(3*L-a)/(2*L**2))
    return msd_q + msd_p, vsd_q + vsd_p

def calcular_flecha_maxima(tipo_viga, L_cm, E, Ix, q_serv_kn_cm=0, p_serv_load=None):
    delta_q, delta_p = 0, 0
    L = L_cm
    if q_serv_kn_cm > 0:
        if tipo_viga == 'Bi-apoiada': delta_q = (5 * q_serv_kn_cm * L**4) / (384 * E * Ix)
        elif tipo_viga == 'Engastada e Livre (Balanço)': delta_q = (q_serv_kn_cm * L**4) / (8 * E * Ix)
        elif tipo_viga == 'Bi-engastada': delta_q = (q_serv_kn_cm * L**4) / (384 * E * Ix)
        elif tipo_viga == 'Engastada e Apoiada': delta_q = (q_serv_kn_cm * L**4) / (185 * E * Ix)
    if p_serv_load:
        P, x = p_serv_load; a, b = x, L - x
        if tipo_viga == 'Bi-apoiada':
            if a >= L/2: a, b = b, a 
            delta_p = (P * a * (L**2 - a**2)**1.5) / (9 * math.sqrt(3) * E * Ix * L) if a < L else 0
        elif tipo_viga == 'Engastada e Livre (Balanço)': delta_p = (P * a**2 * (3*L - a)) / (6 * E * Ix)
        elif tipo_viga == 'Bi-engastada': delta_p = (P * a**3 * b**3) / (3 * E * Ix * L**3)
        elif tipo_viga == 'Engastada e Apoiada':
            if a < b: delta_p = (P * a**2 * b**2 * (3*L+a))/(12*E*Ix*L**3)
            else: delta_p = (P * b * (L**2 - b**2)**1.5)/(9*math.sqrt(3)*E*Ix*L)
    return delta_q + delta_p

def get_profile_properties(profile_series):
    props = {"d": profile_series.get('d (mm)'), "bf": profile_series.get('bf (mm)'), "tw": profile_series.get('tw (mm)'), "tf": profile_series.get('tf (mm)'), "h": profile_series.get('h (mm)'), "Area": profile_series.get('Área (cm2)'), "Ix": profile_series.get('Ix (cm4)'), "Wx": profile_series.get('Wx (cm3)'), "rx": profile_series.get('rx (cm)'), "Zx": profile_series.get('Zx (cm3)'), "Iy": profile_series.get('Iy (cm4)'), "Wy": profile_series.get('Wy (cm3)'), "ry": profile_series.get('ry (cm)'), "Zy": profile_series.get('Zy (cm3)'), "J": profile_series.get('It (cm4)'), "Cw": profile_series.get('Cw (cm6)'), "Peso": profile_series.get('Massa Linear (kg/m)', profile_series.get('Peso (kg/m)'))}
    required_keys = ["d", "bf", "tw", "tf", "h", "Area", "Ix", "Wx", "rx", "Zx", "Iy", "ry", "J", "Cw", "Peso"]
    profile_name = profile_series.get('Bitola (mm x kg/m)', 'Perfil Desconhecido')
    for key in required_keys:
        value = props.get(key)
        if value is None or pd.isna(value) or (isinstance(value, (int, float)) and value <= 0): raise ValueError(f"Propriedade ESSENCIAL '{key}' inválida ou nula no Excel para '{profile_name}'. Verifique a planilha.")
    for key in ['d', 'bf', 'tw', 'tf', 'h']: props[key] /= 10.0
    return props

# ==============================================================================
# 3. GERAÇÃO DO MEMORIAL DE CÁLCULO (MODIFICADO)
# ==============================================================================

# ALTERAÇÃO 3: Função agora retorna duas versões do HTML.
# 1. `html_para_visualizacao`: Apenas o conteúdo, para ser injetado na página com st.markdown.
# 2. `html_para_download`: O arquivo HTML completo e autônomo.
def gerar_memorial_completo(perfil_nome, perfil_tipo, resultados):
    html_interno = f"""
    <div class="container">
        <h1>Memorial de Cálculo Estrutural</h1>
        <h2>Perfil Metálico: {perfil_nome} ({perfil_tipo})</h2>
        <p style="text-align:center; font-style:italic;">Cálculos baseados na norma: <b>{Config.NOME_NORMA}</b></p>
        <h3>1. Resumo Final das Verificações</h3>
        {resultados['resumo_html']}
        {resultados['passo_a_passo_html']}
    </div>
    """
    
    html_para_download = f"""
    <!DOCTYPE html><html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <title>Memorial de Cálculo - {perfil_nome}</title>
        {HTML_TEMPLATE_CSS}
        <script type="text/javascript" async src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.7/MathJax.js?config=TeX-MML-AM_CHTML"></script>
    </head>
    <body>
        {html_interno}
    </body>
    </html>
    """
    
    html_para_visualizacao = html_interno
    return html_para_visualizacao, html_para_download

def _build_verification_block_html(title, solicitante, s_symbol, resistente, r_symbol, eficiencia, status, unit):
    status_class = "pass" if status == "APROVADO" else "fail"
    comp_symbol = "\\le" if status == "APROVADO" else ">"
    return f"""<h4>{title}</h4><div class="formula-block"><p class="formula">$$ {s_symbol} = {solicitante:.2f} \\, {unit} $$</p><p class="formula">$$ {r_symbol} = {resistente:.2f} \\, {unit} $$</p><p class="formula">$$ \\text{{Verificação: }} {s_symbol} {comp_symbol} {r_symbol} $$</p><p class="formula">$$ \\text{{Eficiência}} = \\frac{{{s_symbol}}}{{{r_symbol}}} = \\frac{{{solicitante:.2f}}}{{{resistente:.2f}}} = {eficiencia:.1f}\% $$</p><div class="final-status {status_class}">{status}</div></div>"""

# ==============================================================================
# 4. APLICAÇÃO PRINCIPAL STREAMLIT
# ==============================================================================

@st.cache_data
def load_data_from_local_file():
    try:
        caminho_arquivo_excel = 'perfis.xlsx' 
        return pd.read_excel(caminho_arquivo_excel, sheet_name=None)
    except FileNotFoundError:
        st.error(f"Erro: Arquivo '{caminho_arquivo_excel}' não foi encontrado. Verifique se ele está no mesmo repositório do aplicativo Streamlit.")
        return None
    except Exception as e:
        st.error(f"Erro ao ler o arquivo Excel: {e}")
        return None

def main():
    st.title("🏛️ Calculadora Estrutural Versátil")
    st.caption(f"Utilizando a norma: {Config.NOME_NORMA}")
    all_sheets = load_data_from_local_file()
    if not all_sheets: st.stop()

    with st.sidebar:
        st.header("⚙️ Parâmetros de Entrada")
        st.header("1. Modelo da Viga")
        tipo_viga = st.selectbox("Tipo de Viga:", ('Bi-apoiada', 'Engastada e Livre (Balanço)', 'Bi-engastada', 'Engastada e Apoiada'))
        L_cm = st.number_input("Comprimento da Viga (L, cm)", 10.0, value=500.0, step=10.0)
        st.header("2. Modo de Carregamento")
        input_mode = st.radio("Selecione:", ("Calcular a partir de Cargas na Viga", "Inserir Esforços Manualmente"), horizontal=True, label_visibility="collapsed")
        Msd, Vsd, q_servico_kn_cm, p_load_serv = 0, 0, 0, None

        if input_mode == "Calcular a partir de Cargas na Viga":
            with st.container(border=True):
                st.subheader("Carga Distribuída (q)"); carga_area = st.number_input("Carga Distribuída (serviço, kN/m²)", 0.0, value=4.0, step=0.5); larg_inf = st.number_input("Largura de Influência (m)", 0.0, value=5.0, step=0.5)
                st.subheader("Carga Pontual (P)")
                if st.checkbox("Adicionar Carga Pontual"): p_serv_kn = st.number_input("Valor da Carga P (serviço, kN)", 0.0, 10.0); p_pos_cm = st.number_input("Posição da Carga P (x, cm)", 0.0, L_cm, L_cm/2); p_load_serv = (p_serv_kn, p_pos_cm)
                gamma_f = st.number_input("Coeficiente de Majoração (γf)", 1.0, value=1.4, step=0.1)
                q_servico_kn_cm = (carga_area * larg_inf) / 100.0; q_ult_kn_cm = q_servico_kn_cm * gamma_f
                p_load_ult = (p_load_serv[0] * gamma_f, p_load_serv[1]) if p_load_serv else None
                Msd, Vsd = calcular_esforcos_viga(tipo_viga, L_cm, q_ult_kn_cm, p_load_ult)
        else: 
            with st.container(border=True):
                st.warning("Verificação de flecha (ELS) não realizada em modo manual."); msd_input = st.number_input("Momento Solicitante (Msd, kNm)", 0.0, 100.0); Msd = msd_input * 100; Vsd = st.number_input("Força Cortante (Vsd, kN)", 0.0, 50.0)

        st.header("3. Parâmetros Gerais do Aço"); fy_aco = st.number_input("Tensão de Escoamento (fy, kN/cm²)", 20.0, 50.0, 34.5, 0.5); Lb_projeto = st.number_input("Comprimento Destravado (Lb, cm)", 10.0, value=L_cm, step=10.0); Cb_projeto = st.number_input("Fator de Modificação (Cb)", 1.0, 3.0, 1.10)
        st.header("4. Modo de Análise"); analysis_mode = st.radio("Selecione:", ("Análise em Lote", "Memorial Detalhado"), horizontal=True, label_visibility="collapsed")
    
    display_names = [PROFILE_TYPE_MAP.get(name, name) for name in all_sheets.keys()]
    reverse_name_map = {v: k for k, v in PROFILE_TYPE_MAP.items()}

    if analysis_mode == "Memorial Detalhado":
        st.header("🔍 Memorial de Cálculo Detalhado")
        selected_display_name = st.selectbox("Selecione o Tipo de Perfil:", display_names); sheet_name = reverse_name_map.get(selected_display_name, selected_display_name); df_selecionado = all_sheets[sheet_name]
        perfil_selecionado_nome = st.selectbox("Selecione o Perfil Específico:", df_selecionado['Bitola (mm x kg/m)'])
        if st.button("Gerar Memorial Completo", type="primary", use_container_width=True):
            run_detailed_analysis(df_selecionado, perfil_selecionado_nome, selected_display_name, fy_aco, Lb_projeto, Cb_projeto, L_cm, Msd, Vsd, q_servico_kn_cm, p_load_serv, tipo_viga, input_mode)
    else: # Análise em Lote com Otimização
        st.header("📊 Pré-dimensionamento e Análise por Categoria")
        if st.button("Iniciar Análise Otimizada", type="primary", use_container_width=True):
            run_batch_analysis(all_sheets, fy_aco, Lb_projeto, Cb_projeto, L_cm, Msd, Vsd, q_servico_kn_cm, p_load_serv, tipo_viga, input_mode)

# ==============================================================================
# 5. FUNÇÕES DE ORQUESTRAÇÃO E ANÁLISE
# ==============================================================================

# ALTERAÇÃO 4: A função de análise agora usa st.markdown e o novo gerar_memorial_completo.
def run_detailed_analysis(df, perfil_nome, perfil_tipo_display, fy, Lb, Cb, L, Msd, Vsd, q_serv_kn_cm, p_serv_load, tipo_viga, input_mode):
    with st.spinner(f"Gerando análise completa para {perfil_nome}..."):
        try:
            perfil_series = df[df['Bitola (mm x kg/m)'] == perfil_nome].iloc[0]
            props = get_profile_properties(perfil_series)
            res_flexao, res_cis, res_flecha, passo_a_passo = perform_all_checks(props, fy, Lb, Cb, L, Msd, Vsd, q_serv_kn_cm, p_serv_load, tipo_viga, input_mode, detalhado=True)
            resumo_html = build_summary_html(Msd, Vsd, res_flexao, res_cis, res_flecha)
            resultados = {'resumo_html': resumo_html, 'passo_a_passo_html': passo_a_passo}
            
            # Obtenha ambas as versões do HTML
            html_para_visualizacao, html_para_download = gerar_memorial_completo(perfil_nome, perfil_tipo_display, resultados)
            
            st.success("Análise concluída!")
            
            # Use st.markdown para renderizar o conteúdo diretamente na página (sem iframe)
            st.markdown(html_para_visualizacao, unsafe_allow_html=True)
            
            # Use o conteúdo HTML completo para o botão de download
            st.download_button(
                label="📥 Baixar Memorial HTML",
                data=html_para_download.encode('utf-8'),
                file_name=f"Memorial_{perfil_nome.replace(' ', '_')}.html",
                mime="text/html"
            )
        except (ValueError, KeyError) as e: st.error(f"❌ Erro nos Dados de Entrada: {e}")
        except Exception as e: st.error(f"❌ Ocorreu um erro inesperado: {e}")


def run_batch_analysis(all_sheets, fy, Lb, Cb, L, Msd, Vsd, q_serv_kn_cm, p_serv_load, tipo_viga, input_mode):
    all_results = []
    total_perfis = sum(len(df) for df in all_sheets.values())
    progress_bar = st.progress(0, text=f"Analisando 0 de {total_perfis} perfis...")
    perfis_processados = 0
    
    with st.spinner("Processando todos os perfis..."):
        for sheet_name, df in all_sheets.items():
            for _, row in df.iterrows():
                perfis_processados += 1
                progress_bar.progress(perfis_processados / total_perfis, text=f"Analisando {perfis_processados} de {total_perfis} perfis...")
                try:
                    props = get_profile_properties(row)
                    res_flexao, res_cis, res_flecha, _ = perform_all_checks(props, fy, Lb, Cb, L, Msd, Vsd, q_serv_kn_cm, p_serv_load, tipo_viga, input_mode)
                    status_geral = "APROVADO" if max(res_flexao['ef_flt'], res_flexao['ef_flm'], res_flexao['ef_fla'], res_cis['eficiencia'], res_flecha['eficiencia']) <= 100.1 else "REPROVADO"
                    all_results.append({'Tipo': sheet_name, 'Perfil': row['Bitola (mm x kg/m)'], 'Peso (kg/m)': props.get('Peso', 0), 'Status': status_geral, 'Ef. FLT (%)': res_flexao['ef_flt'], 'Ef. FLM (%)': res_flexao['ef_flm'], 'Ef. FLA (%)': res_flexao['ef_fla'], 'Ef. Cis. (%)': res_cis['eficiencia'], 'Ef. Flecha (%)': res_flecha['eficiencia']})
                except (ValueError, KeyError): continue
    
    progress_bar.empty()
    if not all_results:
        st.error("Não foi possível analisar nenhum perfil. Verifique os parâmetros de entrada."); return
        
    df_all_results = pd.DataFrame(all_results)
    st.success(f"{len(df_all_results)} perfis analisados.")
    tab_names = [PROFILE_TYPE_MAP.get(name, name) for name in all_sheets.keys()]
    tabs = st.tabs(tab_names)
    
    def style_dataframe(df):
        def color_efficiency(val):
            if not isinstance(val, (int, float)) or pd.isna(val): return ''
            color = '#f8d7da' if val > 100 else ('#ffeeba' if val > 95 else ('#fff3cd' if val > 80 else '#d4edda'))
            return f'background-color: {color}'
        efficiency_cols = [col for col in df.columns if '%' in col]
        return df.style.applymap(color_efficiency, subset=efficiency_cols).format("{:.1f}", subset=efficiency_cols)
        
    for i, sheet_name in enumerate(all_sheets.keys()):
        with tabs[i]:
            df_type = df_all_results[df_all_results['Tipo'] == sheet_name].drop(columns=['Tipo'])
            if df_type.empty:
                st.write("Nenhum perfil desta categoria foi analisado."); continue
            
            aprovados = df_type[df_type['Status'] == 'APROVADO'].copy()
            if not aprovados.empty:
                aprovados.sort_values(by='Peso (kg/m)', inplace=True)
                st.subheader("🏆 Perfil Mais Leve Aprovado (Otimizado)")
                st.dataframe(style_dataframe(aprovados.head(1)), use_container_width=True)
                with st.expander("Ver todos os perfis aprovados desta categoria"): st.dataframe(style_dataframe(aprovados), use_container_width=True)
            else: st.info("Nenhum perfil desta categoria foi aprovado.")
            
            reprovados = df_type[df_type['Status'] == 'REPROVADO'].copy()
            if not reprovados.empty:
                with st.expander("Ver perfis reprovados"): st.dataframe(style_dataframe(reprovados), use_container_width=True)

# ... Todas as outras funções (perform_all_checks, build_summary_html, etc.) permanecem iguais...
# (CÓDIGO COMPLETO ABAIXO, SEM OMISSÕES)

def perform_all_checks(props, fy, Lb, Cb, L, Msd, Vsd, q_serv_kn_cm, p_serv_load, tipo_viga, input_mode, detalhado=False):
    res_flt = _calcular_mrdx_flt(props, Lb, Cb, fy); res_flm = _calcular_mrdx_flm(props, fy); res_fla = _calcular_mrdx_fla(props, fy); res_vrd = _calcular_vrd(props, fy)
    Vrd = res_vrd['Vrd']; Mrd_final = min(res_flt['Mrdx'], res_flm['Mrdx'], res_fla['Mrdx'])
    nota_interacao = "Vsd ≤ 0.5*Vrd. Interação não necessária." if Vsd <= 0.5 * Vrd else "Vsd > 0.5*Vrd. Interação deve ser considerada (não implementado)."
    ef_geral = (Msd / Mrd_final) * 100 if Mrd_final > 0 else float('inf')
    status_flexao = "APROVADO" if ef_geral <= 100.1 else "REPROVADO"
    res_flexao = {'Mrd': Mrd_final, 'eficiencia': ef_geral, 'status': status_flexao, 'ef_flt': (Msd / res_flt['Mrdx']) * 100 if res_flt['Mrdx'] > 0 else float('inf'), 'ef_flm': (Msd / res_flm['Mrdx']) * 100 if res_flm['Mrdx'] > 0 else float('inf'), 'ef_fla': (Msd / res_fla['Mrdx']) * 100 if res_fla['Mrdx'] > 0 else float('inf'), 'nota_interacao': nota_interacao}
    
    eficiencia_cisalhamento = (Vsd / Vrd) * 100 if Vrd > 0 else float('inf')
    res_cisalhamento = {'Vrd': Vrd, 'eficiencia': eficiencia_cisalhamento, 'status': "APROVADO" if eficiencia_cisalhamento <= 100.1 else "REPROVADO"}

    flecha_max, flecha_limite, eficiencia_flecha, status_flecha = 0, 0, 0, "N/A"
    if input_mode == "Calcular a partir de Cargas na Viga":
        flecha_max = calcular_flecha_maxima(tipo_viga, L, Config.E_ACO, props['Ix'], q_serv_kn_cm, p_serv_load)
        flecha_limite = L / Config.LIMITE_FLECHA_TOTAL if L > 0 else 0
        eficiencia_flecha = (flecha_max / flecha_limite) * 100 if flecha_limite > 0 else float('inf')
        status_flecha = "APROVADO" if eficiencia_flecha <= 100.1 else "REPROVADO"
    res_flecha = {'flecha_max': flecha_max, 'flecha_limite': flecha_limite, 'eficiencia': eficiencia_flecha, 'status': status_flecha, 'Ix': props['Ix']}
    
    passo_a_passo_html = build_step_by_step_html(L, Msd, Vsd, res_flexao, res_cisalhamento, res_flecha, res_flt, res_flm, res_fla, res_vrd, input_mode) if detalhado else ""
    return res_flexao, res_cisalhamento, res_flecha, passo_a_passo_html

def build_summary_html(Msd, Vsd, res_flexao, res_cisalhamento, res_flecha):
    verificacoes = [('Flexão (M) - ELU', f"{Msd/100:.2f} kNm", f"{res_flexao['Mrd']/100:.2f} kNm", res_flexao['eficiencia'], res_flexao['status']),('Cisalhamento (V) - ELU', f"{Vsd:.2f} kN", f"{res_cisalhamento['Vrd']:.2f} kN", res_cisalhamento['eficiencia'], res_cisalhamento['status']),('Flecha (δ) - ELS', f"{res_flecha['flecha_max']:.2f} cm" if res_flecha['status'] != "N/A" else "N/A", f"≤ {res_flecha['flecha_limite']:.2f} cm" if res_flecha['status'] != "N/A" else "N/A", res_flecha['eficiencia'], res_flecha['status'])]
    rows_html = "".join([f'<tr><td>{n}</td><td>{s}</td><td>{r}</td><td>{e:.1f}%</td><td class="{"pass" if st == "APROVADO" else "fail"}">{st}</td></tr>' for n, s, r, e, st in verificacoes])
    return f'<table class="summary-table"><tr><th>Verificação</th><th>Solicitante</th><th>Resistente/Limite</th><th>Eficiência</th><th>Status</th></tr>{rows_html}</table><p style="text-align:justify; font-size:0.9em;"><b>Nota sobre Interação M-V:</b> {res_flexao["nota_interacao"]}</p>'

def build_step_by_step_html(L, Msd, Vsd, res_flexao, res_cis, res_flecha, res_flt, res_flm, res_fla, res_vrd, input_mode):
    html = f'<h2>2. Esforços Solicitantes</h2><div class="formula-block"><p class="formula">$$ M_{{sd}} = {Msd/100:.2f} \\, kNm $$</p><p class="formula">$$ V_{{sd}} = {Vsd:.2f} \\, kN $$</p></div><h2>3. Verificações (ELU)</h2><h3>3.1 Resistência à Flexão (Mrd)</h3>'
    html += _add_verification_details("Flambagem Lateral com Torção (FLT)", res_flt)
    html += _add_verification_details("Flambagem Local da Mesa (FLM)", res_flm)
    html += _add_verification_details("Flambagem Local da Alma (FLA)", res_fla)
    html += _build_verification_block_html("Verificação Final à Flexão", Msd/100, "M_{sd}", res_flexao['Mrd']/100, "M_{rd}", res_flexao['eficiencia'], res_flexao['status'], "kNm")
    html += f"<h3>3.2 Resistência ao Cisalhamento (Vrd)</h3>"
    html += _add_verification_details("Força Cortante Resistente (VRd)", res_vrd)
    html += _build_verification_block_html("Verificação ao Cisalhamento", Vsd, "V_{sd}", res_cis['Vrd'], "V_{rd}", res_cis['eficiencia'], res_cis['status'], "kN")
    if input_mode == "Calcular a partir de Cargas na Viga":
        html += f'<h2>4. Verificação de Serviço (ELS)</h2><div class="formula-block"><h4>Flecha Atuante (δ_max)</h4><p class="formula">$$ \\delta_{{max}} = {res_flecha["flecha_max"]:.2f} \\, cm $$</p><h4>Flecha Limite (δ_lim)</h4><p class="formula">$$ \\delta_{{lim}} = \\frac{{L}}{{{Config.LIMITE_FLECHA_TOTAL}}} = \\frac{{{L:.2f}}}{{{Config.LIMITE_FLECHA_TOTAL}}} = {res_flecha["flecha_limite"]:.2f} \\, cm $$</p></div>'
        html += _build_verification_block_html("Verificação da Flecha", res_flecha['flecha_max'], "\\delta_{max}", res_flecha['flecha_limite'], "\\delta_{lim}", res_flecha['eficiencia'], res_flecha['status'], "cm")
    return html

def _add_verification_details(title, details_dict):
    html = f"<h4>{title}</h4><div class='formula-block'>"
    for key, value in details_dict.items():
        if isinstance(value, dict) and 'formula' in value:
            formula_valores = value['formula']
            for var, val_num in value.get('valores', {}).items(): formula_valores = formula_valores.replace(var, f"\\mathbf{{{val_num:.2f}}}")
            html += f'<h5>{value["desc"]}</h5><p class="formula">$$ {value["formula"]} $$</p><p class="formula">$$ {formula_valores} = \\mathbf{{{value["valor"]:.2f} {value.get("unidade", "")}}} $$</p><p class="ref-norma">{value.get("ref", "")}</p>'
    final_resistance = details_dict.get('Mrdx', details_dict.get('Vrd', 0))
    unit = 'kNm' if 'Mrdx' in details_dict else 'kN'
    if unit == 'kNm': final_resistance /= 100
    html += f"<p class='final-result'>{title.split('(')[0].strip()} = {final_resistance:.2f} {unit}</p></div>"
    return html

def _calcular_mrdx_flt(props,Lb,Cb,fy):
    Zx,ry,Iy,Cw,J,Wx=props['Zx'],props['ry'],props['Iy'],props['Cw'],props['J'],props['Wx']; Mp=Zx*fy; lambda_val=Lb/ry if ry>0 else float('inf'); lambda_p=Config.FATOR_LAMBDA_P_FLT*math.sqrt(Config.E_ACO/fy); d={'Mrdx':0};d['Mp']={'desc':'Momento de Plastificação','formula':'M_p=Z_x \\cdot f_y','valores':{'Z_x':Zx,'f_y':fy},'valor':Mp,'unidade':'kN.cm'};d['lambda']={'desc':'Índice de Esbeltez','formula':'\\lambda = \\frac{L_b}{r_y}','valores':{'L_b':Lb,'r_y':ry},'valor':lambda_val};d['lambda_p']={'desc':'Esbeltez Limite','formula':'\\lambda_p = 1.76\\sqrt{\\frac{E}{f_y}}','valores':{'E':Config.E_ACO,'f_y':fy},'valor':lambda_p}
    if lambda_val<=lambda_p:d['Mrdx']=Mp/Config.GAMMA_A1
    else:
        Mr=(fy-Config.FATOR_SIGMA_R*fy)*Wx; beta1=((fy-Config.FATOR_SIGMA_R*fy)*Wx)/(Config.E_ACO*J) if Config.E_ACO*J!=0 else 0; lambda_r=float('inf')
        if ry>0 and beta1>0 and J>0 and Cw>0 and Iy>0: t1=1+(27*Cw*(beta1**2)/Iy); t2=1+math.sqrt(t1) if t1>=0 else 1; lambda_r=(1.38*math.sqrt(Iy*J)/(ry*beta1*J))*math.sqrt(t2)
        if lambda_val<=lambda_r: Mcalc=(Cb/Config.GAMMA_A1)*(Mp-((Mp-Mr)*((lambda_val-lambda_p)/(lambda_r-lambda_p)))); d['Mrdx']=min(Mcalc,Mp/Config.GAMMA_A1)
        else: Mcr=0; d['Mrdx']=Mcr/Config.GAMMA_A1
    return d

def _calcular_mrdx_flm(props,fy):
    bf,tf,Zx,Wx=props['bf'],props['tf'],props['Zx'],props['Wx']; Mp=Zx*fy; lambda_val=(bf/2)/tf if tf>0 else float('inf'); lambda_p=Config.FATOR_LAMBDA_P_FLM*math.sqrt(Config.E_ACO/fy); d={'Mrdx':0};d['lambda']={'desc':'Esbeltez da Mesa','formula':'\\lambda=\\frac{b_f/2}{t_f}','valores':{'b_f':bf,'t_f':tf},'valor':lambda_val};d['lambda_p']={'desc':'Esbeltez Limite','formula':'\\lambda_p=0.38\\sqrt{\\frac{E}{f_y}}','valores':{'E':Config.E_ACO,'f_y':fy},'valor':lambda_p}
    if lambda_val<=lambda_p: d['Mrdx']=Mp/Config.GAMMA_A1
    else: lambda_r=Config.FATOR_LAMBDA_R_FLM_LAMINADO*math.sqrt(Config.E_ACO/(fy-Config.FATOR_SIGMA_R*fy)) if(fy-Config.FATOR_SIGMA_R*fy)>0 else float('inf'); Mr=(fy-Config.FATOR_SIGMA_R*fy)*Wx
    if lambda_val<=lambda_r: d['Mrdx']=(1/Config.GAMMA_A1)*(Mp-((Mp-Mr)*((lambda_val-lambda_p)/(lambda_r-lambda_p))))
    else: Mcr=(0.69*Config.E_ACO*Wx)/(lambda_val**2) if lambda_val>0 else 0; d['Mrdx']=Mcr/Config.GAMMA_A1
    return d

def _calcular_mrdx_fla(props,fy):
    h,tw,Zx,Wx=props['h'],props['tw'],props['Zx'],props['Wx']; Mp=Zx*fy; lambda_val=h/tw if tw>0 else float('inf'); lambda_p=Config.FATOR_LAMBDA_P_FLA*math.sqrt(Config.E_ACO/fy); d={'Mrdx':0};d['lambda']={'desc':'Esbeltez da Alma','formula':'\\lambda=\\frac{h}{t_w}','valores':{'h':h,'t_w':tw},'valor':lambda_val};d['lambda_p']={'desc':'Esbeltez Limite','formula':'\\lambda_p=3.76\\sqrt{\\frac{E}{f_y}}','valores':{'E':Config.E_ACO,'f_y':fy},'valor':lambda_p}
    if lambda_val<=lambda_p: d['Mrdx']=Mp/Config.GAMMA_A1
    else: lambda_r=Config.FATOR_LAMBDA_R_FLA*math.sqrt(Config.E_ACO/fy); Mr=fy*Wx
    if lambda_val<=lambda_r: d['Mrdx']=(1/Config.GAMMA_A1)*(Mp-((Mp-Mr)*((lambda_val-lambda_p)/(lambda_r-lambda_p))))
    else: d['Mrdx']=0
    return d

def _calcular_vrd(props,fy):
    d_prop,h,tw=props['d'],props['h'],props['tw']; Vpl=Config.FATOR_VP*d_prop*tw*fy; lambda_val=h/tw if tw>0 else float('inf'); kv=Config.KV_ALMA_SEM_ENRIJECEDORES; lambda_p=Config.FATOR_LAMBDA_P_VRD*math.sqrt((kv*Config.E_ACO)/fy); d={'Vrd':0};d['lambda']={'desc':'Esbeltez da Alma (Cisalhamento)','formula':'\\lambda = \\frac{h}{t_w}','valores':{'h':h,'t_w':tw},'valor':lambda_val};d['lambda_p']={'desc':'Esbeltez Limite','formula':'\\lambda_p = 1.10 \\sqrt{\\frac{k_v E}{f_y}}','valores':{'k_v':kv,'E':Config.E_ACO,'f_y':fy},'valor':lambda_p}
    if lambda_val<=lambda_p: d['Vrd']=Vpl/Config.GAMMA_A1
    else: lambda_r=Config.FATOR_LAMBDA_R_VRD*math.sqrt((kv*Config.E_ACO)/fy)
    if lambda_val<=lambda_r: d['Vrd']=(lambda_p/lambda_val)*(Vpl/Config.GAMMA_A1) if lambda_val>0 else 0
    else: d['Vrd']=(Config.FATOR_VRD_ELASTICO*(lambda_p/lambda_val)**2)*(Vpl/Config.GAMMA_A1) if lambda_val>0 else 0
    return d

if __name__ == '__main__':
    main()