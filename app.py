# ============================================
#  app.py — Dashboard Loja Importados (Kelvin IA Edition — Blindado)
# ============================================

import streamlit as st
import pandas as pd
import plotly.express as px
import re
from datetime import datetime, timedelta
import numpy as np
import requests
from io import BytesIO

st.set_page_config(
    page_title="Loja Importados – Dashboard IA",
    layout="wide",
    initial_sidebar_state="collapsed"
)

URL_PLANILHA = "https://docs.google.com/spreadsheets/d/1TsRjsfw1TVfeEWBBvhKvsGQ5YUCktn2b/export?format=xlsx"


# -------------------------------------------------
# CSS
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

.kpi-row { display:flex; gap:12px; flex-wrap:wrap; margin-top:20px; }
.kpi {
  background: var(--card-bg); padding:14px 18px; border-radius:12px;
  box-shadow:0 6px 16px rgba(0,0,0,0.45); border-left:6px solid var(--accent);
  min-width:170px;
}
.kpi h3 { margin:0; font-size:12px; color:var(--accent-2); }
.kpi .value { margin-top:6px; font-size:22px; font-weight:900; }

.stTabs button {
  background:#1e1e1e !important; border:1px solid #333 !important;
  border-radius:12px !important; padding:8px 14px !important;
  font-weight:700 !important; color:var(--accent-2) !important;
  margin-right:8px !important;
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
}
.product-title {
    font-size:16px; font-weight:800; color:#a78bfa;
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
# FUNÇÕES
# -------------------------------------------------

def force_series(x):
    """Garante que qualquer entrada vire uma Series, nunca um número."""
    if isinstance(x, pd.Series):
        return x
    return pd.Series([x])

def parse_money_value(x):
    try:
        if pd.isna(x): 
            return float("nan")
    except:
        pass
    s = str(x).strip()
    s = re.sub(r"[^\d\.,\-]", "", s)
    if "." in s and "," in s:
        s = s.replace(".","").replace(",",".")
    else:
        if "," in s: s = s.replace(",",".")
    try:
        return float(s)
    except:
        return float("nan")

def parse_money_series(s):
    s = force_series(s)
    return s.astype(str).map(parse_money_value)

def formatar_reais(v):
    try:
        v=float(v)
    except:
        return "R$ 0,00"
    s=f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
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
    if linha is None:
        return None
    tmp = df_raw.copy()
    tmp.columns = tmp.iloc[linha]
    df = tmp.iloc[linha+1:].copy()
    df.columns = [str(c).strip() for c in df.columns]
    df = df.loc[:, ~df.columns.astype(str).str.contains("Unnamed")]
    return df.reset_index(drop=True)

def encontrar(colunas, candidatos):
    for c in colunas:
        for padrao in candidatos:
            if padrao in c.upper():
                return c
    return None


# -------------------------------------------------
# CARREGAR PLANILHA
# -------------------------------------------------
try:
    xls = carregar_xlsx_from_url(URL_PLANILHA)
except:
    st.error("Erro ao carregar planilha.")
    st.stop()

abas = xls.sheet_names
dfs = {}

for aba in ["ESTOQUE","VENDAS","COMPRAS"]:
    if aba in abas:
        raw = pd.read_excel(URL_PLANILHA, sheet_name=aba, header=None)
        dfs[aba] = limpar_aba_raw(raw, aba)


# ==============================================================
# PROCESSAR ESTOQUE — BLINDADO
# ==============================================================
if "ESTOQUE" in dfs and dfs["ESTOQUE"] is not None:
    df_e = dfs["ESTOQUE"].copy()

    colunas_upper = df_e.columns.str.upper()

    col_prod = encontrar(colunas_upper, ["PROD"])
    col_estoque = encontrar(colunas_upper, ["ESTOQUE","QTD","QUANT"])
    col_custo = encontrar(colunas_upper, ["CUSTO","MEDIA"])
    col_venda = encontrar(colunas_upper, ["VENDA","VALOR"])

    if col_prod: df_e.rename(columns={col_prod: "PRODUTO"}, inplace=True)
    if col_estoque: df_e.rename(columns={col_estoque: "EM ESTOQUE"}, inplace=True)
    if col_custo: df_e.rename(columns={col_custo: "PRECO_CUSTO"}, inplace=True)
    if col_venda: df_e.rename(columns={col_venda: "PRECO_VENDA"}, inplace=True)

    df_e["EM ESTOQUE"] = pd.to_numeric(df_e.get("EM ESTOQUE", pd.Series()), errors="coerce").fillna(0).astype(int)
    df_e["PRECO_CUSTO"] = parse_money_series(df_e.get("PRECO_CUSTO", pd.Series())).fillna(0)
    df_e["PRECO_VENDA"] = parse_money_series(df_e.get("PRECO_VENDA", pd.Series())).fillna(0)

    df_e["VALOR_CUSTO_TOTAL"] = df_e["PRECO_CUSTO"] * df_e["EM ESTOQUE"]
    df_e["VALOR_VENDA_TOTAL"] = df_e["PRECO_VENDA"] * df_e["EM ESTOQUE"]

    dfs["ESTOQUE"] = df_e


# ==============================================================
# PROCESSAR VENDAS
# ==============================================================
if "VENDAS" in dfs and dfs["VENDAS"] is not None:
    df_v = dfs["VENDAS"].copy()

    cols = df_v.columns.str.upper()

    col_prod = encontrar(cols, ["PROD"])
    col_valor = encontrar(cols, ["VALOR","VENDA"])
    col_custo = encontrar(cols, ["CUSTO"])
    col_qtd = encontrar(cols, ["QTD","QUANT"])
    col_data = encontrar(cols, ["DATA"])

    if col_prod: df_v.rename(columns={col_prod:"PRODUTO"}, inplace=True)
    if col_valor: df_v.rename(columns={col_valor:"VALOR VENDA"}, inplace=True)
    if col_custo: df_v.rename(columns={col_custo:"CUSTO"}, inplace=True)
    if col_qtd: df_v.rename(columns={col_qtd:"QTD"}, inplace=True)
    if col_data: df_v.rename(columns={col_data:"DATA"}, inplace=True)

    df_v["VALOR VENDA"] = parse_money_series(df_v.get("VALOR VENDA", pd.Series())).fillna(0)
    df_v["CUSTO"] = parse_money_series(df_v.get("CUSTO", pd.Series())).fillna(0)
    df_v["QTD"] = pd.to_numeric(df_v.get("QTD", pd.Series()), errors="coerce").fillna(0).astype(int)

    df_v["DATA"] = pd.to_datetime(df_v["DATA"], errors="coerce")
    df_v["VALOR TOTAL"] = df_v["VALOR VENDA"] * df_v["QTD"]
    df_v["LUCRO TOTAL"] = (df_v["VALOR VENDA"] - df_v["CUSTO"]) * df_v["QTD"]
    df_v["MES_ANO"] = df_v["DATA"].dt.strftime("%Y-%m")

    dfs["VENDAS"] = df_v


# ==============================================================
# PROCESSAR COMPRAS
# ==============================================================
if "COMPRAS" in dfs and dfs["COMPRAS"] is not None:
    df_c = dfs["COMPRAS"].copy()
    cols = df_c.columns.str.upper()

    col_qtd = encontrar(cols, ["QTD","QUANT"])
    col_custo = encontrar(cols, ["CUSTO"])
    col_data = encontrar(cols, ["DATA"])

    if col_qtd: df_c.rename(columns={col_qtd:"QTD"}, inplace=True)
    if col_custo: df_c.rename(columns={col_custo:"CUSTO UNITARIO"}, inplace=True)
    if col_data: df_c.rename(columns={col_data:"DATA"}, inplace=True)

    df_c["QTD"] = pd.to_numeric(df_c.get("QTD", pd.Series()), errors="coerce").fillna(0).astype(int)
    df_c["CUSTO UNITARIO"] = parse_money_series(df_c.get("CUSTO UNITARIO", pd.Series())).fillna(0)
    df_c["CUSTO TOTAL"] = df_c["QTD"] * df_c["CUSTO UNITARIO"]
    df_c["DATA"] = pd.to_datetime(df_c["DATA"], errors="coerce")
    df_c["MES_ANO"] = df_c["DATA"].dt.strftime("%Y-%m")

    dfs["COMPRAS"] = df_c


# ==============================================================
# TELA PRINCIPAL
# ==============================================================
st.title("📊 Painel Geral — Inteligência Comercial")

df_v = dfs.get("VENDAS", pd.DataFrame())

if not df_v.empty:
    total_vendido = df_v["VALOR TOTAL"].sum()
    total_lucro = df_v["LUCRO TOTAL"].sum()
    qtd_itens = df_v["QTD"].sum()

    k1, k2, k3 = st.columns(3)
    k1.markdown(f"<div class='kpi'><h3>Total Vendido</h3><div class='value'>{formatar_reais(total_vendido)}</div></div>", unsafe_allow_html=True)
    k2.markdown(f"<div class='kpi'><h3>Lucro Total</h3><div class='value'>{formatar_reais(total_lucro)}</div></div>", unsafe_allow_html=True)
    k3.markdown(f"<div class='kpi'><h3>Itens Vendidos</h3><div class='value'>{qtd_itens}</div></div>", unsafe_allow_html=True)


# ===================================================
# GRÁFICOS PRINCIPAIS
# ===================================================
st.subheader("📈 Panorama Geral")

if not df_v.empty:
    colA, colB = st.columns(2)

    vendas_mes = df_v.groupby("MES_ANO")["VALOR TOTAL"].sum().reset_index()

    fig1 = px.line(vendas_mes, x="MES_ANO", y="VALOR TOTAL", markers=True, title="Vendas Mensais")
    fig1.update_layout(height=350)
    colA.plotly_chart(fig1, use_container_width=True)

    top_itens = df_v.groupby("PRODUTO")["QTD"].sum().sort_values(ascending=False).head(5).reset_index()
    fig2 = px.bar(top_itens, x="QTD", y="PRODUTO", orientation="h", title="Top Produtos")
    colB.plotly_chart(fig2, use_container_width=True)

    # IA — Tendência
    st.markdown("### 🤖 Inteligência Comercial")

    if len(vendas_mes) >= 2:
        ult = vendas_mes.iloc[-1]["VALOR TOTAL"]
        ant = vendas_mes.iloc[-2]["VALOR TOTAL"]
        dif = ult - ant
        perc = (dif / ant * 100) if ant > 0 else 0

        tendencia = "📈 Crescimento" if perc > 15 else "📉 Queda" if perc < -15 else "🟣 Estável"
        st.info(f"{tendencia} — variação de {perc:.1f}% no mês")

    vendas_mes["MM3"] = vendas_mes["VALOR TOTAL"].rolling(3).mean()
    if vendas_mes["MM3"].notna().any():
        st.success(f"🧠 Projeção IA (próximo mês): {formatar_reais(vendas_mes['MM3'].iloc[-1])}")


# ==============================================================
# ABAS
# ==============================================================
st.markdown("---")
tabs = st.tabs(["📦 Estoque", "💰 Vendas", "🧾 Compras", "🔍 Pesquisar (IA)"])


# ---------------- ESTOQUE ----------------
with tabs[0]:
    st.subheader("📦 Estoque")
    df_e = dfs.get("ESTOQUE", pd.DataFrame())

    if not df_e.empty:
        st.dataframe(df_e, use_container_width=True)

        crit = df_e[df_e["EM ESTOQUE"] <= 3]
        if not crit.empty:
            st.warning("⚠️ Estoque Crítico")
            st.dataframe(crit)


# ---------------- VENDAS ----------------
with tabs[1]:
    st.subheader("💰 Vendas")
    if not df_v.empty:
        meses = df_v["MES_ANO"].unique().tolist()
        sel = st.multiselect("Filtrar por mês:", meses, default=meses[:1])

        df_fil = df_v[df_v["MES_ANO"].isin(sel)] if sel else df_v

        st.dataframe(df_fil, use_container_width=True)

        df_dia = df_fil.groupby("DATA")["VALOR TOTAL"].sum().reset_index()
        fig = px.bar(df_dia, x="DATA", y="VALOR TOTAL", title="Vendas por Dia")
        st.plotly_chart(fig, use_container_width=True)


# ---------------- COMPRAS ----------------
with tabs[2]:
    st.subheader("🧾 Compras")
    df_c = dfs.get("COMPRAS", pd.DataFrame())
    if not df_c.empty:
        st.dataframe(df_c, use_container_width=True)

        df_dia = df_c.groupby("DATA")["CUSTO TOTAL"].sum().reset_index()
        fig = px.line(df_dia, x="DATA", y="CUSTO TOTAL", markers=True, title="Compras por Dia")
        st.plotly_chart(fig, use_container_width=True)


# ---------------- PESQUISA IA ----------------
with tabs[3]:
    st.subheader("🔍 Pesquisa Inteligente")

    df_e = dfs.get("ESTOQUE", pd.DataFrame())
    df_v = dfs.get("VENDAS", pd.DataFrame())

    termo = st.text_input("Buscar produto:")

    df_busca = df_e.copy()
    if termo.strip():
        df_busca = df_busca[df_busca["PRODUTO"].str.contains(termo, case=False, na=False)]

    col1, col2, col3, col4, col5 = st.columns(5)
    f1 = col1.checkbox("📉 Estoque baixo")
    f2 = col2.checkbox("📦 Estoque alto")
    f3 = col3.checkbox("💸 Mais barato")
    f4 = col4.checkbox("💰 Mais caro")
    f5 = col5.checkbox("🔤 A-Z")

    if f1: df_busca = df_busca[df_busca["EM ESTOQUE"] <= 3]
    if f2: df_busca = df_busca[df_busca["EM ESTOQUE"] >= 20]
    if f3: df_busca = df_busca.sort_values("PRECO_VENDA", ascending=True)
    if f4: df_busca = df_busca.sort_values("PRECO_VENDA", ascending=False)
    if f5: df_busca = df_busca.sort_values("PRODUTO")

    def tag_mov(prod):
        if df_v.empty: return "🟣 Sem dados"
        qtd = df_v[df_v["PRODUTO"].str.lower()==prod.lower()]["QTD"].sum()
        if qtd >= 20: return "🔥 Alta procura"
        if qtd >= 5: return "🟡 Estável"
        if qtd == 0: return "❄️ Zerado"
        return "⚠️ Baixa"

    if not df_busca.empty:
        st.markdown("<div class='card-grid'>", unsafe_allow_html=True)

        for _, r in df_busca.iterrows():
            badge = tag_mov(r["PRODUTO"])

            st.markdown(f"""
            <div class='product-card'>
                <div class='product-title'>{r["PRODUTO"]}</div>
                <div style='margin-top:6px;'><span class='card-badge'>{badge}</span></div>

                <p style='margin-top:12px;'>
                <strong>Estoque:</strong> {int(r["EM ESTOQUE"])}<br>
                <strong>Preço venda:</strong> {formatar_reais(r["PRECO_VENDA"])}<br>
                <strong>Custo médio:</strong> {formatar_reais(r["PRECO_CUSTO"])}<br>
                <strong>Total venda:</strong> {formatar_reais(r["VALOR_VENDA_TOTAL"])}<br>
                </p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    else:
        st.info("Nenhum produto encontrado.")
