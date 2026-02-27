import streamlit as st
import pandas as pd

st.set_page_config(page_title="FIFO - Loja Importados", layout="wide")

# ============================================
# CONFIG – sua planilha do Google
# ============================================

URL_PLANILHA = "https://docs.google.com/spreadsheets/d/1TsRjsfw1TVfeEWBBvhKvsGQ5YUCktn2b/export?format=xlsx"


# ============================================
# HELPERS
# ============================================

def parse_money(x):
    """Converte 'R$ 20,70' -> 20.70"""
    if pd.isna(x):
        return 0.0
    s = str(x).strip()
    if s == "":
        return 0.0
    # tira R$, espaços etc
    for lixo in ["R$", "r$", " "]:
        s = s.replace(lixo, "")
    # separador brasileiro
    s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except Exception:
        try:
            return float(str(x))
        except Exception:
            return 0.0


def detectar_coluna(df, tem_substr):
    """Acha primeira coluna cujo nome contém TODAS as substrings informadas"""
    cols = df.columns
    for c in cols:
        nome = c.upper()
        if all(sub in nome for sub in tem_substr):
            return c
    return None


# ============================================
# CARREGAR PLANILHA
# ============================================

@st.cache_data
def carregar_dados():
    xls = pd.ExcelFile(URL_PLANILHA)

    df_compras = pd.read_excel(xls, "COMPRAS")
    df_vendas = pd.read_excel(xls, "VENDAS")

    # normaliza cabeçalhos
    df_compras.columns = df_compras.columns.str.strip().str.upper()
    df_vendas.columns = df_vendas.columns.str.strip().str.upper()

    return df_compras, df_vendas


# ============================================
# FIFO
# ============================================

def calcular_fifo(df_compras_raw: pd.DataFrame, df_vendas_raw: pd.DataFrame):
    compras = df_compras_raw.copy()
    vendas = df_vendas_raw.copy()

    # ---- filtrar só compras ENTREGUE ----
    col_status_c = detectar_coluna(compras, ["STATUS"])
    if col_status_c:
        compras = compras[compras[col_status_c].astype(str).str.upper() == "ENTREGUE"].copy()

    # ---- detectar colunas de interesse ----
    col_data_c = detectar_coluna(compras, ["DATA"])
    col_prod_c = detectar_coluna(compras, ["PRODUTO"])
    col_qtd_c = detectar_coluna(compras, ["QUANT"])
    col_custo_unit = detectar_coluna(compras, ["CUSTO", "UNIT"])
    col_custo_total = detectar_coluna(compras, ["CUSTO", "TOTAL"])

    col_data_v = detectar_coluna(vendas, ["DATA"])
    col_prod_v = detectar_coluna(vendas, ["PRODUTO"])
    col_qtd_v = detectar_coluna(vendas, ["QTD"])
    col_valor_unit = detectar_coluna(vendas, ["VALOR", "VENDA"])
    col_valor_total = detectar_coluna(vendas, ["VALOR", "TOTAL"])

    # ---- preparar COMPRAS ----
    if col_data_c:
        compras[col_data_c] = pd.to_datetime(compras[col_data_c], errors="coerce", dayfirst=True)
        compras = compras.sort_values(col_data_c)

    compras[col_qtd_c] = compras[col_qtd_c].apply(parse_money).astype(float)

    if col_custo_unit:
        compras[col_custo_unit] = compras[col_custo_unit].apply(parse_money).astype(float)
    if col_custo_total:
        compras[col_custo_total] = compras[col_custo_total].apply(parse_money).astype(float)

    # se não tiver custo total, calcula
    if col_custo_total is None and col_custo_unit is not None:
        compras["__CUSTO_TOTAL__"] = compras[col_qtd_c] * compras[col_custo_unit]
        col_custo_total = "__CUSTO_TOTAL__"

    # custo unitário garantido
    if col_custo_unit is None and col_custo_total is not None:
        compras["__CUSTO_UNIT__"] = compras[col_custo_total] / compras[col_qtd_c].replace(0, pd.NA)
        col_custo_unit = "__CUSTO_UNIT__"

    # ---- preparar VENDAS ----
    if col_data_v:
        vendas[col_data_v] = pd.to_datetime(vendas[col_data_v], errors="coerce", dayfirst=True)
        vendas = vendas.sort_values(col_data_v)

    vendas[col_qtd_v] = vendas[col_qtd_v].apply(parse_money).astype(float)

    if col_valor_total:
        vendas[col_valor_total] = vendas[col_valor_total].apply(parse_money).astype(float)
    if col_valor_unit:
        vendas[col_valor_unit] = vendas[col_valor_unit].apply(parse_money).astype(float)

    if col_valor_total is None and col_valor_unit is not None:
        vendas["__VALOR_TOTAL__"] = vendas[col_valor_unit] * vendas[col_qtd_v]
        col_valor_total = "__VALOR_TOTAL__"

    # ---- montar estoque por produto (lotes) ----
    estoque = {}  # produto -> lista de lotes {"qtd":..., "custo":...}

    for _, row in compras.iterrows():
        produto = row[col_prod_c]
        qtd = float(row[col_qtd_c])
        if qtd <= 0:
            continue
        custo_unit = float(row[col_custo_unit])
        if produto not in estoque:
            estoque[produto] = []
        estoque[produto].append({"qtd": qtd, "custo": custo_unit})

    # ---- processar vendas consumindo lotes FIFO ----
    registros_venda = []

    for _, row in vendas.iterrows():
        produto = row[col_prod_v]
        qtd_venda = float(row[col_qtd_v])
        valor_total = float(row[col_valor_total])
        data_venda = row[col_data_v] if col_data_v else None

        restante = qtd_venda
        custo_total = 0.0

        # se não tem estoque desse produto, custo fica 0 (pode sinalizar depois)
        if produto in estoque:
            lotes = estoque[produto]
            while restante > 0 and lotes:
                lote = lotes[0]
                if lote["qtd"] <= restante:
                    # consome lote inteiro
                    custo_total += lote["qtd"] * lote["custo"]
                    restante -= lote["qtd"]
                    lotes.pop(0)
                else:
                    # consome parte do lote
                    custo_total += restante * lote["custo"]
                    lote["qtd"] -= restante
                    restante = 0

        lucro = valor_total - custo_total

        registros_venda.append({
            "DATA": data_venda,
            "PRODUTO": produto,
            "QTD": qtd_venda,
            "VALOR_TOTAL": valor_total,
            "CUSTO_TOTAL": custo_total,
            "LUCRO": lucro
        })

    df_fifo = pd.DataFrame(registros_venda)

    # ---- estoque atual (lotes remanescentes) ----
    estoque_reg = []
    for produto, lotes in estoque.items():
        saldo = sum(l["qtd"] for l in lotes)
        if saldo <= 0:
            continue
        valor = sum(l["qtd"] * l["custo"] for l in lotes)
        custo_medio = valor / saldo if saldo else 0
        estoque_reg.append({
            "PRODUTO": produto,
            "SALDO_QTD": saldo,
            "VALOR_ESTOQUE": valor,
            "CUSTO_MEDIO_FIFO": custo_medio
        })
    df_estoque = pd.DataFrame(estoque_reg)

    return df_fifo, df_estoque


# ============================================
# EXECUÇÃO
# ============================================

st.title("📦 Dashboard FIFO – Loja Importados")

compras, vendas = carregar_dados()

df_fifo, df_estoque = calcular_fifo(compras, vendas)

if df_fifo.empty:
    st.warning("Não foi possível calcular FIFO – verifique se há COMPRAS e VENDAS na planilha.")
    st.stop()

# ============================================
# KPIs GERAIS
# ============================================

total_vendido = df_fifo["VALOR_TOTAL"].sum()
total_custo = df_fifo["CUSTO_TOTAL"].sum()
total_lucro = df_fifo["LUCRO"].sum()

c1, c2, c3 = st.columns(3)
c1.metric("💰 Total vendido", f"R$ {total_vendido:,.2f}")
c2.metric("📉 Custo (FIFO)", f"R$ {total_custo:,.2f}")
c3.metric("📈 Lucro (FIFO)", f"R$ {total_lucro:,.2f}")

st.markdown("---")

# ============================================
# LUCRO REAL POR PRODUTO
# ============================================

st.subheader("💰 Lucro real por produto (FIFO)")

res_prod = (
    df_fifo
    .groupby("PRODUTO", as_index=False)
    .agg({
        "QTD": "sum",
        "VALOR_TOTAL": "sum",
        "CUSTO_TOTAL": "sum",
        "LUCRO": "sum"
    })
    .sort_values("LUCRO", ascending=False)
)

st.dataframe(res_prod, use_container_width=True)

# ============================================
# ESTOQUE ATUAL (FIFO)
# ============================================

st.subheader("📦 Estoque atual (custo médio FIFO)")

if not df_estoque.empty:
    st.dataframe(df_estoque.sort_values("SALDO_QTD", ascending=False), use_container_width=True)
else:
    st.info("Sem saldo em estoque após aplicar FIFO (ou sem compras ENTREGUE).")

# ============================================
# VENDAS DETALHADAS
# ============================================

st.subheader("🧾 Vendas detalhadas (com custo FIFO)")

df_fifo_view = df_fifo.copy()
if df_fifo_view["DATA"].notna().any():
    df_fifo_view["DATA"] = df_fifo_view["DATA"].dt.strftime("%d/%m/%Y")

st.dataframe(df_fifo_view.sort_values("DATA", ascending=False), use_container_width=True)
