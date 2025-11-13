# app.py
import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
import re

# ======================
# Config visual (Dark mode alto contraste)
# ======================
st.set_page_config(page_title="Painel - Loja Importados", layout="wide")

st.markdown(
    """
    <style>
      :root { --primary:#FFFFFF; --bg:#000000; --accent:#8000FF; --muted:#AAAAAA; }
      .stApp { background-color: var(--bg); color: var(--primary); }
      .title { color: var(--primary); font-weight:700; font-size:22px; }
      .subtitle { color: var(--muted); font-size:12px; margin-bottom:12px; }
      .kpi { background: linear-gradient(90deg, #111111, #1a1a1a); padding:12px; border-radius:10px; text-align:center; }
      .kpi-value { color: var(--accent); font-size:22px; font-weight:700; }
      .kpi-label { color:var(--muted); font-size:14px; }
      .stDataFrame table { background-color:#050505; color:#FFFFFF; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown("<div class='title'>📊 Painel — Loja Importados</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Tema: Dark Mode • Abas: Visão Geral / Estoque / Vendas</div>", unsafe_allow_html=True)
st.markdown("---")

# ======================
# Funções auxiliares
# ======================
def detect_header(path, sheet_name, look_for="PRODUTO"):
    raw = pd.read_excel(path, sheet_name=sheet_name, header=None)
    header_row = None
    for i in range(min(len(raw), 12)):
        row = raw.iloc[i].astype(str).str.upper().fillna("")
        if any(look_for.upper() in v for v in row):
            header_row = i
            break
    if header_row is None: header_row = 0
    df = pd.read_excel(path, sheet_name=sheet_name, header=header_row)
    return df

def clean_df(df):
    df.columns = [str(c).strip() for c in df.columns]
    df = df.loc[:, ~df.columns.str.contains("^Unnamed", na=False)]
    df = df.dropna(axis=1, how="all")
    df = df.dropna(axis=0, how="all").reset_index(drop=True)
    return df

def find_col(df, *candidates):
    for cand in candidates:
        pattern = re.sub(r"\s+", " ", str(cand)).strip().upper()
        for c in df.columns:
            if pattern in str(c).upper(): return c
    return None

def to_num(s):
    return pd.to_numeric(s, errors="coerce").fillna(0)

def fmt_brl(x):
    try:
        return f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "R$ 0,00"

# ======================
# Carregar planilha
# ======================
EXCEL = "LOJA IMPORTADOS.xlsx"
if not Path(EXCEL).exists():
    st.error(f"Arquivo '{EXCEL}' não encontrado.")
    st.stop()

xls = pd.ExcelFile(EXCEL)
available = set([s.upper() for s in xls.sheet_names])
needed = {"ESTOQUE", "VENDAS", "COMPRAS"}

def load_sheet(name):
    if name not in available: return None
    df = detect_header(EXCEL, name)
    df = clean_df(df)
    return df

estoque = load_sheet("ESTOQUE")
vendas = load_sheet("VENDAS")
compras = load_sheet("COMPRAS")

# Mapear colunas
e_prod = find_col(estoque,"PRODUTO")
e_qtd = find_col(estoque,"EM ESTOQUE","QTD","QUANTIDADE")
e_val = find_col(estoque,"VALOR","Valor Venda")

v_data = find_col(vendas,"DATA")
v_prod = find_col(vendas,"PRODUTO")
v_qtd = find_col(vendas,"QTD","QUANTIDADE")
v_val = find_col(vendas,"VALOR TOTAL","VALOR_TOTAL","TOTAL")

# Normalizar dados
if vendas is not None:
    vendas[v_data] = pd.to_datetime(vendas[v_data], errors="coerce")
    vendas["_QTD"] = to_num(vendas[v_qtd]) if v_qtd in vendas.columns else 0
    vendas["_VAL_TOTAL"] = to_num(vendas[v_val]) if v_val in vendas.columns else vendas["_QTD"]*0

if estoque is not None:
    estoque["_QTD"] = to_num(estoque[e_qtd]) if e_qtd in estoque.columns else 0
    estoque["_VAL_TOTAL"] = to_num(estoque[e_val]) if e_val in estoque.columns else 0
    estoque["PRODUTO"] = estoque[e_prod].astype(str)

# ======================
# Sidebar Filtros
# ======================
st.sidebar.header("Filtros Gerais")
prod_list = sorted(list(set(vendas[v_prod].dropna().astype(str)) if vendas is not None else []))
prod_filter = st.sidebar.multiselect("Filtrar Produtos", options=prod_list, default=prod_list)

date_min = vendas[v_data].min().date() if vendas is not None else None
date_max = vendas[v_data].max().date() if vendas is not None else None
date_range = st.sidebar.date_input("Período", value=(date_min,date_max))

vendas_f = vendas.copy() if vendas is not None else pd.DataFrame()
if date_range and len(date_range)==2:
    d_from,d_to = date_range
    vendas_f = vendas_f[(vendas_f[v_data].dt.date>=d_from)&(vendas_f[v_data].dt.date<=d_to)]

if prod_filter: vendas_f = vendas_f[vendas_f[v_prod].astype(str).isin(prod_filter)]

# ======================
# Abas
# ======================
tab1, tab2, tab3 = st.tabs(["📈 Visão Geral","📦 Estoque Atual","🛒 Vendas Detalhadas"])

# ----------------------
# Aba Visão Geral
# ----------------------
with tab1:
    st.markdown("## KPIs")
    k1,k2,k3 = st.columns(3)
    total_vendido = vendas_f["_VAL_TOTAL"].sum()
    total_qtd = vendas_f["_QTD"].sum()
    total_estoque = estoque["_VAL_TOTAL"].sum() if estoque is not None else 0
    k1.markdown(f"<div class='kpi'><div class='kpi-label'>💰 Vendido</div><div class='kpi-value'>{fmt_brl(total_vendido)}</div></div>", unsafe_allow_html=True)
    k2.markdown(f"<div class='kpi'><div class='kpi-label'>📈 Qtde Vendida</div><div class='kpi-value'>{int(total_qtd)}</div></div>", unsafe_allow_html=True)
    k3.markdown(f"<div class='kpi'><div class='kpi-label'>📦 Valor Estoque</div><div class='kpi-value'>{fmt_brl(total_estoque)}</div></div>", unsafe_allow_html=True)

    # Top 10 produtos vendidos
    st.markdown("## Top 10 Produtos Mais Vendidos")
    top10 = vendas_f.groupby(v_prod)["_QTD"].sum().reset_index().sort_values("_QTD", ascending=False).head(10)
    fig_top10 = px.bar(top10, x=v_prod, y="_QTD", color="_QTD", color_continuous_scale=["#8000FF","#D280FF"], text="_QTD")
    fig_top10.update_traces(textposition='outside')
    fig_top10.update_layout(plot_bgcolor="#000000", paper_bgcolor="#000000", font_color="#FFFFFF", xaxis_title="Produto", yaxis_title="Quantidade")
    st.plotly_chart(fig_top10,use_container_width=True)

    # Vendas últimos 4 meses
    st.markdown("## Vendas Últimos 4 Meses")
    vendas_f["_MES"] = vendas_f[v_data].dt.strftime("%b %Y")
    ult4 = sorted(vendas_f["_MES"].unique())[-4:]
    df_4m = vendas_f[vendas_f["_MES"].isin(ult4)].groupby("_MES")["_VAL_TOTAL"].sum().reset_index()
    fig_4m = px.bar(df_4m, x="_MES", y="_VAL_TOTAL", color="_VAL_TOTAL", color_continuous_scale=["#8000FF","#D280FF"], text="_VAL_TOTAL")
    fig_4m.update_traces(texttemplate='R$ %{text:,.2f}', textposition='outside')
    fig_4m.update_layout(plot_bgcolor="#000000", paper_bgcolor="#000000", font_color="#FFFFFF", xaxis_title="Mês", yaxis_title="Total R$")
    st.plotly_chart(fig_4m,use_container_width=True)

    # Histórico últimas vendas
    st.markdown("## 🕒 Últimas Vendas")
    ult_vendas = vendas_f[[v_data,v_prod,"_QTD","_VAL_TOTAL"]].sort_values(v_data,ascending=False).head(15)
    ult_vendas_disp = ult_vendas.copy()
    ult_vendas_disp["_VAL_TOTAL"] = ult_vendas_disp["_VAL_TOTAL"].apply(fmt_brl)
    ult_vendas_disp["_QTD"] = ult_vendas_disp["_QTD"].astype(int)
    ult_vendas_disp[v_data] = ult_vendas_disp[v_data].dt.strftime("%d/%m/%Y")
    st.dataframe(ult_vendas_disp.rename(columns={v_data:"Data",v_prod:"Produto","_QTD":"Quantidade","_VAL_TOTAL":"Valor"}))

    # Gráfico linha das últimas vendas
    fig_hist = px.line(ult_vendas, x=v_data, y="_VAL_TOTAL", markers=True, title="Histórico Últimas Vendas")
    fig_hist.update_traces(line_color="#D280FF")
    fig_hist.update_layout(plot_bgcolor="#000000", paper_bgcolor="#000000", font_color="#FFFFFF", xaxis_title="Data", yaxis_title="Valor R$")
    st.plotly_chart(fig_hist,use_container_width=True)

# ----------------------
# Aba Estoque
# ----------------------
with tab2:
    st.markdown("## Estoque Atual")
    est_view = estoque.copy() if estoque is not None else pd.DataFrame()
    if not est_view.empty:
        est_view["PRODUTO"] = est_view[e_prod].astype(str)
        est_view["_QTD"] = to_num(est_view[e_qtd])
        est_view["_VAL_TOTAL"] = to_num(est_view[e_val])
        if prod_filter: est_view = est_view[est_view["PRODUTO"].isin(prod_filter)]

        total_qtd_est = est_view["_QTD"].sum()
        total_val_est = est_view["_VAL_TOTAL"].sum()
        c1,c2 = st.columns(2)
        c1.metric("📦 Qtde total em estoque", f"{int(total_qtd_est)}")
        c2.metric("💰 Valor total do estoque", fmt_brl(total_val_est))

        # Top 15 estoque por quantidade
        top_est = est_view.sort_values("_QTD", ascending=False).head(15)
        fig_est = px.bar(top_est, x="PRODUTO", y="_QTD", color="_QTD", color_continuous_scale=["#8000FF","#D280FF"], text="_QTD")
        fig_est.update_traces(textposition='outside')
        fig_est.update_layout(plot_bgcolor="#000000", paper_bgcolor="#000000", font_color="#FFFFFF", xaxis_title="Produto", yaxis_title="Quantidade")
        st.plotly_chart(fig_est,use_container_width=True)

        est_disp = top_est[["PRODUTO","_QTD","_VAL_TOTAL"]].copy()
        est_disp["_VAL_TOTAL"] = est_disp["_VAL_TOTAL"].apply(fmt_brl)
        st.dataframe(est_disp.rename(columns={"_QTD":"Quantidade","_VAL_TOTAL":"Valor Total"}))
    else:
        st.warning("Aba ESTOQUE não carregada ou vazia.")

# ----------------------
# Aba Vendas Detalhadas
# ----------------------
with tab3:
    st.markdown("## Vendas Detalhadas")
    if not vendas_f.empty:
        vendas_det = vendas_f[[v_data,v_prod,"_QTD","_VAL_TOTAL"]].sort_values(v_data,ascending=False).copy()
        vendas_det["_VAL_TOTAL"] = vendas_det["_VAL_TOTAL"].apply(fmt_brl)
        vendas_det["_QTD"] = vendas_det["_QTD"].astype(int)
        vendas_det[v_data] = vendas_det[v_data].dt.strftime("%d/%m/%Y")
        st.dataframe(vendas_det.rename(columns={v_data:"Data",v_prod:"Produto","_QTD":"Quantidade","_VAL_TOTAL":"Valor"}))
    else:
        st.warning("Nenhuma venda encontrada para o filtro selecionado.")
