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
# ESTILO GLOBAL (CSS) - versão mais "glass" e colorida
# --------------------------------------------------
GLOBAL_CSS = """
<style>
:root{
  --bg:#020617;
  --bg-elevated:#020617;
  --bg-card:rgba(15,23,42,0.90);
  --bg-card-soft:rgba(15,23,42,0.78);
  --border-soft:rgba(148,163,184,0.25);
  --accent:#22d3ee;
  --accent-soft:#0ea5e9;
  --accent-soft2:#a855f7;
  --accent-warm:#f97316;
  --text:#e5e7eb;
  --muted:#9ca3af;
}

html, body, [class*="css"] {
  background-color: var(--bg) !important;
  color: var(--text) !important;
  font-family: system-ui, -apple-system, BlinkMacSystemFont, "Inter", sans-serif;
}

.stApp {
  background:
    radial-gradient(circle at top left, rgba(56,189,248,0.18) 0, transparent 50%),
    radial-gradient(circle at top right, rgba(244,114,182,0.18) 0, transparent 55%),
    radial-gradient(circle at bottom, rgba(15,23,42,0.8) 0, #020617 70%);
}

/* TOP BAR */
.topbar {
  display:flex;
  align-items:center;
  justify-content:space-between;
  gap:18px;
  padding:16px 20px;
  border-radius:22px;
  background: radial-gradient(circle at top left, rgba(56,189,248,0.28), rgba(15,23,42,0.96));
  border:1px solid rgba(148,163,184,0.55);
  box-shadow:0 26px 70px rgba(15,23,42,0.95);
  margin-bottom:22px;
  position:relative;
  overflow:hidden;
}
.topbar::after{
  content:"";
  position:absolute;
  inset:0;
  border-radius:inherit;
  background:radial-gradient(circle at 120% -10%, rgba(248,250,252,0.32), transparent 55%);
  opacity:0.45;
  mix-blend-mode:soft-light;
  pointer-events:none;
}
.logo-pill {
  width:58px;
  height:58px;
  border-radius:20px;
  background:
    conic-gradient(from 210deg, #22d3ee, #a855f7, #f97316, #22d3ee);
  display:flex;
  align-items:center;
  justify-content:center;
  color:white;
  font-weight:900;
  font-size:24px;
  box-shadow:0 18px 45px rgba(15,23,42,0.85);
}
.top-title {
  font-size:22px;
  font-weight:800;
  letter-spacing:-0.04em;
}
.top-subtitle {
  font-size:12px;
  color:var(--muted);
}
.top-right-badge {
  display:flex;
  flex-direction:column;
  align-items:flex-end;
  gap:6px;
  font-size:11px;
}
.top-chip {
  padding:5px 11px;
  border-radius:999px;
  border:1px solid rgba(148,163,184,0.7);
  background:rgba(15,23,42,0.9);
}
.top-chip span {
  color:#a5b4fc;
}

/* KPI CARDS */
.kpi-row {
  display:flex;
  gap:12px;
  flex-wrap:wrap;
  margin-bottom:10px;
}
.kpi-card {
  flex:1 1 180px;
  min-width:0;
  padding:14px 16px;
  border-radius:18px;
  background:var(--bg-card-soft);
  border:1px solid var(--border-soft);
  backdrop-filter:blur(18px);
  -webkit-backdrop-filter:blur(18px);
  box-shadow:0 20px 50px rgba(15,23,42,0.9);
  position:relative;
  overflow:hidden;
  transition:transform .12s ease-out, box-shadow .12s ease-out, border-color .12s ease-out, background .12s ease-out;
}
.kpi-card::before{
  content:"";
  position:absolute;
  inset:-60%;
  background:conic-gradient(from 200deg, rgba(34,211,238,0.15), rgba(244,114,182,0.14), transparent 60%);
  opacity:0;
  transition:opacity .18s ease-out;
  pointer-events:none;
}
.kpi-card:hover{
  transform:translateY(-2px);
  box-shadow:0 26px 64px rgba(15,23,42,0.95);
  border-color:rgba(56,189,248,0.9);
  background:rgba(15,23,42,0.92);
}
.kpi-card:hover::before{
  opacity:0.28;
}
.kpi-label {
  font-size:11px;
  text-transform:uppercase;
  letter-spacing:0.14em;
  color:var(--muted);
  margin-bottom:4px;
}
.kpi-value {
  font-size:22px;
  font-weight:800;
}
.kpi-pill {
  font-size:11px;
  color:var(--muted);
  margin-top:4px;
}

/* SEÇÕES */
.section-title {
  font-size:16px;
  font-weight:700;
  margin-top:2px;
  margin-bottom:2px;
}
.section-sub {
  font-size:12px;
  color:var(--muted);
  margin-bottom:8px;
}

/* CARDS GENERICOS */
.card-soft {
  background:var(--bg-card-soft);
  border-radius:18px;
  padding:14px 16px;
  border:1px solid var(--border-soft);
  backdrop-filter:blur(16px);
  -webkit-backdrop-filter:blur(16px);
  box-shadow:0 18px 45px rgba(15,23,42,0.85);
  margin-bottom:14px;
}

/* BADGES */
.badge-soft {
  display:inline-flex;
  align-items:center;
  gap:4px;
  padding:2px 8px;
  border-radius:999px;
  font-size:11px;
  background:rgba(37,99,235,0.18);
  color:#bfdbfe;
}
.badge-red {
  background:rgba(239,68,68,0.22);
  color:#fecaca;
}
.badge-yellow {
  background:rgba(234,179,8,0.22);
  color:#facc15;
}
.badge-green {
  background:rgba(34,197,94,0.22);
  color:#bbf7d0;
}

/* TABELAS */
.stDataFrame thead tr th {
  background:linear-gradient(90deg, rgba(148,163,184,0.2), rgba(56,189,248,0.12)) !important;
  color:#e5e7eb !important;
  font-size:11px !important;
  text-transform:uppercase;
}
.stDataFrame tbody tr:nth-child(odd) {
  background-color:rgba(15,23,42,0.8);
}
.stDataFrame tbody tr:nth-child(even) {
  background-color:rgba(15,23,42,0.92);
}

/* TABS */
.stTabs [data-baseweb="tab-list"] {
  gap: 4px;
}
.stTabs [data-baseweb="tab"] {
  padding: 4px 10px;
  border-radius:999px;
  background:rgba(15,23,42,0.85);
  color:#9ca3af;
  border:1px solid transparent;
}
.stTabs [aria-selected="true"] {
  background:radial-gradient(circle at top left, rgba(34,211,238,0.45), rgba(56,189,248,0.7));
  color:#f9fafb !important;
  border-color:rgba(59,130,246,0.9);
}

/* PEQUENOS AJUSTES */
hr { border-color:rgba(51,65,85,0.9) !important; }
</style>
"""
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

# --------------------------------------------------
# TOPO
# --------------------------------------------------
st.markdown(
    """
<div class="topbar">
  <div style="display:flex; align-items:center; gap:14px;">
    <div class="logo-pill">LI</div>
    <div>
      <div class="top-title">Loja Importados – Painel FIFO</div>
      <div class="top-subtitle">Visão real de estoque, custo e lucro por produto. Menos achismo, mais dado.</div>
    </div>
  </div>
  <div class="top-right-badge">
    <div class="top-chip">📂 Conectado à planilha <span>Google Sheets</span></div>
    <div style="opacity:0.8;">Modo: <b>FIFO</b> • Base: compras ENTREGUE</div>
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
    max_linhas = min(20, len(df_raw))
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
tab_dash, tab_search, tab_alerts = st.tabs(
    ["📊 Dashboard", "🔎 Pesquisa de produto", "⚠️ Alertas"]
)

# --------------------------------------------------
# TAB 1 – DASHBOARD
# --------------------------------------------------
with tab_dash:
    st.markdown('<div class="card-soft">', unsafe_allow_html=True)

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

    st.markdown(
        """
<div class="section-title">Visão geral do período selecionado</div>
<div class="section-sub">Resumo financeiro real, já considerando custo FIFO.</div>
""",
        unsafe_allow_html=True,
    )

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

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")

    # Top produtos mais vendidos
    st.markdown('<div class="card-soft">', unsafe_allow_html=True)
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
            color_continuous_scale=["#22d3ee", "#0ea5e9", "#a855f7"],
        )
        fig_top.update_traces(
            textposition="inside",
            texttemplate="<b>%{text}</b>",
            insidetextanchor="middle",
            textfont_size=13,
        )
        fig_top.update_layout(
            height=380,
            plot_bgcolor="rgba(15,23,42,0.92)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(
                family="Roboto, system-ui, -apple-system, 'Segoe UI', sans-serif",
                color="#e5e7eb",
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
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")

    # Gráfico mensal (mês atual + 2 anteriores)
    st.markdown('<div class="card-soft">', unsafe_allow_html=True)
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
                    "Mês atual": "#f97316",
                    "Anterior": "#0ea5e9",
                },
            )
            fig.update_traces(
                textposition="inside",
                texttemplate="<b>%{text}</b>",
                insidetextanchor="middle",
                textfont_size=14,
            )
            fig.update_layout(
                height=380,
                yaxis_title="Faturamento (R$)",
                xaxis_title="Mês",
                uniformtext_minsize=10,
                uniformtext_mode="hide",
                plot_bgcolor="rgba(15,23,42,0.92)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(
                    family="Roboto, system-ui, -apple-system, 'Segoe UI', sans-serif",
                    color="#e5e7eb",
                ),
                legend_title_text="",
            )
            st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")

    # Vendas detalhadas + explicação FIFO
    st.markdown('<div class="card-soft">', unsafe_allow_html=True)
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

**Resumo da lógica:**

1. Busco todas as **compras de `{prod_ex}` com STATUS = ENTREGUE**, em ordem de data (mais antigas primeiro).
2. Cada compra vira um **lote de estoque** com quantidade e custo unitário.
3. Quando essa venda de **{qtd_ex:.0f} unid.** acontece, consumo primeiro o lote mais antigo, depois o próximo, até completar a quantidade.
4. O **custo total FIFO** é a soma dos custos dos lotes que foram “comidos” por essa venda.
5. O **custo unitário FIFO** é o custo total dividido pela quantidade vendida.
6. O **lucro** é sempre: **venda − custo FIFO**.
            """
        )
    else:
        st.info("Nenhuma venda no período selecionado.")
    st.markdown("</div>", unsafe_allow_html=True)

# --------------------------------------------------
# TAB 2 – PESQUISA DE PRODUTO
# --------------------------------------------------
with tab_search:
    st.markdown(
        """
<div class="section-title">🔎 Pesquisa de produto – baseado no FIFO</div>
<div class="section-sub">Veja custo médio, margem e histórico para decidir preço e reposição.</div>
""",
        unsafe_allow_html=True,
    )

    if df_fifo.empty and df_estoque.empty:
        st.info("Sem dados de estoque ou vendas para pesquisar.")
    else:
        st.markdown('<div class="card-soft">', unsafe_allow_html=True)

        produtos_estoque = df_estoque["PRODUTO"].unique().tolist() if not df_estoque.empty else []
        produtos_vendas = df_fifo["PRODUTO"].unique().tolist() if not df_fifo.empty else []
        todos_produtos = sorted(set(produtos_estoque) | set(produtos_vendas))

        prod_sel = st.selectbox(
            "Escolha o produto:",
            options=["(selecione)"] + todos_produtos,
            index=0,
        )

        if prod_sel != "(selecione)":
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

            st.markdown("---")
            st.markdown("#### 💡 Leitura rápida")
            st.markdown(
                f"""
- Se o **custo médio FIFO** está muito próximo do **preço médio de venda**, esse item merece atenção no preço ou na compra.
- Se a **margem média** é boa, mas o estoque está baixo, é candidato forte para reposição.
- Se a **margem é ruim**, você pode:
  - negociar melhor na compra,
  - subir preço,
  - ou usar como isca para atrair cliente (sabendo que compensa em outros itens).
                """
            )
        else:
            st.info("Selecione um produto para ver os detalhes baseados no FIFO.")

        st.markdown("</div>", unsafe_allow_html=True)

# --------------------------------------------------
# TAB 3 – ALERTAS
# --------------------------------------------------
with tab_alerts:
    st.markdown(
        """
<div class="section-title">⚠️ Alertas de estoque</div>
<div class="section-sub">Veja o que está voando sem estoque e o que está travando dinheiro na prateleira.</div>
""",
        unsafe_allow_html=True,
    )

    if df_estoque.empty:
        st.info("Sem dados de estoque para gerar alertas.")
    else:
        st.markdown('<div class="card-soft">', unsafe_allow_html=True)
        st.markdown("##### Configurações dos critérios")
        c1, c2, c3 = st.columns(3)
        with c1:
            LIM_VENDE_BEM = st.slider("Vende bem a partir de (unid.)", 5, 50, 10, 1)
        with c2:
            LIM_ESTOQUE_BAIXO = st.slider("Considerar estoque baixo abaixo de (unid.)", 1, 20, 3, 1)
        with c3:
            LIM_DIAS_PARADO = st.slider("Parado há mais de (dias)", 7, 180, 30, 1)
        st.markdown("</div>", unsafe_allow_html=True)

        vendas_tot = (
            df_fifo.groupby("PRODUTO", as_index=False)["QTD"]
            .sum()
            .rename(columns={"QTD": "QTD_VENDIDA_TOTAL"})
        )
        base_alerta = df_estoque.merge(vendas_tot, on="PRODUTO", how="left")
        base_alerta["QTD_VENDIDA_TOTAL"] = base_alerta["QTD_VENDIDA_TOTAL"].fillna(0)

        st.markdown('<div class="card-soft">', unsafe_allow_html=True)
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
                        "SALDO_QTD": "Estoque atual",
                        "QTD_VENDIDA_TOTAL": "Qtd vendida (histórico)",
                        "VALOR_ESTOQUE_FMT": "Valor em estoque (FIFO)",
                    }
                ),
                use_container_width=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="card-soft">', unsafe_allow_html=True)
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

        parado_alerta = parado[
            (parado["DIAS_PARADO"].notna())
            & (parado["DIAS_PARADO"] >= LIM_DIAS_PARADO)
        ].copy()

        if parado_alerta.empty:
            st.info(f"Nenhum produto com estoque parado há mais de {LIM_DIAS_PARADO} dias.")
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
                        "SALDO_QTD": "Estoque atual",
                        "VALOR_ESTOQUE_FMT": "Valor em estoque (FIFO)",
                        "DIAS_PARADO": "Dias parado",
                        "ULT_VENDA_FMT": "Última venda",
                        "ULT_COMPRA_FMT": "Última compra (ENTREGUE)",
                    }
                ),
                use_container_width=True,
            )
        st.markdown(
            f"*Critérios atuais:* vende bem ≥ **{LIM_VENDE_BEM} unid.**, estoque baixo ≤ **{LIM_ESTOQUE_BAIXO} unid.**, parado ≥ **{LIM_DIAS_PARADO} dias**."
        )
        st.markdown("</div>", unsafe_allow_html=True)
