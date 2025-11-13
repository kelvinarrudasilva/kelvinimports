import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# ==============================
# CONFIGURAÇÃO DA PÁGINA
# ==============================
st.set_page_config(
    page_title="Dashboard - Loja Importados",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📊 Dashboard de Desempenho - Loja Importados")
st.markdown("Análise de Estoque, Vendas e Compras em tempo real")

# ==============================
# CARREGAMENTO DOS DADOS
# ==============================
@st.cache_data
def load_data():
    xls = pd.ExcelFile("LOJA IMPORTADOS.xlsx")
    estoque = pd.read_excel(xls, "Tabela1")
    vendas = pd.read_excel(xls, "Tabela2")
    compras = pd.read_excel(xls, "Tabela3")
    return estoque, vendas, compras

estoque, vendas, compras = load_data()

# Normaliza nomes das colunas
vendas.columns = [c.strip().upper() for c in vendas.columns]
compras.columns = [c.strip().upper() for c in compras.columns]
estoque.columns = [c.strip().upper() for c in estoque.columns]

# ==============================
# TRATAMENTO DE DATAS
# ==============================
for df in [vendas, compras]:
    for col in df.columns:
        if "DATA" in col.upper():
            df[col] = pd.to_datetime(df[col], errors="coerce")

# ==============================
# KPIs PRINCIPAIS
# ==============================
total_vendas = vendas["VALOR TOTAL"].sum() if "VALOR TOTAL" in vendas.columns else 0
total_compras = compras["VALOR TOTAL"].sum() if "VALOR TOTAL" in compras.columns else 0
lucro_estimado = total_vendas - total_compras
itens_estoque = estoque["PRODUTO"].nunique() if "PRODUTO" in estoque.columns else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("💰 Total de Vendas", f"R$ {total_vendas:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
col2.metric("🧾 Total de Compras", f"R$ {total_compras:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
col3.metric("📈 Lucro Estimado", f"R$ {lucro_estimado:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
col4.metric("📦 Produtos em Estoque", itens_estoque)

st.markdown("---")

# ==============================
# GRÁFICOS DE VENDAS
# ==============================
if "DATA" in vendas.columns:
    vendas["MÊS"] = vendas["DATA"].dt.to_period("M").astype(str)

    vendas_mensais = vendas.groupby("MÊS")["VALOR TOTAL"].sum().reset_index()
    fig_vendas = px.bar(
        vendas_mensais,
        x="MÊS",
        y="VALOR TOTAL",
        title="📅 Evolução Mensal das Vendas",
        text_auto=True,
        color="VALOR TOTAL",
        color_continuous_scale="tealgrn"
    )
    st.plotly_chart(fig_vendas, use_container_width=True)

# ==============================
# PRODUTOS MAIS VENDIDOS
# ==============================
if "PRODUTO" in vendas.columns:
    top_produtos = vendas.groupby("PRODUTO")["VALOR TOTAL"].sum().nlargest(10).reset_index()
    fig_produtos = px.bar(
        top_produtos,
        x="VALOR TOTAL",
        y="PRODUTO",
        orientation="h",
        title="🏆 Top 10 Produtos Mais Vendidos",
        text_auto=True,
        color="VALOR TOTAL",
        color_continuous_scale="bluered"
    )
    st.plotly_chart(fig_produtos, use_container_width=True)

# ==============================
# EVOLUÇÃO DAS COMPRAS
# ==============================
if "DATA" in compras.columns:
    compras["MÊS"] = compras["DATA"].dt.to_period("M").astype(str)
    compras_mensais = compras.groupby("MÊS")["VALOR TOTAL"].sum().reset_index()
    fig_compras = px.line(
        compras_mensais,
        x="MÊS",
        y="VALOR TOTAL",
        title="📦 Evolução Mensal das Compras",
        markers=True
    )
    st.plotly_chart(fig_compras, use_container_width=True)

# ==============================
# ESTOQUE ATUAL
# ==============================
if "QUANTIDADE" in estoque.columns:
    fig_estoque = px.bar(
        estoque.sort_values("QUANTIDADE", ascending=False).head(15),
        x="PRODUTO",
        y="QUANTIDADE",
        title="📊 Top 15 Itens em Estoque",
        color="QUANTIDADE",
        color_continuous_scale="viridis"
    )
    st.plotly_chart(fig_estoque, use_container_width=True)

# ==============================
# TABELAS DETALHADAS
# ==============================
with st.expander("📋 Visualizar Dados Detalhados"):
    tab1, tab2, tab3 = st.tabs(["🛒 Vendas", "📦 Compras", "🏷️ Estoque"])
    tab1.dataframe(vendas)
    tab2.dataframe(compras)
    tab3.dataframe(estoque)

st.markdown("---")
st.caption("© 2025 Loja Importados | Dashboard gerado em Python + Streamlit + Plotly")
