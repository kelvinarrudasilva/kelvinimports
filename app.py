# app.py (corrigido: mapeamento de sheet names + diagnóstico)
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
      :root { --gold:#FFD700; --bg:#000000; --muted:#bbbbbb; --white:#FFFFFF; }
      .stApp { background-color: var(--bg); color: var(--gold); }
      .title { color: var(--gold); font-weight:700; font-size:22px; }
      .subtitle { color: var(--muted); font-size:12px; margin-bottom:12px; }
      .kpi { background: linear-gradient(90deg, #111111, #0b0b0b); padding:12px; border-radius:10px; text-align:center; }
      .kpi-value { color: var(--gold); font-size:22px; font-weight:700; }
      .kpi-label { color:var(--muted); font-size:13px; }
      .stDataFrame table { background-color:#050505; color:var(--white); }
      div[data-baseweb="select"] > div { background-color:#0d0d0d !important; border:1px solid rgba(255,215,0,0.35) !important; border-radius:6px !important; padding:2px 8px !important; min-height:30px !important; }
      div[data-baseweb="select"] * { color: var(--gold) !important; font-size:13px !important; }
      .table-card { background: linear-gradient(90deg,#0b0b0b,#111111); border: 1px solid rgba(255,215,0,0.08); padding:12px; border-radius:10px; }
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

def parse_num_col(s):
    return pd.to_numeric(
        s.astype(str).str.replace("R$", "").str.replace(".", "").str.replace(",", "."),
        errors="coerce"
    ).fillna(0)

def fmt_brl(x):
    try:
        return f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "R$ 0,00"

# ======================
# Load Excel from Google Drive (robusto)
# ======================
GDRIVE_URL = "https://drive.google.com/uc?id=1TsRjsfw1TVfeEWBBvhKvsGQ5YUCktn2b"

try:
    res = requests.get(GDRIVE_URL)
    res.raise_for_status()
    excel_buffer = BytesIO(res.content)
    xls = pd.ExcelFile(excel_buffer)
    # map uppercase -> original name
    sheet_map = {s.upper(): s for s in xls.sheet_names}
except Exception as e:
    st.error(f"Erro ao acessar planilha do Google Drive: {e}")
    st.stop()

def load_sheet_by_upper(name_upper):
    """
    name_upper: expected sheet name in UPPER (e.g. 'VENDAS', 'ESTOQUE')
    returns cleaned dataframe or None
    """
    if name_upper not in sheet_map:
        return None
    real_name = sheet_map[name_upper]
    try:
        df = pd.read_excel(excel_buffer, sheet_name=real_name)
        return clean_df(df)
    except Exception:
        return None

# load sheets using the mapping (preserve original case)
estoque = load_sheet_by_upper("ESTOQUE")
vendas = load_sheet_by_upper("VENDAS")
compras = load_sheet_by_upper("COMPRAS")

# safety: ensure DataFrames exist
if vendas is None:
    vendas = pd.DataFrame()
if estoque is None:
    estoque = pd.DataFrame()
if compras is None:
    compras = pd.DataFrame()

# ======================
# Colunas fixas VENDAS (conforme você informou)
# ======================
v_data = "DATA"
v_prod = "PRODUTO"
v_qtd = "QTD"
v_val_unit = "VALOR VENDA"
v_val_total = "VALOR TOTAL"
v_custo_unit = "MEDIA CUSTO UNITARIO"
v_lucro_unit = "LUCRO UNITARIO"

# ======================
# Preparar VENDAS (robusto)
# ======================
if not vendas.empty:
    # garantir existência das colunas esperadas; se faltar, tenta correspondência aproximada
    def try_col(df, want):
        if want in df.columns:
            return want
        up = want.upper()
        for c in df.columns:
            if up == str(c).upper():
                return c
        # tentativa parcial (palavra-chave)
        for c in df.columns:
            if up in str(c).upper():
                return c
        return None

    # remap nomes reais se necessário
    real_v_data = try_col(vendas, v_data)
    real_v_prod = try_col(vendas, v_prod)
    real_v_qtd = try_col(vendas, v_qtd)
    real_v_val_unit = try_col(vendas, v_val_unit)
    real_v_val_total = try_col(vendas, v_val_total)
    real_v_lucro_unit = try_col(vendas, v_lucro_unit)

    # se colunas essenciais ausentes, avisar (mas tentamos prosseguir)
    missing = []
    if real_v_prod is None: missing.append("PRODUTO")
    if real_v_qtd is None: missing.append("QTD")
    if real_v_val_unit is None and real_v_val_total is None: missing.append("VALOR (unit/total)")
    if missing:
        st.warning("Atenção: colunas esperadas em VENDAS não encontradas: " + ", ".join(missing))

    # converter DATA
    if real_v_data:
        vendas[real_v_data] = pd.to_datetime(vendas[real_v_data].astype(str).str.strip(), dayfirst=True, errors="coerce")
        vendas[v_data] = vendas[real_v_data]
    else:
        vendas[v_data] = pd.NaT

    # QTD
    if real_v_qtd:
        vendas["_QTD"] = pd.to_numeric(vendas[real_v_qtd], errors="coerce").fillna(0)
    else:
        vendas["_QTD"] = 0

    # VALOR UNIT
    if real_v_val_unit:
        vendas["_VAL_UNIT"] = parse_num_col(vendas[real_v_val_unit])
    else:
        vendas["_VAL_UNIT"] = 0

    # VALOR TOTAL
    if real_v_val_total:
        vendas["_VAL_TOTAL"] = parse_num_col(vendas[real_v_val_total])
    else:
        vendas["_VAL_TOTAL"] = 0

    # preencher VAL_TOTAL a partir de unit*QTD quando faltar
    vendas.loc[vendas["_VAL_TOTAL"] == 0, "_VAL_TOTAL"] = vendas["_VAL_UNIT"] * vendas["_QTD"]

    # LUCRO UNITÁRIO
    if real_v_lucro_unit:
        vendas["_LUCRO_UNIT"] = parse_num_col(vendas[real_v_lucro_unit])
    else:
        # tentar encontrar "LUCRO" genérico
        luccol = try_col(vendas, "LUCRO")
        if luccol:
            vendas["_LUCRO_UNIT"] = parse_num_col(vendas[luccol])
        else:
            vendas["_LUCRO_UNIT"] = 0

    vendas["_LUCRO"] = vendas["_LUCRO_UNIT"] * vendas["_QTD"]

    # periodo (M)
    vendas["_PERIODO"] = vendas[v_data].dt.to_period("M").astype(str)

    # garantir col PROD com nome padrão para agrupamentos
    if real_v_prod:
        vendas["_PROD_NORM"] = vendas[real_v_prod].astype(str)
    else:
        vendas["_PROD_NORM"] = "(sem produto)"
else:
    vendas = pd.DataFrame(columns=[v_data, v_prod, v_qtd, v_val_unit, v_val_total])
    vendas["_QTD"] = 0
    vendas["_VAL_TOTAL"] = 0
    vendas["_LUCRO"] = 0
    vendas["_PERIODO"] = None
    vendas["_PROD_NORM"] = "(vazio)"

# ======================
# Preparar ESTOQUE (robusto)
# ======================
if not estoque.empty:
    # tentar encontrar produto e qtd nas colunas do estoque
    def try_col_est(df, candidates):
        for cand in candidates:
            for c in df.columns:
                if cand.upper() == str(c).upper() or cand.upper() in str(c).upper():
                    return c
        return None

    real_e_prod = try_col_est(estoque, ["PRODUTO", "Produto", "Produto "])
    real_e_qtd = try_col_est(estoque, ["EM ESTOQUE", "QTD", "QUANTIDADE", "Quant"])
    real_e_val_venda = try_col_est(estoque, ["Valor Venda Sugerido", "VALOR VENDA", "Preco Venda"])

    estoque["_QTD"] = pd.to_numeric(estoque[real_e_qtd], errors="coerce").fillna(0) if real_e_qtd else 0
    if real_e_val_venda:
        estoque["_VAL_VENDA_UNIT"] = parse_num_col(estoque[real_e_val_venda])
    else:
        estoque["_VAL_VENDA_UNIT"] = 0
    estoque["_VAL_TOTAL_VENDA"] = estoque["_QTD"] * estoque["_VAL_VENDA_UNIT"]
else:
    estoque = pd.DataFrame(columns=["PRODUTO", "_QTD", "_VAL_VENDA_UNIT", "_VAL_TOTAL_VENDA"])

# ======================
# Period selector build
# ======================
unique_periods = sorted([p for p in vendas["_PERIODO"].dropna().unique()], reverse=True)
period_map = {"Geral": None}
for p in unique_periods:
    try:
        year, month = p.split("-")
        pretty = datetime(int(year), int(month), 1).strftime("%b %Y")
    except Exception:
        pretty = p
    period_map[f"{pretty} ({p})"] = p

period_options = list(period_map.keys())
if not period_options:
    period_options = ["Geral"]

# ======================
# Tabs
# ======================
tab1, tab2 = st.tabs(["📈 Visão Geral", "📦 Estoque Atual"])

# ---- Tab 1: Visão Geral ----
with tab1:
    periodo_sel = st.selectbox("Período", period_options, index=0)
    periodo_val = period_map.get(periodo_sel)

    if periodo_val is None:
        vendas_period = vendas.copy()
    else:
        vendas_period = vendas[vendas["_PERIODO"] == periodo_val].copy()

    total_vendido = vendas_period["_VAL_TOTAL"].sum()
    total_qtd = vendas_period["_QTD"].sum()
    lucro_period = vendas_period["_LUCRO"].sum()
    valor_estoque = estoque["_VAL_TOTAL_VENDA"].sum() if "_VAL_TOTAL_VENDA" in estoque.columns else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💰 Vendido", fmt_brl(total_vendido))
    c2.metric("📈 Quantidade", int(total_qtd))
    c3.metric("💸 Lucro", fmt_brl(lucro_period))
    c4.metric("📦 Valor do Estoque", fmt_brl(valor_estoque))

    st.markdown("---")

    st.subheader("🏆 Top 10 Produtos Mais Vendidos")
    if not vendas_period.empty:
        grp = vendas_period.groupby("_PROD_NORM").agg(QTDE=("_QTD", "sum"), TOTAL=("_VAL_TOTAL", "sum")).reset_index()
        grp = grp.sort_values("TOTAL", ascending=False).head(10)
        if not grp.empty:
            fig = px.bar(grp, x="TOTAL", y="_PROD_NORM", orientation="h", text="QTDE", color="TOTAL", color_continuous_scale=["#FFD700", "#B8860B"])
            fig.update_traces(textposition="outside")
            fig.update_layout(plot_bgcolor="#000", paper_bgcolor="#000", font_color="#FFD700", yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Nenhuma venda para o período selecionado.")

    st.markdown("---")
    st.subheader("📋 Vendas do Período")
    if not vendas_period.empty:
        df_show = vendas_period[[v_data, "_PROD_NORM", "_QTD", "_VAL_TOTAL", "_LUCRO"]].copy()
        df_show[v_data] = pd.to_datetime(df_show[v_data], errors="coerce").dt.strftime("%d/%m/%Y")
        df_show["_VAL_TOTAL"] = df_show["_VAL_TOTAL"].apply(fmt_brl)
        df_show["_LUCRO"] = df_show["_LUCRO"].apply(fmt_brl)
        df_show = df_show.rename(columns={v_data: "Data", "_PROD_NORM": "Produto", "_QTD": "Quantidade", "_VAL_TOTAL": "Valor", "_LUCRO": "Lucro"})
        st.dataframe(df_show.reset_index(drop=True))
    else:
        st.info("Nenhuma venda para o período selecionado.")

# ---- Tab 2: Estoque Atual ----
with tab2:
    st.subheader("📦 Estoque Atual")
    if not estoque.empty:
        # tentamos adotar coluna de produto real
        prod_col = None
        for c in estoque.columns:
            if "PROD" in str(c).upper():
                prod_col = c
                break
        if prod_col is None:
            prod_col = estoque.columns[0] if len(estoque.columns) > 0 else "Produto"

        df_est = estoque[[prod_col, "_QTD", "_VAL_VENDA_UNIT"]].copy() if prod_col in estoque.columns else estoque.copy()
        # format
        df_est["_VAL_VENDA_UNIT"] = df_est["_VAL_VENDA_UNIT"].apply(fmt_brl)
        df_est = df_est.rename(columns={prod_col: "Produto", "_QTD": "Quantidade", "_VAL_VENDA_UNIT": "Preço Venda"})
        st.dataframe(df_est.reset_index(drop=True))
    else:
        st.info("Estoque vazio ou colunas não detectadas.")

# ========== Diagnóstico (útil para depurar) ==========
with st.expander("🔧 Diagnóstico (sheets e colunas detectadas)"):
    st.write("SHEETS (originais):", xls.sheet_names)
    st.write("SHEET MAP (UPPER->original):", sheet_map)
    st.write("VENDAS columns:", list(vendas.columns))
    st.write("ESTOQUE columns:", list(estoque.columns))
    st.write("Mapeamento tentado para VENDAS:", {
        "DATA": v_data,
        "PRODUTO(detected)": "_PROD_NORM",
        "QTD": "_QTD",
        "VAL UNIT detected (col)": real_v_val_unit if 'real_v_val_unit' in locals() else None,
        "VAL TOTAL detected (col)": real_v_val_total if 'real_v_val_total' in locals() else None,
        "LUCRO UNIT detected (col)": real_v_lucro_unit if 'real_v_lucro_unit' in locals() else None
    })

st.markdown("---")
st.caption("Dashboard — Tema: Preto + Dourado. Desenvolvido em Streamlit.")
