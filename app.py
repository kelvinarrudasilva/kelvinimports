# app.py
import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
import re

# ======================
# Configuração inicial
# ======================
st.set_page_config(page_title="Painel - Loja Importados", layout="wide")

# ======================
# Funções utilitárias
# ======================
def detect_header(path, sheet_name, look_for="PRODUTO"):
    raw = pd.read_excel(path, sheet_name=sheet_name, header=None)
    header_row = None
    for i in range(min(len(raw), 12)):
        row = raw.iloc[i].astype(str).str.upper().fillna("")
        if any(look_for.upper() in v for v in row):
            header_row = i
            break
    if header_row is None:
        header_row = 0
    df = pd.read_excel(path, sheet_name=sheet_name, header=header_row)
    return df, header_row

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
        pattern = re.sub(r"\s+", " ", str(cand)).strip().upper()
        for c in df.columns:
            if pattern in str(c).upper():
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
# Seleção de tema
# ======================
theme = st.sidebar.radio("🎨 Tema do Painel", ["Preto + Dourado", "Escuro + Azul", "Claro + Verde"], index=0)

if theme == "Preto + Dourado":
    colors = {"bg":"#000000","gold":"#FFD700","card":"#0f0f0f","muted":"#bfbfbf"}
elif theme == "Escuro + Azul":
    colors = {"bg":"#0B0C2A","gold":"#00BFFF","card":"#101840","muted":"#9DBBF7"}
else:
    colors = {"bg":"#F5F5F5","gold":"#228B22","card":"#DFF0D8","muted":"#555555"}

st.markdown(f"""
<style>
:root {{ --gold:{colors['gold']}; --bg:{colors['bg']}; --card:{colors['card']}; --muted:{colors['muted']}; }}
.stApp {{ background-color: var(--bg); color: var(--gold); }}
.title {{ color: var(--gold); font-weight:700; font-size:22px; }}
.subtitle {{ color: var(--muted); font-size:12px; margin-bottom:12px; }}
.kpi {{ background: var(--card); padding:12px; border-radius:10px; text-align:center; }}
.kpi-value {{ color: var(--gold); font-size:20px; font-weight:700; }}
.kpi-label {{ color:var(--muted); font-size:13px; }}
.stDataFrame table {{ background-color: var(--card); color: var(--gold); }}
</style>
""", unsafe_allow_html=True)

st.markdown("<div class='title'>📊 Painel — Loja Importados</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Tema selecionado: "+theme+"</div>", unsafe_allow_html=True)
st.markdown("---")

# ======================
# Carregar Excel
# ======================
EXCEL = "LOJA IMPORTADOS.xlsx"
if not Path(EXCEL).exists():
    st.error(f"Arquivo '{EXCEL}' não encontrado.")
    st.stop()

xls = pd.ExcelFile(EXCEL)
available = set([s.upper() for s in xls.sheet_names])

def load_sheet(name):
    if name not in available:
        return None, f"Aba '{name}' não encontrada"
    df, hdr = detect_header(EXCEL, name)
    df = clean_df(df)
    return df, None

estoque, err_e = load_sheet("ESTOQUE")
vendas, err_v = load_sheet("VENDAS")
compras, err_c = load_sheet("COMPRAS")

for e in [err_e, err_v, err_c]:
    if e: st.warning(e)

# ======================
# Mapear colunas
# ======================
e_prod = find_col(estoque,"PRODUTO")
e_qtd = find_col(estoque,"EM ESTOQUE","QTD","QUANTIDADE")
e_val = find_col(estoque,"VALOR","VALOR VENDA")

v_data = find_col(vendas,"DATA")
v_prod = find_col(vendas,"PRODUTO")
v_qtd = find_col(vendas,"QTD","QUANTIDADE")
v_val_unit = find_col(vendas,"VALOR VENDA","VALOR_VENDA")
v_val_total = find_col(vendas,"VALOR TOTAL","VALOR_TOTAL","TOTAL")
v_lucro = find_col(vendas,"LUCRO")

# ======================
# Normalizar dados
# ======================
if vendas is not None:
    if v_data in vendas.columns: vendas[v_data] = pd.to_datetime(vendas[v_data], errors="coerce")
    if v_val_unit in vendas.columns: vendas["_VAL_UNIT"] = to_num(vendas[v_val_unit])
    if v_qtd in vendas.columns: vendas["_QTD"] = to_num(vendas[v_qtd])
    if v_val_total in vendas.columns: vendas["_VAL_TOTAL"] = to_num(vendas[v_val_total])
    else: vendas["_VAL_TOTAL"] = vendas["_VAL_UNIT"]*vendas["_QTD"]
    if v_lucro in vendas.columns: vendas["_LUCRO"] = to_num(vendas[v_lucro])
    else: vendas["_LUCRO"] = vendas["_VAL_TOTAL"]  # fallback simples

if estoque is not None:
    if e_qtd in estoque.columns: estoque["_QTD"] = to_num(estoque[e_qtd])
    if e_val in estoque.columns: estoque["_VAL"] = to_num(estoque[e_val])
    if "_QTD" in estoque.columns and "_VAL" in estoque.columns:
        estoque["_VAL_TOTAL"] = estoque["_QTD"]*estoque["_VAL"]
    else: estoque["_VAL_TOTAL"] = 0

# ======================
# Sidebar filtros
# ======================
st.sidebar.header("Filtros")
prod_set = set()
if vendas is not None and v_prod in vendas.columns: prod_set.update(vendas[v_prod].dropna().astype(str).unique())
if estoque is not None and e_prod in estoque.columns: prod_set.update(estoque[e_prod].dropna().astype(str).unique())
prod_list = sorted([p for p in prod_set if str(p).strip()!=""])
prod_filter = st.sidebar.multiselect("Produtos", options=prod_list, default=prod_list)

date_range = None
if vendas is not None and v_data in vendas.columns:
    min_date = vendas[v_data].min().date() if pd.notna(vendas[v_data].min()) else None
    max_date = vendas[v_data].max().date() if pd.notna(vendas[v_data].max()) else None
    date_range = st.sidebar.date_input("Período (Vendas)", value=(min_date,max_date))

# ======================
# Aplicar filtros
# ======================
vendas_f = vendas.copy() if vendas is not None else pd.DataFrame()
if date_range and isinstance(date_range,(list,tuple)) and len(date_range)==2:
    d_from,d_to = date_range
    if v_data in vendas_f.columns:
        vendas_f = vendas_f[(vendas_f[v_data].dt.date>=d_from)&(vendas_f[v_data].dt.date<=d_to)]
if prod_filter:
    vendas_f = vendas_f[vendas_f[v_prod].astype(str).isin(prod_filter)]

# ======================
# Abas
# ======================
tab1, tab2 = st.tabs(["📈 Visão Geral","📦 Estoque Atual"])

with tab1:
    st.subheader("KPIs")
    total_vendido = vendas_f["_VAL_TOTAL"].sum() if "_VAL_TOTAL" in vendas_f.columns else 0
    lucro_total = vendas_f["_LUCRO"].sum() if "_LUCRO" in vendas_f.columns else 0
    val_estoque = estoque["_VAL_TOTAL"].sum() if estoque is not None else 0
    c1,c2,c3 = st.columns(3)
    c1.metric("💰 Vendido", fmt_brl(total_vendido))
    c2.metric("📈 Lucro", fmt_brl(lucro_total))
    c3.metric("📦 Valor Estoque", fmt_brl(val_estoque))

    st.markdown("---")
    st.subheader("Top 10 Produtos")
    if v_prod in vendas_f.columns and v_qtd in vendas_f.columns:
        top = vendas_f.groupby(v_prod).agg(QTDE=(v_qtd, "sum"), VAL_TOTAL=("_VAL_TOTAL","sum")).reset_index()
        top = top.sort_values("VAL_TOTAL",ascending=False).head(10)
        fig = px.bar(top, x="VAL_TOTAL", y=v_prod, orientation="h", color="VAL_TOTAL",
                     color_continuous_scale=[colors['gold'],"#B8860B"], text="QTDE")
        fig.update_traces(texttemplate='%{text}', textposition='outside')
        fig.update_layout(plot_bgcolor=colors['bg'], paper_bgcolor=colors['bg'], font_color=colors['gold'])
        st.plotly_chart(fig, use_container_width=True)
        st.table(top.rename(columns={v_prod:"PRODUTO","QTDE":"QUANTIDADE","VAL_TOTAL":"VALOR TOTAL"}))
    else:
        st.info("Colunas de vendas não encontradas.")

with tab2:
    st.subheader("Estoque Atual")
    if estoque is not None and e_prod in estoque.columns:
        est_view = estoque.copy()
        est_view["PRODUTO"] = est_view[e_prod].astype(str)
        est_view["QUANTIDADE"] = est_view["_QTD"].astype(int) if "_QTD" in est_view.columns else 0
        est_view["VALOR_TOTAL_ESTOQUE"] = est_view["_VAL_TOTAL"] if "_VAL_TOTAL" in est_view.columns else 0
        if prod_filter: est_view = est_view[est_view["PRODUTO"].isin(prod_filter)]
        st.metric("Qtde Total", est_view["QUANTIDADE"].sum())
        st.metric("Valor Total", fmt_brl(est_view["VALOR_TOTAL_ESTOQUE"].sum()))
        st.dataframe(est_view[["PRODUTO","QUANTIDADE","VALOR_TOTAL_ESTOQUE"]])
        fig = px.bar(est_view.sort_values("VALOR_TOTAL_ESTOQUE",ascending=False).head(15),
                     x="PRODUTO", y="VALOR_TOTAL_ESTOQUE", color="VALOR_TOTAL_ESTOQUE",
                     color_continuous_scale=[colors['gold'],"#B8860B"])
        fig.update_layout(plot_bgcolor=colors['bg'], paper_bgcolor=colors['bg'], font_color=colors['gold'])
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Aba ESTOQUE ou colunas não encontradas.")

st.markdown("---")
st.caption("Dashboard — Temas dinâmicos. Desenvolvido em Streamlit.")
