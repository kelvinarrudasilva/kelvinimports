# app.py
import streamlit as st
import pandas as pd
import plotly.express as px
import re
from datetime import datetime

# ======================
# Config visual (Alto contraste: Preto + Dourado)
# ======================
st.set_page_config(page_title="Painel - Loja Importados", layout="wide")

st.markdown(
    """
    <style>
      :root { --gold:#FFD700; --bg:#000000; --card:#0f0f0f; --muted:#bbbbbb; --white:#FFFFFF; }
      .stApp { background-color: var(--bg); color: var(--gold); }
      .title { color: var(--gold); font-weight:700; font-size:22px; }
      .subtitle { color: var(--muted); font-size:12px; margin-bottom:12px; }
      .kpi { background: linear-gradient(90deg, #111111, #0b0b0b); padding:12px; border-radius:10px; text-align:center; }
      .kpi-value { color: var(--gold); font-size:22px; font-weight:700; }
      .kpi-label { color:var(--muted); font-size:13px; }
      .stDataFrame table { background-color:#050505; color:var(--white); }
      .small { color: var(--muted); font-size:12px; }
      .table-card { background: linear-gradient(90deg,#0b0b0b,#111111); border: 1px solid rgba(255,215,0,0.08); padding:12px; border-radius:10px; }
      .table-card h4 { color: var(--gold); margin:0 0 8px 0; }
      .table-card .big { font-size:15px; color:var(--white); }
      .small-select .stSelectbox>div>div { font-size:14px; }
      .summary-table .dataframe td, .summary-table .dataframe th { font-size:13px !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown("<div class='title'>📊 Painel — Loja Importados</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Tema: Preto & Dourado (alto contraste) • Abas: Visão Geral / Estoque / Vendas</div>", unsafe_allow_html=True)
st.markdown("---")

# ======================
# Helpers: detect header, clean df, find_col, numeric, fmt
# ======================
def detect_header(path, sheet_name, look_for="PRODUTO"):
    try:
        raw = pd.read_excel(path, sheet_name=sheet_name, header=None)
    except Exception:
        return None, None
    header_row = None
    for i in range(min(len(raw), 12)):
        row = raw.iloc[i].astype(str).str.upper().fillna("")
        if any(look_for.upper() in v for v in row):
            header_row = i
            break
    if header_row is None:
        header_row = 0
    try:
        df = pd.read_excel(path, sheet_name=sheet_name, header=header_row)
        return df, header_row
    except Exception:
        return None, None

def clean_df(df):
    if df is None:
        return None
    df.columns = [str(c).strip() for c in df.columns]
    df = df.loc[:, ~df.columns.str.contains("^Unnamed", na=False)]
    df = df.dropna(axis=1, how="all")
    df = df.dropna(axis=0, how="all").reset_index(drop=True)
    return df

def find_col(df, *candidates):
    if df is None:
        return None
    for cand in candidates:
        if cand is None:
            continue
        pat = re.sub(r"\s+", " ", str(cand)).strip().upper()
        for c in df.columns:
            if pat in str(c).upper():
                return c
    return None

def to_num(s):
    return pd.to_numeric(s, errors="coerce").fillna(0)

def fmt_brl(x):
    try:
        return f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "R$ 0,00"

# ======================
# Load file from Google Drive
# ======================
GDRIVE_EXCEL = "https://drive.google.com/uc?id=1TsRjsfw1TVfeEWBBvhKvsGQ5YUCktn2b"

try:
    xls = pd.ExcelFile(GDRIVE_EXCEL)
    available_sheets = [s.upper() for s in xls.sheet_names]
except Exception as e:
    st.error(f"Erro ao acessar planilha do Google Drive: {e}")
    st.stop()

def load_and_clean(name):
    if name not in available_sheets:
        return None
    df, hdr = detect_header(GDRIVE_EXCEL, name)
    df = clean_df(df)
    return df

estoque = load_and_clean("ESTOQUE")
vendas = load_and_clean("VENDAS")
compras = load_and_clean("COMPRAS")

# safe empty frames to avoid many ifs
if vendas is None:
    vendas = pd.DataFrame()
if estoque is None:
    estoque = pd.DataFrame()
if compras is None:
    compras = pd.DataFrame()

# ======================
# O resto do seu app continua igual: mapeamento de colunas, preparação numérica, abas, gráficos, KPIs...
# ======================
