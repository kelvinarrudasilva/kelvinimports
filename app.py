# app.py
import streamlit as st
import pandas as pd
import plotly.express as px
import re
from datetime import datetime
import requests
from io import BytesIO

# ======================
# Config visual (Preto + Dourado)
# ======================
st.set_page_config(page_title="Painel - Loja Importados", layout="wide")

st.markdown(
    """
    <style>
      :root { --gold:#FFD700; --bg:#000000; --card:#0f0f0f; --muted:#bbbbbb; --white:#FFFFFF; }
      .stApp { background-color: var(--bg); color: var(--gold); }
      .title { color: var(--gold); font-weight:700; font-size:22px; }
      .subtitle { color: var(--muted); font-size:12px; margin-bottom:12px; }

      /* Botão de período menor e bonito */
      .stSelectbox label { font-size:14px; color: var(--gold); }
      .stSelectbox div div { font-size:13px !important; }

      .kpi { background: linear-gradient(90deg, #111111, #0b0b0b); padding:12px; border-radius:10px; text-align:center; }
      .kpi-value { color: var(--gold); font-size:22px; font-weight:700; }
      .kpi-label { color:var(--muted); font-size:13px; }

      .stDataFrame table { background-color:#050505; color:var(--white); }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown("<div class='title'>📊 Painel — Loja Importados</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Visão Geral e Estoque • Preto + Dourado</div>", unsafe_allow_html=True)
st.markdown("---")

# ======================
# Helpers
# ======================
def clean_df(df):
    if df is None:
        return None
    df.columns = [str(c).strip() for c in df.columns]
    df = df.loc[:, ~df.columns.str.contains("^Unnamed", na=False)]
    df = df.dropna(axis=1, how="all")
    df = df.dropna(axis=0, how="all").reset_index(drop=True)
    return df

def fmt_brl(x):
    try:
        return f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "R$ 0,00"

# ======================
# Load Excel from Google Drive
# ======================
GDRIVE_URL = "https://drive.google.com/uc?id=1TsRjsfw1TVfeEWBBvhKvsGQ5YUCktn2b"

try:
    res = requests.get(GDRIVE_URL)
    res.raise_for_status()
    excel_buffer = BytesIO(res.content)
    xls = pd.ExcelFile(excel_buffer)
    available_sheets = [s.upper() for s in xls.sheet_names]
except Exception as e:
    st.error(f"Erro ao acessar planilha do Google Drive: {e}")
    st.stop()

def load_and_clean(name):
    if name not in available_sheets:
        return None
    df = pd.read_excel(excel_buffer, sheet_name=name)
    return clean_df(df)

estoque = load_and_clean("ESTOQUE")
vendas = load_and_clean("VENDAS")
compras = load_and_clean("COMPRAS")

# ======================
# Map colunas FIXAS da aba VENDAS
# ======================
v_data = "DATA"
v_prod = "PRODUTO"
v_qtd = "QTD"
v_val_unit = "VALOR VENDA"
v_val_total = "VALOR TOTAL"
v_custo_unit = "MEDIA CUSTO UNITARIO"
v_lucro_unit = "LUCRO UNITARIO"

# ======================
# Preparar VENDAS
# ======================
if vendas is not None and not vendas.empty:

    # DATA
    vendas[v_data] = pd.to_datetime(
        vendas[v_data].astype(str).str.replace(" ", ""),
        dayfirst=True,
        errors="coerce"
    )

    # QTD
    vendas["_QTD"] = pd.to_numeric(vendas[v_qtd], errors="coerce").fillna(0)

    # Valor Unitário
    vendas["_VAL_UNIT"] = pd.to_numeric(
        vendas[v_val_unit]
        .astype(str)
        .str.replace("R$", "")
        .str.replace(".", "")
        .str.replace(",", "."),
        errors="coerce"
    ).fillna(0)

    # Valor Total (corrigido)
    vendas["_VAL_TOTAL"] = pd.to_numeric(
        vendas[v_val_total]
        .astype(str)
        .str.replace("R$", "")
        .str.replace(".", "")
        .str.replace(",", "."),
        errors="coerce"
    ).fillna(0)

    # Se valor total vier zerado, calcula
    vendas.loc[vendas["_VAL_TOTAL"] == 0, "_VAL_TOTAL"] = \
        vendas["_VAL_UNIT"] * vendas["_QTD"]

    # Lucro unitário
    vendas["_LUCRO_UNIT"] = pd.to_numeric(
        vendas[v_lucro_unit]
        .astype(str)
        .str.replace("R$", "")
        .str.replace(".", "")
        .str.replace(",", "."),
        errors="coerce"
    ).fillna(0)

    # Lucro total
    vendas["_LUCRO"] = vendas["_LUCRO_UNIT"] * vendas["_QTD"]

    # Criar PERÍODO
    vendas["_PERIODO"] = vendas[v_data].dt.to_period("M").astype(str)

else:
    vendas = pd.DataFrame(columns=[v_data, v_prod, v_qtd])
    vendas["_QTD"] = 0
    vendas["_VAL_TOTAL"] = 0
    vendas["_LUCRO"] = 0
    vendas["_PERIODO"] = None

# ======================
# Preparar ESTOQUE
# ======================
if estoque is not None and not estoque.empty:

    # Detectar colunas esperadas
    e_prod = "Produto" if "Produto" in estoque.columns else "PRODUTO"
    e_qtd = "EM ESTOQUE" if "EM ESTOQUE" in estoque.columns else "QTD"

    estoque["_QTD"] = pd.to_numeric(estoque[e_qtd], errors="coerce").fillna(0)

    # Preços (quando existirem)
    if "Valor Venda Sugerido" in estoque.columns:
        estoque["_VAL_VENDA_UNIT"] = pd.to_numeric(
            estoque["Valor Venda Sugerido"]
            .astype(str)
            .str.replace("R$", "")
            .str.replace(".", "")
            .str.replace(",", "."),
            errors="coerce"
        ).fillna(0)
    else:
        estoque["_VAL_VENDA_UNIT"] = 0

    estoque["_VAL_TOTAL_VENDA"] = estoque["_QTD"] * estoque["_VAL_VENDA_UNIT"]

else:
    estoque = pd.DataFrame(columns=["PRODUTO", "QTD"])
    estoque["_QTD"] = 0
    estoque["_VAL_TOTAL_VENDA"] = 0

# ======================
# Períodos
# ======================
unique_periods = sorted(vendas["_PERIODO"].dropna().unique(), reverse=True)

period_map = {"Geral": None}
for p in unique_periods:
    year, month = p.split("-")
    pretty = datetime(int(year), int(month), 1).strftime("%b %Y")
    period_map[f"{pretty} ({p})"] = p

period_options = list(period_map.keys())

# ======================
# TABS
# ======================
tab1, tab2 = st.tabs(["📈 Visão Geral", "📦 Estoque Atual"])

# ======================================
# TAB 1 — Visão Geral
# ======================================
with tab1:

    periodo_sel = st.selectbox("Período", period_options)
    periodo_val = period_map.get(periodo_sel)

    if periodo_val is None:
        vendas_period = vendas.copy()
    else:
        vendas_period = vendas[vendas["_PERIODO"] == periodo_val].copy()

    # KPIs
    total_vendido = vendas_period["_VAL_TOTAL"].sum()
    total_qtd = vendas_period["_QTD"].sum()
    lucro_period = vendas_period["_LUCRO"].sum()
    valor_estoque = estoque["_VAL_TOTAL_VENDA"].sum()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💰 Vendido", fmt_brl(total_vendido))
    c2.metric("📈 Quantidade", int(total_qtd))
    c3.metric("💸 Lucro", fmt_brl(lucro_period))
    c4.metric("📦 Valor do Estoque", fmt_brl(valor_estoque))

    st.markdown("---")

    # TOP 10
    st.subheader("🏆 Top 10 Produtos Mais Vendidos")
    if not vendas_period.empty:
        grp = vendas_period.groupby(v_prod).agg(
            QTDE=("_QTD", "sum"),
            TOTAL=("_VAL_TOTAL", "sum")
        ).reset_index()
        grp = grp.sort_values("TOTAL", ascending=False).head(10)

        fig = px.bar(
            grp, x="TOTAL", y=v_prod, orientation="h",
            text="QTDE", color="TOTAL",
            color_continuous_scale=["#FFD700", "#B8860B"]
        )
        fig.update_traces(textposition="outside")
        fig.update_layout(
            plot_bgcolor="#000", paper_bgcolor="#000", font_color="#FFD700",
            yaxis={'categoryorder': 'total ascending'}
        )
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Tabela vendas do período
    st.subheader("📋 Vendas do Período")

    if not vendas_period.empty:
        df_show = vendas_period[[v_data, v_prod, "_QTD", "_VAL_TOTAL", "_LUCRO"]].copy()
        df_show[v_data] = df_show[v_data].dt.strftime("%d/%m/%Y")
        df_show["_VAL_TOTAL"] = df_show["_VAL_TOTAL"].apply(fmt_brl)
        df_show["_LUCRO"] = df_show["_LUCRO"].apply(fmt_brl)
        df_show = df_show.rename(columns={
            v_data: "Data",
            v_prod: "Produto",
            "_QTD": "Quantidade",
            "_VAL_TOTAL": "Valor",
            "_LUCRO": "Lucro"
        })
        st.dataframe(df_show.reset_index(drop=True))
    else:
        st.info("Nenhuma venda para este período.")

# ======================================
# TAB 2 — Estoque
# ======================================
with tab2:

    st.subheader("📦 Estoque Atual")

    if not estoque.empty:
        df_estoque = estoque.copy()
        produto_col = "Produto" if "Produto" in df_estoque.columns else "PRODUTO"

        df_estoque = df_estoque[[produto_col, "_QTD", "_VAL_VENDA_UNIT"]].copy()
        df_estoque["_VAL_VENDA_UNIT"] = df_estoque["_VAL_VENDA_UNIT"].apply(fmt_brl)

        df_estoque = df_estoque.rename(columns={
            produto_col: "Produto",
            "_QTD": "Quantidade",
            "_VAL_VENDA_UNIT": "Preço Venda"
        })

        st.dataframe(df_estoque.reset_index(drop=True))

    else:
        st.info("Estoque vazio ou coluna de produto não encontrada.")
