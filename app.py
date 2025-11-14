import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
import re

st.set_page_config(page_title="Gestão de Estoque & Vendas", layout="wide")

st.title("📦 Painel Inteligente – Estoque & Vendas")

# ======================
# Função base: Carregar arquivo do Google Drive
# ======================
def carregar_excel_drive(url):
    try:
        file_id = re.findall(r"/d/(.*?)/", url)[0]
        download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
        df = pd.ExcelFile(download_url)
        return df
    except:
        st.error("❌ Erro ao carregar arquivo do Google Drive")
        return None


url = st.text_input("Cole a URL do Excel no Google Drive:")

if not url:
    st.stop()

excel_file = carregar_excel_drive(url)
if excel_file is None:
    st.stop()

# ======================
# Carregar abas
# ======================
try:
    estoque = pd.read_excel(excel_file, sheet_name="ESTOQUE")
    vendas = pd.read_excel(excel_file, sheet_name="VENDAS")
except:
    st.error("❌ Não consegui ler as abas ESTOQUE e VENDAS. Verifique os nomes.")
    st.stop()

# ======================
# PADRONIZAÇÃO DE COLUNAS (sem mudar nomes!)
# ======================
vendas.columns = vendas.columns.str.strip().str.upper()
estoque.columns = estoque.columns.str.strip().str.upper()

# ======================
# RELATÓRIO DE VENDAS
# ======================

st.header("📊 Relatório de Vendas")

colunas_esperadas = [
    "DATA", "PRODUTO", "QTD", "VALOR VENDA", "VALOR TOTAL",
    "MEDIA CUSTO UNITARIO", "LUCRO UNITARIO", "MAKEUP",
    "% DE LUCRO SOBRE CUSTO", "STATUS", "CLIENTE", "OBS"
]

missing = [c for c in colunas_esperadas if c not in vendas.columns]

if missing:
    st.error(f"❌ As colunas abaixo não existem na aba VENDAS:\n{missing}")
    st.stop()

# Conversões
vendas["DATA"] = pd.to_datetime(vendas["DATA"], errors="coerce")

# ==========================
# Visão geral
# ==========================
st.subheader("📘 Visão Geral das Últimas Vendas")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total vendido (R$)", f"{vendas['VALOR TOTAL'].sum():,.2f}")
col2.metric("Unidades vendidas", f"{vendas['QTD'].sum():,.0f}")
col3.metric("Lucro total (R$)", f"{(vendas['LUCRO UNITARIO'] * vendas['QTD']).sum():,.2f}")
col4.metric("Ticket médio (R$)", f"{vendas['VALOR TOTAL'].mean():,.2f}")

# ==========================
# GRÁFICO – Vendas por Produto
# ==========================
st.subheader("📦 Vendas por Produto")

graf_vendas = vendas.groupby("PRODUTO")["QTD"].sum().reset_index()

fig = px.bar(
    graf_vendas,
    x="PRODUTO",
    y="QTD",
    title="Total de Unidades Vendidas por Produto",
    color="QTD",
)

fig.update_traces(marker_color="purple")
st.plotly_chart(fig, use_container_width=True)

# ==========================
# Histórico
# ==========================
st.subheader("📅 Histórico de Vendas (Linha do Tempo)")

hist = vendas.groupby("DATA")["VALOR TOTAL"].sum().reset_index()

fig2 = px.line(
    hist,
    x="DATA",
    y="VALOR TOTAL",
    title="Histórico Diário de Vendas",
)
fig2.update_traces(line=dict(color="purple"))
st.plotly_chart(fig2, use_container_width=True)

# ==========================
# Mostrar tabela completa
# ==========================
st.subheader("📄 Tabela Completa de Vendas")
st.dataframe(vendas)

# ==========================
# ESTOQUE
# ==========================
st.header("📦 Estoque Atual")

st.dataframe(estoque)

# ==========================
# Fim do app
# ==========================
