# app.py final — Dashboard Loja Importados
import streamlit as st
import pandas as pd
import plotly.express as px
import re
from io import BytesIO

# =============================================================================
# CONFIG VISUAL
# =============================================================================
st.set_page_config(page_title="Painel - Loja Importados", layout="wide")

st.markdown(
    """
    <style>
      :root { --gold:#FFD700; }
      body, .stApp { background-color:#111 !important; color:white !important; }
      h1, h2, h3, h4 { color: var(--gold) !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

# =============================================================================
# 🔥 CARREGAR PLANILHA GOOGLE (CORRIGIDO)
# =============================================================================
def carregar_planilha(link):
    try:
        # Converter link Google Sheets para CSV direto
        if "edit" in link:
            link = link.replace("/edit", "/export?format=csv")
        elif "view" in link:
            link = link.replace("/view", "/export?format=csv")

        # ----- 1ª tentativa UTF-8
        try:
            return pd.read_csv(link, encoding="utf-8", sep=",")
        except:
            pass

        # ----- 2ª tentativa Latin-1
        try:
            return pd.read_csv(link, encoding="latin1", sep=",")
        except:
            pass

        # ----- 3ª tentativa: separador automático
        try:
            return pd.read_csv(link, sep=None, engine="python")
        except:
            pass

        st.error("❌ Não foi possível carregar o arquivo. Verifique o link.")
        return None

    except Exception as e:
        st.error(f"Erro ao carregar planilha: {e}")
        return None

# =============================================================================
# PADRONIZAR COLUNAS
# =============================================================================
def padrao(col):
    col = col.strip()
    col = re.sub(r"\s+", " ", col)
    return col.upper()

# =============================================================================
# CORRIGIR NOME DAS COLUNAS
# =============================================================================
def corrigir_colunas(df, esperadas):
    df_corr = df.copy()
    df_corr.columns = [padrao(c) for c in df_corr.columns]

    esperadas_up = [padrao(c) for c in esperadas]

    mapa = {}
    for col in df_corr.columns:
        melhor = None
        score_melhor = 0

        for esp in esperadas_up:
            iguais = sum(1 for a, b in zip(col, esp) if a == b)
            score = iguais / max(len(col), len(esp))
            if score > score_melhor:
                score_melhor = score
                melhor = esp

        if melhor:
            mapa[col] = melhor

    df_corr.rename(columns=mapa, inplace=True)

    faltando = [c for c in esperadas_up if c not in df_corr.columns]
    extras = [c for c in df_corr.columns if c not in esperadas_up]

    return df_corr, faltando, extras

# =============================================================================
# INTERFACE — LINK FIXO
# =============================================================================
st.title("📊 Dashboard Geral – Gestão Loja Importados")

# 👉 link fixo do Google Sheets
link = st.text_input("Cole o link da planilha ou use o padrão:", 
                     "https://docs.google.com/spreadsheets/d/1TsRjsfw1TVfeEWBBvhKvsGQ5YUCktn2b/edit?usp=sharing")

df = carregar_planilha(link)
if df is None:
    st.stop()

# =============================================================================
# COLUNAS ESPERADAS
# =============================================================================
colunas_estoque = [
    "PRODUTO", "EM ESTOQUE", "COMPRAS",
    "MEDIA C. UNITARIO", "VALOR VENDA SUGERIDO", "VENDAS"
]

colunas_vendas = [
    "DATA", "PRODUTO", "QTD", "VALOR VENDA", "VALOR TOTAL",
    "MEDIA CUSTO UNITARIO", "LUCRO UNITARIO", "MAKEUP",
    "% DE LUCRO SOBRE CUSTO", "STATUS", "CLIENTE", "OBS"
]

# Detectar tipo automaticamente
if "EM ESTOQUE" in df.columns or "ESTOQUE" in df.columns:
    tipo = "ESTOQUE"
    esperadas = colunas_estoque
else:
    tipo = "VENDAS"
    esperadas = colunas_vendas

st.subheader(f"Aba detectada: **{tipo}**")

df_corr, faltando, extras = corrigir_colunas(df, esperadas)

if faltando:
    st.warning("⚠️ Colunas faltando: " + str(faltando))
if extras:
    st.info("ℹ️ Colunas extras detectadas: " + str(extras))

st.success("✔️ Colunas ajustadas automaticamente!")
st.dataframe(df_corr, use_container_width=True)

# Garantir conversões numéricas
for c in df_corr.columns:
    try:
        df_corr[c] = pd.to_numeric(df_corr[c], errors="ignore")
    except:
        pass

# =============================================================================
# DASHBOARD
# =============================================================================
st.header("📈 Dashboard Analítico")

# ----- ESTOQUE -----
if tipo == "ESTOQUE":
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("📦 Total em Estoque", df_corr["EM ESTOQUE"].sum())

    with col2:
        st.metric("🛒 Total Vendido", df_corr["VENDAS"].sum())

    with col3:
        st.metric("💰 Preço Médio Sugerido",
                  f"R$ {df_corr['VALOR VENDA SUGERIDO'].mean():,.2f}")

    fig = px.bar(
        df_corr.sort_values("VENDAS", ascending=False).head(15),
        x="PRODUTO", y="VENDAS",
        title="TOP 15 Produtos Mais Vendidos"
    )
    st.plotly_chart(fig, use_container_width=True)

# ----- VENDAS -----
else:
    df_corr["DATA"] = pd.to_datetime(df_corr["DATA"], errors="coerce")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("💵 Faturamento Total",
                  f"R$ {df_corr['VALOR TOTAL'].sum():,.2f}")

    with col2:
        st.metric("💰 Lucro Total",
                  f"R$ {df_corr['LUCRO UNITARIO'].sum():,.2f}")

    with col3:
        st.metric("🛒 Quantidade Vendida",
                  int(df_corr["QTD"].sum()))

    fig = px.line(
        df_corr.groupby("DATA")["VALOR TOTAL"].sum().reset_index(),
        x="DATA", y="VALOR TOTAL",
        title="Faturamento Diário"
    )
    st.plotly_chart(fig, use_container_width=True)

    fig2 = px.bar(
        df_corr.groupby("PRODUTO")["QTD"].sum().reset_index().sort_values("QTD", ascending=False).head(20),
        x="PRODUTO", y="QTD",
        title="TOP 20 Produtos Vendidos"
    )
    st.plotly_chart(fig2, use_container_width=True)

st.success("✅ Dashboard carregado com sucesso!")

