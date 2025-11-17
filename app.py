# app.py — Loja Importados Dashboard (Dark Roxo Finalíssimo)
# COMPLETO — Tabelas dark + Top10 QTD em pizza com destaque

import streamlit as st
import pandas as pd
import plotly.express as px
import re
from datetime import datetime
import requests
from io import BytesIO

# ============================
# CONFIGURAÇÃO DA PÁGINA
# ============================
st.set_page_config(
    page_title="Loja Importados – Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed"
)

URL_PLANILHA = "https://docs.google.com/spreadsheets/d/1TsRjsfw1TVfeEWBBvhKvsGQ5YUCktn2b/export?format=xlsx"

# ============================
# CSS — DARK TOTAL
# ============================
st.markdown("""
<style>
:root{
  --bg:#0b0b0b;
  --accent:#8b5cf6;
  --accent-2:#a78bfa;
  --muted:#bdbdbd;
  --card-bg:#141414;
  --table-bg:#111;
  --table-head:#202020;
  --table-row:#181818;
}
body, .stApp {
  background: var(--bg) !important;
  color:#f0f0f0 !important;
  font-family: Inter, system-ui;
}

/* Tabelas totalmente DARK */
.stDataFrame, .stTable, .dataframe {
    background: var(--table-bg) !important;
    color: #f0f0f0 !important;
}
.stDataFrame thead th, .dataframe thead th {
    background: var(--table-head) !important;
    color:#fff !important;
    font-weight:700 !important;
}
.stDataFrame tbody tr td, .dataframe tbody tr td {
    background: var(--table-row) !important;
    color:#eaeaea !important;
}

/* Scroll */
::-webkit-scrollbar { width: 8px; height:8px; }
::-webkit-scrollbar-track { background:#111; }
::-webkit-scrollbar-thumb { background:#333; border-radius:10px; }

/* Top bar */
.topbar { display:flex; gap:12px; margin-bottom:8px; align-items:center; }
.logo-wrap {
    width:44px; height:44px; border-radius:10px;
    background: linear-gradient(135deg,var(--accent),var(--accent-2));
}
.title { font-size:20px; font-weight:800; color:var(--accent-2); }
.subtitle { font-size:12px; color:var(--muted); }

/* KPIs */
.kpi-row { display:flex; gap:10px; flex-wrap:wrap; margin-bottom:20px; }
.kpi {
    background:var(--card-bg);
    border-radius:10px;
    padding:10px 14px;
    border-left:6px solid var(--accent);
}
.kpi h3 { font-size:12px; font-weight:800; color:var(--accent-2); margin:0; }
.kpi .value { font-size:20px; margin-top:6px; font-weight:900; }

/* Tabs */
.stTabs button {
    background:#1e1e1e !important;
    border:1px solid #333 !important;
    border-radius:12px !important;
    color:var(--accent-2) !important;
    font-weight:700 !important;
}
</style>
""", unsafe_allow_html=True)

# ============================
# TOP BAR
# ============================
st.markdown("""
<div class="topbar">
  <div class="logo-wrap"></div>
  <div>
    <div class="title">Loja Importados — Dashboard</div>
    <div class="subtitle">Visão rápida de vendas e estoque</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ============================
# HELPERS
# ============================
def parse_money(x):
    try:
        s = re.sub(r"[^\d,.-]", "", str(x))
        if "," in s and "." in s:
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", ".")
        return float(s)
    except:
        return 0.0

def parse_money_series(s): return s.astype(str).map(parse_money)
def parse_int_series(s): return s.astype(str).str.replace(r"\D","",regex=True).replace("",0).astype(int)
def formatar(v): return "R$ " + f"{v:,.0f}".replace(",", ".")

# ============================
# CARREGAR PLANILHA — sem erro de cache
# ============================
def carregar_planilha(url):
    r = requests.get(url)
    r.raise_for_status()
    return BytesIO(r.content)

try:
    buffer = carregar_planilha(URL_PLANILHA)
    xls = pd.ExcelFile(buffer)
except Exception as e:
    st.error("❌ Erro ao carregar planilha")
    st.exception(e)
    st.stop()

# ============================
# LER ABAS
# ============================
dfs = {}
for aba in ["ESTOQUE","VENDAS","COMPRAS"]:
    try:
        dfs[aba] = pd.read_excel(xls, sheet_name=aba)
    except:
        dfs[aba] = pd.DataFrame()

# ============================
# TRATAMENTO ESTOQUE
# ============================
e = dfs.get("ESTOQUE", pd.DataFrame()).copy()
if not e.empty:
    if "Media C. UNITARIO" in e: e["Media C. UNITARIO"] = parse_money_series(e["Media C. UNITARIO"])
    if "Valor Venda Sugerido" in e: e["Valor Venda Sugerido"] = parse_money_series(e["Valor Venda Sugerido"])
    if "EM ESTOQUE" in e: e["EM ESTOQUE"] = parse_int_series(e["EM ESTOQUE"])

# ============================
# TRATAMENTO VENDAS
# ============================
v = dfs.get("VENDAS", pd.DataFrame()).copy()
if not v.empty:
    if "VALOR TOTAL" in v: v["VALOR TOTAL"] = parse_money_series(v["VALOR TOTAL"])
    if "QTD" in v: v["QTD"] = parse_int_series(v["QTD"])
    if "DATA" in v:
        v["DATA"] = pd.to_datetime(v["DATA"], errors="coerce")
        v["MES_ANO"] = v["DATA"].dt.strftime("%Y-%m")

# ============================
# FILTRO
# ============================
meses = ["Todos"] + sorted(v.get("MES_ANO", pd.Series()).dropna().unique(), reverse=True)
mes_atual = datetime.now().strftime("%Y-%m")
mes_sel = st.selectbox("Filtrar por mês (YYYY-MM)", meses, index=(meses.index(mes_atual) if mes_atual in meses else 0))

vf = v if mes_sel=="Todos" else v[v["MES_ANO"]==mes_sel]

# ============================
# KPIs
# ============================
total_vendido = vf.get("VALOR TOTAL", pd.Series()).sum()
total_qtd = vf.get("QTD", pd.Series()).sum()

st.markdown(f"""
<div class='kpi-row'>
  <div class='kpi'><h3>💵 Total Vendido</h3><div class='value'>{formatar(total_vendido)}</div></div>
  <div class='kpi'><h3>🧾 Total Itens Vendidos</h3><div class='value'>{total_qtd}</div></div>
</div>
""", unsafe_allow_html=True)

# ============================
# TABS
# ============================
t1,t2,t3,t4,t5 = st.tabs(["🛒 VENDAS","🏆 TOP10 VALOR","🥧 TOP10 QUANTIDADE","📦 ESTOQUE","🔍 PESQUISA"])

# ============================
# T1 — VENDAS
# ============================
with t1:
    if vf.empty:
        st.warning("Sem dados de vendas.")
    else:
        st.dataframe(vf, use_container_width=True)

# ============================
# T2 — TOP10 VALOR
# ============================
with t2:
    if vf.empty:
        st.warning("Sem dados.")
    else:
        g = vf.groupby("PRODUTO").agg(TOTAL=("VALOR TOTAL","sum")).sort_values("TOTAL", ascending=False).head(10)
        fig = px.bar(g, x=g.index, y="TOTAL", color_discrete_sequence=["#8b5cf6"])
        fig.update_layout(plot_bgcolor="#0b0b0b",paper_bgcolor="#0b0b0b",font_color="#fff")
        st.plotly_chart(fig, use_container_width=True)

# ============================
# T3 — TOP10 QTD EM PIZZA (COM DESTAQUE)
# ============================
with t3:
    if vf.empty:
        st.warning("Sem dados.")
    else:
        g = vf.groupby("PRODUTO").agg(QTD=("QTD","sum")).sort_values("QTD", ascending=False).head(10)
        maior = g["QTD"].idxmax()
        g["EXP"] = [0.15 if i==maior else 0 for i in g.index]

        fig = px.pie(g, names=g.index, values="QTD", hole=0.35)
        fig.update_traces(pull=g["EXP"], textinfo="label+value+percent")
        fig.update_layout(plot_bgcolor="#0b0b0b",paper_bgcolor="#0b0b0b",font_color="#fff")

        st.plotly_chart(fig, use_container_width=True)

# ============================
# T4 — ESTOQUE
# ============================
with t4:
    if e.empty:
        st.warning("Sem estoque.")
    else:
        st.dataframe(e, use_container_width=True)

# ============================
# T5 — PESQUISAR
# ============================
with t5:
    termo = st.text_input("Pesquisar produto")
    if termo.strip():
        res = e[e["PRODUTO"].str.contains(termo, case=False, na=False)]
        if res.empty:
            st.warning("Nenhum resultado.")
        else:
            st.dataframe(res, use_container_width=True)
