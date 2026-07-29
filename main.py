import streamlit as st
import pandas as pd
import math
import plotly.graph_objects as go
from datetime import datetime
import io
import openpyxl
from openpyxl.styles import PatternFill
import hashlib
import pytz
from pathlib import Path
from functools import lru_cache
from calculos_nbr8800_2024 import (
    NORMA,
    analyze_beam,
    calculate_cb as calculate_cb_nbr2024,
    combine_els,
    combine_elu_normal,
    deflection_limit,
    flexural_strength_i,
    local_compression_strength,
    overall_status,
    shear_strength_i,
    validate_material,
)
from memorial_nbr8800_2024 import build_memorial_details
from perfis_metalicos.audit import ExternalEvidence
from perfis_metalicos.catalog import (
    CatalogValidationStatus,
    validate_catalog_workbook,
)
from perfis_metalicos.checks import (
    LimitStateApplicability,
    LocalizedForceCase,
    LocalizedLimitState,
    localized_force_limit_state_matrix,
)
from perfis_metalicos.domain import APPROVED_SCOPE_TEXT
# ==============================================================================
# 1. CONFIGURAÇÕES E CONSTANTES GLOBAIS APRIMORADAS
# ==============================================================================

class Config:
    NOME_NORMA = f'{NORMA} | Er1:2025: NORMATIVE_REVIEW_REQUIRED'

PROFILE_TYPE_MAP = {
    "Laminados": "Perfis Laminados",
    "CS": "Perfis Compactos Soldados",
    "CVS": "Perfis CVS Soldados",
    "VS": "Perfis Soldados"
}
@lru_cache(maxsize=1)
def _catalog_validation_report():
    root = Path(__file__).resolve().parent
    return validate_catalog_workbook(
        root / "perfis.xlsx",
        root / "catalog" / "catalog_manifest.yaml",
    )

PROFILE_FABRICATION_MAP = {
    "Laminados": "Laminado",
    "CS": "Soldado",
    "CVS": "Soldado",
    "VS": "Soldado",
}


def compact_number(value, max_decimals=3):
    """Formata valores exibidos sem zeros decimais que não agregam precisão."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "N/A"
    if not math.isfinite(number):
        return "N/A"
    number = round(number, max_decimals)
    if number == 0:
        number = 0.0
    if max_decimals <= 0:
        return f"{number:.0f}"
    return f"{number:.{max_decimals}f}".rstrip("0").rstrip(".")


HTML_TEMPLATE_CSS_PRO = """
<style>
    /* Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Poppins:wght@600;700;800&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&display=swap');

    /* --- Paleta de Cores Definitiva HQ Engenharia --- */
    :root {
        --background: #0f172a;
        --surface: #1e2b3b;
        --border: #334155;
        --text-display: #ffffff;
        --text-primary: #e2e8f0;
        --text-secondary: #94a3b8;
        --accent-gold: #fbbd24;
        --accent-amber: #f59e0b;
        --button-text: #1e293b;
    }

    /* --- Base e Overrides Globais do Streamlit --- */
    body {
        font-family: 'Inter', sans-serif;
        background-color: var(--background);
        color: var(--text-primary);
    }
    .stApp {
        background-color: var(--background);
    }
    [data-testid="stMain"] {
        width: 100% !important;
        min-width: 0 !important;
    }
    [data-testid="stMainBlockContainer"],
    [data-testid="stMain"] .block-container,
    section.main .block-container,
    .block-container {
        box-sizing: border-box !important;
        width: 100% !important;
        max-width: 1600px !important;
        margin-right: auto !important;
        margin-left: auto !important;
        padding: clamp(1rem, 2.5vw, 2rem) clamp(.85rem, 3.5vw, 3rem) 3rem !important;
    }

    /* --- Títulos e Textos Genéricos --- */
    h1, h2 {
        font-family: 'Poppins', sans-serif;
        color: var(--text-display);
        font-weight: 700;
    }
    /* Força a cor dos títulos de seção (H3) para dourado */
    h3 {
        font-family: 'Poppins', sans-serif;
        color: var(--accent-gold) !important;
        font-weight: 700;
    }
    /* Garante que os títulos H3 dentro do markdown também sejam dourados */
    [data-testid="stMarkdownContainer"] h3 {
        color: var(--accent-gold) !important;
    }
    /* Estiliza o texto "Fator Cb..." para ser branco e legível */
    .metric-footer {
        color: var(--text-primary) !important;
        font-family: 'Inter', sans-serif;
        font-size: 0.9rem;
        text-align: center;
        margin-top: -0.5rem;
        margin-bottom: 2rem;
    }

    /* --- BARRA LATERAL (SIDEBAR) --- */
    [data-testid="stSidebar"] {
        background-color: var(--surface) !important;
        border-right: 1px solid var(--border);
    }
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: var(--accent-gold);
    }
    
    /* RÓTULOS (LABELS) */
    label, [data-testid="stMetricLabel"] {
        color: var(--text-secondary) !important;
        font-weight: 600;
        font-family: 'Inter', sans-serif;
    }
    .stRadio > label, .stCheckbox > label {
        color: var(--text-secondary) !important;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    .stRadio [data-testid="stMarkdownContainer"] p, .stCheckbox [data-testid="stMarkdownContainer"] p {
        color: var(--text-primary);
    }

    /* INPUTS, SELECTBOX, TEXTAREA */
    input, 
    div[data-baseweb="select"] > div,
    textarea {
        background-color: var(--background) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
    }
    .stDateInput input {
        color: var(--text-primary) !important;
    }
    input:focus, 
    div[data-baseweb="select"] > div:focus-within,
    textarea:focus {
        border-color: var(--accent-gold) !important;
        box-shadow: 0 0 0 2px rgba(251, 191, 36, 0.3) !important;
    }
    
    .stSelectbox div[data-baseweb="select"] div,
    .stSelectbox div[data-baseweb="select"] span {
        color: var(--text-primary) !important;
    }
    
    /* --- ST.EXPANDER --- */
    [data-testid="stExpander"] {
        border: none !important;
        box-shadow: none !important;
        background: none !important;
    }
    [data-testid="stExpander"] summary {
        background-color: var(--surface) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
        margin-bottom: 0.5rem;
        padding: 0.75rem 1rem !important;
    }
    [data-testid="stExpander"] summary p {
        color: var(--text-primary) !important;
        font-weight: 600;
        font-size: 1.1rem;
    }
    [data-testid="stExpander"] summary svg {
        fill: var(--text-primary) !important;
    }
    [data-testid="stExpander"] .st-emotion-cache-16txtl3 {
        background-color: var(--surface) !important;
        border: 1px solid var(--border) !important;
        border-top: none !important;
        border-radius: 0 0 8px 8px !important;
        padding: 1rem !important;
        margin-top: -0.5rem;
    }

    /* --- Cabeçalho e Métricas --- */
    .pro-header {
        background: var(--surface); padding: 2.5rem; border-radius: 12px;
        border: 1px solid var(--border); text-align: center; margin-bottom: 2rem;
        box-shadow: 0 8px 30px rgba(0,0,0,0.3);
    }
    .pro-header h1 { font-size: 2.8rem; }
    .pro-header p { color: var(--text-secondary); }
    .gradient-text {
        background: linear-gradient(135deg, #FBBF24 0%, #FDE68A 50%, #D4AF37 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
    }
    /* --- Painel responsivo de parâmetros do projeto --- */
    .project-metrics-shell {
        container-type: inline-size;
        margin: .4rem 0 1.8rem;
    }
    .project-metrics-grid {
        display: grid;
        grid-template-columns: repeat(12, minmax(0, 1fr));
        gap: .85rem;
    }
    .project-metric-card {
        grid-column: span 3;
        min-width: 0;
        min-height: 108px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        background: linear-gradient(145deg, #1e2b3b 0%, #172438 100%);
        border: 1px solid var(--border);
        border-top: 3px solid var(--accent-amber);
        border-radius: 10px;
        padding: .9rem 1rem;
        box-shadow: 0 8px 20px rgba(2, 6, 23, .18);
    }
    .project-metric-label {
        color: var(--text-secondary);
        font-family: 'Inter', sans-serif;
        font-size: .72rem;
        font-weight: 700;
        letter-spacing: .075em;
        line-height: 1.25;
        text-transform: uppercase;
    }
    .project-metric-value {
        color: var(--text-display);
        font-family: 'Poppins', sans-serif;
        font-size: clamp(1.2rem, 2vw, 1.6rem);
        font-weight: 700;
        line-height: 1.15;
        overflow-wrap: anywhere;
        font-variant-numeric: tabular-nums;
    }
    .project-metric-card:nth-child(n + 5) { grid-column: span 4; }
    .project-metric-unit {
        min-height: 1.15em;
        color: var(--text-secondary);
        font-size: .76rem;
        line-height: 1.2;
    }
    .project-metrics-context {
        display: flex;
        flex-wrap: wrap;
        gap: .55rem;
        margin-top: .85rem;
    }
    .project-metrics-context span {
        flex: 1 1 180px;
        color: var(--text-primary);
        background: rgba(30, 43, 59, .72);
        border: 1px solid var(--border);
        border-radius: 999px;
        padding: .48rem .8rem;
        font-size: .78rem;
        line-height: 1.25;
        text-align: center;
    }
    .project-metrics-context strong {
        color: var(--accent-gold);
        margin-right: .3rem;
    }
    @container (max-width: 760px) {
        .project-metrics-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
        .project-metric-card,
        .project-metric-card:nth-child(n + 5) { grid-column: span 1; }
        .project-metric-card:last-child { grid-column: 1 / -1; }
    }
    @container (max-width: 390px) {
        .project-metrics-grid { grid-template-columns: 1fr; }
        .project-metric-card,
        .project-metric-card:nth-child(n + 5),
        .project-metric-card:last-child { grid-column: 1; }
        .project-metrics-context span { flex-basis: 100%; }
    }

    /* --- Adaptação global para tablet e smartphone --- */
    @media (max-width: 768px) {
        [data-testid="stMainBlockContainer"],
        [data-testid="stMain"] .block-container,
        section.main .block-container,
        .block-container {
            max-width: 100% !important;
            padding: .75rem .75rem 2rem !important;
        }
        [data-testid="stSidebar"] {
            width: min(88vw, 21rem) !important;
            min-width: min(88vw, 21rem) !important;
        }
        [data-testid="stHorizontalBlock"] {
            flex-direction: column !important;
            gap: .75rem !important;
        }
        [data-testid="column"] {
            width: 100% !important;
            min-width: 100% !important;
            flex: 1 1 100% !important;
        }
        .pro-header {
            padding: 1.25rem .9rem;
            margin-bottom: 1.25rem;
            border-radius: 10px;
        }
        .pro-header h1 {
            font-size: clamp(1.45rem, 7vw, 2rem);
            line-height: 1.18;
            overflow-wrap: anywhere;
        }
        .pro-header p { font-size: .88rem; line-height: 1.45; }
        h3, [data-testid="stMarkdownContainer"] h3 {
            font-size: clamp(1.15rem, 5.5vw, 1.5rem) !important;
        }
        .stButton > button, .stDownloadButton > button {
            min-height: 2.8rem;
            white-space: normal;
        }
        .stTabs [data-baseweb="tab-list"] {
            overflow-x: auto;
        }
        .stTabs [data-baseweb="tab-list"] button {
            flex: 0 0 auto;
            padding: .75rem;
        }
    }

    /* --- Botões --- */
    .stButton > button, .stDownloadButton > button {
        padding: 12px; border-radius: 8px; font-weight: bold; font-size: 1rem;
        font-family: 'Poppins', sans-serif; border: 2px solid var(--accent-gold);
        transition: all 0.2s ease-in-out;
    }
    .stButton > button[kind="primary"], .stDownloadButton > button {
        background-color: var(--accent-gold); color: var(--button-text) !important;
    }
    .stButton > button[kind="primary"]:hover, .stDownloadButton > button:hover {
        background-color: #ffd042; border-color: #ffd042; transform: translateY(-2px);
    }
    .stButton > button[kind="secondary"] {
        background-color: transparent; color: var(--accent-gold) !important;
    }
    .stButton > button[kind="secondary"]:hover {
        background-color: var(--accent-gold); color: var(--button-text) !important;
    }

    /* --- Abas (Tabs) --- */
    .stTabs [data-baseweb="tab-list"] button {
        color: var(--text-secondary); padding: 1rem;
    }
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
        color: var(--accent-gold); border-bottom-color: var(--accent-gold);
    }

    /* --- Estilos para o MEMORIAL HTML --- */
    .container {
        width: 100%; max-width: 1180px; margin: 0 auto; padding: clamp(.7rem, 3vw, 2rem);
        box-sizing: border-box; font-family: 'Inter', sans-serif; color: var(--text-primary);
    }
    .container .pro-header { background: var(--surface); }
    .container h1, .container h2, .container h3, .container h4 { color: var(--text-display); font-family: 'Poppins', sans-serif; }
    .container h2 { border-bottom: 1px solid var(--border); padding-bottom: 10px; }
    .container h3 { color: var(--accent-gold); }
    .container strong { color: var(--text-display); }
    .container .info-card { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 1.5rem; }
    .container table { width: 100%; border-collapse: collapse; margin-top: 1rem; font-family: 'JetBrains Mono', monospace; }
    .container th, .container td { text-align: left; padding: 0.75rem; border-bottom: 1px solid var(--border); }
    .container th { color: var(--accent-gold); }
    .container td.fail, .container span.fail { color: #FF6B6B !important; font-weight: bold; }
    .container td.pass, .container span.pass { color: #63E6BE !important; font-weight: bold; }
    .container .formula-block { background-color: var(--background); border-left: 4px solid var(--accent-amber); border-radius: 4px; padding: 1px 15px 15px; margin: 15px 0;}

    /* Memorial auditável — hierarquia visual para fórmula, substituição e decisão */
    .container { line-height: 1.62; }
    .container .chapter-intro { color: var(--text-secondary); margin: -0.45rem 0 1.35rem; font-size: 0.98rem; }
    .container .audit-banner {
        display: flex; align-items: center; justify-content: space-between; gap: 1rem;
        background: linear-gradient(135deg, rgba(245,158,11,.18), rgba(251,191,36,.05));
        border: 1px solid rgba(251,191,36,.45); border-radius: 10px; padding: 1rem 1.25rem; margin: 1.5rem 0 2rem;
    }
    .container .audit-banner strong { color: var(--accent-gold); letter-spacing: .09em; font-size: .82rem; }
    .container .audit-banner span { color: var(--text-secondary); font-size: .9rem; }
    .container .calc-step {
        position: relative; background: #111c2e; border: 1px solid var(--border); border-radius: 12px;
        padding: 1.3rem 1.4rem 1.15rem; margin: 0 0 1.2rem; box-shadow: 0 6px 18px rgba(0,0,0,.16);
        break-inside: avoid-page;
    }
    .container .calc-step-head { display: flex; align-items: center; gap: .75rem; margin-bottom: .65rem; }
    .container .calc-step-head h4 { margin: 0; font-size: 1.08rem; }
    .container .calc-step-number {
        display: inline-flex; align-items: center; justify-content: center; min-width: 2.6rem; height: 2rem;
        padding: 0 .45rem; border-radius: 999px; background: var(--accent-gold); color: #172033;
        font: 700 .78rem 'JetBrains Mono', monospace;
    }
    .container .calc-explanation { margin: .3rem 0 1rem; color: var(--text-secondary); }
    .container .equation-label { margin: .8rem 0 .3rem; color: #fcd978; font-size: .72rem; font-weight: 700; letter-spacing: .09em; text-transform: uppercase; }
    .container .formula-symbolic, .container .formula-numeric {
        overflow-x: auto; background: #0b1322; border: 1px solid #27364a; border-radius: 7px;
        padding: .65rem 1rem; margin: .25rem 0; color: #f8fafc;
    }
    .container .formula-numeric { background: #0d1828; border-left: 3px solid #60a5fa; }
    .container .equation-heading { display: flex; align-items: center; margin: 1rem 0 .25rem; }
    .container .equation-heading h5 { margin: 0; color: #f8fafc; font-size: .94rem; }
    .container .formula-chain {
        overflow-x: auto; background: #0b1322; border: 1px solid #31445e;
        border-left: 4px solid #60a5fa; border-radius: 8px; padding: 1rem 1.15rem;
        margin: .25rem 0; color: #f8fafc; scrollbar-width: thin;
    }
    .container .formula-chain mjx-container[display="true"] {
        margin: .35rem 0 !important; min-width: max-content;
    }
    /* Diagramas de engenharia contextuais do memorial */
    .container .engineering-visual-stack {
        display: grid; grid-template-columns: minmax(0, 1fr); gap: 1rem; margin: 1rem 0 0;
    }
    .container .engineering-visual {
        margin: 1rem 0 0; border: 1px solid #30435c; border-radius: 11px;
        background: linear-gradient(145deg, #0c1728, #101d30); overflow: hidden;
        break-inside: avoid-page;
    }
    .container .visual-head {
        display: flex; align-items: center; justify-content: space-between; gap: 1rem;
        padding: .8rem 1rem; border-bottom: 1px solid #2a3c54; background: rgba(30,52,81,.48);
    }
    .container .visual-head > div { min-width: 0; }
    .container .visual-head span {
        display: block; color: #7dd3fc; font-size: .66rem; font-weight: 800;
        letter-spacing: .1em; text-transform: uppercase;
    }
    .container .visual-head h5 { margin: .15rem 0 0; color: #f8fafc; font-size: .95rem; }
    .container .visual-head small { color: #8fa2ba; white-space: nowrap; }
    .container .visual-svg-wrap {
        width: 100%; padding: .7rem .8rem .35rem; box-sizing: border-box;
        background:
          radial-gradient(circle at 20% 15%, rgba(56,189,248,.06), transparent 34%),
          linear-gradient(180deg, rgba(8,15,27,.48), rgba(8,15,27,.18));
        overflow: hidden;
    }
    .container .engineering-svg { display: block; width: 100%; height: auto; max-width: 100%; }
    .container .visual-metrics {
        display: grid; grid-template-columns: repeat(auto-fit, minmax(135px, 1fr));
        gap: .55rem; padding: .75rem 1rem; border-top: 1px solid #263950;
    }
    .container .visual-metric {
        min-width: 0; padding: .55rem .65rem; border: 1px solid #2b4059;
        border-radius: 7px; background: rgba(15,30,49,.78);
    }
    .container .visual-metric span { display: block; color: #8fa2ba; font-size: .68rem; }
    .container .visual-metric strong {
        display: block; margin-top: .12rem; color: #f8fafc; font: 700 .82rem 'JetBrains Mono', monospace;
        overflow-wrap: anywhere;
    }
    .container .engineering-visual figcaption {
        padding: 0 1rem .85rem; color: #91a4bc; font-size: .76rem; line-height: 1.55;
    }
    .container .engineering-svg text { font-family: 'Inter', sans-serif; }
    .container .engineering-svg .beam-line { stroke: #e2e8f0; stroke-width: 9; stroke-linecap: round; }
    .container .engineering-svg .beam-datum { stroke: #94a3b8; stroke-width: 3; }
    .container .engineering-svg .support-shape { fill: #15243a; stroke: #cbd5e1; stroke-width: 2; }
    .container .engineering-svg .support-fill { fill: #cbd5e1; }
    .container .engineering-svg .support-ground { stroke: #64748b; stroke-width: 2; }
    .container .engineering-svg .support-wall { stroke: #cbd5e1; stroke-width: 5; }
    .container .engineering-svg .load-spine { stroke: #fb7185; stroke-width: 2; }
    .container .engineering-svg .load-arrow, .container .engineering-svg .point-arrow {
        stroke: #fb7185; stroke-width: 2.4; fill: none;
    }
    .container .engineering-svg .reaction-arrow { stroke: #38bdf8; stroke-width: 2.6; fill: none; }
    .container .engineering-svg .dimension-line { stroke: #94a3b8; stroke-width: 1.25; fill: none; }
    .container .engineering-svg .guide-line, .container .engineering-svg .load-guide {
        stroke: #64748b; stroke-width: 1.25; stroke-dasharray: 6 5;
    }
    .container .engineering-svg .load-guide { stroke: #fb7185; opacity: .75; }
    .container .engineering-svg .critical-guide { stroke: #38bdf8; stroke-width: 1.4; stroke-dasharray: 5 4; }
    .container .engineering-svg .bearing-patch { fill: rgba(251,191,36,.3); stroke: #fbbf24; stroke-width: 1.5; }
    .container .engineering-svg .chart-grid { stroke: #263950; stroke-width: 1; }
    .container .engineering-svg .chart-zero { stroke: #9aabc0; stroke-width: 1.5; }
    .container .engineering-svg .chart-curve, .container .engineering-svg .deflection-curve {
        fill: none; stroke-width: 3; stroke-linejoin: round; stroke-linecap: round;
    }
    .container .engineering-svg .deflection-curve { stroke: #38bdf8; }
    .container .engineering-svg .chart-marker circle { stroke: #eef2ff; stroke-width: 2; }
    .container .engineering-svg .chart-marker.secondary circle { fill: #22d3ee; }
    .container .engineering-svg .deflection-marker { fill: #38bdf8; stroke: #e0f2fe; stroke-width: 2; }
    .container .engineering-svg .svg-label { fill: #e2e8f0; font-size: 15px; font-weight: 700; }
    .container .engineering-svg .load-label { fill: #fda4af; }
    .container .engineering-svg .reaction-label { fill: #7dd3fc; }
    .container .engineering-svg .reaction-label-local { fill: #7dd3fc; }
    .container .engineering-svg .dimension-label { fill: #a8b5c6; font-size: 13px; text-anchor: middle; }
    .container .engineering-svg .svg-node-label { fill: #f8fafc; font-size: 15px; font-weight: 800; }
    .container .engineering-svg .svg-axis-label {
        fill: #8497af; font-size: 12px; text-anchor: middle; font-family: 'JetBrains Mono', monospace;
    }
    .container .engineering-svg .svg-axis-title { fill: #a8b5c6; font-size: 13px; font-weight: 700; }
    .container .engineering-svg .svg-convention-label {
        fill: #fbbf24; font-size: 11px; font-weight: 800;
        font-family: 'JetBrains Mono', monospace;
    }
    .container .engineering-svg .svg-marker-label {
        fill: #67e8f9; font-size: 11px; text-anchor: middle; font-family: 'JetBrains Mono', monospace;
    }
    .container .engineering-svg .svg-marker-label.load-text { fill: #fda4af; }
    .container .engineering-svg .svg-critical-label {
        fill: #f8fafc; font-size: 13px; font-weight: 800; text-anchor: middle;
        font-family: 'JetBrains Mono', monospace;
    }
    .container .engineering-svg .svg-critical-sub {
        fill: #9eb0c6; font-size: 11px; text-anchor: middle; font-family: 'JetBrains Mono', monospace;
    }
    .container .verification-chain {
        overflow-x: auto; background: #0b1322; border: 1px solid #31445e;
        border-left: 4px solid #94a3b8; border-radius: 8px; padding: .8rem 1rem;
        margin: .45rem 0 0; color: #f8fafc;
    }
    .container .verification-card.pass .verification-chain { border-left-color: #34d399; }
    .container .verification-card.fail .verification-chain { border-left-color: #fb7185; }
    .container .step-theory-panel {
        background: #0d1828; border: 1px solid #2e4159; border-radius: 9px;
        margin: .85rem 0 1rem; overflow: hidden;
    }
    .container .step-theory-panel summary {
        display: flex; align-items: center; gap: .7rem; cursor: pointer; list-style: none;
        padding: .8rem .95rem; background: #132137; color: var(--text-display);
    }
    .container .step-theory-panel summary::-webkit-details-marker { display: none; }
    .container .step-theory-panel summary::before {
        content: '+'; display: inline-flex; align-items: center; justify-content: center;
        width: 1.45rem; height: 1.45rem; flex: 0 0 auto; border-radius: 50%;
        background: rgba(96,165,250,.14); color: #93c5fd; font-weight: 700;
    }
    .container .step-theory-panel[open] summary::before { content: '−'; }
    .container .step-theory-panel summary span {
        color: #93c5fd; font-size: .68rem; font-weight: 700; letter-spacing: .08em; text-transform: uppercase;
    }
    .container .step-theory-panel summary strong { margin-left: auto; text-align: right; font-size: .84rem; }
    .container .step-theory-content { padding: .95rem 1rem 1rem; }
    .container .step-theory-content section + section { margin-top: .9rem; padding-top: .85rem; border-top: 1px solid #25374e; }
    .container .step-theory-content h5 { margin: 0 0 .35rem; color: #fcd978; font-size: .86rem; }
    .container .step-theory-content p { margin: 0; color: var(--text-secondary); font-size: .87rem; line-height: 1.7; }
    .container .calc-result {
        margin-top: .9rem; padding: .8rem 1rem; border-radius: 7px;
        background: rgba(96,165,250,.09); border: 1px solid rgba(96,165,250,.26); color: #dbeafe;
    }
    .container .calc-decision { margin-top: .7rem; padding: .65rem .85rem; border-left: 3px solid var(--accent-gold); background: rgba(251,191,36,.07); color: #fde7a7; }
    .container .norm-ref { color: #7f91aa; font-size: .78rem; margin-top: .8rem; }
    .container .theory-panel {
        background: #111c2e; border: 1px solid #3d4f67; border-radius: 12px;
        margin: 0 0 1.35rem; overflow: hidden; break-inside: avoid-page;
    }
    .container .theory-panel summary {
        display: flex; align-items: center; justify-content: space-between; gap: 1rem;
        cursor: pointer; list-style: none; padding: 1rem 1.2rem; background: #162338;
        color: var(--text-display); font-weight: 700;
    }
    .container .theory-panel summary::-webkit-details-marker { display: none; }
    .container .theory-panel summary::before {
        content: '+'; display: inline-flex; align-items: center; justify-content: center;
        width: 1.65rem; height: 1.65rem; flex: 0 0 auto; border-radius: 50%;
        background: rgba(251,191,36,.16); color: var(--accent-gold); font-size: 1.15rem;
    }
    .container .theory-panel[open] summary::before { content: '−'; }
    .container .theory-panel summary span { color: var(--accent-gold); font-size: .72rem; letter-spacing: .08em; text-transform: uppercase; }
    .container .theory-panel summary strong { margin-left: auto; text-align: right; }
    .container .theory-content { padding: 1.2rem 1.3rem 1.35rem; }
    .container .theory-content > h4 { margin: 1.1rem 0 .55rem; color: #f8fafc; }
    .container .theory-content > h4:first-child { margin-top: 0; }
    .container .variable-table-wrap { overflow-x: auto; border: 1px solid #2c3b50; border-radius: 8px; }
    .container .variable-table { margin: 0; min-width: 650px; }
    .container .variable-table th, .container .variable-table td { padding: .65rem .8rem; vertical-align: top; }
    .container .variable-table td:first-child { color: #bfdbfe; white-space: nowrap; }
    .container .theory-grid { display: grid; grid-template-columns: repeat(2,minmax(0,1fr)); gap: .75rem; }
    .container .theory-concept { background: #0d1828; border: 1px solid #293a50; border-radius: 8px; padding: .8rem .9rem; }
    .container .theory-concept h5 { color: #fcd978; margin: 0 0 .35rem; font-size: .88rem; }
    .container .theory-concept p { color: var(--text-secondary); margin: 0; font-size: .85rem; }
    .container .verification-card {
        border: 1px solid var(--border); border-left: 6px solid #94a3b8; border-radius: 10px;
        background: #111c2e; padding: 1.15rem 1.35rem; margin: 1.2rem 0 1.8rem; break-inside: avoid-page;
    }
    .container .verification-card.pass { border-left-color: #34d399; }
    .container .verification-card.fail { border-left-color: #fb7185; }
    .container .verification-card.pending { border-left-color: #fbbf24; }
    .container .verification-card h4 { margin: .2rem 0 .5rem; }
    .container .verification-kicker { color: var(--text-secondary); font-size: .7rem; font-weight: 700; letter-spacing: .12em; }
    .container .verification-metrics { display: flex; justify-content: space-between; align-items: center; margin-top: .75rem; }
    .container .pending { color: #fbbf24 !important; font-weight: 700; }
    .container .scope-grid { display: grid; grid-template-columns: repeat(2, minmax(0,1fr)); gap: 1rem; }
    .container .global-status { display: flex; justify-content: space-between; align-items: center; border-radius: 10px; padding: 1.1rem 1.3rem; margin: 1.2rem 0; border: 1px solid var(--border); background: #111c2e; }
    .container .global-status span { color: var(--text-secondary); font-size: .75rem; letter-spacing: .12em; }
    .container .global-status.pass strong { color: #63e6be; }
    .container .global-status.fail strong { color: #ff6b6b; }
    .container .global-status.pending strong { color: #fbbf24; }
    .container .notice { background: #162236; border: 1px solid var(--border); border-radius: 8px; padding: .9rem 1rem; margin: 1rem 0; color: var(--text-secondary); }
    @media (max-width: 780px) {
        .container { padding: .65rem; }
        .container .pro-header { padding: 1.1rem .7rem; }
        .container .pro-header h1 { font-size: clamp(1.35rem, 7vw, 1.9rem); }
        .container .info-card, .container .calc-step, .container .verification-card {
            padding: .9rem;
        }
        .container .formula-block { padding: 1px .7rem .7rem; }
        .container .formula-chain, .container .verification-chain,
        .container .formula-symbolic, .container .formula-numeric {
            padding: .7rem;
            max-width: 100%;
        }
        .container table { display: block; overflow-x: auto; white-space: nowrap; }
        .container .scope-grid, .container .theory-grid { grid-template-columns: 1fr; }
        .container .audit-banner, .container .verification-metrics { align-items: flex-start; flex-direction: column; }
        .container .theory-panel summary { align-items: flex-start; flex-wrap: wrap; }
        .container .theory-panel summary strong { margin-left: 0; text-align: left; width: calc(100% - 2.5rem); }
        .container .step-theory-panel summary { align-items: flex-start; flex-wrap: wrap; }
        .container .step-theory-panel summary strong { margin-left: 2.15rem; text-align: left; width: 100%; }
        .container .visual-head { align-items: flex-start; }
        .container .visual-head small { display: none; }
        .container .visual-svg-wrap { padding: .35rem .25rem .2rem; }
        .container .visual-metrics { grid-template-columns: repeat(2, minmax(0, 1fr)); padding: .65rem; }
        .container .engineering-visual figcaption { padding: 0 .7rem .75rem; }
        .container .engineering-svg .svg-label { font-size: 27px; }
        .container .engineering-svg .dimension-label { font-size: 23px; }
        .container .engineering-svg .svg-node-label { font-size: 25px; }
        .container .engineering-svg .svg-axis-label { font-size: 21px; }
        .container .engineering-svg .svg-axis-title { font-size: 22px; }
        .container .engineering-svg .svg-marker-label { font-size: 19px; }
        .container .engineering-svg .svg-critical-label { font-size: 23px; }
        .container .engineering-svg .svg-critical-sub { font-size: 19px; }
        .container .engineering-svg .reaction-label { display: none; }
        .container [data-visual="deflection-diagram"] .svg-critical-label,
        .container [data-visual="deflection-diagram"] .svg-critical-sub,
        .container [data-visual="deflection-diagram"] .svg-axis-title { display: none; }
        .container .engineering-svg .beam-line,
        .container .engineering-svg .chart-curve,
        .container .engineering-svg .deflection-curve { vector-effect: non-scaling-stroke; }
    }
    @media print {
        body { background: white !important; color: #172033 !important; }
        .container { color: #172033 !important; }
        .container .calc-step, .container .verification-card, .container .info-card, .container .notice, .container .theory-panel, .container .theory-panel summary, .container .theory-concept, .container .step-theory-panel, .container .step-theory-panel summary { background: white !important; color: #172033 !important; box-shadow: none; border-color: #cbd5e1; }
        .container .formula-symbolic, .container .formula-numeric, .container .formula-chain, .container .verification-chain { background: #f8fafc !important; color: #0f172a !important; border-color: #cbd5e1; }
        .container .engineering-visual, .container .visual-head, .container .visual-metric { background: white !important; color: #172033 !important; border-color: #cbd5e1 !important; }
        .container .visual-svg-wrap { background: white !important; }
        .container .calc-explanation, .container .chapter-intro, .container .norm-ref { color: #475569 !important; }
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
        caminho_arquivo_excel = Path(__file__).resolve().with_name('perfis.xlsx')
        return pd.read_excel(caminho_arquivo_excel, sheet_name=None)
    except FileNotFoundError:
        st.error(f"Erro: Arquivo '{caminho_arquivo_excel}' não foi encontrado. Verifique se ele está na mesma pasta que o seu script Python.")
        return None
    except Exception as e:
        st.error(f"Erro ao ler o arquivo Excel: {e}")
        return None

def get_profile_properties(profile_series):
    props = {
        "d": profile_series.get('d (mm)'),
        "bf": profile_series.get('bf (mm)'),
        "tw": profile_series.get('tw (mm)'),
        "tf": profile_series.get('tf (mm)'),
        # h_faces é a distância entre faces internas; d' desconta os raios nos laminados.
        "h_faces": profile_series.get('h (mm)'),
        "h_clear": profile_series.get("d' (mm)", profile_series.get('h (mm)')),
        "Area": profile_series.get('Área (cm2)'),
        "Ix": profile_series.get('Ix (cm4)'),
        "Wx": profile_series.get('Wx (cm3)'),
        "rx": profile_series.get('rx (cm)'),
        "Zx": profile_series.get('Zx (cm3)'),
        "Iy": profile_series.get('Iy (cm4)'),
        "Wy": profile_series.get('Wy (cm3)'),
        "ry": profile_series.get('ry (cm)'),
        "Zy": profile_series.get('Zy (cm3)'),
        "rt": profile_series.get('rt (cm)'),
        "J": profile_series.get('It (cm4)'),
        "Cw": profile_series.get('Cw (cm6)'),
        "Peso": profile_series.get('Massa Linear (kg/m)', profile_series.get('Peso (kg/m)')),
    }
    required_keys = ["d", "bf", "tw", "tf", "h_faces", "h_clear", "Area", "Ix", "Wx", "rx", "Zx", "Iy", "ry", "J", "Cw", "Peso"]
    profile_name = profile_series.get('Bitola (mm x kg/m)', 'Perfil Desconhecido')
    for key in required_keys:
        value = props.get(key)
        if value is None or pd.isna(value) or (isinstance(value, (int, float)) and value <= 0):
            raise ValueError(f"Propriedade ESSENCIAL '{key}' inválida ou nula no Excel para '{profile_name}'. Verifique a planilha.")
    for key in ['d', 'bf', 'tw', 'tf', 'h_faces', 'h_clear']:
        props[key] /= 10.0
    # Alias mantido apenas para blocos legados de apresentação.
    props['h'] = props['h_clear']
    return props

def create_excel_with_colors(df_list, sheet_names):
    """
    Cria um arquivo Excel com múltiplas abas, aplicando formatação de cores
    baseada na eficiência dos perfis.
    """
    output = io.BytesIO()
    workbook = openpyxl.Workbook()

    # Remova a folha padrão criada automaticamente
    if 'Sheet' in workbook.sheetnames:
        workbook.remove(workbook['Sheet'])

    for df, sheet_name in zip(df_list, sheet_names):
        sheet = workbook.create_sheet(title=sheet_name)

        # Escreva os cabeçalhos
        for col_idx, col_name in enumerate(df.columns, 1):
            sheet.cell(row=1, column=col_idx, value=col_name)

        # Defina os estilos de cores
        fill_fail = PatternFill(start_color='F8D7DA', end_color='F8D7DA', fill_type='solid') # Vermelho
        fill_warning_high = PatternFill(start_color='FFEBAE', end_color='FFEBAE', fill_type='solid') # Amarelo escuro (95-100%)
        fill_warning_low = PatternFill(start_color='FFF3CD', end_color='FFF3CD', fill_type='solid') # Amarelo claro (80-95%)
        fill_pass = PatternFill(start_color='D4EDDA', end_color='D4EDDA', fill_type='solid') # Verde
        
        # Escreva os dados e aplique as cores
        for row_idx, row_data in enumerate(df.itertuples(index=False), 2):
            for col_idx, value in enumerate(row_data, 1):
                cell = sheet.cell(row=row_idx, column=col_idx, value=value)
                
                # Regras de formatação para as colunas de eficiência
                if 'Ef.' in df.columns[col_idx-1]:
                    try:
                        efficiency = float(value)
                        if efficiency > 100.0:
                            cell.fill = fill_fail
                        elif efficiency > 95:
                            cell.fill = fill_warning_high
                        elif efficiency > 80:
                            cell.fill = fill_warning_low
                        else:
                            cell.fill = fill_pass
                    except (ValueError, TypeError):
                        pass

    workbook.save(output)
    output.seek(0)
    return output

# Mantenha esta função como está:
def create_professional_header():
    st.markdown(f"""
    <div class="pro-header">
        <div class="header-content">
            <h1 class="gradient-text">Calculadora Estrutural de Perfis</h1>
            <p>Análise de Perfis Metálicos | {Config.NOME_NORMA}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

def create_metrics_dashboard(input_params):
    """Cria um dashboard com métricas principais do projeto e esforços."""
    st.markdown("### 📊 Parâmetros do Projeto")
    
    msd_value = input_params.get('Msd', 0)
    vsd_value = input_params.get('Vsd', 0)
    cb_value = input_params.get('Cb_projeto', 1.0)

    def br_number(value, decimals):
        formatted = f"{value:,.{decimals}f}"
        return formatted.replace(",", "_").replace(".", ",").replace("_", ".")

    msd_display = br_number(msd_value / 100, 2) if msd_value > 0 else "—"
    vsd_display = br_number(vsd_value, 2) if vsd_value > 0 else "—"
    cb_display = (
        "automático por perfil"
        if input_params.get('cb_modo_auto')
        else br_number(cb_value, 2)
    )

    st.markdown(f"""
    <section class="project-metrics-shell" aria-label="Parâmetros principais do projeto">
        <div class="project-metrics-grid">
            <article class="project-metric-card">
                <div class="project-metric-label">Norma</div>
                <div class="project-metric-value">NBR 8800:2024</div>
                <div class="project-metric-unit">Errata 1:2025</div>
            </article>
            <article class="project-metric-card">
                <div class="project-metric-label">Módulo de elasticidade</div>
                <div class="project-metric-value">{br_number(input_params['E_aco'], 0)}</div>
                <div class="project-metric-unit">kN/cm²</div>
            </article>
            <article class="project-metric-card">
                <div class="project-metric-label">Coeficiente γa1</div>
                <div class="project-metric-value">1,10</div>
                <div class="project-metric-unit">resistência</div>
            </article>
            <article class="project-metric-card">
                <div class="project-metric-label">Vão da viga</div>
                <div class="project-metric-value">{br_number(input_params['L_cm'] / 100, 2)}</div>
                <div class="project-metric-unit">m</div>
            </article>
            <article class="project-metric-card">
                <div class="project-metric-label">Resistência ao escoamento fy</div>
                <div class="project-metric-value">{br_number(input_params['fy_aco'], 1)}</div>
                <div class="project-metric-unit">kN/cm²</div>
            </article>
            <article class="project-metric-card" title="Momento fletor solicitante de cálculo">
                <div class="project-metric-label">Momento solicitante Msd</div>
                <div class="project-metric-value">{msd_display}</div>
                <div class="project-metric-unit">kN·m</div>
            </article>
            <article class="project-metric-card" title="Força cortante solicitante de cálculo">
                <div class="project-metric-label">Cortante solicitante Vsd</div>
                <div class="project-metric-value">{vsd_display}</div>
                <div class="project-metric-unit">kN</div>
            </article>
        </div>
        <div class="project-metrics-context">
            <span><strong>Cb</strong>{cb_display}</span>
            <span><strong>Lb</strong>{br_number(input_params['Lb_projeto'], 2)} cm</span>
            <span><strong>Limite de flecha</strong>L/{input_params['limite_flecha_divisor']:.0f}</span>
        </div>
    </section>
    """, unsafe_allow_html=True)

def style_classic_dataframe(df):
    """Aplica estilização clássica com cores sólidas ao DataFrame."""
    def color_efficiency(val):
        if pd.isna(val) or not isinstance(val, (int, float)): return ''
        if val > 100:
            background, foreground = '#991b1b', '#fef2f2'
        elif val > 95:
            background, foreground = '#9a3412', '#fff7ed'
        elif val > 80:
            background, foreground = '#854d0e', '#fffbeb'
        else:
            background, foreground = '#166534', '#f0fdf4'
        return (
            f'background-color: {background}; '
            f'font-weight: bold; color: {foreground};'
        )

    def style_status(val):
        if val in {'APROVADO', APPROVED_SCOPE_TEXT}:
            return 'background-color: #d4edda; font-weight: bold; color: #155724;'
        elif val == 'REPROVADO':
            return 'background-color: #f8d7da; font-weight: bold; color: #721c24;'
        elif val == 'NÃO VERIFICADO':
            return 'background-color: #fff3cd; font-weight: bold; color: #856404;'
        return ''

    efficiency_cols = [col for col in df.columns if '%' in col]
    
    styled_df = df.style.map(color_efficiency, subset=efficiency_cols)
    
    if 'Status' in df.columns:
        styled_df = styled_df.map(style_status, subset=['Status'])
        
    format_number_2 = lambda val: "—" if pd.isna(val) else f"{val:.2f}"
    format_number_1 = lambda val: "—" if pd.isna(val) else f"{val:.1f}"
    format_dict = {
        "Peso (kg/m)": format_number_2,
        **{col: format_number_1 for col in efficiency_cols},
    }
    return styled_df.format(format_dict)

# Em create_top_profiles_chart(df_approved, top_n=10):
def create_top_profiles_chart(df_approved, top_n=10):
    if df_approved.empty: return None
    df_top = df_approved.head(top_n).sort_values(by='Peso (kg/m)', ascending=False)
    fig = go.Figure(go.Bar(
        y=df_top['Perfil'], x=df_top['Peso (kg/m)'], orientation='h',
        text=[f'{w:.2f} kg/m' for w in df_top['Peso (kg/m)']], textposition='auto',
        marker=dict(color=df_top['Peso (kg/m)'], colorscale='YlOrBr', colorbar=dict(title="Peso")), # Escala de cor Dourada
        hovertemplate='<b>%{y}</b><br>Peso: %{x:.2f} kg/m<extra></extra>'
    ))
    fig.update_layout(
        title={'text': f'🏆 Top {top_n} Perfis Mais Leves (Aprovados)', 'x': 0.5},
        xaxis_title='Peso (kg/m)', yaxis_title='Perfil', 
        template='plotly_dark', # <--- ADICIONE ESTA LINHA
        height=500, 
        margin=dict(l=80, r=20, t=70, b=55),
        paper_bgcolor='rgba(0,0,0,0)', # Fundo do papel transparente
        plot_bgcolor='rgba(0,0,0,0)'   # Fundo do gráfico transparente
    )
    return fig

# Em create_profile_efficiency_chart(perfil_nome, eficiencias):
# Substitua a função create_profile_efficiency_chart inteira por esta:
def create_profile_efficiency_chart(perfil_nome, eficiencias):
    """
    Cria um gráfico de barras comparando as eficiências de um perfil.
    """
    labels = list(eficiencias.keys())
    values = [min(v, 150) if isinstance(v, (int, float)) else 0 for v in eficiencias.values()]
    
    # Cores baseadas na eficiência
    colors = ['#32CD32' if v <= 100 else '#FF4500' for v in values]
    
    fig = go.Figure(data=[
        go.Bar(
            x=labels,
            y=values,
            text=[f'{v:.1f}%' if isinstance(v, (int, float)) else 'N/A' for v in eficiencias.values()],
            textposition='auto',
            marker_color=colors,
            textfont=dict(color='#FFFFFF', size=14, family='Poppins') # Texto dentro da barra
        )
    ])
    
    fig.add_hline(y=100, line_dash="dash", line_color="#fbbd24", # Linha dourada
                  annotation_text="Limite (100%)",
                  annotation_position="bottom right",
                  annotation_font=dict(color='#fbbd24'))

    # ATUALIZAÇÃO COMPLETA DO LAYOUT PARA O TEMA DARK
    fig.update_layout(
        title=dict(
            text=f'Análise de Eficiência para o Perfil: {perfil_nome}',
            font=dict(color='#FFFFFF', size=20, family='Poppins') # Cor do título
        ),
        yaxis_title='Eficiência (%)',
        xaxis_title='Verificação',
        yaxis_range=[0, max(max(values), 100) + 15],
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#94a3b8', family='Inter'), # Cor padrão para todo o texto do gráfico
        xaxis=dict(
            title_font=dict(color='#e2e8f0'), # Cor do título do eixo X
            tickfont=dict(color='#e2e8f0')     # Cor dos labels do eixo X
        ),
        yaxis=dict(
            title_font=dict(color='#e2e8f0'), # Cor do título do eixo Y
            tickfont=dict(color='#e2e8f0')     # Cor dos labels do eixo Y
        )
    )
    return fig
brazilia_tz = pytz.timezone('America/Sao_Paulo')
# Substitua a função create_professional_memorial_html por esta:
def create_professional_memorial_html(perfil_nome, perfil_tipo, resultados, input_details, projeto_info):
    # (O conteúdo da variável 'conteudo_memorial' continua o mesmo)
    conteudo_memorial = f""" 
    <h2>1. Resumo Executivo</h2>
    <div class="result-highlight">{resultados['resumo_html']}</div>
    <h2>2. Dados de Entrada e Solicitações</h2>
    <div class="info-card">
        <h3>2.1. Propriedades do Perfil e Materiais</h3>
        {input_details}
    </div>
    {resultados.get('esforcos_html', '')}
    {resultados.get('cb_calc_html', '')}
    {resultados['passo_a_passo_html']}
    """
    
    # O template HTML agora tem o <h1> com a classe 'gradient-text'
    html_template = f"""
    <!DOCTYPE html><html lang="pt-BR"><head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Memorial de Cálculo - {perfil_nome}</title>
        {HTML_TEMPLATE_CSS_PRO}
        <script type="text/javascript" async src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.7/MathJax.js?config=TeX-MML-AM_CHTML"></script>
    </head><body><div class="container">
        <div class="pro-header">
            <h1><span class="gradient-text">Memorial de Cálculo Estrutural</span></h1>
            <p><strong>{perfil_nome}</strong> ({perfil_tipo})</p>
        </div>
        <div class="info-card">
            <h3>📋 Identificação do Projeto</h3>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem;">
                <div><strong>Projeto:</strong> {projeto_info['nome']}</div>
                <div><strong>Engenheiro:</strong> {projeto_info['engenheiro']}</div>
                <div><strong>Data:</strong> {projeto_info['data']}</div>
                <div><strong>Revisão:</strong> {projeto_info['revisao']}</div>
            </div>
        </div>
        {conteudo_memorial}
        <div style="text-align: center; margin-top: 3rem; padding-top: 2rem; border-top: 1px solid var(--border); color: var(--text-secondary);">
            <p>Memorial gerado em {datetime.now(brazilia_tz).strftime('%d/%m/%Y às %H:%M')}</p>
        </div>
    </div></body></html>
    """
    return html_template
def _verification_status(demand, resistance, applicable=True):
    if not applicable:
        return 0.0, "NÃO APLICÁVEL"
    if resistance is None or resistance <= 0:
        return float('inf'), "NÃO VERIFICADO"
    efficiency = demand / resistance * 100.0
    return efficiency, "APROVADO" if demand <= resistance else "REPROVADO"

def _memorial_2024_html(bundle):
    """Renderiza o memorial auditável com os dados do núcleo normativo."""
    return build_memorial_details(bundle)


def perform_all_checks(props, fy_aco, Lb_projeto, Cb_projeto, L_cm, Msd, Vsd, q_serv_kn_cm, p_load_serv, tipo_viga, input_mode, tipo_fabricacao, usa_enrijecedores, a_enr, limite_flecha_divisor, projeto_info, E_aco, detalhado=False, fu_aco=45.0, **kwargs):
    automatic = input_mode == "Calcular a partir de Cargas na Viga"
    scope_issues = list(kwargs.get('unsupported_reasons', []))
    scope_notes = list(kwargs.get('scope_notes', []))
    scope_issues.extend(validate_material(fy_aco, fu_aco))
    catalog_report = _catalog_validation_report()
    if catalog_report.status is not CatalogValidationStatus.VALIDATED_CATALOG_SOURCE:
        scope_issues.append(
            f"{catalog_report.status.value}: o catálogo possui "
            f"{len(catalog_report.blocking_issues)} pendência(s) bloqueante(s); "
            "não pode sustentar aprovação executiva."
        )

    self_weight = props['Peso'] * 9.80665 / 100_000.0 if kwargs.get('include_self_weight', True) else 0.0
    elu_response = None
    els_response = None
    elu_loads = None
    els_loads = None
    point_position = kwargs.get('p_pos_cm', p_load_serv[1] if p_load_serv else L_cm / 2.0)
    Cb_final = Cb_projeto
    cb_info = None
    cb_basis = "Cb informado pelo usuário; a origem deve ser registrada no projeto."
    if (
        tipo_viga == 'Engastada e Livre (Balanço)'
        and kwargs.get('cantilever_standard_cb', False)
    ):
        cb_basis = "Cb = 1,0 para a condição de balanço declarada em 5.4.2.3-b."
    elif kwargs.get('cb_source', '').strip():
        cb_basis = f"Cb informado pelo usuário. Origem registrada: {kwargs['cb_source'].strip()}."

    if automatic:
        q_g = kwargs.get('q_g_kn_cm', 0.0)
        q_q = kwargs.get('q_q_kn_cm', q_serv_kn_cm)
        p_g = kwargs.get('p_g_kn', 0.0)
        p_q = kwargs.get('p_q_kn', p_load_serv[0] if p_load_serv else 0.0)
        elu_loads = combine_elu_normal(
            q_g, q_q, self_weight, p_g, p_q,
            gamma_g=kwargs.get('gamma_g', 1.50),
            gamma_q=kwargs.get('gamma_q', 1.50),
            gamma_self_weight=kwargs.get('gamma_self_weight', 1.25),
        )
        elu_response = analyze_beam(
            tipo_viga, L_cm, elu_loads['q'], elu_loads['P'], point_position
        )
        Msd, Vsd = elu_response.max_moment, elu_response.max_shear

        if kwargs.get('cb_modo_auto', False):
            cb_info = calculate_cb_nbr2024(
                elu_response,
                segment_start=kwargs.get('lb_start_cm', 0.0),
                unbraced_length=Lb_projeto,
            )
            Cb_final = cb_info['Cb']
            cb_basis = (
                f"Cálculo automático no trecho x={cb_info['segment_start']/100:.3f} m a "
                f"x={(cb_info['segment_start']+cb_info['Lb'])/100:.3f} m: "
                f"|Mmax|={cb_info['Mmax']/100:.3f}, |MA|={cb_info['MA']/100:.3f}, "
                f"|MB|={cb_info['MB']/100:.3f}, |MC|={cb_info['MC']/100:.3f} kN·m."
            )

        els_loads = combine_els(
            q_g, q_q, self_weight, p_g, p_q,
            combination=kwargs.get('els_combination', 'rare'),
            psi1=kwargs.get('psi1', 0.6),
            psi2=kwargs.get('psi2', 0.4),
        )
        els_response = analyze_beam(
            tipo_viga, L_cm, els_loads['q'], els_loads['P'], point_position,
            E=E_aco, I=props['Ix'],
        )
        scope_issues.append(
            "ELS legado: a flecha total ainda não está decomposta por fase, "
            "permanente antes/depois de elemento frágil, variável principal e "
            "acompanhantes; permanece NOT_CHECKED no fluxo de produção."
        )
        scope_issues.append(
            "ELS de vibração: OUT_OF_SCOPE; a flecha estática não substitui "
            "análise dinâmica."
        )
    else:
        external_evidence = kwargs.get("external_evidence")
        if external_evidence is None:
            scope_issues.append(
                "Modo manual: forças localizadas e ELS exigem evidência externa documental."
            )
        else:
            checked_items = set(external_evidence.checked_items)
            required_items = {"LOCAL_FORCES", "ELS_DEFLECTION"}
            missing_items = sorted(required_items - checked_items)
            if missing_items:
                scope_issues.append(
                    "Evidência externa não cobre os itens obrigatórios: "
                    + ", ".join(missing_items)
                    + "."
                )
            scope_issues.append(
                "Resultados externos foram registrados, mas não foram recalculados nem aprovados "
                "pelo motor; permanecem separados do escopo computacional."
            )

    Afg_tension = None
    Afn_tension = None
    if kwargs.get('has_tension_flange_holes', False):
        Afg_tension = props['bf'] * props['tf']
        Afn_tension = Afg_tension * kwargs.get('tension_flange_net_ratio', 1.0)

    flex = flexural_strength_i(
        props, fy_aco, fu_aco, E_aco, Lb_projeto, Cb_final, tipo_fabricacao,
        stiffener_spacing=a_enr if usa_enrijecedores else None,
        flt_applicable=True,
        net_tension_flange_area=Afn_tension,
        gross_tension_flange_area=Afg_tension,
        section_symmetry="DOUBLE",
        symmetry_basis=(
            "Esquema geométrico do catálogo atual com uma única dimensão bf e tf "
            "comum às mesas superior e inferior."
        ),
    )
    scope_issues.extend(flex['applicability_issues'])

    shear = shear_strength_i(
        props, fy_aco, E_aco,
        stiffener_spacing=a_enr if usa_enrijecedores else None,
        stiffener_width=kwargs.get('stiffener_width'),
        stiffener_thickness=kwargs.get('stiffener_thickness'),
        stiffener_pair=kwargs.get('stiffener_pair', True),
        stiffener_welded_to_web_and_flanges=kwargs.get('stiffener_welded', False),
    )
    if shear['stiffener_requested'] and not shear['stiffener_design_complete']:
        scope_issues.append(
            "Enrijecedores: a triagem geométrica foi calculada, mas resistência "
            "axial, flambagem, transferência, soldas, contato com mesas, painéis "
            "extremos e a Errata 1:2025 permanecem NOT_CHECKED."
        )

    if not kwargs.get("flt_applicable", True):
        scope_issues.append(
            "A declaração global de contenção não desativa a FLT; a aplicabilidade deve ser "
            "demonstrada por mesa e por segmento."
        )
    flt_eff, flt_status = _verification_status(Msd, flex['Mrd_FLT'])
    flm_eff, flm_status = _verification_status(Msd, flex['Mrd_FLM'])
    fla_eff, fla_status = _verification_status(Msd, flex['Mrd_FLA_or_tension'])
    rupture_eff, rupture_status = _verification_status(
        Msd, flex['Mrd_rupture'], flex['Mrd_rupture'] is not None
    )
    shear_eff, shear_status = _verification_status(Vsd, shear['Vrd'])

    res_flt = {'Mrdx': flex['Mrd_FLT'] or flex['Mrd'], 'eficiencia': flt_eff, 'status': flt_status, 'core': flex, 'Msd': Msd, 'titulo': 'Flexão — FLT'}
    res_flt.update({
        'rupture_Mrd': flex['Mrd_rupture'],
        'rupture_efficiency': rupture_eff,
        'rupture_status': rupture_status,
    })
    res_flm = {'Mrdx': flex['Mrd_FLM'], 'eficiencia': flm_eff, 'status': flm_status, 'core': flex, 'Msd': Msd, 'titulo': 'Flexão — FLM'}
    res_fla = {'Mrdx': flex['Mrd_FLA_or_tension'], 'eficiencia': fla_eff, 'status': fla_status, 'core': flex, 'Msd': Msd, 'titulo': 'Flexão — FLA/Anexo E'}
    res_cis = {'Vrd': shear['Vrd'], 'eficiencia': shear_eff, 'status': shear_status, 'core': shear, 'Vsd': Vsd}

    local_checks = []
    local_statuses = []
    if automatic and elu_response:
        if kwargs.get("localized_forces_centered_on_web") is not True:
            scope_issues.append(
                "Forças localizadas: a centralização em relação à alma, exigida "
                "pelo escopo de 5.7.1, não foi comprovada."
            )
        locations = [
            (
                "Apoio esquerdo", abs(elu_response.reaction_left),
                kwargs.get('bearing_left_cm', 10.0), 0.0, 0.0,
                kwargs.get('support_relative_lateral_restrained', True),
            ),
        ]
        if tipo_viga != 'Engastada e Livre (Balanço)':
            locations.append((
                "Apoio direito", abs(elu_response.reaction_right),
                kwargs.get('bearing_right_cm', 10.0), 0.0, L_cm,
                kwargs.get('support_relative_lateral_restrained', True),
            ))
        if elu_loads['P'] > 0:
            locations.append((
                "Carga pontual", elu_loads['P'], kwargs.get('point_bearing_cm', 10.0),
                min(point_position, L_cm - point_position), point_position,
                kwargs.get('point_relative_lateral_restrained', True),
            ))
        for name, demand, bearing, distance_end, x_load, lateral_restrained in locations:
            requirements = localized_force_limit_state_matrix(
                LocalizedForceCase.COMPRESSION_ON_WEB,
                welded_section=tipo_fabricacao.lower().startswith("sold"),
                is_support_or_free_end=name.startswith("Apoio"),
            )
            local = local_compression_strength(
                props, fy_aco, E_aco, bearing, distance_end, tipo_fabricacao,
                weld_root_or_radius=kwargs.get('weld_root_cm', 0.0),
                lateral_unbraced_length=kwargs.get('local_unbraced_cm', Lb_projeto),
                flange_rotation_restrained=kwargs.get('loaded_flange_rotation_restrained', True),
                relative_lateral_movement_restrained=lateral_restrained,
                moment_at_load=elu_response.moment_at(x_load),
            )
            local["limit_state_matrix"] = requirements
            if any(
                item.limit_state is LocalizedLimitState.WELD_FORCE_TRANSFER
                and item.applicability is LimitStateApplicability.REQUIRED
                for item in requirements
            ):
                scope_issues.append(
                    f"{name}: transferência da força pela solda mesa–alma "
                    "permanece NOT_CHECKED."
                )
            if name.startswith("Apoio"):
                scope_issues.append(
                    f"{name}: as condições de apoio/extremidade de 5.7.8 "
                    "permanecem NOT_CHECKED."
                )
            efficiency, status = _verification_status(demand, local['FRd'])
            if demand > local["FRd"]:
                scope_issues.append(
                    f"{name}: há necessidade potencial de enrijecedor, cujo "
                    "dimensionamento completo conforme 5.7.9 permanece NOT_CHECKED."
                )
            local_checks.append({
                'name': name, 'demand': demand, 'resistance': local['FRd'],
                'efficiency': efficiency, 'status': status, 'details': local,
                'position': x_load, 'bearing_length': bearing,
            })
            local_statuses.append(status)

    flecha_max = flecha_limite = eficiencia_flecha = 0.0
    status_flecha = "NÃO VERIFICADO"
    if els_response:
        absolute_limit = 1.5 if kwargs.get('masonry_on_beam', False) else None
        flecha_limite = deflection_limit(tipo_viga, L_cm, limite_flecha_divisor, absolute_limit)
        flecha_max = els_response.max_deflection
        eficiencia_flecha, status_flecha = _verification_status(flecha_max, flecha_limite)
    res_flecha = {
        'flecha_max': flecha_max, 'flecha_limite': flecha_limite,
        'eficiencia': eficiencia_flecha, 'status': status_flecha,
        'Ix': props['Ix'], 'detalhes': {}, 'divisor': limite_flecha_divisor,
        'response': els_response,
    }

    statuses = [
        flt_status, flm_status, fla_status, rupture_status,
        shear_status, status_flecha,
    ] + local_statuses
    if scope_issues:
        statuses.append("NÃO VERIFICADO")
    status_global = overall_status(statuses)
    for result in (res_flt, res_flm, res_fla, res_cis, res_flecha):
        result['status_global'] = status_global
        result['scope_issues'] = scope_issues
        result['local_checks'] = local_checks

    bundle = {
        'Msd': Msd, 'Vsd': Vsd, 'flexure': flex, 'shear': shear,
        'elu_response': elu_response, 'els_response': els_response,
        'elu_loads': elu_loads, 'els_loads': els_loads,
        'elu_combination_text': kwargs.get('elu_combination_text', '1,50·G + 1,25·PP aço + 1,50·Q'),
        'els_combination_text': kwargs.get('els_combination_text', kwargs.get('els_combination', 'rare')),
        'Cb': Cb_final, 'Lb': Lb_projeto, 'cb_basis': cb_basis, 'cb_info': cb_info,
        'props': props, 'fy': fy_aco, 'fu': fu_aco, 'E': E_aco,
        'fabrication': tipo_fabricacao, 'support': tipo_viga, 'length': L_cm,
        'input_mode': input_mode, 'point_position': point_position,
        'self_weight': self_weight, 'gamma_a1': 1.10, 'gamma_a2': 1.35,
        'influence_left_cm': kwargs.get('larg_esq_cm'),
        'influence_right_cm': kwargs.get('larg_dir_cm'),
        'influence_width_m': kwargs.get('larg_inf_total_m'),
        'g_area': kwargs.get('g_area'), 'q_area': kwargs.get('q_area'),
        'masonry_on_beam': kwargs.get('masonry_on_beam', False),
        'local_checks': local_checks,
        'deflection_limit': flecha_limite, 'deflection_divisor': limite_flecha_divisor,
        'deflection_efficiency': eficiencia_flecha, 'deflection_status': status_flecha,
        'scope_notes': scope_notes, 'scope_issues': scope_issues, 'status_global': status_global,
        'external_evidence': kwargs.get('external_evidence'),
        'catalog_status': catalog_report.status.value,
        'catalog_sha256': catalog_report.workbook_sha256,
    }
    passo_a_passo_html = _memorial_2024_html(bundle) if detalhado else ""
    return res_flt, res_flm, res_fla, res_cis, res_flecha, passo_a_passo_html

# Substitua a função build_summary_html por esta versão:
def build_summary_html(Msd, Vsd, res_flt, res_flm, res_fla, res_cisalhamento, res_flecha):
    verificacoes = [
        ('Flexão (FLT)', f"{compact_number(Msd/100,2)} kN·m", f"{compact_number(res_flt['Mrdx']/100,2)} kN·m" if res_flt['status'] != 'N/A' else 'N/A', res_flt['eficiencia'], res_flt['status']),
        ('Flexão (FLM)', f"{compact_number(Msd/100,2)} kN·m", f"{compact_number(res_flm['Mrdx']/100,2)} kN·m", res_flm['eficiencia'], res_flm['status']),
        ('Flexão (FLA/Anexo E)', f"{compact_number(Msd/100,2)} kN·m", f"{compact_number(res_fla['Mrdx']/100,2)} kN·m", res_fla['eficiencia'], res_fla['status']),
        ('Cisalhamento', f"{compact_number(Vsd,2)} kN", f"{compact_number(res_cisalhamento['Vrd'],2)} kN", res_cisalhamento['eficiencia'], res_cisalhamento['status']),
        ('Flecha (ELS)', f"{compact_number(res_flecha['flecha_max'],2)} cm" if res_flecha['status'] != "N/A" else "N/A", f"≤ {compact_number(res_flecha['flecha_limite'],2)} cm" if res_flecha['status'] != "N/A" else "N/A", res_flecha['eficiencia'], res_flecha['status'])
    ]
    if res_flt.get('rupture_Mrd') is not None:
        verificacoes.insert(3, (
            'Flexão — ruptura na mesa tracionada',
            f"{compact_number(Msd/100,2)} kN·m",
            f"{compact_number(res_flt['rupture_Mrd']/100,2)} kN·m",
            res_flt['rupture_efficiency'],
            res_flt['rupture_status'],
        ))
    rows_html = ""
    for nome, sol, res, efic, status in verificacoes:
        # A MUDANÇA ESTÁ AQUI: adiciona a classe 'pass' ou 'fail' ao <td> do status
        status_class = "pass" if status in {"APROVADO", "NÃO APLICÁVEL"} else "fail"
        efic_str = f"{compact_number(efic,1)}%" if status not in {"N/A", "NÃO APLICÁVEL", "NÃO VERIFICADO"} and isinstance(efic, (int, float)) and math.isfinite(efic) else "N/A"
        rows_html += f"""<tr><td>{nome}</td><td>{sol}</td><td>{res}</td><td>{efic_str}</td><td class="{status_class}">{status}</td></tr>"""

    # Retorna o HTML da tabela para ser usado no memorial
    return f"""<table class="summary-table">
        <thead><tr><th>Verificação</th><th>Solicitante</th><th>Resistente</th><th>Eficiência</th><th>Status</th></tr></thead>
        <tbody>{rows_html}</tbody>
        <tfoot><tr><th colspan="4">Status global (inclui forças localizadas e escopo)</th><th>{res_flt.get('status_global', 'NÃO VERIFICADO')}</th></tr></tfoot>
    </table>"""
def main():
    # Esta chamada precisa ocorrer em toda execução do script. Quando ficava no
    # escopo do módulo, o cache de importação podia omiti-la após um refresh e o
    # Streamlit retornava ao contêiner central estreito do layout padrão.
    st.set_page_config(
        page_title="🏗️ Calculadora Estrutural - Perfis Metálicos",
        layout="wide",
        initial_sidebar_state="auto",
        menu_items={
            'Get Help': 'https://www.abnt.org.br',
            'Report a bug': None,
            'About': f"# Calculadora Estrutural\nCálculos baseados na {NORMA} + Errata 1:2025"
        }
    )

    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = None
    if 'detailed_analysis_html' not in st.session_state:
        st.session_state.detailed_analysis_html = None
    if 'analysis_mode' not in st.session_state:
        st.session_state.analysis_mode = "batch"
    if 'profile_efficiency_chart' not in st.session_state:
        st.session_state.profile_efficiency_chart = None

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

        Msd, Vsd, q_serv_kn_cm, p_load_serv = 0.0, 0.0, 0.0, None
        q_g_kn_cm = q_q_kn_cm = p_g_kn = p_q_kn = 0.0
        larg_esq_cm = larg_dir_cm = larg_inf_total_m = 0.0
        g_area = q_area = 0.0
        p_pos_cm = L_cm / 2.0
        point_bearing_cm = 10.0
        external_evidence = None
        include_self_weight = True
        gamma_g, gamma_q, gamma_self_weight = 1.50, 1.50, 1.25
        psi1, psi2 = 0.6, 0.4
        els_combination = 'rare'
        els_combination_text = 'Rara: G + Q principal'
        detalhes_esforcos_memorial = {'input_mode': input_mode, 'Msd': Msd, 'Vsd': Vsd, 'L_cm': L_cm}

        if input_mode == "Calcular a partir de Cargas na Viga":
            with st.container(border=True):
                st.subheader("Ações características")
                larg_esq_cm = st.number_input("Largura da laje à esquerda (cm)", 0.0, value=200.0, step=10.0, key='larg_esq_cm')
                larg_dir_cm = st.number_input("Largura da laje à direita (cm)", 0.0, value=200.0, step=10.0, key='larg_dir_cm')
                larg_inf_total_m = (larg_esq_cm + larg_dir_cm) / 200.0
                st.info(f"Largura de influência B = {larg_inf_total_m:.2f} m")
                g_area = st.number_input("Ação permanente adicional Gk (kN/m²)", 0.0, value=1.5, step=0.25, key='g_area')
                q_area = st.number_input("Ação variável Qk (kN/m²)", 0.0, value=3.0, step=0.25, key='q_area')
                q_g_kn_cm = g_area * larg_inf_total_m / 100.0
                q_q_kn_cm = q_area * larg_inf_total_m / 100.0
                q_serv_kn_cm = q_g_kn_cm + q_q_kn_cm

                st.subheader("Força pontual localizada")
                add_p_load = st.checkbox("Adicionar força pontual", key='add_p_load')
                if add_p_load:
                    p_g_kn = st.number_input("Parcela permanente Pg,k (kN)", 0.0, value=0.0, step=1.0, key='p_g_kn')
                    p_q_kn = st.number_input("Parcela variável Pq,k (kN)", 0.0, value=10.0, step=1.0, key='p_q_kn')
                    p_pos_cm = st.number_input("Posição x desde a esquerda (cm)", 0.0, max_value=L_cm, value=L_cm/2, key='p_pos_cm')
                    point_bearing_cm = st.number_input("Comprimento de atuação ℓn da força (cm)", 0.1, value=10.0, step=0.5, key='point_bearing_cm')
                    p_load_serv = (p_g_kn + p_q_kn, p_pos_cm)

                with st.expander("Combinações ELU/ELS", expanded=False):
                    include_self_weight = st.checkbox("Incluir peso próprio de cada perfil", value=True, key='include_self_weight')
                    gamma_g_label = st.selectbox(
                        "γg da ação permanente adicional — Tabela 1",
                        ("1,50 — elementos construtivos em geral", "1,40 — industrializados com adições in loco", "1,35 — moldados in loco", "1,30 — pré-moldados/madeira/industrializados", "1,25 — aço/equipamentos"),
                        key='gamma_g_label'
                    )
                    gamma_g = float(gamma_g_label[:4].replace(',', '.'))
                    gamma_q_label = st.selectbox(
                        "γq da ação variável principal — Tabela 1",
                        (
                            "1,50 — demais ações variáveis/ações agrupadas",
                            "1,40 — vento",
                            "1,20 — temperatura atmosférica ou ação truncada",
                        ),
                        key='gamma_q_label',
                    )
                    gamma_q = float(gamma_q_label[:4].replace(',', '.'))
                    categoria_psi = st.selectbox(
                        "Categoria da ação variável — Tabela 2",
                        ("Industrial/comercial/escritórios/público", "Residencial de acesso restrito", "Biblioteca/arquivo/depósito/oficina/garagem/cobertura"),
                        key='categoria_psi'
                    )
                    psi_values = {
                        "Industrial/comercial/escritórios/público": (0.7, 0.6, 0.4),
                        "Residencial de acesso restrito": (0.5, 0.4, 0.3),
                        "Biblioteca/arquivo/depósito/oficina/garagem/cobertura": (0.8, 0.7, 0.6),
                    }
                    _, psi1, psi2 = psi_values[categoria_psi]
                    els_label = st.selectbox(
                        "Combinação usada no deslocamento",
                        ("Rara: G + Q principal", "Frequente: G + ψ1 Q", "Quase permanente: G + ψ2 Q", "Somente parcela variável δ3: Q"),
                        key='els_label'
                    )
                    els_map = {
                        "Rara: G + Q principal": 'rare',
                        "Frequente: G + ψ1 Q": 'frequent',
                        "Quase permanente: G + ψ2 Q": 'quasi_permanent',
                        "Somente parcela variável δ3: Q": 'variable_only',
                    }
                    els_combination = els_map[els_label]
                    els_combination_text = els_label
        else:
            with st.container(border=True):
                st.warning("No modo manual, informe esforços já combinados. Sem reações e cargas de serviço, o aplicativo não pode auditar 5.7 nem o ELS.")
                Msd = st.number_input("Momento solicitante Msd (kN·m)", 0.0, value=100.0, key='msd_input') * 100.0
                Vsd = st.number_input("Força cortante Vsd (kN)", 0.0, value=50.0, key='vsd_input')
                st.markdown("#### Evidência externa")
                st.caption(
                    "Uma declaração isolada não conclui verificações. O documento permanece "
                    "separado dos cálculos executados pelo programa."
                )
                evidence_document_id = st.text_input(
                    "Identificação do documento", key="external_document_id"
                )
                evidence_revision = st.text_input(
                    "Revisão do documento", key="external_revision"
                )
                evidence_engineer = st.text_input(
                    "Engenheiro responsável", key="external_engineer"
                )
                evidence_registration = st.text_input(
                    "Registro profissional", key="external_registration"
                )
                evidence_date = st.date_input(
                    "Data do documento", value=datetime.now().date(), key="external_date"
                )
                evidence_checked_items = tuple(
                    st.multiselect(
                        "Itens cobertos pelo documento",
                        ("LOCAL_FORCES", "ELS_DEFLECTION"),
                        key="external_checked_items",
                    )
                )
                evidence_file = st.file_uploader(
                    "Arquivo da evidência", type=("pdf",), key="external_evidence_file"
                )
                if evidence_file is not None:
                    try:
                        external_evidence = ExternalEvidence(
                            document_id=evidence_document_id,
                            revision=evidence_revision,
                            responsible_engineer=evidence_engineer,
                            professional_registration=evidence_registration,
                            date=evidence_date,
                            file_hash=hashlib.sha256(evidence_file.getvalue()).hexdigest(),
                            checked_items=evidence_checked_items,
                        )
                        st.success(
                            "Evidência registrada para rastreabilidade; isso não transforma "
                            "verificação externa em cálculo aprovado pelo programa."
                        )
                    except ValueError as exc:
                        st.error(str(exc))
            detalhes_esforcos_memorial = {'input_mode': input_mode, 'Msd': Msd, 'Vsd': Vsd, 'L_cm': L_cm}

        st.markdown("---")
        st.markdown("### 🔩 Material e estabilidade lateral")
        material = st.selectbox("Aço estrutural (valores nominais)", ("ASTM A572 Grau 50", "ASTM A36", "Personalizado"), key='material')
        if material == "ASTM A572 Grau 50":
            fy_aco, fu_aco = 34.5, 45.0
        elif material == "ASTM A36":
            fy_aco, fu_aco = 25.0, 40.0
        else:
            fy_aco = st.number_input("fy nominal (kN/cm²)", 1.0, 45.0, 34.5, 0.5, key='fy_aco_custom')
            fu_aco = st.number_input("fu nominal (kN/cm²)", 1.0, 80.0, 45.0, 0.5, key='fu_aco_custom')
        E_aco_input = st.number_input("Módulo de elasticidade E (kN/cm²)", 1_000.0, value=20_000.0, step=100.0, key='E_aco_input')
        st.caption(f"fy = {fy_aco:.2f} kN/cm²; fu = {fu_aco:.2f} kN/cm²; fu/fy = {fu_aco/fy_aco:.3f}")
        for material_issue in validate_material(fy_aco, fu_aco):
            st.error(material_issue)
        material_qualified = st.checkbox(
            "Aço com qualificação estrutural assegurada e requisitos medidos de 4.6.2.2.1 atendidos",
            value=material != "Personalizado",
            key='material_qualified',
        )

        has_tension_flange_holes = st.checkbox(
            "Há furos para parafusos na mesa tracionada",
            value=False,
            key='has_tension_flange_holes',
        )
        tension_flange_net_ratio = 1.0
        if has_tension_flange_holes:
            tension_flange_net_ratio = st.number_input(
                "Relação Afn/Afg da mesa tracionada",
                min_value=0.01,
                max_value=1.00,
                value=0.85,
                step=0.01,
                key='tension_flange_net_ratio',
            )

        st.info(
            "A FLT permanece ativa. A não aplicabilidade somente poderá ser demonstrada "
            "por mesa e por segmento no modelo de contenções."
        )
        flt_applicable = True
        Lb_projeto = st.number_input("Comprimento destravado Lb (cm)", 1.0, max_value=L_cm, value=L_cm, step=1.0, key='Lb_projeto')
        lb_start_cm = st.number_input("Início do trecho destravado x0 (cm)", 0.0, max_value=max(L_cm-Lb_projeto, 0.0), value=0.0, step=1.0, key='lb_start_cm')
        load_height = st.selectbox(
            "Posição das forças transversais no trecho destravado",
            ("Semialtura da seção", "Abaixo da semialtura — adoção conservadora da semialtura", "Acima da semialtura sem contenção — exige análise de estabilidade"),
            key='load_height'
        )
        cantilever_standard_cb = True
        if tipo_viga == 'Engastada e Livre (Balanço)':
            cantilever_standard_cb = st.checkbox("Empenamento impedido no apoio e extremidade livre sem restrição lateral/torcional", value=True, key='cantilever_standard_cb')
        auto_cb_allowed = (
            input_mode == "Calcular a partir de Cargas na Viga"
            and flt_applicable
            and not load_height.startswith("Acima")
            and tipo_viga != 'Engastada e Livre (Balanço)'
        )
        cb_modo_auto = st.checkbox("Calcular Cb pelo diagrama no trecho Lb", value=auto_cb_allowed, disabled=not auto_cb_allowed, key='cb_modo_auto')
        Cb_projeto = 1.0
        cb_source = ""
        if tipo_viga == 'Engastada e Livre (Balanço)' and cantilever_standard_cb:
            Cb_projeto = 1.0
            st.info("Cb = 1,0 conforme 5.4.2.3-b para a condição declarada do balanço.")
        elif not cb_modo_auto and flt_applicable:
            Cb_projeto = st.number_input("Cb adotado", 0.1, 10.0, 1.0, step=0.05, key='Cb_projeto')
            cb_source = st.text_input("Origem do Cb manual (análise/procedimento)", key='cb_source')
        detalhes_cb_memorial = None

        with st.container(border=True):
            st.subheader("Enrijecedores transversais para cisalhamento")
            usa_enrijecedores = st.checkbox("Considerar enrijecedores", key='usa_enrijecedores')
            a_enr = 0.0
            stiffener_width = stiffener_thickness = None
            stiffener_welded = False
            if usa_enrijecedores:
                a_enr = st.number_input("Espaçamento a (cm)", 1.0, value=100.0, step=1.0, key='a_enr')
                stiffener_width = st.number_input("Largura de cada chapa bs (cm)", 0.1, value=10.0, step=0.5, key='stiffener_width')
                stiffener_thickness = st.number_input("Espessura ts (cm)", 0.1, value=0.8, step=0.1, key='stiffener_thickness')
                stiffener_welded = st.checkbox("Par de enrijecedores soldado à alma e às mesas conforme 5.4.3.1.3-a", value=False, key='stiffener_welded')

        with st.container(border=True):
            st.subheader("Forças localizadas — apoios e carga pontual")
            bearing_left_cm = st.number_input("Comprimento de apoio esquerdo ℓn (cm)", 0.1, value=10.0, step=0.5, key='bearing_left_cm')
            bearing_right_cm = st.number_input("Comprimento de apoio direito ℓn (cm)", 0.1, value=10.0, step=0.5, key='bearing_right_cm')
            support_relative_lateral_restrained = st.checkbox(
                "Nos apoios, o deslocamento lateral relativo entre as mesas é impedido",
                value=True,
                key='support_lateral_restrained',
            )
            point_relative_lateral_restrained = st.checkbox("Na carga pontual, o deslocamento lateral relativo entre mesas é impedido", value=False, key='point_lateral_restrained')
            loaded_flange_rotation_restrained = st.checkbox("A rotação da mesa carregada é impedida", value=False, key='loaded_flange_rotation')
            local_unbraced_cm = st.number_input("Comprimento destravado local ℓ (cm)", 1.0, value=Lb_projeto, step=1.0, key='local_unbraced_cm')
            weld_root_cm = st.number_input("Raiz do filete mesa–alma em perfis soldados (cm; 0 = conservador)", 0.0, value=0.0, step=0.1, key='weld_root_cm')
            support_torsion_restrained = st.checkbox("Apoios impedem rotação torcional ou a alma é ligada a outro elemento", value=True, key='support_torsion_restrained')

        st.markdown("---")
        st.markdown("### 📐 Estado-limite de serviço")
        service_category = st.selectbox("Categoria de deslocamento — Tabela B.1", ("Viga de piso — L/350", "Viga de cobertura — L/250", "Terça/travessa — L/250", "Viga que suporta pilar — L/500", "Personalizado"), key='service_category')
        service_divisors = {"Viga de piso — L/350": 350, "Viga de cobertura — L/250": 250, "Terça/travessa — L/250": 250, "Viga que suporta pilar — L/500": 500}
        limite_flecha_divisor = service_divisors.get(service_category)
        if limite_flecha_divisor is None:
            limite_flecha_divisor = st.number_input("Divisor personalizado x em L/x", 1.0, value=350.0, step=10.0, key='custom_deflection_divisor')
        masonry_on_beam = st.checkbox("Há alvenaria solidarizada sobre ou sob a viga (limite adicional 15 mm)", value=False, key='masonry_on_beam')

        unsupported_reasons = []
        with st.expander("Triagem de aplicabilidade obrigatória", expanded=False):
            has_axial_torsion = st.checkbox("Há força axial, torção ou flexão biaxial", key='scope_axial_torsion')
            has_web_openings = st.checkbox("Há aberturas na alma", key='scope_openings')
            has_fatigue = st.checkbox("Há mais de 20.000 ciclos relevantes de tensão (fadiga)", key='scope_fatigue')
            has_vibration = st.checkbox("O piso/sistema é suscetível a vibrações", key='scope_vibration')
            outside_ambient_scope = st.checkbox("Há incêndio, sismo ou perfil formado a frio", key='scope_external')
        if has_axial_torsion: unsupported_reasons.append("Interação com força axial/torção/flexão biaxial não verificada por este módulo.")
        if has_web_openings: unsupported_reasons.append("Aberturas na alma exigem o Anexo F e não foram modeladas.")
        if has_fatigue: unsupported_reasons.append("Fadiga aplicável: detalhamento e faixa de tensões do Anexo H não informados.")
        if has_vibration: unsupported_reasons.append("Vibrações aplicáveis: avaliação do Anexo I não realizada.")
        if outside_ambient_scope: unsupported_reasons.append("Situação fora do escopo à temperatura ambiente de perfis laminados/soldados.")
        if not material_qualified:
            unsupported_reasons.append(
                "Qualificação estrutural do aço e requisitos efetivamente medidos de 4.6.2.2.1 não confirmados."
            )
        if not support_torsion_restrained: unsupported_reasons.append("5.7.8 exige enrijecedores nos apoios/extremidades declarados sem restrição torcional e com alma livre.")
        standard_cantilever_cb = (
            tipo_viga == 'Engastada e Livre (Balanço)' and cantilever_standard_cb
        )
        if flt_applicable and not cb_modo_auto and not standard_cantilever_cb and not cb_source.strip():
            unsupported_reasons.append(
                "Cb manual sem origem documentada por análise de estabilidade ou procedimento técnico aceito."
            )

    projeto_info = {'nome': projeto_nome, 'engenheiro': engenheiro, 'data': data_projeto.strftime('%d/%m/%Y'), 'revisao': revisao}
    scope_notes = [
        "Viga prismática I/H duplamente simétrica, carregada no plano da alma e fletida no eixo forte.",
        "Análise elástica de primeira ordem; vinculações ideais selecionadas pelo usuário.",
        "Ações gravitacionais estáticas; valores característicos devem vir das normas de ações aplicáveis.",
        f"Material nominal: {material}; fy={compact_number(fy_aco,2)} kN/cm²; fu={compact_number(fu_aco,2)} kN/cm².",
    ]
    input_params = {
        'tipo_viga': tipo_viga, 'L_cm': L_cm, 'input_mode': input_mode, 'Msd': Msd, 'Vsd': Vsd,
        'q_serv_kn_cm': q_serv_kn_cm, 'p_load_serv': p_load_serv, 'q_g_kn_cm': q_g_kn_cm, 'q_q_kn_cm': q_q_kn_cm,
        'larg_esq_cm': larg_esq_cm, 'larg_dir_cm': larg_dir_cm,
        'larg_inf_total_m': larg_inf_total_m, 'g_area': g_area, 'q_area': q_area,
        'p_g_kn': p_g_kn, 'p_q_kn': p_q_kn, 'p_pos_cm': p_pos_cm,
        'fy_aco': fy_aco, 'fu_aco': fu_aco, 'E_aco': E_aco_input,
        'has_tension_flange_holes': has_tension_flange_holes,
        'tension_flange_net_ratio': tension_flange_net_ratio,
        'Lb_projeto': Lb_projeto, 'lb_start_cm': lb_start_cm, 'Cb_projeto': Cb_projeto,
        'flt_applicable': flt_applicable, 'cb_modo_auto': cb_modo_auto, 'cb_source': cb_source,
        'cantilever_standard_cb': cantilever_standard_cb,
        'detalhes_esforcos_memorial': detalhes_esforcos_memorial, 'detalhes_cb_memorial': detalhes_cb_memorial,
        'usa_enrijecedores': usa_enrijecedores, 'a_enr': a_enr,
        'stiffener_width': stiffener_width, 'stiffener_thickness': stiffener_thickness,
        'stiffener_pair': True, 'stiffener_welded': stiffener_welded,
        'bearing_left_cm': bearing_left_cm, 'bearing_right_cm': bearing_right_cm,
        'support_relative_lateral_restrained': support_relative_lateral_restrained,
        'point_bearing_cm': point_bearing_cm, 'point_relative_lateral_restrained': point_relative_lateral_restrained,
        'loaded_flange_rotation_restrained': loaded_flange_rotation_restrained,
        'local_unbraced_cm': local_unbraced_cm, 'weld_root_cm': weld_root_cm,
        'limite_flecha_divisor': limite_flecha_divisor, 'masonry_on_beam': masonry_on_beam,
        'include_self_weight': include_self_weight, 'gamma_g': gamma_g, 'gamma_q': gamma_q,
        'gamma_self_weight': gamma_self_weight, 'els_combination': els_combination,
        'els_combination_text': els_combination_text, 'psi1': psi1, 'psi2': psi2,
        'elu_combination_text': f'{compact_number(gamma_g,2)}·G + {compact_number(gamma_self_weight,2)}·PP aço + {compact_number(gamma_q,2)}·Q',
        'external_evidence': external_evidence,
        'unsupported_reasons': unsupported_reasons, 'scope_notes': scope_notes,
        'projeto_info': projeto_info,
    }

    create_metrics_dashboard(input_params)

    # st.markdown("### 🎯 Modo de Análise") # <- Esta linha foi removida
    st.subheader("🎯 Modo de Análise") # <- Substituída por esta
    
    col1, col2 = st.columns(2)
    if col1.button("📊 Análise em Lote e Otimização", use_container_width=True, type="secondary"):
        st.session_state.analysis_mode = "batch"
    if col2.button("📋 Memorial Detalhado de Perfil", use_container_width=True, type="secondary"):
        st.session_state.analysis_mode = "detailed"

    if st.session_state.analysis_mode == "batch":
        # st.header("📊 Análise em Lote") # <- Esta linha foi removida
        st.subheader("📊 Análise em Lote") # <- Substituída por esta
        
        if st.button("🚀 Iniciar Análise Otimizada", type="primary", use_container_width=True):
            run_batch_analysis(all_sheets, input_params)
        
        if st.session_state.analysis_results is not None:
            df_all_results = st.session_state.analysis_results
            
            tabs = st.tabs([PROFILE_TYPE_MAP.get(name, name) for name in all_sheets.keys()])
            for i, sheet_name in enumerate(all_sheets.keys()):
                with tabs[i]:
                    df_type = df_all_results[df_all_results['Tipo'] == sheet_name].drop(columns=['Tipo'])
                    df_aprovados_cat = df_type[df_type['Status'] == APPROVED_SCOPE_TEXT].copy().sort_values(by='Peso (kg/m)')
                    df_reprovados_cat = df_type[df_type['Status'] == 'REPROVADO'].copy().sort_values(by='Peso (kg/m)')
                    df_pendentes_cat = df_type[df_type['Status'] == 'NÃO VERIFICADO'].copy().sort_values(by='Peso (kg/m)')

                    # Botão de download para todos os resultados em uma aba
                    if not df_type.empty:
                        df_total = pd.concat([df_aprovados_cat, df_reprovados_cat, df_pendentes_cat])
                        excel_data = create_excel_with_colors([df_total], [f"{sheet_name}_Resultados"])
                        st.download_button(
                            label=f"📥 Baixar todos os resultados ({sheet_name}) em XLSX",
                            data=excel_data,
                            file_name=f"resultados_{sheet_name}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )

                    if not df_aprovados_cat.empty:
                        st.plotly_chart(create_top_profiles_chart(df_aprovados_cat), use_container_width=True)
                        with st.expander(f"Ver todos os {len(df_aprovados_cat)} perfis aprovados"):
                            st.dataframe(style_classic_dataframe(df_aprovados_cat), use_container_width=True)
                    else:
                        st.info("Nenhum perfil aprovado nesta categoria.")

                    if not df_reprovados_cat.empty:
                        with st.expander(f"Ver os {len(df_reprovados_cat)} perfis reprovados"):
                            st.dataframe(style_classic_dataframe(df_reprovados_cat), use_container_width=True)

                    if not df_pendentes_cat.empty:
                        with st.expander(f"Ver os {len(df_pendentes_cat)} perfis não verificados"):
                            st.dataframe(style_classic_dataframe(df_pendentes_cat), use_container_width=True)

    elif st.session_state.analysis_mode == "detailed":
        # st.header("📋 Memorial Detalhado") # <- Esta linha foi removida
        st.subheader("📋 Memorial Detalhado") # <- Substituída por esta
        
        display_names = [PROFILE_TYPE_MAP.get(name, name) for name in all_sheets.keys()]
        reverse_name_map = {v: k for k, v in PROFILE_TYPE_MAP.items()}

        col1, col2 = st.columns(2)
        selected_display_name = col1.selectbox("Selecione o Tipo de Perfil:", display_names)
        sheet_name = reverse_name_map.get(selected_display_name, selected_display_name)
        df_selecionado = all_sheets[sheet_name]
        perfil_selecionado_nome = col2.selectbox("Selecione o Perfil Específico:", df_selecionado['Bitola (mm x kg/m)'])

        if st.button("📄 Gerar Memorial Completo", type="primary", use_container_width=True):
            run_detailed_analysis(df_selecionado, perfil_selecionado_nome, selected_display_name, input_params)

        if st.session_state.detailed_analysis_html:
            with st.expander("📊 Resumo Visual da Análise", expanded=True):
                st.plotly_chart(st.session_state.profile_efficiency_chart, use_container_width=True)

            with st.expander("📄 Visualização do Memorial", expanded=True):
                # O memorial é deliberadamente extenso; a altura maior evita que
                # o leitor precise alternar entre duas barras de rolagem a cada etapa.
                st.components.v1.html(st.session_state.detailed_analysis_html, height=9000, scrolling=True)
            
            st.download_button(
                label="📥 Baixar Memorial em HTML",
                data=st.session_state.detailed_analysis_html.encode('utf-8'),
                file_name=f"Memorial_{perfil_selecionado_nome.replace(' ', '_')}.html",
                mime="text/html",
                use_container_width=True
            )

def run_detailed_analysis(df, perfil_nome, perfil_tipo_display, input_params):
    with st.spinner(f"Gerando análise completa para {perfil_nome}..."):
        try:
            perfil_series = df[df['Bitola (mm x kg/m)'] == perfil_nome].iloc[0]
            props = get_profile_properties(perfil_series)

            tipo_fabricacao = "Soldado" if "Soldado" in perfil_tipo_display else "Laminado"
            # A análise, as combinações e Cb são agora documentados no bloco normativo 2024.
            esforcos_html = ""
            cb_calc_html = ""

            res_flt, res_flm, res_fla, res_cis, res_flecha, passo_a_passo = perform_all_checks(
                props=props, detalhado=True, tipo_fabricacao=tipo_fabricacao, **input_params
            )
            
            eficiencias = {
                "FLT": res_flt['eficiencia'],
                "FLM": res_flm['eficiencia'],
                "FLA": res_fla['eficiencia'],
                "Cisalhamento": res_cis['eficiencia'],
                "Flecha": res_flecha['eficiencia'],
            }
            if res_flt.get('rupture_status') not in {'N/A', 'NÃO APLICÁVEL'}:
                eficiencias["Ruptura da mesa"] = res_flt['rupture_efficiency']
            st.session_state.profile_efficiency_chart = create_profile_efficiency_chart(perfil_nome, eficiencias)
            
            resumo_html = build_summary_html(res_flt['Msd'], res_cis['Vsd'], res_flt, res_flm, res_fla, res_cis, res_flecha)
            resultados = {'resumo_html': resumo_html, 'passo_a_passo_html': passo_a_passo, 'esforcos_html': esforcos_html, 'cb_calc_html': cb_calc_html}
            
            html_content = create_professional_memorial_html(
                perfil_nome, perfil_tipo_display, resultados,
                f"""
                
                <div style="text-align: left;">
                    <p><strong>Módulo de Elasticidade (E):</strong> {compact_number(input_params['E_aco'],2)} kN/cm²</p>
                    <p><strong>Tensão de Escoamento (fy):</strong> {compact_number(input_params['fy_aco'],2)} kN/cm²</p>
                    <p><strong>Tensão de Ruptura (fu):</strong> {compact_number(input_params['fu_aco'],2)} kN/cm²</p>
                    <p><strong>Altura total (d):</strong> {compact_number(perfil_series.get('d (mm)'),2)} mm</p>
                    <p><strong>Largura da Mesa (bf):</strong> {compact_number(perfil_series.get('bf (mm)'),2)} mm</p>
                    <p><strong>Espessura da Alma (tw):</strong> {compact_number(perfil_series.get('tw (mm)'),2)} mm</p>
                    <p><strong>Espessura da Mesa (tf):</strong> {compact_number(perfil_series.get('tf (mm)'),2)} mm</p>
                    <p><strong>Distância entre faces internas (h):</strong> {compact_number(perfil_series.get('h (mm)'),2)} mm</p>
                    <p><strong>Altura livre da alma (d′):</strong> {compact_number(perfil_series.get("d' (mm)"),2)} mm</p>
                    <p><strong>Área (A):</strong> {compact_number(perfil_series.get('Área (cm2)'),2)} cm²</p>
                    <p><strong>Inércia Ix:</strong> {compact_number(perfil_series.get('Ix (cm4)'),2)} cm⁴</p>
                    <p><strong>Módulo de Seção Elástico (Wx):</strong> {compact_number(perfil_series.get('Wx (cm3)'),2)} cm³</p>
                    <p><strong>Raio de Giração (rx):</strong> {compact_number(props.get('rx'),2)} cm</p>
                    <p><strong>Módulo de Seção Plástico (Zx):</strong> {compact_number(props.get('Zx'),2)} cm³</p>
                    <p><strong>Inércia Iy:</strong> {compact_number(props.get('Iy'),2)} cm⁴</p>
                    <p><strong>Raio de Giração (ry):</strong> {compact_number(props.get('ry'),2)} cm</p>
                    <p><strong>Constante de Torção (J):</strong> {compact_number(props.get('J'),2)} cm⁴</p>
                    <p><strong>Constante de Empenamento (Cw):</strong> {compact_number(props.get('Cw'),2)} cm⁶</p>
                </div>
                """, input_params['projeto_info']
            )
            st.session_state.detailed_analysis_html = html_content
        except Exception as e:
            st.error(f"❌ Ocorreu um erro: {e}")

def run_batch_analysis(all_sheets, input_params):
    all_results = []
    progress_bar = st.progress(0, text="Analisando perfis...")
    total_perfis = sum(len(df) for df in all_sheets.values())
    perfis_processados = 0
    
    for sheet_name, df in all_sheets.items():
        tipo_fabricacao_auto = PROFILE_FABRICATION_MAP.get(sheet_name, "Laminado")
        
        for _, row in df.iterrows():
            perfis_processados += 1
            progress_bar.progress(perfis_processados / total_perfis, text=f"Analisando: {row['Bitola (mm x kg/m)']}")
            try:
                props = get_profile_properties(row)
                res_flt, res_flm, res_fla, res_cis, res_flecha, _ = perform_all_checks(
                    props=props, tipo_fabricacao=tipo_fabricacao_auto, **input_params
                )
                
                status_geral = res_flt.get('status_global', 'NÃO VERIFICADO')
                local_efficiencies = [item['efficiency'] for item in res_cis.get('local_checks', [])]
                max_local_efficiency = max(local_efficiencies, default=0.0)
                
                all_results.append({
                    'Tipo': sheet_name, 'Perfil': row['Bitola (mm x kg/m)'],
                    'Peso (kg/m)': props.get('Peso', 0), 'Status': status_geral,
                    'Ef. FLT (%)': res_flt['eficiencia'], 'Ef. FLM (%)': res_flm['eficiencia'],
                    'Ef. FLA (%)': res_fla['eficiencia'], 'Ef. Cisalhamento (%)': res_cis['eficiencia'],
                    'Ef. Ruptura Mesa (%)': (
                        res_flt['rupture_efficiency']
                        if res_flt.get('rupture_status') not in {'N/A', 'NÃO APLICÁVEL'} else None
                    ),
                    'Ef. Forças Locais (%)': max_local_efficiency,
                    'Ef. Flecha (%)': res_flecha['eficiencia']
                })
            except (ValueError, KeyError) as exc:
                all_results.append({
                    'Tipo': sheet_name, 'Perfil': row.get('Bitola (mm x kg/m)', 'N/D'),
                    'Peso (kg/m)': row.get('Massa Linear (kg/m)', 0), 'Status': 'NÃO VERIFICADO',
                    'Observação': str(exc),
                })
    progress_bar.empty()
    st.session_state.analysis_results = pd.DataFrame(all_results) if all_results else pd.DataFrame()

if __name__ == '__main__':
    main()
