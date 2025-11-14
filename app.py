import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from io import BytesIO

st.set_page_config(page_title="Dashboard Importados", layout="wide")

# =====================================================
# FUNÇÃO PARA CARREGAR ARQUIVO DO GOOGLE DRIVE
# =====================================================

URL_DRIVE = "https://drive.google.com/uc?export=download&id=1TsRjsfw1TVfeEWBBvhKvsGQ5YUCktn2b"

@st.cache_data
def load_excel_from_drive():
    try:
        resp = requests.get(URL_DRIVE)
        resp.raise_for_status()
        file_bytes = BytesIO(resp.content)
        return pd.read_excel(file_bytes, sheet_name=None)
    except Exception as e:
        st.error("❌ Erro ao carregar arquivo do Google Drive.")
        st.stop()

sheets = load_excel_from_drive()

# =====================================================
# VERIFICAÇÃO DAS ABAS REAIS
# =====================================================
valid_tabs = list(sheets.keys())

aba_estoque = next((k for k in valid_tabs if "ESTOQUE" in k.upper()), None)
aba_vendas  = next((k for k in valid_tabs if "VENDAS" in k.upper()), None)
aba_compras = next((k for k in valid_tabs if "COMPRAS" in k.upper()), None)

if not aba_estoque or not aba_vendas or not aba_compras:
    st.error("❌ As abas ESTOQUE, VENDAS e COMPRAS precisam existir no arquivo!")
    st.write("Abas encontradas:", valid_tabs)
    st.stop()

estoque = sheets[aba_estoque].copy()
vendas  = sheets[aba_vendas].copy()
compras = sheets[aba_compras].copy()

# =====================================================
# NORMALIZAÇÕES — GARANTE QUE AS COLUNAS EXISTEM
# =====================================================

# --- VENDAS REAL ---
expected_cols = [
    "DATA", "PRODUTO", "QTD", "VALOR VENDA", "VALOR TOTAL",
    "MEDIA CUSTO UNITARIO", "LUCRO UNITARIO", "MAKEUP",
    "% DE LUCRO SOBRE CUSTO", "STATUS", "CLIENTE", "OBS."
]

for col in expected_cols:
    if col not in vendas.columns:
        vendas[col] = None

# Criar coluna período yyyy-mm
vendas["_PERIODO"] = pd.to_datetime(vendas["DATA"], errors="coerce").dt.to_period("M").astype(str)

# Garantir QTD como número
vendas["QTD"] = pd.to_numeric(vendas["QTD"], errors="coerce").fillna(0).astype(int)

# =====================================================
# SIDEBAR
# =====================================================
st.sidebar.title("Filtros")

todos_periodos = sorted(vendas["_PERIODO"].unique())
periodo_select = st.sidebar.selectbox("Período", ["Geral"] + todos_periodos)

if periodo_select != "Geral":
    vendas_filtrado = vendas[vendas["_PERIODO"] == periodo_select]
else:
    vendas_filtrado = vendas.copy()

# =====================================================
# DASH PRINCIPAL
# =====================================================

st.title("📊 Dashboard — Loja de Importados")

st.subheader("📦 Visão Geral do Estoque")
col1, col2 = st.columns(2)

with col1:
    st.metric("Total de Produtos no Estoque", len(estoque))

with col2:
    soma_estoque = 0
    # Tenta pegar qualquer coluna de quantidade válida
    for col in estoque.columns:
        if "QTD" in col.upper() or "QUANT" in col.upper():
            soma_estoque = estoque[col].fillna(0).sum()
            break
    st.metric("Quantidade Total", int(soma_estoque))

# =====================================================
# RESUMO DE VENDAS
# =====================================================

st.subheader("💸 Resumo das Vendas")

colA, colB, colC = st.columns(3)

total_qtd = vendas_filtrado["QTD"].sum()
total_valor = vendas_filtrado["VALOR TOTAL"].fillna(0).sum()
ticket_medio = total_valor / total_qtd if total_qtd > 0 else 0

with colA:
    st.metric("Itens vendidos", int(total_qtd))

with colB:
    st.metric("Faturamento (R$)", f"{total_valor:,.2f}".replace(",", "."))

with colC:
    st.metric("Ticket Médio", f"{ticket_medio:,.2f}".replace(",", "."))

# =====================================================
# GRÁFICO DE PRODUTOS MAIS VENDIDOS — Roxo
# =====================================================

st.subheader("🏆 Produtos Mais Vendidos")

top = vendas_filtrado.groupby("PRODUTO")["QTD"].sum().reset_index().sort_values("QTD", ascending=False)

fig = px.bar(top, x="PRODUTO", y="QTD", title="Ranking de Vendas", color_discrete_sequence=["purple"])
st.plotly_chart(fig, use_container_width=True)

# =====================================================
# RELATÓRIO DE VENDAS
# =====================================================

st.subheader("📑 Relatório de Vendas (Completo)")

st.dataframe(vendas_filtrado[expected_cols], use_container_width=True)

# =====================================================
# LISTA DE COMPRAS
# =====================================================

st.subheader("🧾 Compras Recentes")
st.dataframe(compras, use_container_width=True)
