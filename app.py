import streamlit as st
import pandas as pd
import plotly.express as px

# --------------------------------------------------
# CONFIG BÁSICA
# --------------------------------------------------
st.set_page_config(
    page_title="Loja Importados – Dashboard FIFO",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# URL da sua planilha (gravado)
URL_PLANILHA = "https://docs.google.com/spreadsheets/d/1TsRjsfw1TVfeEWBBvhKvsGQ5YUCktn2b/export?format=xlsx"

# custo unitário máximo plausível (acima disso é dado zoado)
CUSTO_MAX_PLAUSIVEL = 500.0

# --------------------------------------------------
# ESTILO GLOBAL (CSS) – preto básico, elegante, sem neon
# --------------------------------------------------
GLOBAL_CSS = """
<style>
:root{
  --bg:#050505;
  --bg-page:#050505;
  --bg-card:#101010;
  --bg-card-soft:#111111;
  --border-soft:#262626;
  --accent:#22c55e;
  --accent-soft:#14b8a6;
  --accent-warm:#f97316;
  --text:#e5e5e5;
  --muted:#9ca3af;
}

html, body, [class*="css"] {
  background-color: var(--bg-page) !important;
  color: var(--text) !important;
  font-family: system-ui, -apple-system, BlinkMacSystemFont, "Inter", sans-serif;
}

.stApp {
  background-color: var(--bg-page) !important;
}

/* TOP BAR */
.topbar {
  display:flex;
  align-items:center;
  justify-content:space-between;
  gap:16px;
  padding:14px 18px;
  border-radius:18px;
  background:#050505;
  border:1px solid var(--border-soft);
  margin-bottom:20px;
}
.logo-pill {
  width:52px;
  height:52px;
  border-radius:16px;
  background:#111827;
  display:flex;
  align-items:center;
  justify-content:center;
  color:white;
  font-weight:800;
  font-size:22px;
}
.top-title {
  font-size:20px;
  font-weight:800;
  letter-spacing:-0.03em;
}
.top-subtitle {
  font-size:12px;
  color:var(--muted);
}
.top-right-badge {
  display:flex;
  flex-direction:column;
  align-items:flex-end;
  gap:4px;
  font-size:11px;
}
.top-chip {
  padding:4px 10px;
  border-radius:999px;
  border:1px solid var(--border-soft);
  background:#050505;
}
.top-chip span {
  color:var(--accent-soft);
}

/* KPI CARDS */
.kpi-row {
  display:flex;
  gap:10px;
  flex-wrap:wrap;
  margin-bottom:10px;
}
.kpi-card {
  flex:1 1 180px;
  min-width:0;
  padding:14px 16px;
  border-radius:14px;
  background:var(--bg-card-soft);
  border:1px solid var(--border-soft);
  box-shadow:none;
  position:relative;
  transition:transform .1s ease-out, border-color .1s ease-out, background .1s ease-out;
}
.kpi-card:hover{
  transform:translateY(-1px);
  border-color:var(--accent-soft);
  background:#151515;
}
.kpi-label {
  font-size:11px;
  text-transform:uppercase;
  letter-spacing:0.16em;
  color:var(--muted);
  margin-bottom:4px;
}
.kpi-value {
  font-size:20px;
  font-weight:800;
}
.kpi-pill {
  font-size:11px;
  color:var(--muted);
  margin-top:4px;
}

/* SEÇÕES / CARDS */
.section-title {
  font-size:16px;
  font-weight:700;
  margin-top:0;
  margin-bottom:2px;
}
.section-sub {
  font-size:12px;
  color:var(--muted);
  margin-bottom:8px;
}

/* CARD-SOFT (DESLIGADO VISUALMENTE) */
.card-soft {
  background: transparent;
  border-radius: 0;
  padding: 0;
  border: none;
  margin-bottom: 0;
}

/* BADGES */
.badge-soft {
  display:inline-flex;
  align-items:center;
  gap:4px;
  padding:1px 8px;
  border-radius:999px;
  font-size:11px;
  background:#111827;
  color:#e5e7eb;
}
.badge-red {
  background:#451a1a;
  color:#fecaca;
}
.badge-yellow {
  background:#422006;
  color:#facc15;
}
.badge-green {
  background:#022c22;
  color:#bbf7d0;
}

/* TABELAS */
.stDataFrame thead tr th {
  background:#111827 !important;
  color:#e5e7eb !important;
  font-size:11px !important;
  text-transform:uppercase;
}
.stDataFrame tbody tr:nth-child(odd) {
  background-color:#050505;
}
.stDataFrame tbody tr:nth-child(even) {
  background-color:#0a0a0a;
}

/* TABS */
.stTabs [data-baseweb="tab-list"] {
  gap: 4px;
}
.stTabs [data-baseweb="tab"] {
  padding: 4px 12px;
  border-radius:999px;
  background:#050505;
  color:#9ca3af;
  border:1px solid transparent;
}
.stTabs [aria-selected="true"] {
  background:#111111;
  color:#f9fafb !important;
  border-color:var(--accent-soft);
}

/* INPUTS */
[data-baseweb="input"], [data-baseweb="select"], .stSelectbox, .stTextInput {
  background:#050505 !important;
}

/* HR */
hr { border-color:#1f2933 !important; }
</style>
"""
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

# --------------------------------------------------
# TOPO
# --------------------------------------------------
st.markdown(
    """
<div class="topbar">
  <div style="display:flex; align-items:center; gap:12px;">
    <div class="logo-pill">LI</div>
    <div>
      <div class="top-title">Loja Importados – Painel FIFO</div>
      <div class="top-subtitle">Estoque, custo e lucro por produto, em preto básico sem firula.</div>
    </div>
  </div>
  <div class="top-right-badge">
    <div class="top-chip">📂 Planilha conectada <span>Google Sheets</span></div>
    <div>Modo: <b>FIFO</b> (base: compras ENTREGUE)</div>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

# --------------------------------------------------
# HELPERS
# --------------------------------------------------
def parse_money(x):
    """Converte valores da planilha para float em reais com saneamento."""
    if isinstance(x, (int, float)):
        if pd.isna(x):
            return 0.0
        return float(x)

    if pd.isna(x):
        return 0.0

    s = str(x).strip()
    if s == "" or s.lower() == "nan":
        return 0.0

    s = s.replace("R$", "").replace("r$", "").replace(" ", "")

    digits = "".join(ch for ch in s if ch.isdigit())
    if len(digits) >= 12 and ("," not in s and "." not in s):
        return 0.0

    if "." in s and "," in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")

    try:
        return float(s)
    except Exception:
        return 0.0


def format_reais(v):
    try:
        v = float(v)
    except Exception:
        return "R$ 0,00"
    s = f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {s}"


def detectar_linha_cabecalho(df_raw: pd.DataFrame, must_have):
    # AQUI AJEITADO: procura até 200 linhas (antes era só 20)
    max_linhas = min(200, len(df_raw))
    for i in range(max_linhas):
        linha = " ".join([str(x).upper() for x in df_raw.iloc[i].tolist()])
        if all(pal in linha for pal in must_have):
            return i
    return None


def limpar_aba(xls, nome_aba):
    df_raw = pd.read_excel(xls, sheet_name=nome_aba, header=None)

    if nome_aba.upper() == "COMPRAS":
        must_have = ["DATA", "PRODUTO", "STATUS", "QUANT", "CUSTO"]
    elif nome_aba.upper() == "VENDAS":
        must_have = ["DATA", "PRODUTO", "QTD", "VALOR"]
    else:
        must_have = ["DATA", "PRODUTO"]

    linha_header = detectar_linha_cabecalho(df_raw, must_have)

    if linha_header is None:
        linha_header = 0

    cabecalho = df_raw.iloc[linha_header]
    df = df_raw.iloc[linha_header + 1 :].copy()
    df.columns = [str(c).strip().upper() for c in cabecalho]
    df = df.loc[:, ~df.isna().all()]
    df = df.dropna(how="all").reset_index(drop=True)
    return df


@st.cache_data
def carregar_dados():
    xls = pd.ExcelFile(URL_PLANILHA)
    df_compras = limpar_aba(xls, "COMPRAS")
    df_vendas = limpar_aba(xls, "VENDAS")
    return df_compras, df_vendas


# --------------------------------------------------
# FIFO
# --------------------------------------------------
def calcular_fifo(df_compras_raw: pd.DataFrame, df_vendas_raw: pd.DataFrame):
    compras = df_compras_raw.copy()
    vendas = df_vendas_raw.copy()

    compras.columns = [c.strip().upper() for c in compras.columns]
    vendas.columns = [c.strip().upper() for c in vendas.columns]

    cols_compras_obrig = ["DATA", "PRODUTO", "STATUS", "QUANTIDADE", "CUSTO UNITÁRIO"]
    cols_vendas_obrig = ["DATA", "PRODUTO", "QTD", "VALOR TOTAL"]

    faltando_compras = [c for c in cols_compras_obrig if c not in compras.columns]
    faltando_vendas = [c for c in cols_vendas_obrig if c not in vendas.columns]

    if faltando_compras:
        st.error(
            f"Aba COMPRAS após limpeza ainda está sem colunas: {faltando_compras}. "
            f"Colunas atuais: {list(compras.columns)}"
        )
        st.stop()
    if faltando_vendas:
        st.error(
            f"Aba VENDAS após limpeza ainda está sem colunas: {faltando_vendas}. "
            f"Colunas atuais: {list(vendas.columns)}"
        )
        st.stop()

    compras = compras[compras["STATUS"].astype(str).str.upper() == "ENTREGUE"].copy()
    if compras.empty:
        st.warning("Nenhuma compra com STATUS = ENTREGUE encontrada.")
        return pd.DataFrame(), pd.DataFrame()

    compras["DATA"] = pd.to_datetime(compras["DATA"], errors="coerce", dayfirst=True)
    vendas["DATA"] = pd.to_datetime(vendas["DATA"], errors="coerce", dayfirst=True)
    compras = compras.sort_values("DATA")
    vendas = vendas.sort_values("DATA")

    compras["QUANTIDADE"] = compras["QUANTIDADE"].apply(parse_money).astype(float)
    compras["CUSTO UNITÁRIO"] = compras["CUSTO UNITÁRIO"].apply(parse_money).astype(float)
    compras["CUSTO TOTAL"] = compras["QUANTIDADE"] * compras["CUSTO UNITÁRIO"]
    compras["CUSTO_UNIT_CALC"] = compras["CUSTO TOTAL"] / compras["QUANTIDADE"].replace(0, pd.NA)

    compras = compras[
        (compras["CUSTO_UNIT_CALC"].notna())
        & (compras["CUSTO_UNIT_CALC"] >= 0)
        & (compras["CUSTO_UNIT_CALC"] <= CUSTO_MAX_PLAUSIVEL)
    ].copy()

    if compras.empty:
        st.warning("Todas as linhas de COMPRAS ficaram inválidas após o filtro de custo.")
        return pd.DataFrame(), pd.DataFrame()

    vendas["QTD"] = vendas["QTD"].apply(parse_money).astype(float)
    vendas["VALOR TOTAL"] = vendas["VALOR TOTAL"].apply(parse_money).astype(float)

    estoque = {}
    for _, row in compras.iterrows():
        produto = str(row["PRODUTO"])
        qtd = float(row["QUANTIDADE"])
        if qtd <= 0:
            continue
        custo_unit = float(row["CUSTO_UNIT_CALC"])

        if produto not in estoque:
            estoque[produto] = []
        estoque[produto].append({"qtd": qtd, "custo": custo_unit})

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
            custo_total = 0.0

        registros_venda.append(
            {
                "DATA": data_venda,
                "PRODUTO": produto,
                "QTD": qtd_venda,
                "VALOR_TOTAL": valor_total,
                "CUSTO_TOTAL": custo_total,
                "CLIENTE": row.get("CLIENTE"),
                "STATUS": row.get("STATUS"),
            }
        )

    df_fifo = pd.DataFrame(registros_venda)
    df_fifo["CUSTO_UNIT"] = df_fifo["CUSTO_TOTAL"] / df_fifo["QTD"].replace(0, pd.NA)

    mask_insano = df_fifo["CUSTO_UNIT"] > CUSTO_MAX_PLAUSIVEL
    df_fifo.loc[mask_insano, "CUSTO_TOTAL"] = 0.0
    df_fifo.loc[mask_insano, "CUSTO_UNIT"] = 0.0

    df_fifo["LUCRO"] = df_fifo["VALOR_TOTAL"] - df_fifo["CUSTO_TOTAL"]
    df_fifo["MES_ANO"] = df_fifo["DATA"].dt.strftime("%Y-%m")

    estoque_reg = []
    for produto, lotes in estoque.items():
        saldo = sum(l["qtd"] for l in lotes)
        if saldo <= 0:
            continue
        valor = sum(l["qtd"] * l["custo"] for l in lotes)
        custo_medio = valor / saldo if saldo else 0.0
        estoque_reg.append(
            {
                "PRODUTO": produto,
                "SALDO_QTD": saldo,
                "VALOR_ESTOQUE": valor,
                "CUSTO_MEDIO_FIFO": custo_medio,
            }
        )
    df_estoque = pd.DataFrame(estoque_reg)

    return df_fifo, df_estoque


# --------------------------------------------------
# CARREGAMENTO + BOTÃO ATUALIZAR
# --------------------------------------------------
col_btn, _ = st.columns([1, 4])
with col_btn:
    if st.button("🔄 Atualizar dados da planilha"):
        st.cache_data.clear()
        st.rerun()

df_compras, df_vendas = carregar_dados()
df_fifo, df_estoque = calcular_fifo(df_compras, df_vendas)

if df_fifo.empty:
    st.warning("Não foi possível calcular FIFO (sem vendas ou sem compras ENTREGUE válidas).")
    st.stop()

# --------------------------------------------------
# TABS
# --------------------------------------------------
tab_dash, tab_search, tab_alerts, tab_compras = st.tabs(
    ["📊 Dashboard", "🔎 Pesquisa de produto", "⚠️ Alertas", "🧾 Compras"]
)

# --------------------------------------------------
# TAB 1 – DASHBOARD
# --------------------------------------------------
with tab_dash:
    st.markdown(
        """
<div class="section-title">Visão geral do período selecionado</div>
<div class="section-sub">Resumo financeiro real, já considerando custo FIFO.</div>
""",
        unsafe_allow_html=True,
    )

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

    qtd_total = df_fifo_filt["QTD"].sum()
    total_vendido = df_fifo_filt["VALOR_TOTAL"].sum()
    total_custo = df_fifo_filt["CUSTO_TOTAL"].sum()
    total_lucro = df_fifo_filt["LUCRO"].sum()
    ticket_medio = total_vendido / qtd_total if qtd_total else 0.0
    num_vendas = len(df_fifo_filt)

    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        st.markdown(
            f"""
<div class="kpi-card">
  <div class="kpi-label">Faturamento</div>
  <div class="kpi-value">{format_reais(total_vendido)}</div>
  <div class="kpi-pill">Somatório de VALOR TOTAL</div>
</div>
""",
            unsafe_allow_html=True,
        )
    with k2:
        st.markdown(
            f"""
<div class="kpi-card">
  <div class="kpi-label">Custo (FIFO)</div>
  <div class="kpi-value">{format_reais(total_custo)}</div>
  <div class="kpi-pill">Somatório de CUSTO_TOTAL</div>
</div>
""",
            unsafe_allow_html=True,
        )
    with k3:
        cor_lucro = "badge-green" if total_lucro >= 0 else "badge-red"
        st.markdown(
            f"""
<div class="kpi-card">
  <div class="kpi-label">Lucro (FIFO)</div>
  <div class="kpi-value">{format_reais(total_lucro)}</div>
  <div class="kpi-pill"><span class="badge-soft {cor_lucro}">Lucro = Venda − Custo FIFO</span></div>
</div>
""",
            unsafe_allow_html=True,
        )
    with k4:
        st.markdown(
            f"""
<div class="kpi-card">
  <div class="kpi-label">Ticket médio</div>
  <div class="kpi-value">{format_reais(ticket_medio)}</div>
  <div class="kpi-pill">Faturamento / Qtd. total vendida</div>
</div>
""",
            unsafe_allow_html=True,
        )
    with k5:
        st.markdown(
            f"""
<div class="kpi-card">
  <div class="kpi-label">Nº de vendas</div>
  <div class="kpi-value">{num_vendas}</div>
  <div class="kpi-pill">Registros de venda no filtro</div>
</div>
""",
            unsafe_allow_html=True,
        )

    # Valor de estoque total (FIFO) e compras no período
    if not df_estoque.empty and "VALOR_ESTOQUE" in df_estoque.columns:
        valor_estoque_total = df_estoque["VALOR_ESTOQUE"].sum()
    else:
        valor_estoque_total = 0.0

    dfc = df_compras.copy()
    dfc.columns = [c.strip().upper() for c in dfc.columns]

    if "DATA" in dfc.columns:
        dfc["DATA"] = pd.to_datetime(dfc["DATA"], errors="coerce", dayfirst=True)
        dfc["MES_ANO"] = dfc["DATA"].dt.strftime("%Y-%m")
    if "STATUS" in dfc.columns:
        dfc = dfc[dfc["STATUS"].astype(str).str.upper() == "ENTREGUE"].copy()

    if "QUANTIDADE" in dfc.columns:
        dfc["QUANTIDADE"] = dfc["QUANTIDADE"].apply(parse_money).astype(float)
    if "CUSTO UNITÁRIO" in dfc.columns:
        dfc["CUSTO UNITÁRIO"] = dfc["CUSTO UNITÁRIO"].apply(parse_money).astype(float)

    dfc["CUSTO_TOTAL"] = dfc.get("QUANTIDADE", 0) * dfc.get("CUSTO UNITÁRIO", 0)

    if mes_selecionado == "Todos":
        total_compras_periodo = dfc["CUSTO_TOTAL"].sum()
    else:
        total_compras_periodo = dfc.loc[dfc["MES_ANO"] == mes_selecionado, "CUSTO_TOTAL"].sum()

    st.markdown(
        f"""
<div class="kpi-row">
  <div class="kpi-card">
    <div class="kpi-label">Valor do estoque (FIFO)</div>
    <div class="kpi-value">{format_reais(valor_estoque_total)}</div>
    <div class="kpi-pill">Soma do valor em estoque de todos os produtos (custo FIFO)</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-label">Compras no período</div>
    <div class="kpi-value">{format_reais(total_compras_periodo)}</div>
    <div class="kpi-pill">Somatório de compras com STATUS = ENTREGUE no filtro</div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # Top produtos mais vendidos
    st.markdown(
        """
<div class="section-title">🥇 Produtos mais vendidos</div>
<div class="section-sub">Top 6 produtos por quantidade vendida, com custo FIFO, preço médio de venda e estoque atual.</div>
""",
        unsafe_allow_html=True,
    )

    if df_fifo_filt.empty:
        st.info("Nenhuma venda no período selecionado para montar o ranking de produtos.")
    else:
        top_prod = (
            df_fifo_filt.groupby("PRODUTO", as_index=False)
            .agg(
                QTD_VENDIDA=("QTD", "sum"),
                RECEITA=("VALOR_TOTAL", "sum"),
                CUSTO=("CUSTO_TOTAL", "sum"),
                LUCRO=("LUCRO", "sum"),
            )
        )

        if not df_estoque.empty:
            top_prod = top_prod.merge(
                df_estoque[["PRODUTO", "SALDO_QTD"]],
                on="PRODUTO",
                how="left",
            )
        else:
            top_prod["SALDO_QTD"] = 0

        top_prod["SALDO_QTD"] = top_prod["SALDO_QTD"].fillna(0)
        top_prod["CUSTO_MEDIO_FIFO"] = top_prod["CUSTO"] / top_prod["QTD_VENDIDA"].replace(0, pd.NA)
        top_prod["PRECO_MEDIO_VENDA"] = top_prod["RECEITA"] / top_prod["QTD_VENDIDA"].replace(0, pd.NA)

        top_view = top_prod.sort_values("QTD_VENDIDA", ascending=False).head(6).copy()
        top_view["LABEL"] = top_view.apply(
            lambda r: f"{int(r['QTD_VENDIDA'])} un\n{format_reais(r['RECEITA'])}",
            axis=1,
        )

        fig_top = px.bar(
            top_view,
            x="PRODUTO",
            y="QTD_VENDIDA",
            text="LABEL",
            labels={"PRODUTO": "Produto", "QTD_VENDIDA": "Qtd vendida"},
            color="QTD_VENDIDA",
            color_continuous_scale=["#1f2937", "#22c55e"],
        )
        fig_top.update_traces(
            textposition="inside",
            texttemplate="<b>%{text}</b>",
            insidetextanchor="middle",
            textfont_size=13,
        )
        fig_top.update_layout(
            height=360,
            plot_bgcolor="#050505",
            paper_bgcolor="#050505",
            font=dict(
                family="system-ui, -apple-system, 'Segoe UI', sans-serif",
                color="#e5e5e5",
            ),
            coloraxis_showscale=False,
            uniformtext_minsize=10,
            uniformtext_mode="hide",
        )
        st.plotly_chart(fig_top, use_container_width=True)

        top_view["CUSTO_MEDIO_FIFO_FMT"] = top_view["CUSTO_MEDIO_FIFO"].map(format_reais)
        top_view["PRECO_MEDIO_VENDA_FMT"] = top_view["PRECO_MEDIO_VENDA"].map(format_reais)
        top_view["LUCRO_FMT"] = top_view["LUCRO"].map(format_reais)
        top_view["RECEITA_FMT"] = top_view["RECEITA"].map(format_reais)

        tabela_top = top_view[
            [
                "PRODUTO",
                "QTD_VENDIDA",
                "SALDO_QTD",
                "CUSTO_MEDIO_FIFO_FMT",
                "PRECO_MEDIO_VENDA_FMT",
                "RECEITA_FMT",
                "LUCRO_FMT",
            ]
        ].rename(
            columns={
                "PRODUTO": "Produto",
                "QTD_VENDIDA": "Qtd vendida",
                "SALDO_QTD": "Estoque atual",
                "CUSTO_MEDIO_FIFO_FMT": "Custo médio FIFO (unid.)",
                "PRECO_MEDIO_VENDA_FMT": "Preço médio venda (unid.)",
                "RECEITA_FMT": "Receita total",
                "LUCRO_FMT": "Lucro total (FIFO)",
            }
        )

        st.dataframe(tabela_top, use_container_width=True)

        # ----------------------------------------
        # INDICADOR DE PRODUTOS ÂNCORA
        # ----------------------------------------
        st.markdown(
            """
<div class="section-title">🧱 Produtos âncora da loja</div>
<div class="section-sub">
Produtos que vendem bem, trazem boa margem e sustentam grande parte da receita.
</div>
""",
            unsafe_allow_html=True,
        )

        # margem em %
        top_prod["MARGEM_PCT"] = (top_prod["LUCRO"] / top_prod["RECEITA"].replace(0, pd.NA)) * 100

        # critérios (ajustáveis se quiser depois)
        ANC_MIN_QTD = 10        # mínimo de unidades vendidas no período
        ANC_MIN_RECEITA = 500   # receita mínima no período
        ANC_MIN_MARGEM = 20.0   # margem mínima em %

        ancora = top_prod[
            (top_prod["QTD_VENDIDA"] >= ANC_MIN_QTD)
            & (top_prod["RECEITA"] >= ANC_MIN_RECEITA)
            & (top_prod["MARGEM_PCT"] >= ANC_MIN_MARGEM)
        ].copy()

        if ancora.empty:
            st.info(
                "Nenhum produto bateu todos os critérios de âncora nesse período "
                f"(≥ {ANC_MIN_QTD} un, ≥ {format_reais(ANC_MIN_RECEITA)} em vendas e margem ≥ {ANC_MIN_MARGEM:.0f}%)."
            )
        else:
            ancora["RECEITA_FMT"] = ancora["RECEITA"].map(format_reais)
            ancora["LUCRO_FMT"] = ancora["LUCRO"].map(format_reais)
            ancora["MARGEM_PCT_FMT"] = ancora["MARGEM_PCT"].map(lambda x: f"{x:.1f}%")

            tabela_ancora = ancora.sort_values("RECEITA", ascending=False)[
                [
                    "PRODUTO",
                    "QTD_VENDIDA",
                    "SALDO_QTD",
                    "RECEITA_FMT",
                    "LUCRO_FMT",
                    "MARGEM_PCT_FMT",
                ]
            ].rename(
                columns={
                    "PRODUTO": "Produto",
                    "QTD_VENDIDA": "Qtd vendida",
                    "SALDO_QTD": "Estoque atual",
                    "RECEITA_FMT": "Receita período",
                    "LUCRO_FMT": "Lucro período",
                    "MARGEM_PCT_FMT": "Margem (%)",
                }
            )

            st.dataframe(tabela_ancora, use_container_width=True)

            st.markdown(
                """
- Esses são os itens que **mais carregam a loja** em volume + margem.
- Ideias:
  - destaque em anúncios,
  - vitrine,
  - kits,
  - e cuidado para não deixar zerar estoque.
                """
            )

    st.markdown("---")

    # Gráfico mensal (mês atual + 2 anteriores)
    st.markdown(
        """
<div class="section-title">📊 Faturamento – mês atual e 2 anteriores</div>
<div class="section-sub">Valores em real dentro das colunas, com o mês atual em destaque.</div>
""",
        unsafe_allow_html=True,
    )

    df_mes = df_fifo.dropna(subset=["MES_ANO"]).copy()
    if df_mes.empty:
        st.info("Sem dados suficientes para montar o gráfico mensal.")
    else:
        resumo_mes = (
            df_mes.groupby("MES_ANO", as_index=False)[["VALOR_TOTAL", "LUCRO"]]
            .sum()
            .sort_values("MES_ANO")
        )

        meses_unicos = resumo_mes["MES_ANO"].tolist()
        if not meses_unicos:
            st.info("Sem meses para exibir no gráfico.")
        else:
            mes_atual_data = pd.Timestamp.now().strftime("%Y-%m")
            if mes_atual_data in meses_unicos:
                idx_atual = meses_unicos.index(mes_atual_data)
                start_idx = max(0, idx_atual - 2)
                meses_plot = meses_unicos[start_idx : idx_atual + 1]
            else:
                meses_plot = meses_unicos[-3:]

            resumo_mes = resumo_mes[resumo_mes["MES_ANO"].isin(meses_plot)]
            resumo_mes = resumo_mes.sort_values("MES_ANO")

            resumo_mes["VALOR_TOTAL_FMT"] = resumo_mes["VALOR_TOTAL"].map(format_reais)
            resumo_mes["TIPO_MES"] = resumo_mes["MES_ANO"].apply(
                lambda m: "Mês atual" if m == mes_atual_data else "Anterior"
            )

            fig = px.bar(
                resumo_mes,
                x="MES_ANO",
                y="VALOR_TOTAL",
                text="VALOR_TOTAL_FMT",
                labels={"MES_ANO": "Mês", "VALOR_TOTAL": "Faturamento"},
                color="TIPO_MES",
                color_discrete_map={
                    "Mês atual": "#22c55e",
                    "Anterior": "#4b5563",
                },
            )
            fig.update_traces(
                textposition="inside",
                texttemplate="<b>%{text}</b>",
                insidetextanchor="middle",
                textfont_size=13,
            )
            fig.update_layout(
                height=360,
                yaxis_title="Faturamento (R$)",
                xaxis_title="Mês",
                uniformtext_minsize=10,
                uniformtext_mode="hide",
                plot_bgcolor="#050505",
                paper_bgcolor="#050505",
                font=dict(
                    family="system-ui, -apple-system, 'Segoe UI', sans-serif",
                    color="#e5e5e5",
                ),
                legend_title_text="",
            )
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Vendas detalhadas + explicação FIFO
    st.markdown(
        """
<div class="section-title">🧾 Vendas detalhadas (com custo FIFO)</div>
<div class="section-sub">Cada linha já traz o custo correto de acordo com o giro do estoque.</div>
""",
        unsafe_allow_html=True,
    )

    df_fifo_view = df_fifo_filt.copy()
    if not df_fifo_view.empty:
        df_fifo_view["CUSTO_UNIT"] = df_fifo_view["CUSTO_TOTAL"] / df_fifo_view["QTD"].replace(0, pd.NA)

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

        cols_ordem = [
            "DATA",
            "PRODUTO",
            "CLIENTE",
            "STATUS",
            "QTD",
            "VALOR_TOTAL",
            "CUSTO_TOTAL",
            "CUSTO_UNIT",
            "LUCRO",
            "MES_ANO",
        ]
        cols_ordem = [c for c in cols_ordem if c in df_fifo_view.columns]

        st.dataframe(
            df_fifo_view[cols_ordem].sort_values("DATA", ascending=False),
            use_container_width=True,
        )

        st.markdown("#### 📘 Como o FIFO é calculado (exemplo real)")
        st.markdown(
            f"""
**Produto do exemplo:** `{prod_ex}`  

- Quantidade vendida: **{qtd_ex:.0f} unid.**  
- Valor da venda: **{venda_ex}**  
- Custo total FIFO dessa venda: **{custo_total_ex}**  
- Custo unitário FIFO: **{custo_unit_ex}**  
- Lucro nessa venda: **{lucro_ex}**  

**Lógica resumida:**

1. Buscamos todas as **compras de `{prod_ex}` com STATUS = ENTREGUE**, em ordem de data (mais antigas primeiro).
2. Cada compra vira um **lote** com quantidade e custo unitário.
3. Quando essa venda de **{qtd_ex:.0f} unid.** acontece, consumimos primeiro o lote mais antigo, depois o próximo, até completar a quantidade.
4. O **custo total FIFO** é a soma dos custos desses lotes “comidos” pela venda.
5. O **custo unitário FIFO** é o custo total dividido pela quantidade vendida.
6. O **lucro** é sempre: **venda − custo FIFO**.
            """
        )
    else:
        st.info("Nenhuma venda no período selecionado.")

# --------------------------------------------------
# TAB 2 – PESQUISA DE PRODUTO
# --------------------------------------------------
with tab_search:
    st.markdown(
        """
<div class="section-title">🔎 Pesquisa de produto – baseado no FIFO</div>
<div class="section-sub">Veja custo médio, margem, histórico de vendas e histórico de compras.</div>
""",
        unsafe_allow_html=True,
    )

    if df_fifo.empty and df_estoque.empty:
        st.info("Sem dados de estoque ou vendas para pesquisar.")
    else:
        produtos_estoque = df_estoque["PRODUTO"].unique().tolist() if not df_estoque.empty else []
        produtos_vendas = df_fifo["PRODUTO"].unique().tolist() if not df_fifo.empty else []
        todos_produtos = sorted(set(produtos_estoque) | set(produtos_vendas))

        prod_sel = st.selectbox(
            "Escolha o produto:",
            options=["(selecione)"] + todos_produtos,
            index=0,
        )

        if prod_sel != "(selecione)":
            # --- Estoque + vendas agregadas ---
            linha_est = df_estoque[df_estoque["PRODUTO"] == prod_sel]
            if not linha_est.empty:
                saldo = float(linha_est["SALDO_QTD"].iloc[0])
                valor_estoque = float(linha_est["VALOR_ESTOQUE"].iloc[0])
                custo_medio_fifo = float(linha_est["CUSTO_MEDIO_FIFO"].iloc[0])
            else:
                saldo = 0.0
                valor_estoque = 0.0
                custo_medio_fifo = 0.0

            vendas_prod = df_fifo[df_fifo["PRODUTO"] == prod_sel].copy()
            if not vendas_prod.empty:
                qtd_total_vendida = vendas_prod["QTD"].sum()
                receita_total = vendas_prod["VALOR_TOTAL"].sum()
                preco_medio_venda = receita_total / qtd_total_vendida if qtd_total_vendida else 0.0
                custo_total_hist = vendas_prod["CUSTO_TOTAL"].sum()
                margem_media = (receita_total - custo_total_hist) / receita_total if receita_total else 0.0

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

            st.markdown(f"### 📦 {prod_sel}")

            cA, cB, cC = st.columns(3)
            with cA:
                st.markdown(
                    f"""
<div class="kpi-card">
  <div class="kpi-label">Custo médio FIFO</div>
  <div class="kpi-value">{format_reais(custo_medio_fifo)}</div>
  <div class="kpi-pill">Baseado nas compras ENTREGUE restantes em estoque</div>
</div>
""",
                    unsafe_allow_html=True,
                )
            with cB:
                st.markdown(
                    f"""
<div class="kpi-card">
  <div class="kpi-label">Preço médio de venda</div>
  <div class="kpi-value">{format_reais(preco_medio_venda)}</div>
  <div class="kpi-pill">Receita total / quantidade vendida</div>
</div>
""",
                    unsafe_allow_html=True,
                )
            with cC:
                st.markdown(
                    f"""
<div class="kpi-card">
  <div class="kpi-label">Margem média histórica</div>
  <div class="kpi-value">{margem_media*100:,.1f}%</div>
  <div class="kpi-pill">({format_reais(receita_total)} − {format_reais(custo_total_hist)}) / receita</div>
</div>
""",
                    unsafe_allow_html=True,
                )

            cD, cE, cF = st.columns(3)
            with cD:
                st.markdown(
                    f"""
<div class="kpi-card">
  <div class="kpi-label">Saldo em estoque</div>
  <div class="kpi-value">{int(saldo)} unid.</div>
  <div class="kpi-pill">Valor em estoque: {format_reais(valor_estoque)}</div>
</div>
""",
                    unsafe_allow_html=True,
                )
            with cE:
                st.markdown(
                    f"""
<div class="kpi-card">
  <div class="kpi-label">Receita acumulada</div>
  <div class="kpi-value">{format_reais(receita_total)}</div>
  <div class="kpi-pill">Total vendido no histórico</div>
</div>
""",
                    unsafe_allow_html=True,
                )
            with cF:
                st.markdown(
                    f"""
<div class="kpi-card">
  <div class="kpi-label">Qtd total vendida</div>
  <div class="kpi-value">{int(qtd_total_vendida)} unid.</div>
  <div class="kpi-pill">Somatório das vendas registradas</div>
</div>
""",
                    unsafe_allow_html=True,
                )

            st.markdown("---")

            # --- Última venda ---
            st.markdown("#### 🕒 Última venda")
            if data_ultima is not None and pd.notna(data_ultima):
                st.write(
                    f"- Data: **{data_ultima.strftime('%d/%m/%Y')}**  \n"
                    f"- Preço unitário na venda: **{format_reais(preco_unit_ultima)}**  \n"
                    f"- Quantidade nessa venda: **{int(ultima['QTD'])} unid.**  \n"
                    f"- Valor total: **{format_reais(ultima['VALOR_TOTAL'])}**"
                )
            else:
                st.write("Nenhuma venda registrada para esse produto ainda.")

            st.markdown("---")
            st.markdown("#### 📄 Histórico recente de vendas")

            # --- Histórico de vendas do produto ---
            if not vendas_prod.empty:
                vendas_prod_hist = vendas_prod.copy()
                vendas_prod_hist["CUSTO_UNIT"] = (
                    vendas_prod_hist["CUSTO_TOTAL"] / vendas_prod_hist["QTD"].replace(0, pd.NA)
                )
                vendas_prod_hist["DATA"] = vendas_prod_hist["DATA"].dt.strftime("%d/%m/%Y")
                vendas_prod_hist["VALOR_TOTAL"] = vendas_prod_hist["VALOR_TOTAL"].map(format_reais)
                vendas_prod_hist["CUSTO_TOTAL"] = vendas_prod_hist["CUSTO_TOTAL"].map(format_reais)
                vendas_prod_hist["LUCRO"] = vendas_prod_hist["LUCRO"].map(format_reais)
                vendas_prod_hist["CUSTO_UNIT"] = vendas_prod_hist["CUSTO_UNIT"].map(format_reais)

                cols_hist = [
                    "DATA",
                    "QTD",
                    "VALOR_TOTAL",
                    "CUSTO_TOTAL",
                    "CUSTO_UNIT",
                    "LUCRO",
                    "MES_ANO",
                ]
                cols_hist = [c for c in cols_hist if c in vendas_prod_hist.columns]

                st.dataframe(
                    vendas_prod_hist[cols_hist].sort_values("DATA", ascending=False).head(30),
                    use_container_width=True,
                )
            else:
                st.info("Sem histórico de vendas para esse produto.")

            # --- Histórico de compras do produto ---
            st.markdown("---")
            st.markdown("#### 🧾 Histórico de compras (ENTREGUE)")

            compras_prod = df_compras.copy()
            compras_prod.columns = [c.strip().upper() for c in compras_prod.columns]

            if "PRODUTO" in compras_prod.columns:
                compras_prod = compras_prod[compras_prod["PRODUTO"] == prod_sel].copy()
            else:
                compras_prod = pd.DataFrame()

            if not compras_prod.empty and "STATUS" in compras_prod.columns:
                compras_prod = compras_prod[
                    compras_prod["STATUS"].astype(str).str.upper() == "ENTREGUE"
                ].copy()

            if compras_prod.empty:
                st.info("Nenhuma compra ENTREGUE registrada para esse produto.")
            else:
                if "DATA" in compras_prod.columns:
                    compras_prod["DATA"] = pd.to_datetime(
                        compras_prod["DATA"], errors="coerce", dayfirst=True
                    )
                    compras_prod = compras_prod.sort_values("DATA", ascending=False)
                    compras_prod["DATA_FMT"] = compras_prod["DATA"].dt.strftime("%d/%m/%Y")
                else:
                    compras_prod["DATA_FMT"] = ""

                if "QUANTIDADE" in compras_prod.columns:
                    compras_prod["QUANTIDADE"] = compras_prod["QUANTIDADE"].apply(parse_money).astype(float)
                else:
                    compras_prod["QUANTIDADE"] = 0.0

                if "CUSTO UNITÁRIO" in compras_prod.columns:
                    compras_prod["CUSTO UNITÁRIO"] = compras_prod["CUSTO UNITÁRIO"].apply(parse_money).astype(float)
                else:
                    compras_prod["CUSTO UNITÁRIO"] = 0.0

                compras_prod["CUSTO_TOTAL"] = compras_prod.get("CUSTO_TOTAL", compras_prod["QUANTIDADE"] * compras_prod["CUSTO UNITÁRIO"])

                compras_prod["CUSTO_UNIT_FMT"] = compras_prod["CUSTO UNITÁRIO"].map(format_reais)
                compras_prod["CUSTO_TOTAL_FMT"] = compras_prod["CUSTO_TOTAL"].map(format_reais)

                total_qtd_comp = compras_prod["QUANTIDADE"].sum()
                total_valor_comp = compras_prod["CUSTO_TOTAL"].sum()

                st.write(
                    f"- Total comprado (histórico ENTREGUE): **{int(total_qtd_comp)} unid.**  "
                    f"– **{format_reais(total_valor_comp)}**"
                )

                cols_comp = ["DATA_FMT", "STATUS", "QUANTIDADE", "CUSTO_UNIT_FMT", "CUSTO_TOTAL_FMT"]
                cols_comp = [c for c in cols_comp if c in compras_prod.columns]

                st.dataframe(
                    compras_prod[cols_comp].rename(
                        columns={
                            "DATA_FMT": "Data",
                            "STATUS": "Status",
                            "QUANTIDADE": "Qtd.",
                            "CUSTO_UNIT_FMT": "Custo unitário",
                            "CUSTO_TOTAL_FMT": "Custo total",
                        }
                    ).head(40),
                    use_container_width=True,
                )

            st.markdown("---")
            st.markdown("#### 💡 Leitura rápida")
            st.markdown(
                f"""
- Se o **custo médio FIFO** está muito próximo do **preço médio de venda**, esse item merece atenção no preço ou na compra.
- Se a **margem média** é boa, mas o estoque está baixo, é candidato forte para reposição.
- Olhando o **histórico de compras**, você enxerga:
  - se está pagando mais caro ou mais barato ao longo do tempo,
  - se vale negociar de novo com o fornecedor,
  - e se não está enchendo estoque de um item que não gira tanto assim.
                """
            )
        else:
            st.info("Selecione um produto para ver os detalhes baseados no FIFO.")

# --------------------------------------------------
# TAB 3 – ALERTAS + SAÚDE DA LOJA
# --------------------------------------------------
with tab_alerts:
    st.markdown(
        """
<div class="section-title">⚠️ Alertas de estoque</div>
<div class="section-sub">Veja o que está vendendo forte com pouco estoque e o que está encalhado.</div>
""",
        unsafe_allow_html=True,
    )

    if df_estoque.empty:
        st.info("Sem dados de estoque para gerar alertas.")
    else:
        LIM_VENDE_BEM = st.slider("Vende bem a partir de (unid.)", 5, 50, 10, 1)
        LIM_ESTOQUE_BAIXO = st.slider("Considerar estoque baixo abaixo de (unid.)", 1, 20, 3, 1)
        LIM_DIAS_PARADO = st.slider("Parado há mais de (dias)", 7, 180, 30, 1)

        # Base para "vendendo bem e com pouco estoque"
        vendas_tot = (
            df_fifo.groupby("PRODUTO", as_index=False)["QTD"]
            .sum()
            .rename(columns={"QTD": "QTD_VENDIDA_TOTAL"})
        )
        base_alerta = df_estoque.merge(vendas_tot, on="PRODUTO", how="left")
        base_alerta["QTD_VENDIDA_TOTAL"] = base_alerta["QTD_VENDIDA_TOTAL"].fillna(0)

        st.markdown("### 🔥 Vendendo bem e com pouco estoque")

        vendendo_bem_baixo_estoque = base_alerta[
            (base_alerta["QTD_VENDIDA_TOTAL"] >= LIM_VENDE_BEM)
            & (base_alerta["SALDO_QTD"] > 0)
            & (base_alerta["SALDO_QTD"] <= LIM_ESTOQUE_BAIXO)
        ].copy()

        if vendendo_bem_baixo_estoque.empty:
            st.info("Nenhum produto com vendas fortes e estoque muito baixo pelos critérios atuais.")
        else:
            df_vb = vendendo_bem_baixo_estoque.copy()
            df_vb["VALOR_ESTOQUE_FMT"] = df_vb["VALOR_ESTOQUE"].map(format_reais)
            df_vb = df_vb.sort_values(["SALDO_QTD", "QTD_VENDIDA_TOTAL"], ascending=[True, False])

            st.dataframe(
                df_vb[
                    ["PRODUTO", "SALDO_QTD", "QTD_VENDIDA_TOTAL", "VALOR_ESTOQUE_FMT"]
                ].rename(
                    columns={
                        "PRODUTO": "Produto",
                        "SALDO_QTD": "Estoque atual",
                        "QTD_VENDIDA_TOTAL": "Qtd vendida (histórico)",
                        "VALOR_ESTOQUE_FMT": "Valor em estoque (FIFO)",
                    }
                ),
                use_container_width=True,
            )

        st.markdown("### 🐌 Estoque parado há muito tempo")

        df_compras_alert = df_compras.copy()
        df_compras_alert.columns = [c.strip().upper() for c in df_compras_alert.columns]
        if "STATUS" in df_compras_alert.columns:
            df_compras_alert = df_compras_alert[
                df_compras_alert["STATUS"].astype(str).str.upper() == "ENTREGUE"
            ].copy()
        if "DATA" in df_compras_alert.columns:
            df_compras_alert["DATA"] = pd.to_datetime(
                df_compras_alert["DATA"], errors="coerce", dayfirst=True
            )

        df_vendas_alert = df_vendas.copy()
        df_vendas_alert.columns = [c.strip().upper() for c in df_vendas_alert.columns]
        if "DATA" in df_vendas_alert.columns:
            df_vendas_alert["DATA"] = pd.to_datetime(
                df_vendas_alert["DATA"], errors="coerce", dayfirst=True
            )

        if not df_vendas_alert.empty and "DATA" in df_vendas_alert.columns:
            last_sale = (
                df_vendas_alert.groupby("PRODUTO", as_index=False)["DATA"]
                .max()
                .rename(columns={"DATA": "ULT_VENDA"})
            )
        else:
            last_sale = pd.DataFrame(columns=["PRODUTO", "ULT_VENDA"])

        if not df_compras_alert.empty and "DATA" in df_compras_alert.columns:
            last_buy = (
                df_compras_alert.groupby("PRODUTO", as_index=False)["DATA"]
                .max()
                .rename(columns={"DATA": "ULT_COMPRA"})
            )
        else:
            last_buy = pd.DataFrame(columns=["PRODUTO", "ULT_COMPRA"])

        parado = (
            df_estoque.merge(last_sale, on="PRODUTO", how="left")
            .merge(last_buy, on="PRODUTO", how="left")
        )
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

        parado_filtrado = parado[
            (parado["DIAS_PARADO"].notna())
            & (parado["DIAS_PARADO"] >= LIM_DIAS_PARADO)
        ].copy()

        if parado_filtrado.empty:
            st.info(f"Nenhum produto com estoque parado há mais de {LIM_DIAS_PARADO} dias.")
        else:
            df_p = parado_filtrado.copy()
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
                df_p[
                    [
                        "PRODUTO",
                        "SALDO_QTD",
                        "VALOR_ESTOQUE_FMT",
                        "DIAS_PARADO",
                        "ULT_VENDA_FMT",
                        "ULT_COMPRA_FMT",
                    ]
                ].rename(
                    columns={
                        "PRODUTO": "Produto",
                        "SALDO_QTD": "Estoque atual",
                        "VALOR_ESTOQUE_FMT": "Valor em estoque (FIFO)",
                        "DIAS_PARADO": "Dias parado",
                        "ULT_VENDA_FMT": "Última venda",
                        "ULT_COMPRA_FMT": "Última compra (ENTREGUE)",
                    }
                ),
                use_container_width=True,
            )

        # ----------------------------------------
        # PAINEL SAÚDE DA LOJA
        # ----------------------------------------
        st.markdown("---")
        st.markdown(
            """
<div class="section-title">🩺 Saúde da loja</div>
<div class="section-sub">
Indicadores de concentração de vendas, estoque parado e risco de dependência em poucos produtos.
</div>
""",
            unsafe_allow_html=True,
        )

        # % do valor do estoque que está parado >= LIM_DIAS_PARADO
        valor_estoque_total_alert = df_estoque["VALOR_ESTOQUE"].sum() if "VALOR_ESTOQUE" in df_estoque.columns else 0.0
        valor_estoque_parado = parado_filtrado["VALOR_ESTOQUE"].sum() if "VALOR_ESTOQUE" in parado_filtrado.columns else 0.0
        pct_estoque_parado = (
            (valor_estoque_parado / valor_estoque_total_alert) * 100
            if valor_estoque_total_alert > 0
            else 0.0
        )

        # % da receita total concentrada nos 5 produtos com maior faturamento (histórico)
        receita_por_prod = (
            df_fifo.groupby("PRODUTO", as_index=False)["VALOR_TOTAL"]
            .sum()
            .rename(columns={"VALOR_TOTAL": "RECEITA_TOTAL"})
        )
        receita_total_geral = receita_por_prod["RECEITA_TOTAL"].sum()
        top5_receita = (
            receita_por_prod.sort_values("RECEITA_TOTAL", ascending=False)
            .head(5)["RECEITA_TOTAL"]
            .sum()
        )
        pct_receita_top5 = (
            (top5_receita / receita_total_geral) * 100 if receita_total_geral > 0 else 0.0
        )

        # % do valor do estoque concentrado em 5 produtos com maior valor de estoque
        if not df_estoque.empty and "VALOR_ESTOQUE" in df_estoque.columns:
            top5_estoque = (
                df_estoque.sort_values("VALOR_ESTOQUE", ascending=False)
                .head(5)["VALOR_ESTOQUE"]
                .sum()
            )
            pct_estoque_top5 = (
                (top5_estoque / valor_estoque_total_alert) * 100
                if valor_estoque_total_alert > 0
                else 0.0
            )
        else:
            pct_estoque_top5 = 0.0

        h1, h2, h3 = st.columns(3)
        with h1:
            st.markdown(
                f"""
<div class="kpi-card">
  <div class="kpi-label">Estoque parado</div>
  <div class="kpi-value">{pct_estoque_parado:,.1f}%</div>
  <div class="kpi-pill">
    Valor em estoque parado ≥ {LIM_DIAS_PARADO} dias / estoque total
  </div>
</div>
""",
                unsafe_allow_html=True,
            )
        with h2:
            st.markdown(
                f"""
<div class="kpi-card">
  <div class="kpi-label">Vendas concentradas</div>
  <div class="kpi-value">{pct_receita_top5:,.1f}%</div>
  <div class="kpi-pill">
    Receita vinda dos 5 produtos que mais faturam (histórico)
  </div>
</div>
""",
                unsafe_allow_html=True,
            )
        with h3:
            st.markdown(
                f"""
<div class="kpi-card">
  <div class="kpi-label">Estoque concentrado</div>
  <div class="kpi-value">{pct_estoque_top5:,.1f}%</div>
  <div class="kpi-pill">
    Valor do estoque nos 5 produtos mais caros em estoque
  </div>
</div>
""",
                unsafe_allow_html=True,
            )

        st.markdown(
            f"*Critérios atuais:* vende bem ≥ **{LIM_VENDE_BEM} unid.**, estoque baixo ≤ **{LIM_ESTOQUE_BAIXO} unid.**, parado ≥ **{LIM_DIAS_PARADO} dias**."
        )

# --------------------------------------------------
# TAB 4 – COMPRAS
# --------------------------------------------------
with tab_compras:
    st.markdown(
        """
<div class="section-title">🧾 Compras</div>
<div class="section-sub">
Visão das compras da loja por mês, com foco no que realmente importa para o caixa.
</div>
""",
        unsafe_allow_html=True,
    )

    dfc = df_compras.copy()
    dfc.columns = [c.strip().upper() for c in dfc.columns]

    if "DATA" not in dfc.columns:
        st.info("A aba COMPRAS da planilha precisa ter uma coluna 'DATA'.")
    else:
        dfc["DATA"] = pd.to_datetime(dfc["DATA"], errors="coerce", dayfirst=True)

        if "STATUS" in dfc.columns:
            dfc = dfc[dfc["STATUS"].astype(str).str.upper() == "ENTREGUE"].copy()

        if "QUANTIDADE" in dfc.columns:
            dfc["QUANTIDADE"] = dfc["QUANTIDADE"].apply(parse_money).astype(float)
        else:
            dfc["QUANTIDADE"] = 0.0

        if "CUSTO UNITÁRIO" in dfc.columns:
            dfc["CUSTO UNITÁRIO"] = dfc["CUSTO UNITÁRIO"].apply(parse_money).astype(float)
        else:
            dfc["CUSTO UNITÁRIO"] = 0.0

        dfc["CUSTO_TOTAL"] = dfc["QUANTIDADE"] * dfc["CUSTO UNITÁRIO"]
        dfc["MES_ANO"] = dfc["DATA"].dt.strftime("%Y-%m")

        if dfc["MES_ANO"].dropna().empty:
            st.info("Não encontrei compras com DATA válida para montar a aba de Compras.")
        else:
            meses_comp = ["Todos"]
            meses_disp_comp = sorted(
                dfc["MES_ANO"].dropna().unique().tolist(),
                reverse=True
            )
            meses_comp += meses_disp_comp

            mes_atual = pd.Timestamp.now().strftime("%Y-%m")
            idx_padrao_comp = meses_comp.index(mes_atual) if mes_atual in meses_comp else 0

            mes_sel_comp = st.selectbox(
                "Filtrar compras por mês (AAAA-MM):",
                meses_comp,
                index=idx_padrao_comp,
            )

            if mes_sel_comp == "Todos":
                dfc_filt = dfc.copy()
            else:
                dfc_filt = dfc[dfc["MES_ANO"] == mes_sel_comp].copy()

            if dfc_filt.empty:
                st.info("Não há compras no período selecionado.")
            else:
                total_compras = dfc_filt["CUSTO_TOTAL"].sum()
                qtd_total_comp = dfc_filt["QUANTIDADE"].sum()
                custo_medio_geral = (
                    total_compras / qtd_total_comp if qtd_total_comp > 0 else 0.0
                )
                num_prod_dif = (
                    dfc_filt["PRODUTO"].nunique()
                    if "PRODUTO" in dfc_filt.columns
                    else 0
                )

                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    st.markdown(
                        f"""
<div class="kpi-card">
  <div class="kpi-label">Total em compras</div>
  <div class="kpi-value">{format_reais(total_compras)}</div>
  <div class="kpi-pill">Somatório de CUSTO_TOTAL no período</div>
</div>
""",
                        unsafe_allow_html=True,
                    )
                with c2:
                    st.markdown(
                        f"""
<div class="kpi-card">
  <div class="kpi-label">Qtd comprada</div>
  <div class="kpi-value">{int(qtd_total_comp)} unid.</div>
  <div class="kpi-pill">Somatório de QUANTIDADE</div>
</div>
""",
                        unsafe_allow_html=True,
                    )
                with c3:
                    st.markdown(
                        f"""
<div class="kpi-card">
  <div class="kpi-label">Custo médio por unidade</div>
  <div class="kpi-value">{format_reais(custo_medio_geral)}</div>
  <div class="kpi-pill">CUSTO_TOTAL / QUANTIDADE</div>
</div>
""",
                        unsafe_allow_html=True,
                    )
                with c4:
                    st.markdown(
                        f"""
<div class="kpi-card">
  <div class="kpi-label">Produtos comprados</div>
  <div class="kpi-value">{num_prod_dif}</div>
  <div class="kpi-pill">Produtos diferentes no período</div>
</div>
""",
                        unsafe_allow_html=True,
                    )

                st.markdown("---")

                st.markdown(
                    """
<div class="section-title">📥 Top produtos comprados no período</div>
<div class="section-sub">
Veja onde está indo o dinheiro das compras, em quantidade e valor.
</div>
""",
                    unsafe_allow_html=True,
                )

                if "PRODUTO" in dfc_filt.columns:
                    top_comp = (
                        dfc_filt.groupby("PRODUTO", as_index=False)
                        .agg(
                            QTD_COMP=("QUANTIDADE", "sum"),
                            VALOR_COMP=("CUSTO_TOTAL", "sum"),
                        )
                        .sort_values("VALOR_COMP", ascending=False)
                    )

                    top_comp["VALOR_COMP_FMT"] = top_comp["VALOR_COMP"].map(format_reais)

                    st.dataframe(
                        top_comp.rename(
                            columns={
                                "PRODUTO": "Produto",
                                "QTD_COMP": "Qtd comprada",
                                "VALOR_COMP_FMT": "Valor em compras",
                            }
                        )[["Produto", "Qtd comprada", "Valor em compras"]]
                        .head(20),
                        use_container_width=True,
                    )
                else:
                    st.info("Não encontrei coluna 'PRODUTO' na aba de COMPRAS.")

                st.markdown("---")

                st.markdown(
                    """
<div class="section-title">🧾 Compras detalhadas</div>
<div class="section-sub">
Cada lançamento com data, produto, quantidade e custo.
</div>
""",
                    unsafe_allow_html=True,
                )

                dfc_view = dfc_filt.copy()

                dfc_view["DATA_FMT"] = dfc_view["DATA"].dt.strftime("%d/%m/%Y")
                dfc_view["CUSTO_UNIT_FMT"] = dfc_view["CUSTO UNITÁRIO"].map(format_reais)
                dfc_view["CUSTO_TOTAL_FMT"] = dfc_view["CUSTO_TOTAL"].map(format_reais)

                cols_comp = ["DATA_FMT"]
                if "PRODUTO" in dfc_view.columns:
                    cols_comp.append("PRODUTO")
                if "STATUS" in dfc_view.columns:
                    cols_comp.append("STATUS")
                cols_comp += ["QUANTIDADE", "CUSTO_UNIT_FMT", "CUSTO_TOTAL_FMT", "MES_ANO"]
                cols_comp = [c for c in cols_comp if c in dfc_view.columns]

                st.dataframe(
                    dfc_view[cols_comp]
                    .rename(
                        columns={
                            "DATA_FMT": "Data",
                            "PRODUTO": "Produto",
                            "STATUS": "Status",
                            "QUANTIDADE": "Qtd",
                            "CUSTO_UNIT_FMT": "Custo unitário",
                            "CUSTO_TOTAL_FMT": "Custo total",
                            "MES_ANO": "Mês/ano",
                        }
                    )
                    .sort_values("Data", ascending=False),
                    use_container_width=True,
                )
