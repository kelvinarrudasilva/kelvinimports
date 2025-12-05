# app.py – NOVE STORE Dashboard
# Compatível com Streamlit Cloud / Atualização de dados / Logo fixa

import streamlit as st
import pandas as pd
import plotly.express as px
import re
from datetime import datetime, timedelta
import requests
from io import BytesIO

st.set_page_config(
    page_title="NOVE STORE — Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed"
)

URL_PLANILHA = "https://docs.google.com/spreadsheets/d/1TsRjsfw1TVfeEWBBvhKvsGQ5YUCktn2b/export?format=xlsx"

def parse_money_value(x):
    try:
        if pd.isna(x):
            return float("nan")
    except:
        pass
    s = str(x).strip()
    s = re.sub(r"[^\d\.,\-]", "", s)
    if "." in s and "," in s:
        s = s.replace(".", "").replace(",", ".")
    else:
        if "," in s: s = s.replace(",", ".")
    try: return float(s)
    except: return float("nan")

def parse_money_series(s):
    return s.astype(str).map(parse_money_value).astype("float64")

def formatar_reais(v):
    try: v = float(v)
    except: return "R$ 0,00"
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

@st.cache_resource
def carregar_xlsx_from_url(url):
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    return pd.ExcelFile(BytesIO(r.content))


def parse_int_series(s):
    def to_int(x):
        try:
            if pd.isna(x): return pd.NA
        except: pass
        x = re.sub(r"[^\d\-]", "", str(x))
        if x in ("", "-"): return pd.NA
        try: return int(float(x))
        except: return pd.NA
    return s.map(to_int).astype("Int64")

st.markdown("""
<style>
:root{
  --bg:#0b0b0b;
  --accent:#8b5cf6;
  --accent2:#a78bfa;
}
body, .stApp { background: var(--bg) !important; color:#fff !important; font-family: 'Inter','Segoe UI',sans-serif; }
.logo {width:52px;border-radius:10px;}
</style>
""", unsafe_allow_html=True)

# 🔝 TOPO
top1, top2, top3 = st.columns([0.18, 1.5, 0.4])
with top1:
    try:
        st.image("logo.png", width=52)
    except:
        st.write("NS")

with top2:
    st.markdown("### **NOVE STORE — Dashboard**")
    st.markdown("Visão geral de vendas, estoque e compras")

with top3:
    if st.button("🔄 Atualizar dados", use_container_width=True):
        try: carregar_xlsx_from_url.clear()
        except: pass
        st.cache_data.clear()

# ────────────── CARREGAR PLANILHA ──────────────
try:
    xls = carregar_xlsx_from_url(URL_PLANILHA)
except Exception as e:
    st.error("Erro ao carregar planilha!")
    st.stop()

abas = xls.sheet_names
dfs = {}

for aba in ["VENDAS", "ESTOQUE", "COMPRAS"]:
    if aba in abas:
        df = pd.read_excel(xls, aba)
        df.columns = df.columns.str.upper()
        dfs[aba] = df.copy()
# NORMALIZAÇÃO
if "VENDAS" in dfs:
    df_v = dfs["VENDAS"]
    if "DATA" in df_v.columns:
        df_v["DATA"] = pd.to_datetime(df_v["DATA"], errors="coerce")
        df_v["MES"] = df_v["DATA"].dt.strftime("%Y-%m")
    for col in ["VALOR TOTAL","LUCRO UNITARIO"]:
        if col in df_v.columns:
            df_v[col] = parse_money_series(df_v[col]).fillna(0)
    qtd_cols = [c for c in df_v.columns if "QTD" in c]
    if qtd_cols:
        df_v["QTD"] = parse_int_series(df_v[qtd_cols[0]]).fillna(0).astype(int)
    dfs["VENDAS"] = df_v

if "ESTOQUE" in dfs:
    df_e = dfs["ESTOQUE"]
    custo_cols = [c for c in df_e.columns if "C." in c]
    if custo_cols:
        df_e["CUSTO"] = parse_money_series(df_e[custo_cols[0]]).fillna(0)
    qtd_cols = [c for c in df_e.columns if "ESTO" in c]
    if qtd_cols:
        df_e["EM ESTOQUE"] = parse_int_series(df_e[qtd_cols[0]]).fillna(0).astype(int)
    dfs["ESTOQUE"] = df_e

if "COMPRAS" in dfs:
    df_c = dfs["COMPRAS"]
    df_c["QUANTIDADE"] = parse_int_series(df_c.get("QUANTIDADE",0)).fillna(0).astype(int)
    custo_cols = [c for c in df_c.columns if "CUSTO" in c]
    if custo_cols:
        df_c["CUSTO UNIT"] = parse_money_series(df_c[custo_cols[0]]).fillna(0)
    df_c["CUSTO TOTAL"] = (df_c["QUANTIDADE"] * df_c["CUSTO UNIT"]).fillna(0)
    if "DATA" in df_c.columns:
        df_c["DATA"] = pd.to_datetime(df_c["DATA"], errors="coerce")
        df_c["MES"] = df_c["DATA"].dt.strftime("%Y-%m")
    dfs["COMPRAS"] = df_c

# KPIs
df_v = dfs.get("VENDAS", pd.DataFrame())
df_e = dfs.get("ESTOQUE", pd.DataFrame())
df_c = dfs.get("COMPRAS", pd.DataFrame())

faturamento = df_v["VALOR TOTAL"].sum() if "VALOR TOTAL" in df_v else 0
lucro = (df_v["LUCRO UNITARIO"] * df_v["QTD"]).sum() if "LUCRO UNITARIO" in df_v else 0
custo_estoque = (df_e["CUSTO"] * df_e["EM ESTOQUE"]).sum() if "CUSTO" in df_e else 0
# 👁️ Toggle estilo "saldo oculto"
mostrar_saldos = st.toggle("👁️ Mostrar valores", value=False)

def display_money(v):
    return formatar_reais(v) if mostrar_saldos else "••••"

# KPIs visual
st.markdown("### 📊 Indicadores Gerais")
k1, k2, k3 = st.columns(3)
k1.metric("💰 Faturamento", display_money(faturamento))
k2.metric("🏆 Lucro Líquido", display_money(lucro))
k3.metric("📦 Custo Estoque", display_money(custo_estoque))

st.write("---")

# ABAS
tabs = st.tabs(["🛒 Vendas", "📦 Estoque", "🧾 Compras", "🔍 Pesquisa"])

# TAB VENDAS
with tabs[0]:
    st.subheader("📅 Últimas vendas registradas")

    if df_v.empty:
        st.warning("Nenhuma venda registrada.")
    else:
        df_print = df_v.copy()
        if "DATA" in df_print.columns:
            df_print["DATA"] = df_print["DATA"].dt.strftime("%d/%m/%Y")

        st.dataframe(df_print, use_container_width=True)

        if "VALOR TOTAL" in df_v.columns:
            fig = px.bar(
                df_v.groupby("MES")["VALOR TOTAL"].sum().reset_index(),
                x="MES", y="VALOR TOTAL", text="VALOR TOTAL",
                title="Faturamento por mês",
            )
            st.plotly_chart(fig, use_container_width=True)

# TAB ESTOQUE
with tabs[1]:
    st.subheader("📦 Estoque Atual")

    if df_e.empty:
        st.warning("Sem dados de estoque.")
    else:
        st.dataframe(df_e, use_container_width=True)

        if "EM ESTOQUE" in df_e.columns:
            fig2 = px.bar(
                df_e.sort_values("EM ESTOQUE", ascending=False).head(10),
                x="PRODUTO", y="EM ESTOQUE", text="EM ESTOQUE",
                title="Top 10 itens em estoque",
            )
            st.plotly_chart(fig2, use_container_width=True)

# TAB COMPRAS
with tabs[2]:
    st.subheader("🧾 Compras Realizadas")

    if df_c.empty:
        st.info("Nenhuma compra registrada.")
    else:
        df_cprint = df_c.copy()
        if "DATA" in df_cprint.columns:
            df_cprint["DATA"] = df_cprint["DATA"].dt.strftime("%d/%m/%Y")

        st.dataframe(df_cprint, use_container_width=True)

# TAB PESQUISA
with tabs[3]:
    st.subheader("🔍 Buscar Produto no Estoque")
    termo = st.text_input("Digite para buscar:", "")

    if not termo.strip():
        st.info("Digite o nome de um produto para pesquisar.")
    else:
        resultado = df_e[df_e["PRODUTO"].str.contains(termo, case=False, na=False)] \
                    if not df_e.empty else pd.DataFrame()

        if resultado.empty:
            st.error("Nenhum produto encontrado.")
        else:
            st.success(f"{len(resultado)} produto(s) encontrado(s):")
            st.dataframe(resultado, use_container_width=True)

st.write("---")
st.caption("NOVE STORE — Dashboard 🚀")
