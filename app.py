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
    """Converte 'R$ 20,70' ou '1,00' -> 20.70 (float)."""
    if pd.isna(x):
        return 0.0
    s = str(x).strip()
    if s == "":
        return 0.0
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


def detectar_linha_cabecalho(df_raw: pd.DataFrame, must_have):
    """
    Acha a linha onde está o cabeçalho verdadeiro (DATA, PRODUTO, QTD, etc.)
    """
    max_linhas = min(20, len(df_raw))
    for i in range(max_linhas):
        linha = " ".join([str(x).upper() for x in df_raw.iloc[i].tolist()])
        if all(pal in linha for pal in must_have):
            return i
    return None


def limpar_aba(xls, nome_aba):
    """
    Lê aba com header=None, detecta cabeçalho real e retorna df limpo.
    """
    df_raw = pd.read_excel(xls, sheet_name=nome_aba, header=None)

    if nome_aba.upper() == "COMPRAS":
        must_have = ["DATA", "PRODUTO", "STATUS", "QUANT", "CUSTO"]
    elif nome_aba.upper() == "VENDAS":
        must_have = ["DATA", "PRODUTO", "QTD", "VALOR"]
    else:
        must_have = ["DATA", "PRODUTO"]

    linha_header = detectar_linha_cabecalho(df_raw, must_have)

    if linha_header is None:
        st.error(f"Não encontrei cabeçalho claro na aba {nome_aba}. Colunas lidas: {list(df_raw.columns)}")
        st.stop()

    # linha do cabeçalho
    cabecalho = df_raw.iloc[linha_header]
    df = df_raw.iloc[linha_header + 1:].copy()
    df.columns = [str(c).strip().upper() for c in cabecalho]

    # remove colunas totalmente vazias
    df = df.loc[:, ~df.isna().all()]

    # drop linhas totalmente vazias
    df = df.dropna(how="all").reset_index(drop=True)

    return df


@st.cache_data
def carregar_dados():
    """Lê as abas COMPRAS e VENDAS já limpas, com cabeçalho certo."""
    xls = pd.ExcelFile(URL_PLANILHA)

    df_compras = limpar_aba(xls, "COMPRAS")
    df_vendas = limpar_aba(xls, "VENDAS")

    return df_compras, df_vendas


# ============================================
# FIFO
# ============================================

def calcular_fifo(df_compras_raw: pd.DataFrame, df_vendas_raw: pd.DataFrame):
    compras = df_compras_raw.copy()
    vendas = df_vendas_raw.copy()

    # ---------- normalizar nomes ----------
    compras.columns = [c.strip().upper() for c in compras.columns]
    vendas.columns = [c.strip().upper() for c in vendas.columns]

    # nomes esperados depois da limpeza, pela sua planilha:
    # COMPRAS: DATA | PRODUTO | STATUS | QUANTIDADE | CUSTO UNITÁRIO | CUSTO TOTAL | OBSERVAÇÃO
    # VENDAS:  DATA | PRODUTO | QTD | VALOR VENDA | VALOR TOTAL | ...

    # conferir se tudo existe
    cols_compras_obrig = ["DATA", "PRODUTO", "STATUS", "QUANTIDADE", "CUSTO UNITÁRIO", "CUSTO TOTAL"]
    cols_vendas_obrig = ["DATA", "PRODUTO", "QTD", "VALOR TOTAL"]

    faltando_compras = [c for c in cols_compras_obrig if c not in compras.columns]
    faltando_vendas = [c for c in cols_vendas_obrig if c not in vendas.columns]

    if faltando_compras:
        st.error(f"Aba COMPRAS após limpeza ainda está sem colunas: {faltando_compras}. Colunas: {list(compras.columns)}")
        st.stop()
    if faltando_vendas:
        st.error(f"Aba VENDAS após limpeza ainda está sem colunas: {faltando_vendas}. Colunas: {list(vendas.columns)}")
        st.stop()

    # ---------- filtrar apenas STATUS = ENTREGUE ----------
    compras = compras[compras["STATUS"].astype(str).str.upper() == "ENTREGUE"].copy()

    if compras.empty:
        st.warning("Nenhuma compra com STATUS = ENTREGUE encontrada.")
        return pd.DataFrame(), pd.DataFrame()

    # ---------- datas ----------
    compras["DATA"] = pd.to_datetime(compras["DATA"], errors="coerce", dayfirst=True)
    vendas["DATA"] = pd.to_datetime(vendas["DATA"], errors="coerce", dayfirst=True)

    compras = compras.sort_values("DATA")
    vendas = vendas.sort_values("DATA")

    # ---------- números ----------
    compras["QUANTIDADE"] = compras["QUANTIDADE"].apply(parse_money).astype(float)
    compras["CUSTO UNITÁRIO"] = compras["CUSTO UNITÁRIO"].apply(parse_money).astype(float)
    compras["CUSTO TOTAL"] = compras["CUSTO TOTAL"].apply(parse_money).astype(float)

    vendas["QTD"] = vendas["QTD"].apply(parse_money).astype(float)
    vendas["VALOR TOTAL"] = vendas["VALOR TOTAL"].apply(parse_money).astype(float)

    # se custo total veio 0, recalcula
    mask_zero = compras["CUSTO TOTAL"] == 0
    compras.loc[mask_zero, "CUSTO TOTAL"] = compras.loc[mask_zero, "QUANTIDADE"] * compras.loc[mask_zero, "CUSTO UNITÁRIO"]

    # ---------- montar estoque (lotes) ----------
    estoque = {}  # produto -> [ {qtd, custo}, ... ]

    for _, row in compras.iterrows():
        produto = str(row["PRODUTO"])
        qtd = float(row["QUANTIDADE"])
        if qtd <= 0:
            continue
        custo_unit = float(row["CUSTO TOTAL"]) / qtd if qtd else 0.0

        if produto not in estoque:
            estoque[produto] = []
        estoque[produto].append({"qtd": qtd, "custo": custo_unit})

    # ---------- processar vendas em FIFO ----------
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
            # sem estoque registrado desse produto
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

    # ---------- estoque atual remanescente ----------
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
