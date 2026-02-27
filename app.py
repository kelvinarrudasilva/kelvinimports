import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")

# ============================================
# CONFIG
# ============================================

URL_PLANILHA = "https://docs.google.com/spreadsheets/d/1TsRjsfw1TVfeEWBBvhKvsGQ5YUCktn2b/export?format=xlsx"

# ============================================
# FUNÇÕES
# ============================================

@st.cache_data
def carregar_planilha(url):

    xls = pd.ExcelFile(url)

    compras = pd.read_excel(xls, "COMPRAS")
    vendas = pd.read_excel(xls, "VENDAS")

    # normalizar nomes
    compras.columns = compras.columns.str.strip().str.upper()
    vendas.columns = vendas.columns.str.strip().str.upper()

    return compras, vendas


def detectar_coluna(df, nome):

    for col in df.columns:
        if nome in col:
            return col

    return None


def preparar_dados(compras, vendas):

    col_data_compra = detectar_coluna(compras, "DATA")
    col_produto_compra = detectar_coluna(compras, "PRODUTO")
    col_qtd_compra = detectar_coluna(compras, "QUANT")
    col_custo_total = detectar_coluna(compras, "CUSTO")

    col_data_venda = detectar_coluna(vendas, "DATA")
    col_produto_venda = detectar_coluna(vendas, "PRODUTO")
    col_qtd_venda = detectar_coluna(vendas, "QTD")
    col_valor_venda = detectar_coluna(vendas, "VALOR")

    if col_data_compra:
        compras[col_data_compra] = pd.to_datetime(
            compras[col_data_compra],
            errors="coerce",
            dayfirst=True
        )
        compras = compras.sort_values(col_data_compra)

    if col_data_venda:
        vendas[col_data_venda] = pd.to_datetime(
            vendas[col_data_venda],
            errors="coerce",
            dayfirst=True
        )
        vendas = vendas.sort_values(col_data_venda)

    return {
        "compras": compras,
        "vendas": vendas,
        "col_data_compra": col_data_compra,
        "col_produto_compra": col_produto_compra,
        "col_qtd_compra": col_qtd_compra,
        "col_custo_total": col_custo_total,
        "col_data_venda": col_data_venda,
        "col_produto_venda": col_produto_venda,
        "col_qtd_venda": col_qtd_venda,
        "col_valor_venda": col_valor_venda,
    }


def calcular_fifo(dados):

    compras = dados["compras"]
    vendas = dados["vendas"]

    estoque = {}

    # montar estoque
    for _, row in compras.iterrows():

        produto = row[dados["col_produto_compra"]]
        qtd = float(row[dados["col_qtd_compra"]])
        custo_total = float(row[dados["col_custo_total"]])

        custo_unit = custo_total / qtd if qtd else 0

        if produto not in estoque:
            estoque[produto] = []

        estoque[produto].append({
            "qtd": qtd,
            "custo": custo_unit
        })

    resultado = []

    # processar vendas
    for _, row in vendas.iterrows():

        produto = row[dados["col_produto_venda"]]
        qtd_venda = float(row[dados["col_qtd_venda"]])
        valor_venda = float(row[dados["col_valor_venda"]])

        custo_total = 0

        if produto in estoque:

            restante = qtd_venda

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

        lucro = valor_venda - custo_total

        resultado.append({
            "DATA": row[dados["col_data_venda"]] if dados["col_data_venda"] else None,
            "PRODUTO": produto,
            "QTD": qtd_venda,
            "VALOR": valor_venda,
            "CUSTO": custo_total,
            "LUCRO": lucro
        })

    return pd.DataFrame(resultado)


# ============================================
# EXECUÇÃO
# ============================================

compras, vendas = carregar_planilha(URL_PLANILHA)

dados = preparar_dados(compras, vendas)

fifo = calcular_fifo(dados)


# ============================================
# DASHBOARD
# ============================================

st.title("📦 Sistema de Estoque FIFO")

total_vendido = fifo["VALOR"].sum()
total_custo = fifo["CUSTO"].sum()
total_lucro = fifo["LUCRO"].sum()

col1, col2, col3 = st.columns(3)

col1.metric("💰 Total vendido", f"R$ {total_vendido:,.2f}")
col2.metric("📉 Custo", f"R$ {total_custo:,.2f}")
col3.metric("📈 Lucro", f"R$ {total_lucro:,.2f}")


# ============================================
# LUCRO POR PRODUTO
# ============================================

st.subheader("Lucro por produto")

resumo = (
    fifo.groupby("PRODUTO")
    .agg({
        "QTD": "sum",
        "VALOR": "sum",
        "CUSTO": "sum",
        "LUCRO": "sum"
    })
    .reset_index()
)

st.dataframe(resumo, use_container_width=True)


# ============================================
# VENDAS DETALHADAS
# ============================================

st.subheader("Vendas detalhadas")

st.dataframe(fifo, use_container_width=True)
