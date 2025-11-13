import streamlit as st
import pandas as pd
import plotly.express as px
import re

# ==============================
# CONFIGURAÇÕES GERAIS
# ==============================
st.set_page_config(page_title="Dashboard Loja Importados", layout="wide")
st.markdown("""
    <style>
        body { background-color: #0e1117; color: #f1c40f; }
        [data-testid="stAppViewContainer"] { background-color: #0e1117; }
        [data-testid="stHeader"] { background: none; }
        .kpi-card {
            background-color: #1e1e1e; padding: 15px; border-radius: 10px;
            text-align: center; box-shadow: 0 0 8px #00000055;
        }
        .kpi-value { font-size: 26px; color: #f1c40f; font-weight: bold; }
        .kpi-label { font-size: 14px; color: #aaa; }
    </style>
""", unsafe_allow_html=True)

# ==============================
# LEITURA DE PLANILHA
# ==============================
@st.cache_data
def load_data():
    try:
        xls = pd.ExcelFile("LOJA IMPORTADOS.xlsx")

        def read_sheet(name):
            try:
                # Lê a planilha pulando até 2 cabeçalhos, tentando limpar “Unnamed”
                df = pd.read_excel(xls, sheet_name=name, header=None)
                df.columns = df.iloc[1].fillna("").astype(str)
                df = df.drop([0, 1], errors="ignore").reset_index(drop=True)
                df.columns = [re.sub(r"Unnamed.*", "", str(c)).strip().upper() for c in df.columns]
                df = df.loc[:, df.columns != ""]
                return df
            except Exception as e:
                st.warning(f"⚠️ Erro ao ler {name}: {e}")
                return pd.DataFrame()

        return read_sheet("ESTOQUE"), read_sheet("VENDAS"), read_sheet("COMPRAS")
    except Exception as e:
        st.error(f"❌ Falha ao carregar o arquivo: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

estoque, vendas, compras = load_data()

# ==============================
# FUNÇÕES DE AJUDA
# ==============================
def achar_coluna(df, *possiveis):
    """Tenta achar a coluna certa ignorando acentos e variações."""
    if df.empty:
        return None
    cols = [c.upper() for c in df.columns]
    for alvo in possiveis:
        for c in cols:
            if alvo in c:
                return c
    return None

def safe_num(df, col):
    if col and col in df.columns:
        return pd.to_numeric(df[col], errors="coerce").fillna(0)
    return pd.Series([0]*len(df))

# ==============================
# CÁLCULOS DE KPI
# ==============================
total_vendas = total_compras = lucro_estimado = qtd_estoque = 0

if not vendas.empty:
    col_qtd = achar_coluna(vendas, "QTD", "QUANT", "QUANTIDADE")
    col_valor_venda = achar_coluna(vendas, "VALOR VENDA", "PREÇO", "VALOR UNIT")
    col_custo = achar_coluna(vendas, "CUSTO", "MEDIA CUSTO", "CUSTO UNIT")

    if all([col_qtd, col_valor_venda, col_custo]):
        vendas["QTD"] = safe_num(vendas, col_qtd)
        vendas["VALOR_VENDA"] = safe_num(vendas, col_valor_venda)
        vendas["CUSTO"] = safe_num(vendas, col_custo)
        vendas["LUCRO_CALC"] = (vendas["VALOR_VENDA"] - vendas["CUSTO"]) * vendas["QTD"]

        total_vendas = (vendas["VALOR_VENDA"] * vendas["QTD"]).sum()
        lucro_estimado = vendas["LUCRO_CALC"].sum()
    else:
        st.warning("⚠️ Não foi possível identificar todas as colunas de vendas (QTD, VALOR VENDA, CUSTO).")

if not compras.empty:
    col_total = achar_coluna(compras, "VALOR TOTAL", "TOTAL", "COMPRA")
    if col_total:
        compras["VALOR_TOTAL"] = safe_num(compras, col_total)
        total_compras = compras["VALOR_TOTAL"].sum()

if not estoque.empty:
    col_qtd = achar_coluna(estoque, "QTD", "QUANT", "QUANTIDADE")
    if col_qtd:
        estoque["QTD"] = safe_num(estoque, col_qtd)
        qtd_estoque = estoque["QTD"].sum()

# ==============================
# KPIs
# ==============================
st.markdown("<h2 style='color:#f1c40f;text-align:center;'>📊 Painel Gerencial - Loja Importados</h2>", unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)
col1.markdown(f"<div class='kpi-card'><div class='kpi-value'>R$ {total_vendas:,.2f}</div><div class='kpi-label'>💰 Total de Vendas</div></div>", unsafe_allow_html=True)
col2.markdown(f"<div class='kpi-card'><div class='kpi-value'>R$ {total_compras:,.2f}</div><div class='kpi-label'>🧾 Total de Compras</div></div>", unsafe_allow_html=True)
col3.markdown(f"<div class='kpi-card'><div class='kpi-value'>R$ {lucro_estimado:,.2f}</div><div class='kpi-label'>📈 Lucro Estimado</div></div>", unsafe_allow_html=True)
col4.markdown(f"<div class='kpi-card'><div class='kpi-value'>{int(qtd_estoque):,}</div><div class='kpi-label'>📦 Qtde em Estoque</div></div>", unsafe_allow_html=True)

st.markdown("---")

# ==============================
# GRÁFICOS
# ==============================
aba = st.sidebar.radio("📂 Escolha uma aba", ["Vendas", "Compras", "Estoque", "Diagnóstico"])

if aba == "Vendas" and not vendas.empty:
    col_produto = achar_coluna(vendas, "PRODUTO", "ITEM")
    if col_produto and "VALOR_VENDA" in vendas.columns:
        graf = vendas.groupby(col_produto)["VALOR_VENDA"].sum().reset_index()
        fig = px.bar(graf, x=col_produto, y="VALOR_VENDA",
                     title="💵 Vendas por Produto", color="VALOR_VENDA",
                     color_continuous_scale="YlOrBr")
        fig.update_layout(template="plotly_dark", plot_bgcolor="#0e1117", paper_bgcolor="#0e1117", font_color="white")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("⚠️ Colunas necessárias para o gráfico de vendas não encontradas.")

elif aba == "Compras" and not compras.empty:
    col_produto = achar_coluna(compras, "PRODUTO", "ITEM")
    if col_produto and "VALOR_TOTAL" in compras.columns:
        graf = compras.groupby(col_produto)["VALOR_TOTAL"].sum().reset_index()
        fig = px.bar(graf, x=col_produto, y="VALOR_TOTAL",
                     title="🧾 Compras por Produto", color="VALOR_TOTAL",
                     color_continuous_scale="YlOrBr")
        fig.update_layout(template="plotly_dark", plot_bgcolor="#0e1117", paper_bgcolor="#0e1117", font_color="white")
        st.plotly_chart(fig, use_container_width=True)

elif aba == "Estoque" and not estoque.empty:
    col_produto = achar_coluna(estoque, "PRODUTO", "ITEM")
    if col_produto:
        fig = px.bar(estoque, x=col_produto, y="QTD",
                     title="📦 Estoque Atual", color="QTD",
                     color_continuous_scale="YlOrBr")
        fig.update_layout(template="plotly_dark", plot_bgcolor="#0e1117", paper_bgcolor="#0e1117", font_color="white")
        st.plotly_chart(fig, use_container_width=True)

elif aba == "Diagnóstico":
    st.subheader("🔍 Diagnóstico de Colunas Detectadas")
    st.write("**ESTOQUE:**", list(estoque.columns))
    st.write("**VENDAS:**", list(vendas.columns))
    st.write("**COMPRAS:**", list(compras.columns))
