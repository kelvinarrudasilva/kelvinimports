# app.py
import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from io import BytesIO
import re

# ======================
# CONFIGURAÇÕES ONE DRIVE / GRAPH API
# ======================
TENANT_ID = "7f62cdaf-4d31-4ea5-840b-f3e9cdad7ce8"
CLIENT_ID = "55b457d1-fc13-48ba-b62d-aa42f45c7913"
CLIENT_SECRET = "7e048363-4fa2-4a38-8dd5-b6df2cf44412"
FILE_ID = "a714c9c7-aa92-4184-94f5-560f5edd5270"

# ======================
# FUNÇÕES DE AUTENTICAÇÃO E DOWNLOAD
# ======================
def get_access_token(tenant_id, client_id, client_secret):
    url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    payload = {
        "client_id": client_id,
        "scope": "https://graph.microsoft.com/.default",
        "client_secret": client_secret,
        "grant_type": "client_credentials"
    }
    r = requests.post(url, data=payload)
    r.raise_for_status()
    return r.json()["access_token"]

def download_excel(file_id, access_token):
    url = f"https://graph.microsoft.com/v1.0/me/drive/items/{file_id}/content"
    headers = {"Authorization": f"Bearer {access_token}"}
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    return BytesIO(r.content)

# ======================
# OBTER O ARQUIVO
# ======================
st.set_page_config(page_title="Painel - Loja Importados", layout="wide")

try:
    token = get_access_token(TENANT_ID, CLIENT_ID, CLIENT_SECRET)
    excel_file = download_excel(FILE_ID, token)
except Exception as e:
    st.error(f"Erro ao baixar o arquivo do OneDrive: {e}")
    st.stop()

# ======================
# FUNÇÕES AUXILIARES
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
    df.columns = [str(c).strip() for c in df.columns]
    df = df.loc[:, ~df.columns.str.contains("^Unnamed", na=False)]
    df = df.dropna(axis=1, how="all")
    df = df.dropna(axis=0, how="all").reset_index(drop=True)
    return df

def find_col(df, *candidates):
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
# CARREGAR PLANILHA
# ======================
xls = pd.ExcelFile(excel_file)
available = set([s.upper() for s in xls.sheet_names])
needed = {"ESTOQUE", "VENDAS", "COMPRAS"}
found = needed.intersection(available)

# Função de carregamento
def load_sheet(name):
    if name not in available:
        return None, f"Aba '{name}' não encontrada"
    df, hdr = detect_header(excel_file, name)
    df = clean_df(df)
    return df, None

estoque, err_e = load_sheet("ESTOQUE")
vendas, err_v = load_sheet("VENDAS")
compras, err_c = load_sheet("COMPRAS")

if err_e: st.warning(err_e)
if err_v: st.warning(err_v)
if err_c: st.warning(err_c)

# ======================
# MAPEAR COLUNAS
# ======================
# Estoque
e_prod = find_col(estoque, "PRODUTO")
e_qtd = find_col(estoque, "EM ESTOQUE", "QTD", "QUANTIDADE")
e_valor_unit = find_col(estoque, "Valor Venda Sugerido", "VALOR VENDA")

# Vendas
v_data = find_col(vendas, "DATA")
v_prod = find_col(vendas, "PRODUTO")
v_qtd = find_col(vendas, "QTD", "QUANTIDADE")
v_val_unit = find_col(vendas, "VALOR VENDA", "VALOR_VENDA")
v_val_total = find_col(vendas, "VALOR TOTAL", "VALOR_TOTAL", "TOTAL")
v_media_custo = find_col(vendas, "MEDIA CUSTO UNITARIO", "MEDIA C. UNITARIO")
v_lucro = find_col(vendas, "LUCRO")

# Compras
c_data = find_col(compras, "DATA")
c_prod = find_col(compras, "PRODUTO")
c_qtd = find_col(compras, "QUANTIDADE", "QTD")
c_custo_unit = find_col(compras, "CUSTO UNITÁRIO", "CUSTO UNIT")
c_custo_total = find_col(compras, "CUSTO TOTAL", "VALOR TOTAL")

# ======================
# PROCESSAR DADOS
# ======================
if vendas is not None and v_data in vendas.columns:
    vendas[v_data] = pd.to_datetime(vendas[v_data], errors="coerce")
    vendas["_VAL_UNIT"] = to_num(vendas[v_val_unit])
    vendas["_QTD"] = to_num(vendas[v_qtd])
    vendas["_VAL_TOTAL"] = to_num(vendas[v_val_total]) if v_val_total else vendas["_VAL_UNIT"]*vendas["_QTD"]
    if v_lucro in vendas.columns:
        vendas["_LUCRO"] = to_num(vendas[v_lucro])
    else:
        vendas["_CUSTO_UNIT"] = to_num(vendas[v_media_custo]) if v_media_custo else 0
        vendas["_LUCRO"] = (vendas["_VAL_UNIT"] - vendas["_CUSTO_UNIT"]) * vendas["_QTD"]

if compras is not None and c_data in compras.columns:
    compras[c_data] = pd.to_datetime(compras[c_data], errors="coerce")
    compras["_CUSTO_TOTAL"] = to_num(compras[c_custo_total])
    compras["_CUSTO_UNIT"] = to_num(compras[c_custo_unit])
    compras["_QTD"] = to_num(compras[c_qtd])

if estoque is not None:
    estoque["_QTD_ESTOQUE"] = to_num(estoque[e_qtd]) if e_qtd else 0
    estoque["_VAL_UNIT_ESTOQ"] = to_num(estoque[e_valor_unit]) if e_valor_unit else 0
    estoque["_VAL_TOTAL_ESTOQUE"] = estoque["_QTD_ESTOQUE"]*estoque["_VAL_UNIT_ESTOQ"]

# ======================
# SIDEBAR FILTROS
# ======================
st.sidebar.header("Filtros")
if vendas is not None and v_data in vendas.columns:
    min_date = vendas[v_data].min().date()
    max_date = vendas[v_data].max().date()
    date_range = st.sidebar.date_input("Período (Vendas)", value=(min_date, max_date))
else:
    date_range = None

prod_set = set()
if vendas is not None and v_prod in vendas.columns:
    prod_set.update(vendas[v_prod].dropna().astype(str).unique())
if estoque is not None and e_prod in estoque.columns:
    prod_set.update(estoque[e_prod].dropna().astype(str).unique())
prod_list = sorted([p for p in prod_set if str(p).strip()!=""])
prod_filter = st.sidebar.multiselect("Produtos (filtrar)", options=prod_list, default=prod_list)

# ======================
# FILTRAR VENDAS
# ======================
vendas_f = vendas.copy() if vendas is not None else pd.DataFrame()
if date_range and isinstance(date_range, (list, tuple)) and len(date_range)==2:
    d_from, d_to = date_range
    vendas_f = vendas_f[(vendas_f[v_data].dt.date >= d_from) & (vendas_f[v_data].dt.date <= d_to)]

if prod_filter:
    vendas_f = vendas_f[vendas_f[v_prod].astype(str).isin(prod_filter)]

# ======================
# TABS VISUALIZAÇÃO
# ======================
tab1, tab2 = st.tabs(["📈 Visão Geral", "📦 Estoque Atual"])

with tab1:
    st.markdown("## Visão Geral — vendas e lucro (período filtrado)")
    total_vendido_period = vendas_f["_VAL_TOTAL"].sum() if "_VAL_TOTAL" in vendas_f.columns else 0
    lucro_period = vendas_f["_LUCRO"].sum() if "_LUCRO" in vendas_f.columns else 0
    valor_total_estoque = estoque["_VAL_TOTAL_ESTOQUE"].sum() if estoque is not None else 0
    k1, k2, k3 = st.columns(3)
    k1.metric("💰 Vendido no período", fmt_brl(total_vendido_period))
    k2.metric("📈 Lucro no período", fmt_brl(lucro_period))
    k3.metric("📦 Valor total do estoque", fmt_brl(valor_total_estoque))

    st.markdown("---")
    st.subheader("🏆 Top 10 — Produtos Mais Vendidos")
    if not vendas_f.empty:
        top = vendas_f.groupby(v_prod).agg(
            QTDE_SOMADA=(v_qtd, lambda s: to_num(s).sum()),
            VAL_TOTAL=("_VAL_TOTAL", lambda s: to_num(s).sum())
        ).reset_index().sort_values("VAL_TOTAL", ascending=False).head(10)
        if not top.empty:
            fig_top = px.bar(top, x="VAL_TOTAL", y=v_prod, orientation="h", text="QTDE_SOMADA", color="VAL_TOTAL", color_continuous_scale=["#FFD700","#B8860B"])
            fig_top.update_traces(texttemplate='%{text:.0f} un', textposition='outside')
            fig_top.update_layout(plot_bgcolor="#000000", paper_bgcolor="#000000", font_color="#FFD700", yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_top, use_container_width=True)
            top_display = top.copy()
            top_display["VAL_TOTAL"] = top_display["VAL_TOTAL"].apply(fmt_brl)
            top_display["QTDE_SOMADA"] = top_display["QTDE_SOMADA"].astype(int)
            st.table(top_display.rename(columns={v_prod:"PRODUTO","QTDE_SOMADA":"QUANTIDADE","VAL_TOTAL":"VALOR TOTAL"}))
        else:
            st.info("Nenhuma venda no período/filtragem selecionada.")
    else:
        st.info("Sem vendas filtradas.")

with tab2:
    st.markdown("## Estoque Atual — controle claro")
    if estoque is not None:
        est_view = estoque.copy()
        est_view["PRODUTO"] = est_view[e_prod].astype(str)
        est_view["QUANTIDADE"] = est_view["_QTD_ESTOQUE"].astype(int)
        est_view["PRECO_UNITARIO_VENDA"] = est_view["_VAL_UNIT_ESTOQ"]
        est_view["VALOR_TOTAL_ESTOQUE"] = est_view["_VAL_TOTAL_ESTOQUE"]

        if prod_filter:
            est_view = est_view[est_view["PRODUTO"].isin(prod_filter)]

        total_qty_est = est_view["QUANTIDADE"].sum()
        total_val_est = est_view["VALOR_TOTAL_ESTOQUE"].sum()
        c1, c2 = st.columns(2)
        c1.metric("📦 Qtde total em estoque", f"{int(total_qty_est):,}".replace(",", "."))
        c2.metric("💰 Valor total do estoque", fmt_brl(total_val_est))

        st.markdown("---")
        st.subheader("Tabela de Estoque")
        display_cols = ["PRODUTO", "QUANTIDADE", "PRECO_UNITARIO_VENDA", "VALOR_TOTAL_ESTOQUE"]
        df_show = est_view[display_cols].copy()
        df_show["PRECO_UNITARIO_VENDA"] = df_show["PRECO_UNITARIO_VENDA"].apply(fmt_brl)
        df_show["VALOR_TOTAL_ESTOQUE"] = df_show["VALOR_TOTAL_ESTOQUE"].apply(fmt_brl)
        st.dataframe(df_show.sort_values("QUANTIDADE", ascending=False).reset_index(drop=True))

        top_value = est_view.sort_values("VALOR_TOTAL_ESTOQUE", ascending=False).head(15)
        if not top_value.empty:
            fig_e = px.bar(top_value, x="PRODUTO", y="VALOR_TOTAL_ESTOQUE", color="VALOR_TOTAL_ESTOQUE", color_continuous_scale=["#FFD700","#B8860B"])
            fig_e.update_layout(plot_bgcolor="#000000", paper_bgcolor="#000000", font_color="#FFD700")
            st.plotly_chart(fig_e, use_container_width=True)
