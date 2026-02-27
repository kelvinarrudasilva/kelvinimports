import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")

# ============================================
# SUA PLANILHA (já configurada)
# ============================================

URL_PLANILHA = "https://docs.google.com/spreadsheets/d/1TsRjsfw1TVfeEWBBvhKvsGQ5YUCktn2b/export?format=xlsx"


# ============================================
# CARREGAR PLANILHA
# ============================================

@st.cache_data
def carregar_planilha():

    xls = pd.ExcelFile(URL_PLANILHA)

    compras = pd.read_excel(xls, "COMPRAS")
    vendas = pd.read_excel(xls, "VENDAS")

    compras.columns = compras.columns.str.strip().str.upper()
    vendas.columns = vendas.columns.str.strip().str.upper()

    return compras, vendas


# ============================================
# DETECTAR COLUNAS
# ============================================

def detectar(df, nome):

    for col in df.columns:
        if nome in col:
            return col
    return None


# ============================================
# FIFO REAL
# ============================================

def calcular_fifo(compras, vendas):

    col_data_c = detectar(compras, "DATA")
    col_prod_c = detectar(compras, "PRODUTO")
    col_qtd_c = detectar(compras, "QUANT")
    col_custo = detectar(compras, "CUSTO")

    col_data_v = detectar(vendas, "DATA")
    col_prod_v = detectar(vendas, "PRODUTO")
    col_qtd_v = detectar(vendas, "QTD")
    col_valor_v = detectar(vendas, "VALOR")

    if col_data_c:
        compras[col_data_c] = pd.to_datetime(compras[col_data_c], dayfirst=True, errors="coerce")
        compras = compras.sort_values(col_data_c)

    if col_data_v:
        vendas[col_data_v] = pd.to_datetime(vendas[col_data_v], dayfirst=True, errors="coerce")
        vendas = vendas.sort_values(col_data_v)

    estoque = {}

    # construir estoque
    for _, row in compras.iterrows():

        produto = row[col_prod_c]
        qtd = float(row[col_qtd_c])
        custo_unit = float(row[col_custo]) / qtd

        if produto not in estoque:
            estoque[produto] = []

        estoque[produto].append({
            "qtd": qtd,
            "custo": custo_unit
        })

    resultado = []

    # processar vendas
    for _, row in vendas.iterrows():

        produto = row[col_prod_v]
        qtd_venda = float(row[col_qtd_v])
        valor = float(row[col_valor_v])

        restante = qtd_venda
        custo_total = 0

        if produto in estoque:

            while restante > 0 and estoque[produto]:

                lote = estoque[produto][0]

                if lote["qtd"] <= restante:

                    custo_total += lote["qtd"] * lote["custo"]
                    restante -= lote["qtd"]
                    estoque[produto].pop(0)

                else:

                    custo_total += restante * lote["custo"]
                    lote["qtd"] -= restante
                    restante = 0

        resultado.append({
            "DATA": row[col_data_v] if col_data_v else None,
            "PRODUTO": produto,
            "QTD": qtd_venda,
            "VALOR": valor,
            "CUSTO": custo_total,
            "LUCRO": valor - custo_total
        })

    return pd.DataFrame(resultado)


# ============================================
# EXECUÇÃO
# ============================================

compras, vendas = carregar_planilha()

fifo = calcular_fifo(compras, vendas)


# ============================================
# DASHBOARD
# ============================================

st.title("📦 Controle Financeiro FIFO")

total_vendido = fifo["VALOR"].sum()
total_custo = fifo["CUSTO"].sum()
total_lucro = fifo["LUCRO"].sum()

c1, c2, c3 = st.columns(3)

c1.metric("Total vendido", f"R$ {total_vendido:,.2f}")
c2.metric("Custo total", f"R$ {total_custo:,.2f}")
c3.metric("Lucro total", f"R$ {total_lucro:,.2f}")


# ============================================
# POR PRODUTO
# ============================================

st.subheader("Resultado por produto")

resumo = fifo.groupby("PRODUTO").agg(
    QTD=("QTD", "sum"),
    RECEITA=("VALOR", "sum"),
    CUSTO=("CUSTO", "sum"),
    LUCRO=("LUCRO", "sum")
).reset_index()

st.dataframe(resumo, use_container_width=True)


# ============================================
# DETALHADO
# ============================================

st.subheader("Vendas detalhadas")

st.dataframe(fifo, use_container_width=True)
