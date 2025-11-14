# app.py - Dashboard Loja Importados
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="Painel - Loja Importados", layout="wide")

# ===================================================
# LINK FIXO DA PLANILHA
# ===================================================
URL_PLANILHA = "https://drive.google.com/uc?export=download&id=1TsRjsfw1TVfeEWBBvhKvsGQ5YUCktn2b"

# ===================================================
# FUNÇÃO PARA CARREGAR PLANILHA
# ===================================================
def carregar_planilha(url):
    try:
        xls = pd.ExcelFile(url)
        return xls
    except Exception as e:
        st.error(f"Erro ao carregar planilha: {e}")
        st.stop()

xls = carregar_planilha(URL_PLANILHA)

# ignorar aba EXCELENTEJOAO
abas = [a for a in xls.sheet_names if a.upper() != "EXCELENTEJOAO"]
st.write("📄 Abas detectadas:", abas)

# ===================================================
# FUNÇÃO PARA LIMPAR ABA
# ===================================================
def limpar_aba(df, nome_aba):
    busca = "PRODUTO" if nome_aba not in ["VENDAS", "COMPRAS"] else "DATA"
    linha_cab = None
    for i in range(len(df)):
        linha = df.iloc[i].astype(str).str.upper().tolist()
        if busca in " ".join(linha):
            linha_cab = i
            break
    if linha_cab is None:
        st.error(f"⚠ Não encontrou cabeçalho da aba {nome_aba}")
        return None
    df.columns = df.iloc[linha_cab]
    df = df.iloc[linha_cab+1:]
    df = df.loc[:, ~df.columns.astype(str).str.contains("Unnamed")]
    df = df.reset_index(drop=True)
    return df

# ===================================================
# COLUNAS ESPERADAS
# ===================================================
colunas_esperadas = {
    "ESTOQUE": ["PRODUTO", "EM ESTOQUE", "COMPRAS", "Media C. UNITario", "Valor Venda Sugerido", "VENDAS"],
    "VENDAS": ["DATA", "PRODUTO", "QTD", "VALOR VENDA", "VALOR TOTAL", "MEDIA CUSTO UNITARIO", "LUCRO UNITARIO", "MAKEUP", "% DE LUCRO SOBRE CUSTO", "STATUS", "CLIENTE", "OBS"],
    "COMPRAS": ["DATA", "PRODUTO", "STATUS", "QUANTIDADE", "CUSTO UNITÁRIO", "CUSTO TOTAL"]
}

# ===================================================
# CARREGAR E LIMPAR ABAS
# ===================================================
dfs = {}
for aba in colunas_esperadas.keys():
    if aba not in abas:
        continue
    df = pd.read_excel(URL_PLANILHA, sheet_name=aba, header=None)
    limpo = limpar_aba(df, aba)
    if limpo is not None:
        dfs[aba] = limpo

# ===================================================
# CONVERSÃO DE MOEDA E NÚMEROS
# ===================================================
def converter_moeda(df, colunas):
    for c in colunas:
        if c in df.columns:
            df[c] = (
                df[c].astype(str)
                .str.replace("R$", "")
                .str.replace(".", "")
                .str.replace(",", ".", regex=False)
            )
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    return df

if "ESTOQUE" in dfs:
    dfs["ESTOQUE"] = converter_moeda(dfs["ESTOQUE"], ["Media C. UNITario", "Valor Venda Sugerido", "VENDAS", "EM ESTOQUE", "COMPRAS"])
if "VENDAS" in dfs:
    dfs["VENDAS"] = converter_moeda(dfs["VENDAS"], ["VALOR VENDA", "VALOR TOTAL", "MEDIA CUSTO UNITARIO", "LUCRO UNITARIO", "QTD"])
if "COMPRAS" in dfs:
    dfs["COMPRAS"] = converter_moeda(dfs["COMPRAS"], ["CUSTO UNITÁRIO", "CUSTO TOTAL", "QUANTIDADE"])

# ===================================================
# FILTRO POR MÊS
# ===================================================
if "VENDAS" in dfs:
    dfv = dfs["VENDAS"].copy()
    dfv["DATA"] = pd.to_datetime(dfv["DATA"], errors="coerce")
    meses = dfv["DATA"].dt.to_period("M").dropna().unique()
    mes_escolhido = st.selectbox("📅 Filtrar por mês", options=sorted(meses.astype(str)), index=len(meses)-1)
    dfv = dfv[dfv["DATA"].dt.to_period("M").astype(str) == mes_escolhido]
else:
    dfv = None

# ===================================================
# KPIs DO TOPO
# ===================================================
if dfv is not None:
    total_vendido = dfv["VALOR TOTAL"].sum()
    total_lucro = dfv["LUCRO UNITARIO"].sum()
    total_qtd = dfv["QTD"].sum()
else:
    total_vendido = total_lucro = total_qtd = 0

if "COMPRAS" in dfs:
    total_compras = dfs["COMPRAS"]["CUSTO TOTAL"].sum()
else:
    total_compras = 0

k1, k2, k3 = st.columns(3)
k1.metric("💵 Total Vendido", f"R$ {total_vendido:,.2f}")
k2.metric("🧾 Total Lucro", f"R$ {total_lucro:,.2f}")
k3.metric("💸 Total Compras", f"R$ {total_compras:,.2f}")

# ===================================================
# DASHBOARD TOP 10 VALOR
# ===================================================
st.subheader("🏆 Top 10 Produtos Mais Vendidos (por VALOR)")
if dfv is not None and not dfv.empty:
    top_val = dfv.groupby("PRODUTO")["VALOR TOTAL"].sum().reset_index().sort_values("VALOR TOTAL", ascending=False).head(10)
    top_val["VALOR_TOTAL_FMT"] = top_val["VALOR TOTAL"].map(lambda x: f"R$ {x:,.2f}")
    fig_val = px.bar(top_val, x="PRODUTO", y="VALOR TOTAL", text="VALOR_TOTAL_FMT")
    fig_val.update_traces(textposition="inside")
    st.plotly_chart(fig_val, use_container_width=True)
    st.dataframe(top_val.drop(columns=["VALOR_TOTAL_FMT"]).style.format({"VALOR TOTAL":"R$ {:,.2f}"}))

# ===================================================
# DASHBOARD TOP 10 QUANTIDADE
# ===================================================
st.subheader("🏆 Top 10 Produtos Mais Vendidos (por QUANTIDADE)")
if dfv is not None and not dfv.empty:
    top_qtd = dfv.groupby("PRODUTO")["QTD"].sum().reset_index().sort_values("QTD", ascending=False).head(10)
    top_qtd["QTD_TEXT"] = top_qtd["QTD"].astype(int).astype(str)
    fig_qtd = px.bar(top_qtd, x="PRODUTO", y="QTD", text="QTD_TEXT")
    fig_qtd.update_traces(textposition="inside")
    st.plotly_chart(fig_qtd, use_container_width=True)
    st.dataframe(top_qtd.drop(columns=["QTD_TEXT"]).style.format({"QTD":"{:,.0f}"}))

# ===================================================
# ABA DE ESTOQUE
# ===================================================
st.subheader("📦 Estoque Completo")
if "ESTOQUE" in dfs:
    dfest = dfs["ESTOQUE"].copy()
    st.dataframe(dfest.style.format({
        "Media C. UNITario": "R$ {:,.2f}",
        "Valor Venda Sugerido": "R$ {:,.2f}",
        "VENDAS": "{:,.0f}",
        "EM ESTOQUE": "{:,.0f}",
        "COMPRAS": "{:,.0f}"
    }), use_container_width=True)

st.success("✅ Dashboard carregado com sucesso!")
