import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")

# ============================================
# URL DA SUA PLANILHA GOOGLE
# ============================================

URL = "https://docs.google.com/spreadsheets/d/1TsRjsfw1TVfeEWBBvhKvsGQ5YUCktn2b/export?format=xlsx"

@st.cache_data
def carregar():
    xls = pd.ExcelFile(URL)

    compras = pd.read_excel(xls, "COMPRAS")
    vendas = pd.read_excel(xls, "VENDAS")

    return compras, vendas


# ============================================
# FIFO REAL
# ============================================

def calcular_fifo(compras, vendas):

    compras = compras.copy()
    vendas = vendas.copy()

    compras["DATA"] = pd.to_datetime(compras["DATA"], errors="coerce", dayfirst=True)
    vendas["DATA"] = pd.to_datetime(vendas["DATA"], errors="coerce", dayfirst=True)

    compras = compras.sort_values("DATA")
    vendas = vendas.sort_values("DATA")

    estoque = {}

    for _, row in compras.iterrows():

        produto = row["PRODUTO"]
        qtd = row["QUANTIDADE"]
        custo_unit = row["CUSTO TOTAL"] / row["QUANTIDADE"]

        if produto not in estoque:
            estoque[produto] = []

        estoque[produto].append({
            "qtd": qtd,
            "custo": custo_unit
        })

    resultado = []

    for _, venda in vendas.iterrows():

        produto = venda["PRODUTO"]
        qtd_venda = venda["QTD"]

        custo_total = 0

        if produto not in estoque:
            continue

        while qtd_venda > 0 and estoque[produto]:

            lote = estoque[produto][0]

            if lote["qtd"] <= qtd_venda:

                custo_total += lote["qtd"] * lote["custo"]
                qtd_venda -= lote["qtd"]
                estoque[produto].pop(0)

            else:

                custo_total += qtd_venda * lote["custo"]
                lote["qtd"] -= qtd_venda
                qtd_venda = 0

        resultado.append({
            "DATA": venda["DATA"],
            "PRODUTO": produto,
            "QTD": venda["QTD"],
            "VALOR": venda["VALOR"],
            "CUSTO": custo_total,
            "LUCRO": venda["VALOR"] - custo_total
        })

    return pd.DataFrame(resultado)


# ============================================
# CARREGAR
# ============================================

compras, vendas = carregar()

fifo = calcular_fifo(compras, vendas)


# ============================================
# DASHBOARD
# ============================================

st.title("📦 Dashboard FIFO")

col1, col2, col3 = st.columns(3)

total_vendido = fifo["VALOR"].sum()
total_custo = fifo["CUSTO"].sum()
total_lucro = fifo["LUCRO"].sum()

col1.metric("💰 Total vendido", f"R$ {total_vendido:,.2f}")
col2.metric("📉 Custo total", f"R$ {total_custo:,.2f}")
col3.metric("📈 Lucro total", f"R$ {total_lucro:,.2f}")


# ============================================
# POR PRODUTO
# ============================================

st.subheader("Lucro por produto")

por_produto = (
    fifo.groupby("PRODUTO")
    .agg({
        "QTD": "sum",
        "VALOR": "sum",
        "CUSTO": "sum",
        "LUCRO": "sum"
    })
    .reset_index()
)

st.dataframe(por_produto, use_container_width=True)


# ============================================
# VENDAS DETALHADAS
# ============================================

st.subheader("Vendas detalhadas")

st.dataframe(fifo, use_container_width=True)
