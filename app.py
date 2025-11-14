# ============================================================
# app.py – Versão FINAL (automático pelo Google Drive)
# ============================================================

import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

# ============================================================
# CONFIGURAÇÃO VISUAL
# ============================================================
st.set_page_config(page_title="Dashboard Loja Importados", layout="wide")

st.markdown("""
<style>
    :root { --gold:#FFD700; }
    body, .stApp { background-color: #000; color: white; }
    h1, h2, h3, h4, h5 { color: var(--gold); }
    .stMetric { background:#111; padding:20px; border-radius:12px; border:1px solid var(--gold); }
</style>
""", unsafe_allow_html=True)

# ============================================================
# LINK FIXO DO GOOGLE DRIVE
# ============================================================
URL = "https://drive.google.com/uc?export=download&id=1TsRjsfw1TVfeEWBBvhKvsGQ5YUCktn2b"

# ============================================================
# CARREGAR PLANILHA
# ============================================================
st.title("📊 Dashboard – Loja Importados")

try:
    xls = pd.ExcelFile(URL)
except Exception as e:
    st.error("Erro ao carregar planilha do Google Drive.")
    st.code(str(e))
    st.stop()

abas = xls.sheet_names

# ============================================================
# FUNÇÃO DE LIMPEZA E PADRONIZAÇÃO
# ============================================================
def limpar(df):
    df.columns = [str(c).strip() for c in df.columns]
    df = df.loc[:, ~df.columns.str.contains("Unnamed")]
    df = df.dropna(how="all")
    return df.reset_index(drop=True)

# ============================================================
# LER E PROCESSAR CADA ABA
# ============================================================
def carregar_aba(nome):
    try:
        df = pd.read_excel(URL, sheet_name=nome, header=0)
        return limpar(df)
    except:
        st.error(f"Erro ao carregar a aba {nome}")
        return pd.DataFrame()

# ----- Carregar abas -----
estoque_df = carregar_aba("ESTOQUE")
vendas_df  = carregar_aba("VENDAS")
compras_df = carregar_aba("COMPRAS")

# ============================================================
# CONVERTER VALORES MONETÁRIOS
# ============================================================
def conv(df, col):
    if col in df.columns:
        df[col] = (
            df[col]
            .astype(str)
            .str.replace("R$", "", regex=False)
            .str.replace(".", "", regex=False)
            .str.replace(",", ".", regex=False)
        )
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df

# ESTOQUE
for c in ["Media C. UNITARIO", "Valor Venda Sugerido"]:
    estoque_df = conv(estoque_df, c)

# VENDAS
for c in ["VALOR VENDA", "VALOR TOTAL", "MEDIA CUSTO UNITARIO", "LUCRO UNITARIO"]:
    vendas_df = conv(vendas_df, c)

# COMPRAS
for c in ["CUSTO UNITÁRIO", "CUSTO TOTAL"]:
    compras_df = conv(compras_df, c)

# ============================================================
# KPIs
# ============================================================
st.header("📌 Indicadores Gerais")

col1, col2, col3 = st.columns(3)

try:
    col1.metric("Total em Estoque", f"{estoque_df['EM ESTOQUE'].sum():,.0f}")
except:
    col1.metric("Total em Estoque", "Erro")

try:
    col2.metric("Faturamento Total", f"R$ {vendas_df['VALOR TOTAL'].sum():,.2f}")
except:
    col2.metric("Faturamento Total", "Erro")

try:
    col3.metric("Lucro Total", f"R$ {vendas_df['LUCRO UNITARIO'].sum():,.2f}")
except:
    col3.metric("Lucro Total", "Erro")

# ============================================================
# GRÁFICOS
# ============================================================

# -------- VENDAS POR PRODUTO --------
st.subheader("📦 Vendas por Produto")

try:
    vendas_produto = vendas_df.groupby("PRODUTO")["VALOR TOTAL"].sum().reset_index()
    fig1 = px.bar(vendas_produto, x="PRODUTO", y="VALOR TOTAL", title="Vendas por Produto")
    st.plotly_chart(fig1, use_container_width=True)
except:
    st.error("Erro ao gerar gráfico de vendas por produto.")

# -------- TOP 10 MAIS VENDIDOS --------
st.subheader("🔥 Top 10 Produtos Mais Vendidos")

try:
    qtd = vendas_df.groupby("PRODUTO")["QTD"].sum().reset_index()
    top = qtd.sort_values("QTD", ascending=False).head(10)
    fig2 = px.bar(top, x="PRODUTO", y="QTD", title="Top 10 Mais Vendidos")
    st.plotly_chart(fig2, use_container_width=True)
except:
    st.error("Erro ao gerar ranking de vendas.")

# -------- EVOLUÇÃO DO FATURAMENTO --------
st.subheader("📈 Evolução do Faturamento")

try:
    vendas_df["DATA"] = pd.to_datetime(vendas_df["DATA"], errors="coerce")
    fat = vendas_df.groupby("DATA")["VALOR TOTAL"].sum().reset_index()
    fig3 = px.line(fat, x="DATA", y="VALOR TOTAL", title="Faturamento ao Longo do Tempo")
    st.plotly_chart(fig3, use_container_width=True)
except:
    st.error("Erro ao gerar gráfico de faturamento.")

# ============================================================
# MOSTRAR ABAS
# ============================================================
st.header("📄 Dados Brutos")

aba_mostrar = st.selectbox("Ver aba:", ["ESTOQUE", "VENDAS", "COMPRAS"])

if aba_mostrar == "ESTOQUE":
    st.dataframe(estoque_df)
elif aba_mostrar == "VENDAS":
    st.dataframe(vendas_df)
else:
    st.dataframe(compras_df)

# ============================================================
# FIM
# ============================================================
st.success("Dashboard carregado com sucesso!")
