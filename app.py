import streamlit as st
import pandas as pd

st.set_page_config(page_title="📦 Dashboard FIFO – Loja Importados", layout="wide")

# ============================================
# CONFIG – sua planilha
# ============================================

URL_PLANILHA = "https://docs.google.com/spreadsheets/d/1TsRjsfw1TVfeEWBBvhKvsGQ5YUCktn2b/export?format=xlsx"

# limite máximo plausível de custo unitário (qualquer coisa acima disso é lixo)
CUSTO_MAX_PLAUSIVEL = 500.0


# ============================================
# HELPERS
# ============================================

def parse_money(x):
    """
    Converte valores da planilha para float em reais.

    Exemplos:
    - 'R$ 23,75'   -> 23.75
    - '1.299,00'   -> 1299.00
    - 237.55       -> 237.55  (já é número, não mexe)
    - códigos de barras grandões (só dígitos, 12+ casas) -> 0.0
    """
    # se já é número (float ou int), só converte direto
    if isinstance(x, (int, float)):
        if pd.isna(x):
            return 0.0
        return float(x)

    if pd.isna(x):
        return 0.0

    s = str(x).strip()
    if s == "" or s.lower() == "nan":
        return 0.0

    # tira símbolo de moeda e espaços
    s = s.replace("R$", "").replace("r$", "").replace(" ", "")

    # se for praticamente só dígitos MUITO longos, trata como código de barras
    digitos = "".join(ch for ch in s if ch.isdigit())
    if len(digitos) >= 12 and ("," not in s and "." not in s):
        return 0.0

    # CASOS DE FORMATACÃO:
    # 1) Tem ponto E vírgula -> padrão BR: 1.234,56  (ponto milhar, vírgula decimal)
    if "." in s and "," in s:
        s = s.replace(".", "").replace(",", ".")
    # 2) Só vírgula -> decimal BR: 23,75
    elif "," in s:
        s = s.replace(",", ".")
    # 3) Só ponto -> provavelmente já é decimal de número interno: 237.55 (NÃO mexe)

    try:
        return float(s)
    except Exception:
        return 0.0


def format_reais(v):
    """Formata float -> 'R$ X.XXX,YY'."""
    try:
        v = float(v)
    except Exception:
        return "R$ 0,00"
    s = f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {s}"


def detectar_linha_cabecalho(df_raw: pd.DataFrame, must_have):
    """
    Acha a linha onde está o cabeçalho verdadeiro (DATA, PRODUTO, QTD, etc.).
    must_have = lista de palavras que devem aparecer na linha.
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
        st.error(f"Não encontrei cabeçalho claro na aba {nome_aba}. Primeiras linhas lidas:\n{df_raw.head(5)}")
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

    # COMPRAS: DATA | PRODUTO | STATUS | QUANTIDADE | CUSTO UNITÁRIO | CUSTO TOTAL | ...
    # VENDAS:  DATA | PRODUTO | QTD | VALOR VENDA | VALOR TOTAL | ...

    cols_compras_obrig = ["DATA", "PRODUTO", "STATUS", "QUANTIDADE", "CUSTO UNITÁRIO"]
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

    # ---------- números (COMPRAS) ----------
    compras["QUANTIDADE"] = compras["QUANTIDADE"].apply(parse_money).astype(float)
    compras["CUSTO UNITÁRIO"] = compras["CUSTO UNITÁRIO"].apply(parse_money).astype(float)

    # recalcula SEMPRE o CUSTO TOTAL a partir de qtd * custo unitário
    compras["CUSTO TOTAL"] = compras["QUANTIDADE"] * compras["CUSTO UNITÁRIO"]

    # custo unitário calculado para sanity check
    compras["CUSTO_UNIT_CALC"] = compras["CUSTO TOTAL"] / compras["QUANTIDADE"].replace(0, pd.NA)

    # descartar linhas com custo unitário absurdo (provável lixo)
    compras = compras[
        (compras["CUSTO_UNIT_CALC"].notna()) &
        (compras["CUSTO_UNIT_CALC"] >= 0) &
        (compras["CUSTO_UNIT_CALC"] <= CUSTO_MAX_PLAUSIVEL)
    ].copy()

    if compras.empty:
        st.warning("Todas as linhas de COMPRAS ficaram com custo unitário inválido após filtro.")
        return pd.DataFrame(), pd.DataFrame()

    # ---------- números (VENDAS) ----------
    vendas["QTD"] = vendas["QTD"].apply(parse_money).astype(float)
    vendas["VALOR TOTAL"] = vendas["VALOR TOTAL"].apply(parse_money).astype(float)

    # ---------- montar estoque (lotes FIFO) ----------
    estoque = {}  # produto -> [ {qtd, custo}, ... ]

    for _, row in compras.iterrows():
        produto = str(row["PRODUTO"])
        qtd = float(row["QUANTIDADE"])
        if qtd <= 0:
            continue
        custo_unit = float(row["CUSTO_UNIT_CALC"])

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

        registros_venda.append({
            "DATA": data_venda,
            "PRODUTO": produto,
            "QTD": qtd_venda,
            "VALOR_TOTAL": valor_total,
            "CUSTO_TOTAL": custo_total,
        })

    df_fifo = pd.DataFrame(registros_venda)

    # ---------- sanity no resultado: cortar custos insanos ----------
    df_fifo["CUSTO_UNIT"] = df_fifo["CUSTO_TOTAL"] / df_fifo["QTD"].replace(0, pd.NA)
    mask_insano = df_fifo["CUSTO_UNIT"] > CUSTO_MAX_PLAUSIVEL
    df_fifo.loc[mask_insano, "CUSTO_TOTAL"] = 0.0
    df_fifo.loc[mask_insano, "CUSTO_UNIT"] = 0.0

    # lucro final
    df_fifo["LUCRO"] = df_fifo["VALOR_TOTAL"] - df_fifo["CUSTO_TOTAL"]

    # mês/ano pra filtro
    df_fifo["MES_ANO"] = df_fifo["DATA"].dt.strftime("%Y-%m")

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

# ---------- Botão para recarregar a planilha (limpa cache) ----------
col_btn, _ = st.columns([1, 3])
with col_btn:
    if st.button("🔄 Atualizar dados da planilha"):
        st.cache_data.clear()
        st.experimental_rerun()

# carrega dados (com cache)
df_compras, df_vendas = carregar_dados()

df_fifo, df_estoque = calcular_fifo(df_compras, df_vendas)

if df_fifo.empty:
    st.warning("Não foi possível calcular FIFO (sem vendas ou sem compras ENTREGUE válidas).")
    st.stop()

# ============================================
# FILTRO POR MÊS
# ============================================

meses = ["Todos"]
meses_disp = sorted(df_fifo["MES_ANO"].dropna().unique().tolist(), reverse=True)
meses += meses_disp

mes_atual = pd.Timestamp.now().strftime("%Y-%m")
idx_padrao = meses.index(mes_atual) if mes_atual in meses else 0

mes_selecionado = st.selectbox("Filtrar por mês (YYYY-MM):", meses, index=idx_padrao)

if mes_selecionado == "Todos":
    df_fifo_filt = df_fifo.copy()
else:
    df_fifo_filt = df_fifo[df_fifo["MES_ANO"] == mes_selecionado].copy()

# ============================================
# KPIs GERAIS (MÊS FILTRADO)
# ============================================

total_vendido = df_fifo_filt["VALOR_TOTAL"].sum()
total_custo = df_fifo_filt["CUSTO_TOTAL"].sum()
total_lucro = df_fifo_filt["LUCRO"].sum()

c1, c2, c3 = st.columns(3)
c1.metric("💰 Total vendido", format_reais(total_vendido))
c2.metric("📉 Custo (FIFO)", format_reais(total_custo))
c3.metric("📈 Lucro (FIFO)", format_reais(total_lucro))

st.markdown("---")

# ============================================
# LUCRO REAL POR PRODUTO (MÊS FILTRADO)
# ============================================

st.subheader("💰 Lucro real por produto (FIFO) – período filtrado")

if df_fifo_filt.empty:
    st.info("Nenhuma venda no período selecionado.")
else:
    res_prod = (
        df_fifo_filt
        .groupby("PRODUTO", as_index=False)
        .agg({
            "QTD": "sum",
            "VALOR_TOTAL": "sum",
            "CUSTO_TOTAL": "sum",
            "LUCRO": "sum",
        })
        .sort_values("LUCRO", ascending=False)
    )

    res_view = res_prod.copy()
    res_view["VALOR_TOTAL"] = res_view["VALOR_TOTAL"].map(format_reais)
    res_view["CUSTO_TOTAL"] = res_view["CUSTO_TOTAL"].map(format_reais)
    res_view["LUCRO"] = res_view["LUCRO"].map(format_reais)

    st.dataframe(res_view, use_container_width=True)

# ============================================
# ESTOQUE ATUAL (GLOBAL, COM REAIS)
# ============================================

st.subheader("📦 Estoque atual (custo médio FIFO – global)")

if not df_estoque.empty:
    est_view = df_estoque.copy()
    est_view["VALOR_ESTOQUE"] = est_view["VALOR_ESTOQUE"].map(format_reais)
    est_view["CUSTO_MEDIO_FIFO"] = est_view["CUSTO_MEDIO_FIFO"].map(format_reais)
    est_view["SALDO_QTD"] = est_view["SALDO_QTD"].astype(int)
    st.dataframe(
        est_view.sort_values("SALDO_QTD", ascending=False),
        use_container_width=True
    )
else:
    st.info("Sem saldo em estoque após aplicar FIFO (ou todas as compras foram consumidas nas vendas).")

# ============================================
# VENDAS DETALHADAS (MÊS FILTRADO)
# ============================================

st.subheader("🧾 Vendas detalhadas (com custo FIFO) – período filtrado")

df_fifo_view = df_fifo_filt.copy()

if not df_fifo_view.empty:
    # garantir custo unitário numérico antes de formatar
    df_fifo_view["CUSTO_UNIT"] = df_fifo_view["CUSTO_TOTAL"] / df_fifo_view["QTD"].replace(0, pd.NA)

    # exemplo REAL para legenda – primeira linha do período filtrado
    exemplo = df_fifo_filt.iloc[0]
    prod_ex = str(exemplo["PRODUTO"])
    qtd_ex = float(exemplo["QTD"])
    venda_ex = format_reais(exemplo["VALOR_TOTAL"])
    custo_total_ex = format_reais(exemplo["CUSTO_TOTAL"])
    custo_unit_ex = format_reais(exemplo["CUSTO_TOTAL"] / exemplo["QTD"] if exemplo["QTD"] else 0)
    lucro_ex = format_reais(exemplo["LUCRO"])

    if df_fifo_view["DATA"].notna().any():
        df_fifo_view["DATA"] = df_fifo_view["DATA"].dt.strftime("%d/%m/%Y")

    df_fifo_view["VALOR_TOTAL"] = df_fifo_view["VALOR_TOTAL"].map(format_reais)
    df_fifo_view["CUSTO_TOTAL"] = df_fifo_view["CUSTO_TOTAL"].map(format_reais)
    df_fifo_view["LUCRO"] = df_fifo_view["LUCRO"].map(format_reais)
    df_fifo_view["CUSTO_UNIT"] = df_fifo_view["CUSTO_UNIT"].map(format_reais)

    cols_ordem = ["DATA", "PRODUTO", "QTD", "VALOR_TOTAL", "CUSTO_TOTAL", "CUSTO_UNIT", "LUCRO", "MES_ANO"]
    cols_ordem = [c for c in cols_ordem if c in df_fifo_view.columns]

    st.dataframe(
        df_fifo_view[cols_ordem].sort_values("DATA", ascending=False),
        use_container_width=True
    )

    # LEGENDA FIFO
    st.markdown("### 📘 Como o FIFO é calculado (exemplo real)")
    st.markdown(
        f"""
**Produto usado no exemplo:** `{prod_ex}`  

- Quantidade vendida nesta linha: **{qtd_ex:.0f} unid.**
- Valor total da venda: **{venda_ex}**
- Custo total FIFO dessa venda: **{custo_total_ex}**
- Custo unitário FIFO: **{custo_unit_ex}**
- Lucro dessa venda: **{lucro_ex}**

**Passo a passo:**

1. O app pega todas as **compras de `{prod_ex}` com STATUS = ENTREGUE**, na aba COMPRAS, em ordem de data (mais antigas primeiro).
2. Cada compra vira um **lote de estoque** com quantidade e custo unitário daquela compra.
3. Quando essa venda de **{qtd_ex:.0f} unidade(s)** acontece, o app:
   - consome primeiro o lote mais antigo,
   - depois o próximo, e assim por diante,
   - até somar as {qtd_ex:.0f} unidades vendidas.
4. O **custo total FIFO** (**{custo_total_ex}**) é a soma dos custos de todos esses lotes consumidos.
5. O **custo unitário FIFO** (**{custo_unit_ex}**) é esse custo total dividido pela quantidade vendida.
6. O **lucro** (**{lucro_ex}**) é:  
   **lucro = valor da venda ({venda_ex}) − custo total FIFO ({custo_total_ex})**.
        """
    )
else:
    st.info("Nenhuma venda no período selecionado.")
