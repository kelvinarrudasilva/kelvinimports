import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import numpy as np

# --------------------------
# Configuração da página
# --------------------------
st.set_page_config(page_title="Dashboard - Loja Importados", layout="wide", initial_sidebar_state="expanded")
st.markdown(
    """
    <style>
    /* fundo escuro + header dourado */
    .stApp { background-color: #0b0b0b; color: #e6e2d3; }
    .stHeader, .css-18e3th9 { color: #e6e2d3; }
    .big-title { color: #E8C36A; font-weight:700; font-size:30px; }
    .kpi-card { background: linear-gradient(90deg, rgba(20,20,20,0.9), rgba(10,10,10,0.9)); border-radius:12px; padding:12px; }
    .gold { color: #E8C36A; font-weight:700; }
    .stCaption { color: #9e9b8f; }
    /* make dataframes background dark */
    .dataframe, .stDataFrame div.st-df { background: #0b0b0b !important; color: #e6e2d3 !important; }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown('<div class="big-title">📊 Dashboard - Loja Importados</div>', unsafe_allow_html=True)
st.markdown("**Visualização dark elegante (preto + dourado)** — análise de Estoque, Vendas e Compras")

# --------------------------
# Helpers
# --------------------------
def fmt_brl(value):
    try:
        return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return f"R$ 0,00"

def find_header_row(path, sheet, keywords=("PRODUTO", "DATA", "QUANTIDADE", "VALOR")):
    """
    Procura em até as primeiras 12 linhas a linha que contém um dos keywords (case-insensitive).
    Retorna índice da linha que deve ser usada como header (0-index).
    """
    try:
        preview = pd.read_excel(path, sheet_name=sheet, header=None, nrows=12)
    except Exception as e:
        return None, str(e)
    for i in range(len(preview)):
        row_vals = preview.iloc[i].astype(str).str.upper().fillna("")
        for kw in keywords:
            if any(row_vals.str.contains(kw)):
                return i, None
    # fallback: se nenhuma linha encontrada, retorna 0
    return 0, None

def clean_df(df):
    # drop fully empty columns
    df = df.loc[:, ~df.columns.str.contains("^Unnamed", na=False)]
    # remove columns that are all NaN
    df = df.dropna(axis=1, how="all")
    # strip names and uppercase
    df.columns = [str(c).strip().upper() for c in df.columns]
    # drop rows that are completely NaN
    df = df.dropna(axis=0, how="all")
    # reset index
    df = df.reset_index(drop=True)
    return df

def col_like(df, candidates):
    """Procura a primeira coluna cujo nome contém qualquer candidato (case-insensitive)."""
    if df is None:
        return None
    cols = list(df.columns)
    for cand in candidates:
        for c in cols:
            if cand.upper() in c.upper():
                return c
    return None

# --------------------------
# Leitura robusta das abas
# --------------------------
@st.cache_data
def load_sheet(path, sheet_name):
    header_idx, err = find_header_row(path, sheet_name)
    if err:
        return None, f"Erro lendo folha {sheet_name}: {err}"
    try:
        df = pd.read_excel(path, sheet_name=sheet_name, header=header_idx)
    except Exception as e:
        return None, f"Erro lendo folha {sheet_name}: {e}"
    df = clean_df(df)
    return df, None

EXCEL_PATH = "LOJA IMPORTADOS.xlsx"

with st.sidebar:
    st.markdown("### ⚙️ Controles")
    show_diag = st.button("🔍 Diagnóstico (mostrar colunas detectadas)")
    st.markdown("---")
    st.markdown("Arquivo: **LOJA IMPORTADOS.xlsx** (deve estar no mesmo diretório do app)")

# Carrega abas
estoque, err_e = load_sheet(EXCEL_PATH, "ESTOQUE")
vendas, err_v = load_sheet(EXCEL_PATH, "VENDAS")
compras, err_c = load_sheet(EXCEL_PATH, "COMPRAS")

# Mostrar erros de leitura (se houver)
if err_e:
    st.error(err_e)
if err_v:
    st.error(err_v)
if err_c:
    st.error(err_c)

# --------------------------
# Diagnóstico (opcional)
# --------------------------
if show_diag:
    st.markdown("## 🔍 Diagnóstico de colunas detectadas")
    def show_df_info(name, df):
        if df is None or df.shape[0] == 0:
            st.warning(f"{name}: dados vazios ou não carregados.")
            return
        st.write(f"**{name}** — {df.shape[0]} linhas × {df.shape[1]} colunas")
        st.write(list(df.columns))
        st.dataframe(df.head(6))
    show_df_info("ESTOQUE", estoque)
    show_df_info("VENDAS", vendas)
    show_df_info("COMPRAS", compras)

# --------------------------
# Detectar colunas usadas (vendas)
# --------------------------
# Possíveis nomes usados nas suas planilhas (vamos tentar várias opções)
v_col_valor_total = None
v_col_valor_unit = None
v_col_qtd = None
v_col_prod = None
v_col_data = None

if vendas is not None:
    v_col_prod = col_like(vendas, ["PRODUTO", "ITEM", "DESCRICAO"])
    v_col_data = col_like(vendas, ["DATA", "DT"])
    v_col_qtd = col_like(vendas, ["QUANTIDADE", "QTD", "QTDE"])
    # valor total pode ter 'VALOR TOTAL', 'TOTAL', 'VALOR', 'VALOR VENDA'
    v_col_valor_total = col_like(vendas, ["VALOR TOTAL", "VALOR_VENDA", "VALOR VENDA", "TOTAL", "VALOR"])
    v_col_valor_unit = col_like(vendas, ["VALOR UNIT", "VALOR UNITÁRIO", "VALOR UNITARIO", "PRECO UNITARIO", "VALOR_UNITARIO", "PREÇO"])

# Compras
c_col_valor_total = None
c_col_valor_unit = None
c_col_qtd = None
c_col_prod = None
c_col_data = None

if compras is not None:
    c_col_prod = col_like(compras, ["PRODUTO", "ITEM", "DESCRICAO"])
    c_col_data = col_like(compras, ["DATA", "DT"])
    c_col_qtd = col_like(compras, ["QUANTIDADE", "QTD", "QTDE"])
    c_col_valor_total = col_like(compras, ["CUSTO TOTAL", "VALOR TOTAL", "TOTAL", "CUSTO_TOTAL", "VALOR"])
    c_col_valor_unit = col_like(compras, ["CUSTO UNIT", "CUSTO UNITARIO", "CUSTO UNITÁRIO", "CUSTO", "CUSTO_UNITARIO"])

# Estoque
e_col_prod = None
e_col_qtd = None
e_col_custo_unit = None
if estoque is not None:
    e_col_prod = col_like(estoque, ["PRODUTO", "ITEM", "DESCRICAO"])
    e_col_qtd = col_like(estoque, ["EM ESTOQUE", "QUANTIDADE", "QTD", "QTDE"])
    e_col_custo_unit = col_like(estoque, ["MEDIA C", "CUSTO UNIT", "CUSTO", "CUSTO UNITARIO", "CUSTO UNITÁRIO", "MEDIA C. UNITARIO"])

# Mensagens de aviso para colunas não encontradas
missing_msgs = []
if vendas is None:
    missing_msgs.append("A aba VENDAS não foi carregada.")
else:
    if not v_col_prod: missing_msgs.append("VENDAS: coluna PRODUTO não encontrada.")
    if not (v_col_valor_total or v_col_valor_unit): missing_msgs.append("VENDAS: coluna de VALOR (valor total ou unitário) não encontrada.")
    if not v_col_qtd: missing_msgs.append("VENDAS: coluna QUANTIDADE não encontrada (usar QTD, QUANTIDADE, QTDE).")

if compras is None:
    missing_msgs.append("A aba COMPRAS não foi carregada.")
else:
    if not (c_col_valor_total or (c_col_valor_unit and c_col_qtd)): missing_msgs.append("COMPRAS: coluna de VALOR/CUSTO não encontrada.")
    if not c_col_prod: missing_msgs.append("COMPRAS: coluna PRODUTO não encontrada.")

if estoque is None:
    missing_msgs.append("A aba ESTOQUE não foi carregada.")
else:
    if not e_col_qtd: missing_msgs.append("ESTOQUE: coluna de QUANTIDADE não encontrada.")
    if not e_col_prod: missing_msgs.append("ESTOQUE: coluna PRODUTO não encontrada.")

if missing_msgs:
    with st.expander("⚠️ Avisos / Colunas faltando (clique para ver)"):
        for m in missing_msgs:
            st.warning(m)

# --------------------------
# Normalizações básicas
# --------------------------
# Converter colunas de data
def convert_dates(df, colname):
    try:
        df[colname] = pd.to_datetime(df[colname], errors="coerce")
    except:
        pass

if vendas is not None and v_col_data:
    convert_dates(vendas, v_col_data)
if compras is not None and c_col_data:
    convert_dates(compras, c_col_data)

# --------------------------
# Cálculo: Total Vendas
# --------------------------
total_vendas = 0.0
if vendas is not None:
    # tentar calcular por linha:
    # Prioridade: se existir valor unitário e quantidade -> soma((valor_unit - custo_unit)*qtd) se custo disponivel
    # Caso contrário: somar VALOR_TOTAL (se existir)
    try:
        # identificar col de custo unit (se existir) a partir de VENDAS ou ESTOQUE
        v_col_custo_unit = col_like(vendas, ["CUSTO UNIT", "CUSTO", "MEDIA C", "CUSTO_UNITARIO"])
        if not v_col_custo_unit:
            # fallback para coluna de custo no estoque, se houver correspondência por produto
            v_col_custo_unit = e_col_custo_unit

        # Se tiver coluna VALOR_UNIT e QTD
        if v_col_valor_unit and v_col_qtd and v_col_custo_unit:
            # lucro por linha: (valor_unit - custo_unit) * qtd
            vendas["__VAL_UNIT"] = pd.to_numeric(vendas[v_col_valor_unit], errors="coerce")
            vendas["__CUST_UNIT"] = pd.to_numeric(vendas[v_col_custo_unit], errors="coerce")
            vendas["__QTD"] = pd.to_numeric(vendas[v_col_qtd], errors="coerce").fillna(0)
            vendas["__LUCRO_LIN"] = (vendas["__VAL_UNIT"].fillna(0) - vendas["__CUST_UNIT"].fillna(0)) * vendas["__QTD"]
            total_vendas = vendas[v_col_valor_unit].astype(float).mul(vendas["__QTD"]).sum(skipna=True) if v_col_valor_unit else vendas.get("__LUCRO_LIN", pd.Series()).sum()
        elif v_col_valor_total:
            total_vendas = pd.to_numeric(vendas[v_col_valor_total], errors="coerce").sum(skipna=True)
        else:
            total_vendas = 0.0
    except Exception as e:
        st.error(f"Erro ao calcular total de vendas: {e}")
        total_vendas = 0.0

# --------------------------
# Cálculo: Total Compras (Custo)
# --------------------------
total_compras = 0.0
if compras is not None:
    try:
        if c_col_valor_total:
            total_compras = pd.to_numeric(compras[c_col_valor_total], errors="coerce").sum(skipna=True)
        elif c_col_valor_unit and c_col_qtd:
            total_compras = (pd.to_numeric(compras[c_col_valor_unit], errors="coerce") * pd.to_numeric(compras[c_col_qtd], errors="coerce").fillna(0)).sum(skipna=True)
        else:
            total_compras = 0.0
    except Exception as e:
        st.error(f"Erro ao calcular total de compras: {e}")
        total_compras = 0.0

# --------------------------
# Cálculo: Lucro estimado (recalcula)
# --------------------------
lucro_estimado = 0.0
try:
    # Se calculamos lucro por linha já, use somatório
    if "__LUCRO_LIN" in (vendas.columns if vendas is not None else []):
        lucro_estimado = vendas["__LUCRO_LIN"].sum(skipna=True)
    else:
        # fallback: total_vendas - total_compras
        lucro_estimado = (total_vendas - total_compras)
except Exception as e:
    st.error(f"Erro ao calcular lucro: {e}")
    lucro_estimado = total_vendas - total_compras

# --------------------------
# Cálculo: Estoque total (quantidade)
# --------------------------
qtde_estoque = 0
if estoque is not None and e_col_qtd:
    try:
        qtde_estoque = int(pd.to_numeric(estoque[e_col_qtd], errors="coerce").fillna(0).sum())
    except:
        qtde_estoque = 0

# --------------------------
# Exibir KPIs
# --------------------------
k1, k2, k3, k4 = st.columns(4)
k1.markdown(f"<div class='kpi-card'><h3 class='gold'>💰 Total de Vendas</h3><h2>{fmt_brl(total_vendas)}</h2></div>", unsafe_allow_html=True)
k2.markdown(f"<div class='kpi-card'><h3 class='gold'>🧾 Total de Compras</h3><h2>{fmt_brl(total_compras)}</h2></div>", unsafe_allow_html=True)
k3.markdown(f"<div class='kpi-card'><h3 class='gold'>📈 Lucro Estimado</h3><h2>{fmt_brl(lucro_estimado)}</h2></div>", unsafe_allow_html=True)
k4.markdown(f"<div class='kpi-card'><h3 class='gold'>📦 Qtde em Estoque</h3><h2>{qtde_estoque}</h2></div>", unsafe_allow_html=True)

st.markdown("---")

# --------------------------
# Gráficos (Plotly - tema escuro)
# --------------------------
px.defaults.template = "plotly_dark"
gold_seq = ["#E8C36A"]

# Vendas mensais
if vendas is not None and v_col_data and (v_col_valor_total or v_col_valor_unit):
    try:
        vendas["_DATA_MES"] = pd.to_datetime(vendas[v_col_data], errors="coerce").dt.to_period("M").astype(str)
        if v_col_valor_total:
            vendas_mensais = vendas.groupby("_DATA_MES")[v_col_valor_total].sum().reset_index()
            fig = px.bar(vendas_mensais, x="_DATA_MES", y=v_col_valor_total, title="📅 Evolução Mensal das Vendas",
                         color_discrete_sequence=gold_seq)
        elif v_col_valor_unit and v_col_qtd:
            vendas["_VAL_TOTAL_calc"] = pd.to_numeric(vendas[v_col_valor_unit], errors="coerce") * pd.to_numeric(vendas[v_col_qtd], errors="coerce").fillna(0)
            vendas_mensais = vendas.groupby("_DATA_MES")["_VAL_TOTAL_calc"].sum().reset_index()
            fig = px.bar(vendas_mensais, x="_DATA_MES", y="_VAL_TOTAL_calc", title="📅 Evolução Mensal das Vendas (calc)",
                         color_discrete_sequence=gold_seq)
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Erro ao gerar gráfico de vendas mensais: {e}")

# Top produtos vendidos
if vendas is not None and v_col_prod and (v_col_valor_total or (v_col_valor_unit and v_col_qtd)):
    try:
        if v_col_valor_total:
            top = vendas.groupby(v_col_prod)[v_col_valor_total].sum().nlargest(10).reset_index()
            fig2 = px.bar(top, x=v_col_valor_total, y=v_col_prod, orientation="h", title="🏆 Top 10 Produtos (Vendas)",
                          color_discrete_sequence=gold_seq)
        else:
            vendas["_VAL_TOTAL_calc"] = pd.to_numeric(vendas[v_col_valor_unit], errors="coerce") * pd.to_numeric(vendas[v_col_qtd], errors="coerce").fillna(0)
            top = vendas.groupby(v_col_prod)["_VAL_TOTAL_calc"].sum().nlargest(10).reset_index()
            fig2 = px.bar(top, x="_VAL_TOTAL_calc", y=v_col_prod, orientation="h", title="🏆 Top 10 Produtos (Vendas calculadas)",
                          color_discrete_sequence=gold_seq)
        st.plotly_chart(fig2, use_container_width=True)
    except Exception as e:
        st.error(f"Erro ao gerar top produtos: {e}")

# Compras mensais (custo)
if compras is not None and c_col_data and (c_col_valor_total or (c_col_valor_unit and c_col_qtd)):
    try:
        compras["_DATA_MES"] = pd.to_datetime(compras[c_col_data], errors="coerce").dt.to_period("M").astype(str)
        if c_col_valor_total:
            comp_m = compras.groupby("_DATA_MES")[c_col_valor_total].sum().reset_index()
            fig3 = px.line(comp_m, x="_DATA_MES", y=c_col_valor_total, title="📦 Evolução Mensal das Compras", markers=True, color_discrete_sequence=gold_seq)
        else:
            compras["_CUST_TOTAL_calc"] = pd.to_numeric(compras[c_col_valor_unit], errors="coerce") * pd.to_numeric(compras[c_col_qtd], errors="coerce").fillna(0)
            comp_m = compras.groupby("_DATA_MES")["_CUST_TOTAL_calc"].sum().reset_index()
            fig3 = px.line(comp_m, x="_DATA_MES", y="_CUST_TOTAL_calc", title="📦 Evolução Mensal das Compras (calc)", markers=True, color_discrete_sequence=gold_seq)
        st.plotly_chart(fig3, use_container_width=True)
    except Exception as e:
        st.error(f"Erro ao gerar gráfico de compras mensais: {e}")

# Estoque top
if estoque is not None and e_col_prod and e_col_qtd:
    try:
        top_e = estoque[[e_col_prod, e_col_qtd]].copy()
        top_e[e_col_qtd] = pd.to_numeric(top_e[e_col_qtd], errors="coerce").fillna(0)
        top_e = top_e.sort_values(e_col_qtd, ascending=False).head(15)
        fig4 = px.bar(top_e, x=e_col_prod, y=e_col_qtd, title="📊 Top 15 Itens em Estoque", color_discrete_sequence=gold_seq)
        st.plotly_chart(fig4, use_container_width=True)
    except Exception as e:
        st.error(f"Erro ao gerar gráfico de estoque: {e}")

# --------------------------
# Tabelas detalhadas e diagnóstico extra
# --------------------------
st.markdown("---")
with st.expander("📋 Visualizar Dados Detalhados (Vendas / Compras / Estoque)"):
    t1, t2, t3 = st.tabs(["🛒 Vendas", "📦 Compras", "🏷️ Estoque"])
    with t1:
        if vendas is not None:
            st.dataframe(vendas.head(500))
        else:
            st.info("Vendas não carregada.")
    with t2:
        if compras is not None:
            st.dataframe(compras.head(500))
        else:
            st.info("Compras não carregada.")
    with t3:
        if estoque is not None:
            st.dataframe(estoque.head(500))
        else:
            st.info("Estoque não carregado.")

st.markdown("---")
st.caption("© 2025 Loja Importados | Dashboard gerado com Streamlit + Plotly — tema: Dark (Preto + Dourado)")
