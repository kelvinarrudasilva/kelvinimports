# ============================================
#  app.py — Dashboard Loja Importados (v. Busca Premium)
#  Kelvin Edition — Dark Purple Vision
# ============================================

import streamlit as st
import pandas as pd
import plotly.express as px
import re
from datetime import datetime, timedelta
import numpy as np
import requests
from io import BytesIO

# -------------------------------------------------
# CONFIG INICIAL
# -------------------------------------------------
st.set_page_config(
    page_title="Loja Importados – Dashboard IA",
    layout="wide",
    initial_sidebar_state="collapsed"
)

URL_PLANILHA = "https://docs.google.com/spreadsheets/d/1TsRjsfw1TVfeEWBBvhKvsGQ5YUCktn2b/export?format=xlsx"

# -------------------------------------------------
# CSS — Dark Theme + Busca Premium
# -------------------------------------------------
st.markdown("""
<style>
:root {
  --bg: #0b0b0b;
  --accent: #8b5cf6;
  --accent-2: #a78bfa;
  --muted: #bdbdbd;
  --card-bg: #141414;
}
body, .stApp { background: var(--bg) !important; color: #f0f0f0 !important; }

/* KPIs */
.kpi-row { display:flex; gap:12px; flex-wrap:wrap; margin-top:20px; }
.kpi {
  background: var(--card-bg); padding:14px 18px; border-radius:12px;
  box-shadow:0 6px 16px rgba(0,0,0,0.45); border-left:6px solid var(--accent);
  min-width:170px;
}
.kpi h3 { margin:0; font-size:12px; color:var(--accent-2); }
.kpi .value { margin-top:6px; font-size:22px; font-weight:900; }

/* TABS */
.stTabs button {
  background:#1e1e1e !important; border:1px solid #333 !important;
  border-radius:12px !important; padding:8px 14px !important;
  font-weight:700 !important; color:var(--accent-2) !important;
  margin-right:8px !important;
}

/* Busca Premium */
.search-box input {
    background: rgba(255,255,255,0.06) !important;
    padding: 12px 14px !important;
    border-radius: 10px !important;
    border: 1px solid #333 !important;
    font-size: 15px !important;
    color: #fff !important;
}
.filter-pill {
    display:inline-block;
    padding:6px 14px;
    background:#1b1b1b;
    border:1px solid #333;
    color:#dcdcdc;
    border-radius:50px;
    margin-right:6px;
    font-size:12px;
    cursor:pointer;
}
.filter-pill:hover {
    background:#262626;
    border-color:#555;
}
.card-grid {
    display:grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap:16px;
    margin-top:20px;
}
.product-card {
    background:#141414;
    padding:16px;
    border-radius:14px;
    box-shadow:0 4px 14px rgba(0,0,0,0.55);
    border:1px solid rgba(255,255,255,0.05);
}
.product-title {
    font-size:16px;
    font-weight:800;
    color:#a78bfa;
}
.card-badge {
    display:inline-block;
    padding:4px 10px;
    background:#222;
    border-radius:8px;
    margin-right:5px;
    font-size:11px;
}
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------
# FUNÇÕES AUXILIARES
# -------------------------------------------------
def parse_money_value(x):
    try:
        if pd.isna(x): return float("nan")
    except: pass
    s = str(x).strip()
    s = re.sub(r"[^\d\.,\-]", "", s)
    if "." in s and "," in s: s = s.replace(".","").replace(",",".")
    else:
        if "," in s: s = s.replace(",",".")
    try: return float(s)
    except: return float("nan")

def parse_money_series(s):
    return s.astype(str).map(parse_money_value)

def formatar_reais_com_centavos(v):
    try: v=float(v)
    except: return "R$ 0,00"
    s=f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {s}"

def formatar_reais_sem_centavos(v):
    try: v=float(v)
    except: return "R$ 0"
    s=f"{v:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {s}"

def carregar_xlsx_from_url(url):
    r=requests.get(url, timeout=25)
    r.raise_for_status()
    return pd.ExcelFile(BytesIO(r.content))

def detectar_linha_cabecalho(df_raw, keywords):
    for i in range(12):
        linha = " ".join(df_raw.iloc[i].astype(str).str.upper().tolist())
        if any(k.upper() in linha for k in keywords):
            return i
    return None

def limpar_aba_raw(df_raw, nome):
    busca = {"ESTOQUE":["PRODUTO","ESTOQUE"],"VENDAS":["DATA","PRODUTO"],"COMPRAS":["DATA","CUSTO"]}.get(nome,["PRODUTO"])
    linha = detectar_linha_cabecalho(df_raw, busca)
    if linha is None: return None
    tmp = df_raw.copy()
    tmp.columns = tmp.iloc[linha]
    df = tmp.iloc[linha+1:].copy()
    df.columns = [str(c).strip() for c in df.columns]
    df = df.loc[:, ~df.columns.astype(str).str.contains("Unnamed")]
    return df.reset_index(drop=True)

# -------------------------------------------------
# CARREGAR PLANILHA
# -------------------------------------------------
try:
    xls = carregar_xlsx_from_url(URL_PLANILHA)
except:
    st.error("Não foi possível carregar a planilha.")
    st.stop()

abas = xls.sheet_names
dfs = {}

for aba in ["ESTOQUE","VENDAS","COMPRAS"]:
    if aba in abas:
        raw = pd.read_excel(URL_PLANILHA, sheet_name=aba, header=None)
        dfs[aba] = limpar_aba_raw(raw, aba)
