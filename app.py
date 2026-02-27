import streamlit as st
import pandas as pd

st.set_page_config(page_title="📦 Dashboard FIFO – Loja Importados", layout="wide")

# ============================================
# CONFIG – sua planilha
# ============================================

URL_PLANILHA = "https://docs.google.com/spreadsheets/d/1TsRjsfw1TVfeEWBBvhKvsGQ5YUCktn2b/export?format=xlsx"


# ============================================
# HELPERS
# ============================================

def parse_money(x):
    """Converte coisas tipo 'R$ 20,70' para float 20.70."""
    if pd.isna(x):
        return 0.0
    s = str(x).strip()
    if s == "":
        return 0.0
    # remove R$, espaços etc
    s = s.replace("R$", "").replace("r$", "").replace(" ", "")
    # formato BR: 1.234,56
    s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except Exception:
        try:
            return float(str(x))
        except Exception:
            return 0.0


@st.cache_data
def carregar_dados():
    """Lê as abas COMPRAS e VENDAS da planilha."""
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

    # ---------- conferir colunas obrigatórias ----------
    cols_compras_obrig = ["DATA", "PRODUTO", "STATUS", "QUANTIDADE", "CUSTO UNITÁRIO", "CUSTO TOTAL"]
    cols_vendas_obrig = ["DATA", "PRODUTO", "QTD", "VALOR TOTAL"]

    faltando_compras = [c for c in cols_compras_obrig if c not in compras.columns]
    faltando_vendas = [c for c in cols_vendas_obrig if c not in vendas.columns]

    if faltando_compras:
        st.error(f"Na aba COMPRAS estão faltando as colunas: {faltando_compras}. Colunas encontradas: {list(compras.columns)}")
        st.stop()
    if faltando_vendas:
        st.error(f"Na aba VENDAS estão faltando as colunas: {faltando_vendas}. Colunas encontradas: {list(vendas.columns)}")
        st.stop()

    # ---------- filtrar apenas STATUS = ENTREGUE ----------
    compras = compras[compras["STATUS"].astype(str).str.upper() == "ENTREGUE"].copy()

    if compras.empty:
        st.warning("Nenhuma compra com STATUS = ENTREGUE encontrada.")
        return pd.DataFrame(), pd.DataFrame()

    # ---------- tratar datas ----------
    compras["DATA"] = pd.to_datetime(compras["DATA"], errors="coerce", dayfirst=True)
    vendas["DATA"] = pd.to_datetime(vendas["DATA"], errors="coerce", dayfirst=True)

    compras = compras.sort_values("DATA")
    vendas = vendas.sort_values("DATA")

    # ---------- garantir numéricos ----------
    compras["QUANTIDADE"] = compras["QUANTIDADE"].apply(parse_money).astype(float)
    compras["CUSTO UNITÁRIO"] = compras["CUSTO UNITÁRIO"].apply(parse_money).astype(float)
    compras["CUSTO TOTAL"] = compras["CUSTO TOTAL"].apply(parse_money).astype(float)

    vendas["QTD"] = vendas["QTD"].apply(parse_money).astype(float)
    vendas["VALOR TOTAL"] = vendas["VALOR TOTAL"].apply(parse_money).astype(float)

    # se CUSTO TOTAL vier zerado, recalcula
    compras.loc[compras["CUSTO TOTAL"] == 0, "CUSTO TOTAL"] = (
        compras["QUANTIDADE"] * compras["CUSTO UNITÁRIO"]
    )

    # ---------- montar estoque por produto (lotes) ----------
    estoque = {}  # produto -> lista de {qtd, custo}

    for _, row in compras.iterrows():
        produto = str(row["PRODUTO"])
        qtd = float(row["QUANTIDADE"])
        if qtd <= 0:
            continue
        custo_unit = float(row["CUSTO TOTAL"]) / qtd if qtd else 0.0
        if produto not in estoque:
            estoque[produto] = []
        estoque[produto].append({"qtd": qtd, "custo": custo_unit})

    # ---------- processar vendas consumindo lotes FIFO ----------
    registros_venda = []

    for _, row in vendas.iterrows():
        produto = str(row["PRODUTO"])
        qtd_venda = float(row["QTD"])
        valor_total = float(row["VALOR TOTAL"])
        data_venda = row["DATA"]

        restante = qtd_venda
        custo_total = 0.0

        if produto in estoque:
            lotes = estoque[produto]
            # consome lotes na ordem
            while restante > 0 and lotes:
                lote = lotes[0]
                if lote["qtd"] <= restante:
                    custo_total += lote["qtd"] * lote["custo"]
                    restante -= lote["qtd"]
                    lotes.pop(0)
                else:
                    custo_total += restante * lote["custo"]
                    lote["qtd"] -= restante
                    restante = 0
        else:
            # se não tem estoque registrado, custo 0 (pode ser venda de produto antigo)
            custo_total = 0.0

        lucro = valor_total - custo_total

        registros_venda.append({
            "DATA": data_venda,
            "PRODUTO": produto,
            "QTD": qtd_venda,
            "VALOR_TOTAL": valor_total,
            "CUSTO_TOTAL": custo_total,
            "LUCRO": lucro,
        })

    df_fifo = pd.DataFrame(registros_venda)

    # ---------- calcular estoque atual remanescente ----------
    estoque_reg = []
    for produto, lotes in estoque.items():
        saldo = sum(l["qtd"] for l in lotes)
        if saldo <= 0:
            continue
        valor = sum(l["qtd"] * l["custo"] for l in lotes)
        custo_medio = valor / saldo if saldo else 0.0
        estoque_reg.append({
            "PRODUTO": produto,
            "SALDO_QTD": saldo,
            "VALOR_ESTOQUE": valor,
            "CUSTO_MEDIO_FIFO": custo_medio,
        })

    df_estoque = pd.DataFrame(estoque_reg)

    return df_fifo, df_estoque


# ============================================
# EXECUÇÃO
# ============================================

st.title("📦 Dashboard FIFO – Loja Importados")

df_compras, df_vendas = carregar_dados()

df_fifo, df_estoque = calcular_fifo(df_compras, df_vendas)

if df_fifo.empty:
    st.warning("Não foi possível calcular FIFO (sem vendas ou sem compras ENTREGUE).")
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
        "LUCRO": "sum",
    })
    .sort_values("LUCRO", ascending=False)
)

st.dataframe(res_prod, use_container_width=True)

# ============================================
# ESTOQUE ATUAL (FIFO)
# ============================================

st.subheader("📦 Estoque atual (custo médio FIFO)")

if not df_estoque.empty:
    st.dataframe(
        df_estoque.sort_values("SALDO_QTD", ascending=False),
        use_container_width=True
    )
else:
    st.info("Sem saldo em estoque após aplicar FIFO (ou todas as compras foram consumidas nas vendas).")

# ============================================
# VENDAS DETALHADAS
# ============================================

st.subheader("🧾 Vendas detalhadas (com custo FIFO)")

df_fifo_view = df_fifo.copy()
if df_fifo_view["DATA"].notna().any():
    df_fifo_view["DATA"] = df_fifo_view["DATA"].dt.strftime("%d/%m/%Y")

st.dataframe(
    df_fifo_view.sort_values("DATA", ascending=False),
    use_container_width=True
)
