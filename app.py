# app.py
import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
import re
from datetime import datetime

# ======================
# CONFIG GOOGLE SHEETS
# ======================
BASE_SHEET = "1TsRjsfw1TVfeEWBBvhKvsGQ5YUCktn2b"

URL_ESTOQUE = f"https://docs.google.com/spreadsheets/d/{BASE_SHEET}/export?format=xlsx&gid=686416620"
URL_VENDAS  = f"https://docs.google.com/spreadsheets/d/{BASE_SHEET}/export?format=xlsx&gid=1438389679"
URL_COMPRAS = f"https://docs.google.com/spreadsheets/d/{BASE_SHEET}/export?format=xlsx&gid=466603396"

def load_sheet(url):
    try:
        df = pd.read_excel(url)
        return df
    except Exception as e:
        st.error(f"Erro ao carregar planilha: {e}")
        return pd.DataFrame()

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
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown("<div class='title'>📊 Painel — Loja Importados</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Tema: Preto & Dourado • Abas: Visão Geral / Estoque / Vendas</div>", unsafe_allow_html=True)
st.markdown("---")

# ======================
# Helpers originais (mantidos)
# ======================
def detect_header(df, look_for="PRODUTO"):
    header_row = None
    for i in range(min(len(df), 12)):
        row = df.iloc[i].astype(str).str.upper().fillna("")
        if any(look_for.upper() in v for v in row):
            header_row = i
            break
    return header_row if header_row is not None else 0

def clean_df(df):
    if df is None or df.empty:
        return pd.DataFrame()
    df.columns = [str(c).strip() for c in df.columns]
    df = df.loc[:, ~df.columns.str.contains("^Unnamed", na=False)]
    df = df.dropna(axis=1, how="all")
    df = df.dropna(axis=0, how="all").reset_index(drop=True)
    return df

def find_col(df, *candidates):
    if df is None:
        return None
    for cand in candidates:
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
# LOAD — agora via Google Sheets
# ======================
def load_and_clean_url(url):
    df_raw = load_sheet(url)
    if df_raw.empty:
        return pd.DataFrame()
    hdr = detect_header(df_raw)
    df = df_raw.iloc[hdr:].reset_index(drop=True)
    df.columns = df_raw.iloc[hdr].values
    return clean_df(df)

estoque = load_and_clean_url(URL_ESTOQUE)
vendas  = load_and_clean_url(URL_VENDAS)
compras = load_and_clean_url(URL_COMPRAS)

if vendas is None:
    vendas = pd.DataFrame()
if estoque is None:
    estoque = pd.DataFrame()
if compras is None:
    compras = pd.DataFrame()

# ======================
# ⬇ DAQUI PARA BAIXO — NADA MUDOU
# ======================

# (todo resto do seu código permanece idêntico)  
# KPI, tabs, gráficos, tabelas, diagnósticos, etc.

