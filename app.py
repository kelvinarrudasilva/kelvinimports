# ================================================
# app.py – Dashboard Loja Importados (compatível com seu Excel)
# - Detecta header na 2ª linha
# - Limpa Unnamed
# - Auto-detecta PRODUTO / DATA / QTD / VALORES
# - Top5 Geral Quantidade e Valor
# - Faturamento semanal filtrado por mês
# ================================================

import streamlit as st
import pandas as pd
import plotly.express as px
import re
from datetime import datetime, timedelta
import requests
from io import BytesIO

st.set_page_config(page_title="Loja Importados – Dashboard", layout="wide")

# ----------------------------
# CONFIG
# ----------------------------
URL_PLANILHA = "https://docs.google.com/spreadsheets/d/1TsRjsfw1TVfeEWBBvhKvsGQ5YUCktn2b/export?format=xlsx"

# ----------------------------
# CSS Dark Roxo Premium
# ----------------------------
st.markdown("""
<style>
:root{
  --bg:#0b0b0b;
  --card:#141414;
  --accent:#8b5cf6;
  --accent2:#a78bfa;
  --text:#f2f2f2;
}
body, .stApp { background:var(--bg) !important; color:var(--text) !important; }
.kpi-box{
  background:var(--card);
  padding:14px 18px;
  border-radius:12px;
  border-left:5px solid var(--accent);
  box-shadow:0 6px 14px rgba(0,0,0,0.4);
}
</style>
""", unsafe_allow_html=True)

# ----------------------------
# HELPERS
# ----------------------------
def baixar_xlsx(url):
    r = requests.get(url, timeout=25)
    r.raise_for_status()
    return BytesIO(r.content)

def limpar_header(df_raw):
    """ usa a segunda linha da planilha como cabeçalho real """
    cols = df_raw.iloc[1].tolist()
    df = df_raw.iloc[2:].copy()
    df.columns = cols
    df = df.loc[:, ~df.columns.astype(str).str.contains("Unnamed")]
    return df.reset_index(drop=True)

def limpar_moeda(x):
    if pd.isna(x): return 0
    s = str(x).replace("R$","").replace(".","").replace(",",".")
    s = re.sub(r"[^0-9.\-]", "", s)
    try: return float(s)
    except: return 0

def formatar(v):
    try: v = float(v)
    except: return "R$ 0"
    return f"R$ {v:,.0f}".replace(",", ".")

def dark(fig):
    fig.update_layout(
        plot_bgcolor="#0b0b0b",
        paper_bgcolor="#0b0b0b",
        font_color="#f2f2f2"
    )
    return fig

def detectar_col(df, palavras):
    for c in df.columns:
        cu = str(c).upper().replace(" ", "")
        for p in palavras:
            if p.upper().replace(" ", "") in cu:
                return c
    return None

# ----------------------------
# CARREGAR PLANILHA
# ----------------------------
try:
    file = baixar_xlsx(URL_PLANILHA)
    df_raw_v = pd.read_excel(file, sheet_name="VENDAS", header=None)
    df_raw_c = pd.read_excel(file, sheet_name="COMPRAS", header=None)
    df_raw_e = pd.read_excel(file, sheet_name="ESTOQUE", header=None)
except Exception as e:
    st.error("Erro ao carregar planilha.")
    st.stop()

# ----------------------------
# LIMPEZA DAS ABAS
# ----------------------------
vendas = limpar_header(df_raw_v)
compras = limpar_header(df_raw_c)
estoque = limpar_header(df_raw_e)

# ----------------------------
# NORMALIZAR VENDAS
# ----------------------------
col_data = detectar_col(vendas, ["DATA"])
col_prod = detectar_col(vendas, ["PRODUTO", "ITEM", "NOME", "DESC"])
col_qtd = detectar_col(vendas, ["QTD", "QUANT"])
col_unit = detectar_col(vendas, ["VALORVENDA", "VENDA", "PRECO", "UNIT"])
col_total = detectar_col(vendas, ["VALOR TOTAL"])

if col_data: vendas = vendas.rename(columns={col_data: "DATA"})
if col_prod: vendas = vendas.rename(columns={col_prod: "PRODUTO"})
if col_qtd: vendas = vendas.rename(columns={col_qtd: "QTD"})
if col_unit: vendas = vendas.rename(columns={col_unit: "VALOR VENDA"})
if col_total: vendas = vendas.rename(columns={col_total: "VALOR TOTAL"})

# converter
vendas["DATA"] = pd.to_datetime(vendas["DATA"], errors="coerce")
vendas["QTD"] = pd.to_numeric(vendas["QTD"], errors="coerce").fillna(0).astype(int)

# valor total
if "VALOR TOTAL" in vendas.columns:
    vendas["VALOR TOTAL"] = vendas["VALOR TOTAL"].map(limpar_moeda)
elif "VALOR VENDA" in vendas.columns:
    vendas["VALOR VENDA"] = vendas["VALOR VENDA"].map(limpar_moeda)
    vendas["VALOR TOTAL"] = vendas["VALOR VENDA"] * vendas["QTD"]
else:
    vendas["VALOR TOTAL"] = 0.0

if "PRODUTO" not in vendas.columns:
    vendas["PRODUTO"] = "SEM_PRODUTO"

vendas["MES_ANO"] = vendas["DATA"].dt.strftime("%Y-%m")

# ----------------------------
# NORMALIZAR COMPRAS
# ----------------------------
col_data_c = detectar_col(compras, ["DATA"])
col_qtd_c = detectar_col(compras, ["QTD", "QUANT"])
col_custo_c = detectar_col(compras, ["CUSTO", "VALOR", "PRECO", "UNIT"])

if col_data_c: compras = compras.rename(columns={col_data_c: "DATA"})
if col_qtd_c: compras = compras.rename(columns={col_qtd_c: "QTD"})
if col_custo_c: compras = compras.rename(columns={col_custo_c: "CUSTO"})

compras["DATA"] = pd.to_datetime(compras["DATA"], errors="coerce")
compras["QTD"] = pd.to_numeric(compras["QTD"], errors="coerce").fillna(0).astype(int)
compras["CUSTO"] = compras["CUSTO"].map(limpar_moeda) if "CUSTO" in compras.columns else 0
compras["CUSTO TOTAL"] = compras["QTD"] * compras["CUSTO"]
compras["MES_ANO"] = compras["DATA"].dt.strftime("%Y-%m")

# ----------------------------
# NORMALIZAR ESTOQUE
# ----------------------------
col_prod_e = detectar_col(estoque, ["PRODUTO", "ITEM", "NOME"])
col_qtd_e = detectar_col(estoque, ["EM ESTOQUE", "ESTOQUE"])
col_custo_e = detectar_col(estoque, ["MEDIA", "CUSTO"])
col_venda_e = detectar_col(estoque, ["VENDA", "SUGERIDO"])

if col_prod_e: estoque = estoque.rename(columns={col_prod_e:"PRODUTO"})
if col_qtd_e: estoque = estoque.rename(columns={col_qtd_e:"EM_ESTOQUE"})
if col_custo_e: estoque = estoque.rename(columns={col_custo_e:"CUSTO_UNIT"})
if col_venda_e: estoque = estoque.rename(columns={col_venda_e:"PRECO_VENDA"})

estoque["EM_ESTOQUE"] = pd.to_numeric(estoque["EM_ESTOQUE"], errors="coerce").fillna(0).astype(int)
estoque["CUSTO_UNIT"] = estoque["CUSTO_UNIT"].map(limpar_moeda) if "CUSTO_UNIT" in estoque.columns else 0
estoque["PRECO_VENDA"] = estoque["PRECO_VENDA"].map(limpar_moeda) if "PRECO_VENDA" in estoque.columns else 0

estoque["VALOR_CUSTO_TOTAL"] = estoque["CUSTO_UNIT"] * estoque["EM_ESTOQUE"]
estoque["VALOR_VENDA_TOTAL"] = estoque["PRECO_VENDA"] * estoque["EM_ESTOQUE"]

# ----------------------------
# FILTRO MÊS
# ----------------------------
meses = ["Todos"] + sorted(vendas["MES_ANO"].dropna().unique().tolist(), reverse=True)
mes_padrao = datetime.now().strftime("%Y-%m")
idx = meses.index(mes_padrao) if mes_padrao in meses else 0

mes = st.selectbox("Filtrar por mês:", meses, index=idx)

def filtrar(df):
    if df.empty or mes == "Todos": return df
    return df[df["MES_ANO"] == mes]

vendas_f = filtrar(vendas)
compras_f = filtrar(compras)

# ----------------------------
# KPIs
# ----------------------------
k_vendas = vendas_f["VALOR TOTAL"].sum()
k_qtd = vendas_f["QTD"].sum()
k_compras = compras_f["CUSTO TOTAL"].sum()
k_est_venda = estoque["VALOR_VENDA_TOTAL"].sum()
k_est_custo = estoque["VALOR_CUSTO_TOTAL"].sum()

c1,c2,c3,c4,c5 = st.columns(5)
c1.markdown(f"<div class='kpi-box'><h4>💵 Vendas</h4><h2>{formatar(k_vendas)}</h2></div>", unsafe_allow_html=True)
c2.markdown(f"<div class='kpi-box'><h4>📦 Itens Vendidos</h4><h2>{k_qtd}</h2></div>", unsafe_allow_html=True)
c3.markdown(f"<div class='kpi-box'><h4>💸 Compras</h4><h2>{formatar(k_compras)}</h2></div>", unsafe_allow_html=True)
c4.markdown(f"<div class='kpi-box'><h4>🏷 Estoque (Venda)</h4><h2>{formatar(k_est_venda)}</h2></div>", unsafe_allow_html=True)
c5.markdown(f"<div class='kpi-box'><h4>📥 Estoque (Custo)</h4><h2>{formatar(k_est_custo)}</h2></div>", unsafe_allow_html=True)

# ----------------------------
# ABAS (SEM TOP10)
# ----------------------------
aba1, aba2, aba3 = st.tabs(["🛒 VENDAS", "📦 ESTOQUE", "🔍 PESQUISAR"])

# ---------------------------------------------------
# 🛒 ABA VENDAS — LAYOUT 3 (confirmado)
# ---------------------------------------------------
with aba1:

    # ---------------------------------------------------
    # 🔥 TOP 5 GERAL (QUANTIDADE)
    # ---------------------------------------------------
    st.subheader("🔥 Top 5 Produtos Mais Vendidos (por Quantidade) — Geral")

    top5_qtd = (
        vendas.groupby("PRODUTO", dropna=False)["QTD"]
        .sum().reset_index().sort_values("QTD", ascending=False).head(5)
    )

    if not top5_qtd.empty:
        fig_qtd = px.bar(
            top5_qtd,
            x="QTD",
            y="PRODUTO",
            orientation="h",
            text="QTD",
            color_discrete_sequence=["#8b5cf6"],
            height=380
        )
        fig_qtd.update_traces(textposition="inside")
        st.plotly_chart(dark(fig_qtd), use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("Nenhum dado disponível para Top 5 por quantidade.")

    st.markdown("---")

    # ---------------------------------------------------
    # 💰 TOP 5 GERAL (VALOR TOTAL)
    # ---------------------------------------------------
    st.subheader("💰 Top 5 Produtos Mais Vendidos (por Valor Total) — Geral")

    top5_val = (
        vendas.groupby("PRODUTO", dropna=False)["VALOR TOTAL"]
        .sum().reset_index().sort_values("VALOR TOTAL", ascending=False).head(5)
    )

    if not top5_val.empty:
        top5_val["LABEL"] = top5_val["VALOR TOTAL"].apply(formatar)

        fig_val = px.bar(
            top5_val,
            x="VALOR TOTAL",
            y="PRODUTO",
            orientation="h",
            text="LABEL",
            color_discrete_sequence=["#8b5cf6"],
            height=380
        )
        fig_val.update_traces(textposition="inside")
        st.plotly_chart(dark(fig_val), use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("Nenhum dado disponível para Top 5 por valor.")

    st.markdown("---")

    # ---------------------------------------------------
    # 📅 FATURAMENTO SEMANAL (FILTRADO POR MÊS)
    # ---------------------------------------------------
    st.subheader("📅 Faturamento Semanal (somente do mês selecionado)")

    df_sem = vendas_f.copy()
    if "DATA" in df_sem.columns and df_sem["DATA"].notna().any():
        df_sem = df_sem.dropna(subset=["DATA"])
        df_sem["SEMANA"] = df_sem["DATA"].dt.isocalendar().week
        df_sem["ANO"] = df_sem["DATA"].dt.year

        df_week = df_sem.groupby(["ANO","SEMANA"])["VALOR TOTAL"].sum().reset_index()

        def intervalo_semana(row):
            try:
                ini = datetime.fromisocalendar(int(row["ANO"]), int(row["SEMANA"]), 1)
                fim = ini + timedelta(days=6)
                return f"{ini.strftime('%d/%m')} → {fim.strftime('%d/%m')}"
            except:
                return "N/A"

        df_week["INTERVALO"] = df_week.apply(intervalo_semana, axis=1)
        df_week["LABEL"] = df_week["VALOR TOTAL"].apply(formatar)

        fig_sem = px.bar(
            df_week,
            x="INTERVALO",
            y="VALOR TOTAL",
            text="LABEL",
            color_discrete_sequence=["#8b5cf6"],
            height=380
        )
        fig_sem.update_traces(textposition="inside")
        st.plotly_chart(dark(fig_sem), use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("Sem dados com DATA válida no mês selecionado.")

    st.markdown("---")

    # ---------------------------------------------------
    # 📄 TABELA DE VENDAS DO PERÍODO
    # ---------------------------------------------------
    st.subheader("📄 Tabela de Vendas (do mês selecionado)")

    if vendas_f.empty:
        st.info("Nenhuma venda neste mês.")
    else:
        colunas_uteis = [c for c in ["DATA","PRODUTO","QTD","VALOR VENDA","VALOR TOTAL"] if c in vendas_f.columns]
        df_show = vendas_f[colunas_uteis].copy()
        st.dataframe(df_show.sort_values("DATA", ascending=False).reset_index(drop=True), use_container_width=True)

# ---------------------------------------------------
# ABA ESTOQUE
# ---------------------------------------------------
with aba2:
    st.subheader("📦 Estoque Atual")
    if not estoque.empty:
        st.dataframe(estoque, use_container_width=True)
    else:
        st.info("Nenhum item no estoque.")

# ---------------------------------------------------
# ABA PESQUISAR
# ---------------------------------------------------
with aba3:
    st.subheader("🔍 Buscar produto no estoque")
    termo = st.text_input("Digite parte do nome:")
    if termo and not estoque.empty:
        res = estoque[estoque["PRODUTO"].astype(str).str.contains(termo, case=False, na=False)]
        st.dataframe(res if not res.empty else pd.DataFrame(), use_container_width=True)
