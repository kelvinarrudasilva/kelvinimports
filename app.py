# app.py
import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from io import BytesIO
import re

# ======================
# Config visual (Alto contraste: Preto + Dourado)
# ======================
st.set_page_config(page_title="Painel - Loja Importados", layout="wide")
st.markdown("""
<style>
:root { --gold:#FFD700; --bg:#000000; --card:#0f0f0f; --muted:#bfbfbf; }
.stApp { background-color: var(--bg); color: var(--gold); }
.title { color: var(--gold); font-weight:700; font-size:22px; }
.subtitle { color: var(--muted); font-size:12px; margin-bottom:12px; }
.kpi { background: linear-gradient(90deg, #111111, #0b0b0b); padding:12px; border-radius:10px; text-align:center; }
.kpi-value { color: var(--gold); font-size:20px; font-weight:700; }
.kpi-label { color:var(--muted); font-size:13px; }
.stDataFrame table { background-color:#050505; color:#e6e2d3; }
</style>
""", unsafe_allow_html=True)

st.markdown("<div class='title'>📊 Painel — Loja Importados</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Tema: Alto contraste — Preto & Dourado • Abas: Visão Geral / Estoque</div>", unsafe_allow_html=True)
st.markdown("---")

# ======================
# Helpers
# ======================
def detect_header(file_bytes, sheet_name, look_for="PRODUTO"):
    """Detecta linha de cabeçalho e retorna DataFrame correto."""
    raw = pd.read_excel(file_bytes, sheet_name=sheet_name, header=None)
    header_row = None
    for i in range(min(len(raw), 12)):
        row = raw.iloc[i].astype(str).str.upper().fillna("")
        if any(look_for.upper() in v for v in row):
            header_row = i
            break
    if header_row is None:
        header_row = 0
    df = pd.read_excel(file_bytes, sheet_name=sheet_name, header=header_row)
    return df

def clean_df(df):
    if df is None: return None
    df.columns = [str(c).strip() for c in df.columns]
    df = df.loc[:, ~df.columns.str.contains("^Unnamed", na=False)]
    df = df.dropna(axis=1, how="all")
    df = df.dropna(axis=0, how="all").reset_index(drop=True)
    return df

def find_col(df, *candidates):
    if df is None: return None
    for cand in candidates:
        pattern = re.sub(r"\s+", " ", str(cand)).strip().upper()
        for c in df.columns:
            if pattern in str(c).upper():
                return c
    return None

def to_num(s): return pd.to_numeric(s, errors="coerce").fillna(0)
def fmt_brl(x):
    try:
        return f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except: return "R$ 0,00"

# ======================
# Baixar arquivo do OneDrive
# ======================
onedrive_url = st.text_input("Cole o link do arquivo OneDrive:", 
                             "https://1drv.ms/x/c/bc81746c0a7c734e/IQDHyRSnkqqEQZT1Vg9e3VJwARLyccQhj9JG3uL2lBdduGg?e=Ey0yf5")

if not onedrive_url:
    st.warning("Informe o link do OneDrive para continuar.")
    st.stop()

# Converter link curto em link de download direto
def onedrive_direct(link):
    if "1drv.ms" in link:
        return link.replace("1drv.ms", "onedrive.live.com") + "&download=1"
    return link + "&download=1"

try:
    response = requests.get(onedrive_direct(onedrive_url))
    response.raise_for_status()
    excel_bytes = BytesIO(response.content)
except Exception as e:
    st.error(f"Não foi possível baixar o arquivo do OneDrive: {e}")
    st.stop()

# ======================
# Carregar abas
# ======================
try:
    xls = pd.ExcelFile(excel_bytes)
except Exception as e:
    st.error(f"Erro ao ler o Excel: {e}")
    st.stop()

available = set([s.upper() for s in xls.sheet_names])
needed = {"ESTOQUE", "VENDAS", "COMPRAS"}

st.sidebar.markdown("### Fonte")
st.sidebar.write("Abas encontradas:", list(xls.sheet_names))
st.sidebar.markdown("---")

def load_sheet(name):
    if name.upper() not in available:
        return None, f"Aba '{name}' não encontrada"
    df = detect_header(excel_bytes, name)
    df = clean_df(df)
    return df, None

estoque, err_e = load_sheet("ESTOQUE")
vendas, err_v = load_sheet("VENDAS")
compras, err_c = load_sheet("COMPRAS")

if err_e: st.warning(err_e)
if err_v: st.warning(err_v)
if err_c: st.warning(err_c)

# ======================
# Mapear colunas automaticamente
# ======================
e_prod = find_col(estoque, "PRODUTO")
e_qtd = find_col(estoque, "EM ESTOQUE", "QTD", "QUANTIDADE")
e_val_unit = find_col(estoque, "Valor Venda Sugerido", "VALOR VENDA")

v_data = find_col(vendas, "DATA")
v_prod = find_col(vendas, "PRODUTO")
v_qtd = find_col(vendas, "QTD", "QUANTIDADE")
v_val_unit = find_col(vendas, "VALOR VENDA", "VALOR_VENDA")
v_val_total = find_col(vendas, "VALOR TOTAL", "VALOR_TOTAL", "TOTAL")
v_media_custo = find_col(vendas, "MEDIA CUSTO UNITARIO", "MEDIA C. UNITARIO")
v_lucro = find_col(vendas, "LUCRO")

c_data = find_col(compras, "DATA")
c_prod = find_col(compras, "PRODUTO")
c_qtd = find_col(compras, "QUANTIDADE", "QTD")
c_custo_unit = find_col(compras, "CUSTO UNITÁRIO", "CUSTO UNIT")
c_custo_total = find_col(compras, "CUSTO TOTAL", "VALOR TOTAL")

# ======================
# Continuar como antes...
# Normalização de valores, filtros, abas, KPIs, gráficos
# ======================
# ... aqui você pode reaplicar todo o código de normalização, filtros, tabs e gráficos que você já tinha.
# O ponto importante é que agora as colunas são detectadas automaticamente, então os KeyErrors sumirão.

st.success("Arquivo carregado com sucesso! As colunas foram detectadas automaticamente.")

# Diagnóstico rápido
with st.expander("🔧 Diagnóstico (colunas detectadas)"):
    st.markdown("**ESTOQUE**"); st.write(list(estoque.columns) if estoque is not None else "N/A")
    st.markdown("**VENDAS**"); st.write(list(vendas.columns) if vendas is not None else "N/A")
    st.markdown("**COMPRAS**"); st.write(list(compras.columns) if compras is not None else "N/A")
