import streamlit as st
import pandas as pd
import math
import base64

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

# ==============================================================================
# 2. FUNÇÕES DE CÁLCULO DE ENGENHARIA
# ==============================================================================

def calcular_esforcos_viga(tipo_viga, L_cm, q_kn_cm=0, p_load=None):
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
            msd_q = (q_kn_cm * L**2) / 12 # Momento no engaste
            vsd_q = (q_kn_cm * L) / 2
        elif tipo_viga == 'Engastada e Apoiada':
            msd_q = (q_kn_cm * L**2) / 8
            vsd_q = (5 * q_kn_cm * L) / 8
            
    # Parte da carga pontual (P)
    if p_load:
        P, x = p_load # P em kN, x em cm
        a = x
        b = L - a
        if tipo_viga == 'Bi-apoiada':
            msd_p = (P * a * b) / L
            vsd_p = max((P * b) / L, (P * a) / L)
        elif tipo_viga == 'Engastada e Livre (Balanço)':
            msd_p = P * a # Momento no engaste
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
# 3. FUNÇÕES DE GERAÇÃO DO MEMORIAL DE CÁLCULO (NATIVO STREAMLIT)
# ==============================================================================

def _build_verification_block_native(title, solicitante, s_symbol, resistente, r_symbol, eficiencia, status, unit):
    """Renderiza um bloco de verificação usando st.latex() e st.info/success/error."""
    status_emoji = "✅" if status == "APROVADO" else "❌"
    comp_symbol = "≤" if status == "APROVADO" else ">"
    
    st.subheader(title)
    
    # Usando st.latex() para fórmulas
    st.latex(f"{s_symbol} = {solicitante:.2f} \\, {unit}")
    st.latex(f"{r_symbol} = {resistente:.2f} \\, {unit}")
    st.latex(f"\\text{{Verificação: }} {s_symbol} {comp_symbol} {r_symbol}")
    st.latex(f"\\text{{Eficiência}} = \\frac{{{s_symbol}}}{{{r_symbol}}} = \\frac{{{solicitante:.2f}}}{{{resistente:.2f}}} = {eficiencia:.1f}\\%")
    
    if status == "APROVADO":
        st.success(f"{status_emoji} **Status: APROVADO**")
    else:
        st.error(f"{status_emoji} **Status: REPROVADO**")
    st.divider()

def _add_verification_details_native(title, details_dict):
    """Renderiza os detalhes de uma verificação usando componentes nativos."""
    for key, value in details_dict.items():
        if isinstance(value, dict) and 'formula' in value:
            st.write(f"**{value['desc']}**")
            
            # Renderiza a fórmula usando st.latex()
            st.latex(value['formula'])
            
            # Mostra os valores substituídos
            formula_com_valores = value['formula']
            for var, val_num in value['valores'].items():
                formula_com_valores = formula_com_valores.replace(var, f"{val_num:.2f}")
            
            st.latex(f"{formula_com_valores} = {value['valor']:.2f} {value.get('unidade', '')}")
            
            # Referência da norma
            if value.get('ref'):
                st.caption(f"*Referência: {value['ref']}*")
            
            st.divider()
    
    # Resultado final
    final_resistance = details_dict.get('Mrdx', details_dict.get('Vrd', 0))
    unit = 'kNm' if 'Mrdx' in details_dict else 'kN'
    if unit == 'kNm':
        final_resistance /= 100
    
    st.info(f"**Resultado da Resistência: {final_resistance:.2f} {unit}**")

def build_summary_table_native(Msd, Vsd, res_flexao, res_cisalhamento, res_flecha):
    """Tabela de resumo usando componentes nativos do Streamlit"""
    
    # Dados da tabela
    verificacoes = [
        ('Flexão (M) - ELU', f"{Msd/100:.2f} kNm", f"{res_flexao['Mrd']/100:.2f} kNm", res_flexao['eficiencia'], res_flexao['status']),
        ('Cisalhamento (V) - ELU', f"{Vsd:.2f} kN", f"{res_cisalhamento['Vrd']:.2f} kN", res_cisalhamento['eficiencia'], res_cisalhamento['status']),
        ('Flecha (δ) - ELS',
         f"{res_flecha['flecha_max']:.2f} cm" if res_flecha['status'] != "N/A" else "N/A",
         f"≤ {res_flecha['flecha_limite']:.2f} cm" if res_flecha['status'] != "N/A" else "N/A",
         res_flecha['eficiencia'], res_flecha['status'])
    ]
    
    # Criar DataFrame para exibição
    df_resumo = pd.DataFrame(verificacoes, columns=['Verificação', 'Solicitante/Atuante', 'Resistência/Limite', 'Eficiência (%)', 'Status'])
    
    # Função para colorir as células baseado no status
    def color_status(val):
        if val == "APROVADO":
            return 'background-color: #d4edda; color: #155724'
        elif val == "REPROVADO":
            return 'background-color: #f8d7da; color: #721c24'
        else:
            return ''
    
    # Aplicar estilo e exibir
    styled_df = df_resumo.style.applymap(color_status, subset=['Status'])
    st.dataframe(styled_df, use_container_width=True)
    
    # Nota sobre interação
    if res_flexao.get('nota_interacao'):
        st.info(f"**Nota sobre Interação M-V:** {res_flexao['nota_interacao']}")

def build_step_by_step_native(L, Msd, Vsd, res_flexao, res_cisalhamento, res_flecha, res_flt, res_flm, res_fla, res_vrd, input_mode):
    """Renderiza o passo a passo completo usando componentes nativos do Streamlit."""
    
    st.header("2. Esforços de Cálculo")
    col1, col2 = st.columns(2)
    with col1:
        st.latex(f"M_{{sd}} = {Msd/100:.2f} \\, kNm")
    with col2:
        st.latex(f"V_{{sd}} = {Vsd:.2f} \\, kN")
    
    st.header("3. Verificações de Resistência (ELU)")
    
    # 3.1 Flexão
    st.subheader("3.1 Cálculo da Resistência à Flexão (Mrd)")
    
    # FLT
    with st.expander("Flambagem Lateral com Torção (FLT)", expanded=True):
        _add_verification_details_native("FLT", res_flt)
    
    # FLM 
    with st.expander("Flambagem Local da Mesa (FLM)", expanded=True):
        _add_verification_details_native("FLM", res_flm)
    
    # FLA
    with st.expander("Flambagem Local da Alma (FLA)", expanded=True):
        _add_verification_details_native("FLA", res_fla)
    
    # Verificação final de flexão
    _build_verification_block_native(
        "Verificação Final à Flexão", 
        Msd/100, "M_{sd}", 
        res_flexao['Mrd']/100, "M_{rd}", 
        res_flexao['eficiencia'], res_flexao['status'], "kNm"
    )
    
    # 3.2 Cisalhamento
    st.subheader("3.2 Cálculo da Resistência ao Cisalhamento (Vrd)")
    with st.expander("Força Cortante (VRd)", expanded=True):
        _add_verification_details_native("VRd", res_vrd)
    
    _build_verification_block_native(
        "Verificação ao Cisalhamento", 
        Vsd, "V_{sd}", 
        res_cisalhamento['Vrd'], "V_{rd}", 
        res_cisalhamento['eficiencia'], res_cisalhamento['status'], "kN"
    )
    
    # 4. ELS (se aplicável)
    if input_mode == "Calcular a partir de Cargas na Viga":
        st.header("4. Verificação de Serviço (ELS)")
        
        col1, col2 = st.columns(2)
        with col1:
            st.latex(f"\\delta_{{max}} = {res_flecha['flecha_max']:.2f} \\, cm")
        with col2:
            st.latex(f"\\delta_{{lim}} = \\frac{{L}}{{{Config.LIMITE_FLECHA_TOTAL}}} = \\frac{{{L:.2f}}}{{{Config.LIMITE_FLECHA_TOTAL}}} = {res_flecha['flecha_limite']:.2f} \\, cm")
        
        _build_verification_block_native(
            "Verificação da Flecha", 
            res_flecha['flecha_max'], "\\delta_{max}", 
            res_flecha['flecha_limite'], "\\delta_{lim}", 
            res_flecha['eficiencia'], res_flecha['status'], "cm"
        )
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
    st.title("🏛️ Calculadora Estrutural Versátil")
    st.caption(f"Utilizando a norma: {Config.NOME_NORMA}")

    # CARREGAMENTO AUTOMÁTICO DOS DADOS
    all_sheets = load_data_from_local_file()

    # Para a aplicação se os dados não puderem ser carregados
    if not all_sheets:
        st.stop()

    # --- ENTRADA DE DADOS NA SIDEBAR ---
    with st.sidebar:
        st.header("⚙️ Parâmetros de Entrada")
        
        st.header("1. Modelo da Viga")
        tipo_viga = st.selectbox("Tipo de Viga:", ('Bi-apoiada', 'Engastada e Livre (Balanço)', 'Bi-engastada', 'Engastada e Apoiada'))
        L_cm = st.number_input("Comprimento da Viga (L, cm)", 10.0, value=500.0, step=10.0)

        st.header("2. Modo de Carregamento")
        input_mode = st.radio("Selecione o modo de entrada dos esforços:", ("Calcular a partir de Cargas na Viga", "Inserir Esforços Manualmente"), horizontal=True, label_visibility="collapsed")

        Msd, Vsd, q_servico_kn_cm, p_load_serv = 0, 0, 0, None

        if input_mode == "Calcular a partir de Cargas na Viga":
            with st.container(border=True):
                st.subheader("Carga Distribuída (q)")
                carga_area = st.number_input("Carga Distribuída (serviço, kN/m²)", 0.0, value=4.0, step=0.5)
                larg_inf = st.number_input("Largura de Influência (m)", 0.0, value=5.0, step=0.5)
                
                st.subheader("Carga Pontual (P)")
                add_p_load = st.checkbox("Adicionar Carga Pontual (ex: parede)")
                if add_p_load:
                    p_serv_kn = st.number_input("Valor da Carga P (serviço, kN)", min_value=0.0, value=10.0)
                    p_pos_cm = st.number_input("Posição da Carga P (x, cm do apoio esquerdo)", min_value=0.0, max_value=L_cm, value=L_cm/2)
                    p_load_serv = (p_serv_kn, p_pos_cm)

                gamma_f = st.number_input("Coeficiente de Majoração de Cargas (γf)", 1.0, value=1.4, step=0.1)

            q_servico_kn_cm = (carga_area * larg_inf) / 100.0
            q_ult_kn_cm = q_servico_kn_cm * gamma_f
            p_load_ult = (p_load_serv[0] * gamma_f, p_load_serv[1]) if p_load_serv else None
            
            Msd, Vsd = calcular_esforcos_viga(tipo_viga, L_cm, q_ult_kn_cm, p_load_ult)

        else: # Inserir Esforços Manualmente
             with st.container(border=True):
                st.warning("No modo manual, a verificação de flecha (ELS) não é realizada.")
                msd_input = st.number_input("Momento Solicitante de Cálculo (Msd, kNm)", min_value=0.0, value=100.0)
                Msd = msd_input * 100 # Convertendo para kN.cm
                Vsd = st.number_input("Força Cortante Solicitante de Cálculo (Vsd, kN)", min_value=0.0, value=50.0)

        st.header("3. Parâmetros Gerais do Aço")
        fy_aco = st.number_input("Tensão de Escoamento (fy, kN/cm²)", 20.0, 50.0, 34.5, 0.5)
        Lb_projeto = st.number_input("Comprimento Destravado (Lb, cm)", 10.0, value=L_cm, step=10.0)
        Cb_projeto = st.number_input("Fator de Modificação (Cb)", 1.0, 3.0, 1.10)
        
        st.header("4. Modo de Análise")
        analysis_mode = st.radio("Selecione o modo de análise:", ("Análise em Lote com Otimização", "Memorial Detalhado de um Perfil"), horizontal=True, label_visibility="collapsed")
    
    # --- Lógica de execução da análise (agora fora do 'with st.sidebar:') ---
    
    display_names = [PROFILE_TYPE_MAP.get(name, name) for name in all_sheets.keys()]
    reverse_name_map = {v: k for k, v in PROFILE_TYPE_MAP.items()}

    if analysis_mode == "Memorial Detalhado de um Perfil":
        st.header("🔍 Memorial de Cálculo Detalhado")
        selected_display_name = st.selectbox("Selecione o Tipo de Perfil:", display_names)
        sheet_name = reverse_name_map.get(selected_display_name, selected_display_name)
        df_selecionado = all_sheets[sheet_name]
        perfil_selecionado_nome = st.selectbox("Selecione o Perfil Específico:", df_selecionado['Bitola (mm x kg/m)'])
        if st.button("Gerar Memorial Completo", type="primary", use_container_width=True):
            run_detailed_analysis(df_selecionado, perfil_selecionado_nome, selected_display_name, fy_aco, Lb_projeto, Cb_projeto, L_cm, Msd, Vsd, q_servico_kn_cm, p_load_serv, tipo_viga, input_mode)

    elif analysis_mode == "Análise em Lote com Otimização":
        st.header("📊 Pré-dimensionamento e Análise por Categoria")
        st.info("Analisa todos os perfis e organiza os resultados em abas por tipo, destacando a opção mais leve de cada categoria.")
        if st.button("Iniciar Análise Otimizada", type="primary", use_container_width=True):
            run_batch_analysis(all_sheets, fy_aco, Lb_projeto, Cb_projeto, L_cm, Msd, Vsd, q_servico_kn_cm, p_load_serv, tipo_viga, input_mode)

# ==============================================================================
# 5. FUNÇÕES DE ORQUESTRAÇÃO E ANÁLISE
# ==============================================================================

def run_detailed_analysis(df, perfil_nome, perfil_tipo_display, fy, Lb, Cb, L, Msd, Vsd, q_serv_kn_cm, p_serv_load, tipo_viga, input_mode):
    with st.spinner(f"Gerando análise completa para {perfil_nome}..."):
        try:
            perfil_series = df[df['Bitola (mm x kg/m)'] == perfil_nome].iloc[0]
            props = get_profile_properties(perfil_series)
            
            # Chama a função de verificação e armazena os resultados
            # A função perform_all_checks foi corrigida para retornar os valores de res_flx, res_cis, etc.
            res_flexao_det, res_cis_det, res_flecha_det, res_flt_det, res_flm_det, res_fla_det, res_vrd_det = perform_all_checks(props, fy, Lb, Cb, L, Msd, Vsd, q_serv_kn_cm, p_serv_load, tipo_viga, input_mode)
            
            st.success(f"Análise concluída para {perfil_nome}!")
            
            # Cabeçalho
            st.title("Memorial de Cálculo Estrutural")
            st.subheader(f"Perfil Metálico: {perfil_nome} ({perfil_tipo_display})")
            st.caption(f"Cálculos baseados na norma: **{Config.NOME_NORMA}**")
            
            # 1. Resumo
            st.header("1. Resumo Final das Verificações")
            build_summary_table_native(Msd, Vsd, res_flexao_det, res_cis_det, res_flecha_det)
            
            # 2. Detalhamento
            st.header("2. Detalhamento dos Cálculos")
            build_step_by_step_native(L, Msd, Vsd, res_flexao_det, res_cis_det, res_flecha_det, res_flt_det, res_flm_det, res_fla_det, res_vrd_det, input_mode)

        except (ValueError, KeyError) as e: st.error(f"❌ Erro nos Dados de Entrada: {e}")
        except Exception as e: st.error(f"❌ Ocorreu um erro inesperado: {e}")

def run_batch_analysis(all_sheets, fy, Lb, Cb, L, Msd, Vsd, q_serv_kn_cm, p_serv_load, tipo_viga, input_mode):
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
                    res_flexao, res_cis, res_flecha, _, _, _, _ = perform_all_checks(props, fy, Lb, Cb, L, Msd, Vsd, q_servico_kn_cm, p_serv_load, tipo_viga, input_mode)
                    status_geral = "APROVADO" if max(res_flexao['ef_flt'], res_flexao['ef_flm'], res_flexao['ef_fla'], res_cis['eficiencia'], res_flecha['eficiencia']) <= 100.1 else "REPROVADO"
                    all_results.append({'Tipo': sheet_name, 'Perfil': row['Bitola (mm x kg/m)'], 'Peso (kg/m)': props.get('Peso', 0), 'Status': status_geral, 'Ef. FLT (%)': res_flexao['ef_flt'], 'Ef. FLM (%)': res_flexao['ef_flm'], 'Ef. FLA (%)': res_flexao['ef_fla'], 'Ef. Cisalhamento (%)': res_cis['eficiencia'], 'Ef. Flecha (%)': res_flecha['eficiencia']})
                except (ValueError, KeyError): continue
    progress_bar.empty()
    if not all_results:
        st.error("Não foi possível analisar nenhum perfil.")
        return
    df_all_results = pd.DataFrame(all_results)
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
        return df.style.applymap(color_efficiency, subset=efficiency_cols).format("{:.1f}", subset=efficiency_cols)
    for i, sheet_name in enumerate(all_sheets.keys()):
        with tabs[i]:
            df_type = df_all_results[df_all_results['Tipo'] == sheet_name].drop(columns=['Tipo'])
            if df_type.empty:
                st.write("Nenhum perfil desta categoria foi analisado.")
                continue
            aprovados = df_type[df_type['Status'] == 'APROVADO'].copy()
            reprovados = df_type[df_type['Status'] == 'REPROVADO'].copy()
            if not aprovados.empty:
                aprovados.sort_values(by='Peso (kg/m)', inplace=True)
                st.subheader("🏆 Perfil Mais Leve Aprovado (Otimizado)")
                st.dataframe(style_dataframe(aprovados.head(1)), use_container_width=True)
                with st.expander("Ver todos os perfis aprovados desta categoria"):
                    st.dataframe(style_dataframe(aprovados), use_container_width=True)
            else: st.info("Nenhum perfil desta categoria foi aprovado.")
            if not reprovados.empty:
                with st.expander("Ver perfis reprovados desta categoria"):
                    st.dataframe(style_dataframe(reprovados), use_container_width=True)

def perform_all_checks(props, fy, Lb, Cb, L, Msd, Vsd, q_servico_kn_cm, p_serv_load, tipo_viga, input_mode, detalhado=False):
    res_flt = _calcular_mrdx_flt(props, Lb, Cb, fy)
    res_flm = _calcular_mrdx_flm(props, fy)
    res_fla = _calcular_mrdx_fla(props, fy)
    res_vrd = _calcular_vrd(props, fy)
    
    Vrd = res_vrd['Vrd']
    Mrd_final = min(res_flt['Mrdx'], res_flm['Mrdx'], res_fla['Mrdx'])
    
    nota_interacao = "Vsd ≤ 0.5*Vrd. Interação desconsiderada."
    if Vrd > 0 and Vsd > 0.5 * Vrd: nota_interacao = "Vsd > 0.5*Vrd. Interação deve ser considerada."
    
    ef_geral = (Msd / Mrd_final) * 100 if Mrd_final > 0 else float('inf')
    ef_flt = (Msd / res_flt['Mrdx']) * 100 if res_flt['Mrdx'] > 0 else float('inf')
    ef_flm = (Msd / res_flm['Mrdx']) * 100 if res_flm['Mrdx'] > 0 else float('inf')
    ef_fla = (Msd / res_fla['Mrdx']) * 100 if res_fla['Mrdx'] > 0 else float('inf')
    status_flexao = "APROVADO" if ef_geral <= 100.1 else "REPROVADO"
    res_flexao = {'Mrd': Mrd_final, 'eficiencia': ef_geral, 'status': status_flexao, 'ef_flt': ef_flt, 'ef_flm': ef_flm, 'ef_fla': ef_fla, 'nota_interacao': nota_interacao}
    
    eficiencia_cisalhamento = (Vsd / Vrd) * 100 if Vrd > 0 else float('inf')
    status_cisalhamento = "APROVADO" if eficiencia_cisalhamento <= 100.1 else "REPROVADO"
    res_cisalhamento = {'Vrd': Vrd, 'eficiencia': eficiencia_cisalhamento, 'status': status_cisalhamento}

    flecha_max, flecha_limite, eficiencia_flecha, status_flecha = 0, 0, 0, "N/A"
    if input_mode == "Calcular a partir de Cargas na Viga":
        flecha_max = calcular_flecha_maxima(tipo_viga, L, Config.E_ACO, props['Ix'], q_servico_kn_cm, p_serv_load)
        flecha_limite = L / Config.LIMITE_FLECHA_TOTAL if L > 0 else 0
        eficiencia_flecha = (flecha_max / flecha_limite) * 100 if flecha_limite > 0 else float('inf')
        status_flecha = "APROVADO" if eficiencia_flecha <= 100.1 else "REPROVADO"
    res_flecha = {'flecha_max': flecha_max, 'flecha_limite': flecha_limite, 'eficiencia': eficiencia_flecha, 'status': status_flecha, 'Ix': props['Ix']}
    
    return res_flexao, res_cisalhamento, res_flecha, res_flt, res_flm, res_fla, res_vrd

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
        detalhes['lambda_r'] = {'desc': 'Esbeltez Limite (Inelástica)', 'symbol': '\\lambda_r', 'formula': '\\lambda_r = 1.38 \\sqrt{\\frac{I_y \\cdot J}{r_y^2 \\cdot J^2 \\cdot \\beta_1^2}} \\sqrt{1 + \\sqrt{1 + \\frac{27 \\cdot C_w \\cdot \\beta_1^2}{I_y}}}', 'valores': {'I_y': Iy, 'J': J, 'r_y': ry, '\\beta_1': beta1, 'C_w': Cw}, 'valor': lambda_r, 'ref': 'Eq. F-3'}
        if lambda_val <= lambda_r:
            termo_interp = (Mp - Mr) * ((lambda_val - lambda_p) / (lambda_r - lambda_p))
            Mrdx_calc = (Cb / Config.GAMMA_A1) * (Mp - termo_interp)
            Mrdx = min(Mrdx_calc, Mp / Config.GAMMA_A1)
            detalhes['Mrdx_calc'] = {'desc': 'Momento Resistente (Inelástico)', 'symbol': 'M_{rd}', 'formula': 'M_{rd} = \\frac{C_b}{\\gamma_{a1}} [M_p - (M_p - M_r) (\\frac{\\lambda - \\lambda_p}{\\lambda_r - \\lambda_p})] \\le \\frac{M_p}{\\gamma_{a1}}', 'valores': {'C_b': Cb, 'M_p': Mp, 'M_r': Mr, '\\lambda': lambda_val, '\\lambda_p': lambda_p, '\\lambda_r': lambda_r}, 'valor': Mrdx, 'unidade': 'kN.cm', 'ref': 'Eq. F-1'}
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
            detalhes['Mrdx_calc'] = {'desc': 'Momento Resistente (Mesa Semicompacta)', 'symbol': 'M_{rd}', 'formula': 'M_{rd} = \\frac{1}{\\gamma_{a1}} [M_p - (M_p - M_r) (\\frac{\\lambda - \\lambda_p}{\\lambda_r - \\lambda_p})]', 'valores': {'M_p': Mp, 'M_r': Mr, '\\lambda': lambda_val, '\\lambda_p': lambda_p, '\\lambda_r': lambda_r}, 'valor': Mrdx, 'unidade': 'kN.cm'}
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
            detalhes['Mrdx_calc'] = {'desc': 'Momento Resistente (Alma Semicompacta)', 'symbol': 'M_{rd}', 'formula': 'M_{rd} = \\frac{1}{\\gamma_{a1}} [M_p - (M_p - M_r) (\\frac{\\lambda - \\lambda_p}{\\lambda_r - \\lambda_p})]', 'valores': {'M_p': Mp, 'M_r': Mr, '\\lambda': lambda_val, '\\lambda_p': lambda_p, '\\lambda_r': lambda_r}, 'valor': Mrdx, 'unidade': 'kN.cm'}
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
