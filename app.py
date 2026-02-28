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
        st.rerun()

# carrega dados (com cache)
df_compras, df_vendas = carregar_dados()

df_fifo, df_estoque = calcular_fifo(df_compras, df_vendas)

if df_fifo.empty:
    st.warning("Não foi possível calcular FIFO (sem vendas ou sem compras ENTREGUE válidas).")
    st.stop()

# ============================================
# TABS
# ============================================

tab_dash, tab_search, tab_alerts = st.tabs(["📊 Dashboard", "🔎 Pesquisa de produto", "⚠️ Alertas"])

# ============================================
# TAB 1 – DASHBOARD
# ============================================
with tab_dash:
    # -------- FILTRO POR MÊS --------
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

    # -------- KPIs GERAIS (MÊS FILTRADO) --------
    total_vendido = df_fifo_filt["VALOR_TOTAL"].sum()
    total_custo = df_fifo_filt["CUSTO_TOTAL"].sum()
    total_lucro = df_fifo_filt["LUCRO"].sum()

    c1, c2, c3 = st.columns(3)
    c1.metric("💰 Total vendido", format_reais(total_vendido))
    c2.metric("📉 Custo (FIFO)", format_reais(total_custo))
    c3.metric("📈 Lucro (FIFO)", format_reais(total_lucro))

    st.markdown("---")

    # -------- GRÁFICO: FATURAMENTO DIÁRIO --------
    st.subheader("📊 Faturamento diário (período filtrado)")
    if df_fifo_filt.empty:
        st.info("Nenhuma venda no período selecionado.")
    else:
        df_dia = df_fifo_filt.copy()
        df_dia["DIA"] = df_dia["DATA"].dt.date
        resumo_dia = df_dia.groupby("DIA", as_index=False)["VALOR_TOTAL"].sum().sort_values("DIA")
        resumo_dia = resumo_dia.set_index("DIA")
        st.line_chart(resumo_dia)

    # -------- VENDAS DETALHADAS (MÊS FILTRADO) --------
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

# ============================================
# TAB 2 – PESQUISA DE PRODUTO (PREÇO FIFO)
# ============================================
with tab_search:
    st.subheader("🔎 Pesquisa de produto – baseado no FIFO")

    if df_fifo.empty and df_estoque.empty:
        st.info("Sem dados de estoque ou vendas para pesquisar.")
    else:
        # lista de produtos (estoque + vendas)
        produtos_estoque = df_estoque["PRODUTO"].unique().tolist() if not df_estoque.empty else []
        produtos_vendas = df_fifo["PRODUTO"].unique().tolist() if not df_fifo.empty else []
        todos_produtos = sorted(set(produtos_estoque) | set(produtos_vendas))

        prod_sel = st.selectbox(
            "Escolha o produto:",
            options=["(selecione)"] + todos_produtos,
            index=0
        )

        if prod_sel != "(selecione)":
            # ---------- dados de estoque FIFO ----------
            linha_est = df_estoque[df_estoque["PRODUTO"] == prod_sel]
            if not linha_est.empty:
                saldo = float(linha_est["SALDO_QTD"].iloc[0])
                valor_estoque = float(linha_est["VALOR_ESTOQUE"].iloc[0])
                custo_medio_fifo = float(linha_est["CUSTO_MEDIO_FIFO"].iloc[0])
            else:
                saldo = 0.0
                valor_estoque = 0.0
                custo_medio_fifo = 0.0

            # ---------- dados de vendas ----------
            vendas_prod = df_fifo[df_fifo["PRODUTO"] == prod_sel].copy()

            if not vendas_prod.empty:
                # preço médio de venda histórico
                qtd_total_vendida = vendas_prod["QTD"].sum()
                receita_total = vendas_prod["VALOR_TOTAL"].sum()
                preco_medio_venda = receita_total / qtd_total_vendida if qtd_total_vendida else 0.0

                # custo total histórico pra margem
                custo_total_hist = vendas_prod["CUSTO_TOTAL"].sum()
                margem_media = (receita_total - custo_total_hist) / receita_total if receita_total else 0.0

                # última venda (unitária)
                vendas_prod_ord = vendas_prod.sort_values("DATA")
                ultima = vendas_prod_ord.iloc[-1]
                preco_unit_ultima = ultima["VALOR_TOTAL"] / ultima["QTD"] if ultima["QTD"] else 0.0
                data_ultima = ultima["DATA"]
            else:
                qtd_total_vendida = 0.0
                receita_total = 0.0
                preco_medio_venda = 0.0
                preco_unit_ultima = 0.0
                data_ultima = None
                margem_media = 0.0
                custo_total_hist = 0.0

            # ---------- cards / métricas ----------
            st.markdown(f"### 📦 {prod_sel}")

            col_m1, col_m2, col_m3 = st.columns(3)
            with col_m1:
                st.metric("Custo médio FIFO", format_reais(custo_medio_fifo))
            with col_m2:
                st.metric("Preço médio de venda", format_reais(preco_medio_venda))
            with col_m3:
                st.metric("Margem média histórica", f"{margem_media*100:,.1f}%")

            col_m4, col_m5, col_m6 = st.columns(3)
            with col_m4:
                st.metric("Saldo em estoque", f"{int(saldo)} unid.")
            with col_m5:
                st.metric("Receita total acumulada", format_reais(receita_total))
            with col_m6:
                st.metric("Quantidade total vendida", f"{int(qtd_total_vendida)} unid.")

            st.markdown("---")

            # bloco texto com última venda
            st.markdown("#### 🕒 Última venda")
            if data_ultima is not None and pd.notna(data_ultima):
                st.write(
                    f"- Data: **{data_ultima.strftime('%d/%m/%Y')}**  \n"
                    f"- Preço unitário na venda: **{format_reais(preco_unit_ultima)}**  \n"
                    f"- Quantidade vendida nesse dia: **{int(ultima['QTD'])} unid.**  \n"
                    f"- Valor total da venda: **{format_reais(ultima['VALOR_TOTAL'])}**"
                )
            else:
                st.write("Nenhuma venda registrada para esse produto ainda.")

            st.markdown("---")
            st.markdown("#### 📄 Histório recente de vendas do produto")

            if not vendas_prod.empty:
                vendas_prod_hist = vendas_prod.copy()
                vendas_prod_hist["CUSTO_UNIT"] = vendas_prod_hist["CUSTO_TOTAL"] / vendas_prod_hist["QTD"].replace(0, pd.NA)
                vendas_prod_hist["DATA"] = vendas_prod_hist["DATA"].dt.strftime("%d/%m/%Y")
                vendas_prod_hist["VALOR_TOTAL"] = vendas_prod_hist["VALOR_TOTAL"].map(format_reais)
                vendas_prod_hist["CUSTO_TOTAL"] = vendas_prod_hist["CUSTO_TOTAL"].map(format_reais)
                vendas_prod_hist["LUCRO"] = vendas_prod_hist["LUCRO"].map(format_reais)
                vendas_prod_hist["CUSTO_UNIT"] = vendas_prod_hist["CUSTO_UNIT"].map(format_reais)

                cols_hist = ["DATA", "QTD", "VALOR_TOTAL", "CUSTO_TOTAL", "CUSTO_UNIT", "LUCRO", "MES_ANO"]
                cols_hist = [c for c in cols_hist if c in vendas_prod_hist.columns]

                st.dataframe(
                    vendas_prod_hist[cols_hist].sort_values("DATA", ascending=False).head(20),
                    use_container_width=True
                )
            else:
                st.info("Sem histórico de vendas para esse produto.")

            st.markdown("---")
            st.markdown("#### 💡 Como usar esses números na prática")
            st.markdown(
                f"""
- Se o **custo médio FIFO** estiver aumentando, é sinal de que suas últimas compras de `{prod_sel}` vieram mais caras.
- Compare o **preço médio de venda** com o custo médio: isso te diz se esse produto costuma ser saudável ou apertado.
- A **margem média histórica** mostra como você vem tratando esse produto ao longo do tempo.  
  Se hoje a margem estiver bem abaixo da média, vale revisar seu preço ou suas condições de compra.
                """
            )
        else:
            st.info("Selecione um produto acima para ver os números baseados no FIFO.")

# ============================================
# TAB 3 – ALERTAS
# ============================================
with tab_alerts:
    st.subheader("⚠️ Alertas de estoque")

    if df_estoque.empty:
        st.info("Sem dados de estoque para gerar alertas.")
    else:
        # ---------- PREPARO BASE ----------
        # vendas totais por produto (quantidade)
        vendas_tot = (
            df_fifo
            .groupby("PRODUTO", as_index=False)["QTD"]
            .sum()
            .rename(columns={"QTD": "QTD_VENDIDA_TOTAL"})
        )

        base_alerta = df_estoque.merge(vendas_tot, on="PRODUTO", how="left")
        base_alerta["QTD_VENDIDA_TOTAL"] = base_alerta["QTD_VENDIDA_TOTAL"].fillna(0)

        # thresholds
        LIM_VENDE_BEM = 10       # vendeu 10 ou mais unidades no histórico
        LIM_ESTOQUE_BAIXO = 3    # no máximo 3 unidades em estoque
        LIM_DIAS_PARADO = 30     # 30 dias sem movimento

        # ---------- 1) Produtos vendendo bem mas com pouco estoque ----------
        st.markdown("### 🔥 Vendendo bem e com pouco estoque")

        vendendo_bem_baixo_estoque = base_alerta[
            (base_alerta["QTD_VENDIDA_TOTAL"] >= LIM_VENDE_BEM) &
            (base_alerta["SALDO_QTD"] > 0) &
            (base_alerta["SALDO_QTD"] <= LIM_ESTOQUE_BAIXO)
        ].copy()

        if vendendo_bem_baixo_estoque.empty:
            st.info("Nenhum produto ao mesmo tempo com vendas fortes e estoque muito baixo pelos critérios atuais.")
        else:
            df_vb = vendendo_bem_baixo_estoque.copy()
            df_vb["VALOR_ESTOQUE_FMT"] = df_vb["VALOR_ESTOQUE"].map(format_reais)
            df_vb = df_vb.sort_values(["SALDO_QTD", "QTD_VENDIDA_TOTAL"], ascending=[True, False])

            st.dataframe(
                df_vb[["PRODUTO", "SALDO_QTD", "QTD_VENDIDA_TOTAL", "VALOR_ESTOQUE_FMT"]]
                .rename(columns={
                    "SALDO_QTD": "Estoque atual",
                    "QTD_VENDIDA_TOTAL": "Qtd vendida (histórico)",
                    "VALOR_ESTOQUE_FMT": "Valor em estoque (FIFO)"
                }),
                use_container_width=True
            )

            st.markdown(
                f"*Critério usado:* vendeu **≥ {LIM_VENDE_BEM} unid.** no histórico e tem **≤ {LIM_ESTOQUE_BAIXO} unid.** em estoque."
            )

        st.markdown("---")

        # ---------- 2) Produtos com estoque parado há muito tempo ----------
        st.markdown("### 🐌 Estoque parado há muito tempo")

        # preparar df_compras e df_vendas para datas de última movimentação
        df_compras_alert = df_compras.copy()
        df_compras_alert.columns = [c.strip().upper() for c in df_compras_alert.columns]
        if "STATUS" in df_compras_alert.columns:
            df_compras_alert = df_compras_alert[
                df_compras_alert["STATUS"].astype(str).str.upper() == "ENTREGUE"
            ].copy()
        if "DATA" in df_compras_alert.columns:
            df_compras_alert["DATA"] = pd.to_datetime(df_compras_alert["DATA"], errors="coerce", dayfirst=True)

        df_vendas_alert = df_vendas.copy()
        df_vendas_alert.columns = [c.strip().upper() for c in df_vendas_alert.columns]
        if "DATA" in df_vendas_alert.columns:
            df_vendas_alert["DATA"] = pd.to_datetime(df_vendas_alert["DATA"], errors="coerce", dayfirst=True)

        # última venda por produto
        if not df_vendas_alert.empty and "DATA" in df_vendas_alert.columns:
            last_sale = (
                df_vendas_alert
                .groupby("PRODUTO", as_index=False)["DATA"]
                .max()
                .rename(columns={"DATA": "ULT_VENDA"})
            )
        else:
            last_sale = pd.DataFrame(columns=["PRODUTO", "ULT_VENDA"])

        # última compra (ENTREGUE) por produto
        if not df_compras_alert.empty and "DATA" in df_compras_alert.columns:
            last_buy = (
                df_compras_alert
                .groupby("PRODUTO", as_index=False)["DATA"]
                .max()
                .rename(columns={"DATA": "ULT_COMPRA"})
            )
        else:
            last_buy = pd.DataFrame(columns=["PRODUTO", "ULT_COMPRA"])

        parado = (
            df_estoque
            .merge(last_sale, on="PRODUTO", how="left")
            .merge(last_buy, on="PRODUTO", how="left")
        )

        # só faz sentido se tem estoque > 0
        parado = parado[parado["SALDO_QTD"] > 0].copy()

        today = pd.Timestamp.now().normalize()

        def dias_parado(row):
            ult_venda = row.get("ULT_VENDA")
            ult_compra = row.get("ULT_COMPRA")
            if pd.notna(ult_venda):
                return (today - ult_venda.normalize()).days
            if pd.notna(ult_compra):
                return (today - ult_compra.normalize()).days
            return None

        parado["DIAS_PARADO"] = parado.apply(dias_parado, axis=1)

        parado_alerta = parado[
            (parado["DIAS_PARADO"].notna()) &
            (parado["DIAS_PARADO"] >= LIM_DIAS_PARADO)
        ].copy()

        if parado_alerta.empty:
            st.info(f"Nenhum produto com estoque parado há mais de {LIM_DIAS_PARADO} dias pelos critérios atuais.")
        else:
            df_p = parado_alerta.copy()
            if "ULT_VENDA" in df_p.columns:
                df_p["ULT_VENDA_FMT"] = df_p["ULT_VENDA"].dt.strftime("%d/%m/%Y")
            else:
                df_p["ULT_VENDA_FMT"] = ""

            if "ULT_COMPRA" in df_p.columns:
                df_p["ULT_COMPRA_FMT"] = df_p["ULT_COMPRA"].dt.strftime("%d/%m/%Y")
            else:
                df_p["ULT_COMPRA_FMT"] = ""

            df_p["VALOR_ESTOQUE_FMT"] = df_p["VALOR_ESTOQUE"].map(format_reais)

            df_p = df_p.sort_values("DIAS_PARADO", ascending=False)

            st.dataframe(
                df_p[[
                    "PRODUTO",
                    "SALDO_QTD",
                    "VALOR_ESTOQUE_FMT",
                    "DIAS_PARADO",
                    "ULT_VENDA_FMT",
                    "ULT_COMPRA_FMT"
                ]].rename(columns={
                    "SALDO_QTD": "Estoque atual",
                    "VALOR_ESTOQUE_FMT": "Valor em estoque (FIFO)",
                    "DIAS_PARADO": "Dias parado",
                    "ULT_VENDA_FMT": "Última venda",
                    "ULT_COMPRA_FMT": "Última compra (ENTREGUE)"
                }),
                use_container_width=True
            )

            st.markdown(
                f"*Critério usado:* produto com estoque > 0 e **sem venda há ≥ {LIM_DIAS_PARADO} dias** "
                f"(ou nunca vendeu, mas a última compra é mais antiga que isso)."
            )
