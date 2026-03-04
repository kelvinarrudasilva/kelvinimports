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

# URL da sua planilha
URL_PLANILHA = "https://docs.google.com/spreadsheets/d/1TsRjsfw1TVfeEWBBvhKvsGQ5YUCktn2b/export?format=xlsx"

# custo unitário máximo plausível (acima disso é dado zoado)
CUSTO_MAX_PLAUSIVEL = 500.0

# --------------------------------------------------
# TEMA: DARK PRETÃO + TOQUES DE COR (sem neon exagerado)
# --------------------------------------------------
GLOBAL_CSS = """
<style>
:root{
  --bg:#040404;
  --bg-page:#040404;
  --card:#0b0b0c;
  --card2:#0f0f11;
  --border:#232326;
  --border2:#2b2b31;

  --text:#f3f4f6;
  --muted:#a1a1aa;

  /* cores de acento (bem dosadas) */
  --g:#22c55e;    /* verde */
  --o:#fb923c;    /* laranja */
  --b:#60a5fa;    /* azul */
  --p:#a78bfa;    /* roxo */

  --shadow: 0 10px 30px rgba(0,0,0,.35);
}

html, body, [class*="css"]{
  background: var(--bg-page) !important;
  color: var(--text) !important;
  font-family: system-ui, -apple-system, BlinkMacSystemFont, "Inter", sans-serif;
}

.stApp { background: var(--bg-page) !important; }

/* remove espaços excessivos */
.block-container { padding-top: 1.0rem; }

/* -------------------------------------------------- */
/* TOPBAR com gradiente sutil */
/* -------------------------------------------------- */
.topbar{
  display:flex;
  align-items:center;
  justify-content:space-between;
  gap:16px;
  padding:14px 18px;
  border-radius:18px;

  background:
    radial-gradient(1000px 200px at 10% 0%, rgba(34,197,94,.10), transparent 60%),
    radial-gradient(900px 200px at 90% 0%, rgba(251,146,60,.10), transparent 60%),
    linear-gradient(180deg, rgba(255,255,255,.03), rgba(255,255,255,0));

  border:1px solid var(--border);
  box-shadow: var(--shadow);
  margin-bottom:16px;
}

.logo-pill{
  width:52px; height:52px;
  border-radius:16px;
  display:flex; align-items:center; justify-content:center;
  font-weight:900; font-size:20px;
  background:
    linear-gradient(135deg, rgba(96,165,250,.20), rgba(167,139,250,.18));
  border:1px solid rgba(96,165,250,.25);
  color: var(--text);
}

.top-title{
  font-size:20px;
  font-weight:900;
  letter-spacing:-0.03em;
}

.top-subtitle{
  font-size:12px;
  color: var(--muted);
}

.top-right{
  display:flex;
  flex-direction:column;
  align-items:flex-end;
  gap:6px;
  font-size:11px;
  color: var(--muted);
}

.chip{
  display:inline-flex;
  align-items:center;
  gap:8px;
  padding:6px 10px;
  border-radius:999px;
  border:1px solid var(--border2);
  background: rgba(255,255,255,.03);
}
.chip b{ color: var(--text); }
.chip .dot{
  width:8px; height:8px; border-radius:99px;
  background: var(--g);
  box-shadow: 0 0 0 3px rgba(34,197,94,.12);
}

/* -------------------------------------------------- */
/* KPIs */
/* -------------------------------------------------- */
.kpi{
  padding:14px 16px;
  border-radius:16px;
  background:
    linear-gradient(180deg, rgba(255,255,255,.03), rgba(255,255,255,.01));
  border:1px solid var(--border);
  box-shadow: var(--shadow);
  transition: transform .12s ease, border-color .12s ease;
}
.kpi:hover{
  transform: translateY(-1px);
  border-color: rgba(96,165,250,.35);
}

.kpi-label{
  font-size:11px;
  letter-spacing:.16em;
  text-transform:uppercase;
  color: var(--muted);
  margin-bottom:6px;
}

.kpi-value{
  font-size:20px;
  font-weight:900;
}

.kpi-sub{
  margin-top:6px;
  font-size:11px;
  color: var(--muted);
}

.kpi-line{
  height:2px;
  margin-top:10px;
  border-radius:99px;
  background: linear-gradient(90deg, rgba(34,197,94,.9), rgba(96,165,250,.9), rgba(251,146,60,.9));
  opacity:.25;
}

/* -------------------------------------------------- */
/* Seções */
/* -------------------------------------------------- */
.section-title{
  font-size:16px;
  font-weight:850;
  margin:0 0 2px 0;
}
.section-sub{
  font-size:12px;
  color: var(--muted);
  margin:0 0 8px 0;
}

/* -------------------------------------------------- */
/* Tabs */
/* -------------------------------------------------- */
.stTabs [data-baseweb="tab-list"]{ gap:6px; }
.stTabs [data-baseweb="tab"]{
  padding:6px 12px !important;
  border-radius:999px !important;
  background: rgba(255,255,255,.02) !important;
  border:1px solid var(--border) !important;
  color: var(--muted) !important;
}
.stTabs [aria-selected="true"]{
  color: var(--text) !important;
  border-color: rgba(34,197,94,.35) !important;
  background:
    radial-gradient(400px 60px at 10% 50%, rgba(34,197,94,.12), transparent 60%),
    radial-gradient(400px 60px at 90% 50%, rgba(96,165,250,.10), transparent 60%),
    rgba(255,255,255,.03) !important;
}

/* -------------------------------------------------- */
/* Dataframe header */
/* -------------------------------------------------- */
.stDataFrame thead tr th{
  background: rgba(255,255,255,.03) !important;
  color: var(--text) !important;
  font-size:11px !important;
  text-transform:uppercase !important;
  border-bottom: 1px solid var(--border) !important;
}
.stDataFrame tbody tr:nth-child(odd){ background-color: rgba(255,255,255,.01) !important; }
.stDataFrame tbody tr:nth-child(even){ background-color: rgba(255,255,255,.02) !important; }

/* -------------------------------------------------- */
/* Botões */
/* -------------------------------------------------- */
.stButton button{
  border-radius: 12px !important;
  border: 1px solid rgba(34,197,94,.35) !important;
  background:
    radial-gradient(420px 60px at 20% 50%, rgba(34,197,94,.18), transparent 60%),
    rgba(255,255,255,.03) !important;
  color: var(--text) !important;
  font-weight: 700 !important;
}
.stButton button:hover{
  border-color: rgba(96,165,250,.40) !important;
  background:
    radial-gradient(420px 60px at 20% 50%, rgba(96,165,250,.18), transparent 60%),
    rgba(255,255,255,.05) !important;
}

/* Inputs */
[data-baseweb="input"] input{
  background: rgba(255,255,255,.02) !important;
  border:1px solid var(--border) !important;
  color: var(--text) !important;
}
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
      <div class="top-subtitle">Pretão elegante com cor na medida certa. FIFO + estoque atual nas tabelas.</div>
    </div>
  </div>
  <div class="top-right">
    <div class="chip"><span class="dot"></span> Planilha <b>Google Sheets</b> conectada</div>
    <div>Modo: <b>FIFO</b> (base: compras <b>ENTREGUE</b>)</div>
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
# BOTÃO ATUALIZAR
# --------------------------------------------------
cbtn, _ = st.columns([1, 5])
with cbtn:
    if st.button("🔄 Atualizar dados da planilha"):
        st.cache_data.clear()
        st.rerun()

df_compras, df_vendas = carregar_dados()
df_fifo, df_estoque = calcular_fifo(df_compras, df_vendas)

if df_fifo.empty:
    st.warning("Não foi possível calcular FIFO (sem vendas ou sem compras ENTREGUE válidas).")
    st.stop()

# -----------------------------
# MAPA: ESTOQUE ATUAL POR PRODUTO
# -----------------------------
if not df_estoque.empty and ("PRODUTO" in df_estoque.columns) and ("SALDO_QTD" in df_estoque.columns):
    estoque_atual_map = df_estoque.set_index("PRODUTO")["SALDO_QTD"].to_dict()
else:
    estoque_atual_map = {}

def add_estoque_atual(df, col_produto="PRODUTO", nome_col="ESTOQUE_ATUAL"):
    out = df.copy()
    if col_produto in out.columns:
        out[nome_col] = out[col_produto].map(estoque_atual_map).fillna(0)
        out[nome_col] = out[nome_col].apply(lambda x: int(round(float(x))) if pd.notna(x) else 0)
    else:
        out[nome_col] = 0
    return out


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
    st.markdown('<div class="section-title">Visão geral do período selecionado</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Resumo financeiro real, considerando custo FIFO + estoque atual nas tabelas.</div>', unsafe_allow_html=True)

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
        st.markdown(f"""
<div class="kpi">
  <div class="kpi-label">Faturamento</div>
  <div class="kpi-value">{format_reais(total_vendido)}</div>
  <div class="kpi-sub">Somatório de VALOR TOTAL</div>
  <div class="kpi-line"></div>
</div>""", unsafe_allow_html=True)
    with k2:
        st.markdown(f"""
<div class="kpi">
  <div class="kpi-label">Custo (FIFO)</div>
  <div class="kpi-value">{format_reais(total_custo)}</div>
  <div class="kpi-sub">Somatório de CUSTO_TOTAL</div>
  <div class="kpi-line"></div>
</div>""", unsafe_allow_html=True)
    with k3:
        st.markdown(f"""
<div class="kpi">
  <div class="kpi-label">Lucro (FIFO)</div>
  <div class="kpi-value">{format_reais(total_lucro)}</div>
  <div class="kpi-sub">Venda − Custo FIFO</div>
  <div class="kpi-line"></div>
</div>""", unsafe_allow_html=True)
    with k4:
        st.markdown(f"""
<div class="kpi">
  <div class="kpi-label">Ticket médio</div>
  <div class="kpi-value">{format_reais(ticket_medio)}</div>
  <div class="kpi-sub">Faturamento / Qtd vendida</div>
  <div class="kpi-line"></div>
</div>""", unsafe_allow_html=True)
    with k5:
        st.markdown(f"""
<div class="kpi">
  <div class="kpi-label">Nº de vendas</div>
  <div class="kpi-value">{num_vendas}</div>
  <div class="kpi-sub">Registros no filtro</div>
  <div class="kpi-line"></div>
</div>""", unsafe_allow_html=True)

    st.markdown("---")

    st.markdown('<div class="section-title">🥇 Produtos mais vendidos</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Top 6 por quantidade vendida, com lucro FIFO e estoque atual.</div>', unsafe_allow_html=True)

    if df_fifo_filt.empty:
        st.info("Nenhuma venda no período selecionado.")
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
        )
        fig_top.update_traces(
            textposition="inside",
            texttemplate="<b>%{text}</b>",
            insidetextanchor="middle",
            textfont_size=13,
        )
        fig_top.update_layout(
            height=360,
            plot_bgcolor="#040404",
            paper_bgcolor="#040404",
            font=dict(family="system-ui", color="#f3f4f6"),
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

    st.markdown("---")

    st.markdown('<div class="section-title">🧾 Vendas detalhadas (com custo FIFO)</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Agora com a coluna <b>ESTOQUE_ATUAL</b> do item vendido.</div>', unsafe_allow_html=True)

    df_fifo_view = df_fifo_filt.copy()
    if not df_fifo_view.empty:
        df_fifo_view = add_estoque_atual(df_fifo_view, col_produto="PRODUTO", nome_col="ESTOQUE_ATUAL")

        df_fifo_view["CUSTO_UNIT"] = df_fifo_view["CUSTO_TOTAL"] / df_fifo_view["QTD"].replace(0, pd.NA)
        df_fifo_view["DATA"] = df_fifo_view["DATA"].dt.strftime("%d/%m/%Y")

        df_fifo_view["VALOR_TOTAL"] = df_fifo_view["VALOR_TOTAL"].map(format_reais)
        df_fifo_view["CUSTO_TOTAL"] = df_fifo_view["CUSTO_TOTAL"].map(format_reais)
        df_fifo_view["LUCRO"] = df_fifo_view["LUCRO"].map(format_reais)
        df_fifo_view["CUSTO_UNIT"] = df_fifo_view["CUSTO_UNIT"].map(format_reais)

        cols_ordem = [
            "DATA","PRODUTO","CLIENTE","STATUS","QTD",
            "VALOR_TOTAL","CUSTO_TOTAL","CUSTO_UNIT","LUCRO",
            "ESTOQUE_ATUAL","MES_ANO"
        ]
        cols_ordem = [c for c in cols_ordem if c in df_fifo_view.columns]

        st.dataframe(
            df_fifo_view[cols_ordem].sort_values("DATA", ascending=False),
            use_container_width=True,
        )
    else:
        st.info("Nenhuma venda no período selecionado.")

# --------------------------------------------------
# TAB 2 – PESQUISA DE PRODUTO
# --------------------------------------------------
with tab_search:
    st.markdown('<div class="section-title">🔎 Pesquisa de produto</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Custo médio FIFO, margem, histórico e saldo atual.</div>', unsafe_allow_html=True)

    produtos_estoque = df_estoque["PRODUTO"].unique().tolist() if not df_estoque.empty else []
    produtos_vendas = df_fifo["PRODUTO"].unique().tolist() if not df_fifo.empty else []
    todos_produtos = sorted(set(produtos_estoque) | set(produtos_vendas))

    prod_sel = st.selectbox("Escolha o produto:", options=["(selecione)"] + todos_produtos, index=0)

    if prod_sel != "(selecione)":
        linha_est = df_estoque[df_estoque["PRODUTO"] == prod_sel]
        if not linha_est.empty:
            saldo = float(linha_est["SALDO_QTD"].iloc[0])
            valor_estoque = float(linha_est["VALOR_ESTOQUE"].iloc[0])
            custo_medio_fifo = float(linha_est["CUSTO_MEDIO_FIFO"].iloc[0])
        else:
            saldo, valor_estoque, custo_medio_fifo = 0.0, 0.0, 0.0

        vendas_prod = df_fifo[df_fifo["PRODUTO"] == prod_sel].copy()
        if not vendas_prod.empty:
            qtd_total_vendida = vendas_prod["QTD"].sum()
            receita_total = vendas_prod["VALOR_TOTAL"].sum()
            custo_total_hist = vendas_prod["CUSTO_TOTAL"].sum()
            margem_media = (receita_total - custo_total_hist) / receita_total if receita_total else 0.0
            preco_medio_venda = receita_total / qtd_total_vendida if qtd_total_vendida else 0.0
        else:
            qtd_total_vendida, receita_total, custo_total_hist = 0.0, 0.0, 0.0
            margem_media, preco_medio_venda = 0.0, 0.0

        a, b, c = st.columns(3)
        with a:
            st.markdown(f"""
<div class="kpi">
  <div class="kpi-label">Custo médio FIFO</div>
  <div class="kpi-value">{format_reais(custo_medio_fifo)}</div>
  <div class="kpi-sub">Base no estoque restante</div>
  <div class="kpi-line"></div>
</div>""", unsafe_allow_html=True)
        with b:
            st.markdown(f"""
<div class="kpi">
  <div class="kpi-label">Preço médio de venda</div>
  <div class="kpi-value">{format_reais(preco_medio_venda)}</div>
  <div class="kpi-sub">Histórico total</div>
  <div class="kpi-line"></div>
</div>""", unsafe_allow_html=True)
        with c:
            st.markdown(f"""
<div class="kpi">
  <div class="kpi-label">Margem média</div>
  <div class="kpi-value">{margem_media*100:,.1f}%</div>
  <div class="kpi-sub">{format_reais(receita_total)} − {format_reais(custo_total_hist)}</div>
  <div class="kpi-line"></div>
</div>""", unsafe_allow_html=True)

        d, e, f = st.columns(3)
        with d:
            st.markdown(f"""
<div class="kpi">
  <div class="kpi-label">Estoque atual</div>
  <div class="kpi-value">{int(saldo)} unid.</div>
  <div class="kpi-sub">Valor em estoque: {format_reais(valor_estoque)}</div>
  <div class="kpi-line"></div>
</div>""", unsafe_allow_html=True)
        with e:
            st.markdown(f"""
<div class="kpi">
  <div class="kpi-label">Receita acumulada</div>
  <div class="kpi-value">{format_reais(receita_total)}</div>
  <div class="kpi-sub">Total vendido</div>
  <div class="kpi-line"></div>
</div>""", unsafe_allow_html=True)
        with f:
            st.markdown(f"""
<div class="kpi">
  <div class="kpi-label">Qtd vendida</div>
  <div class="kpi-value">{int(qtd_total_vendida)} unid.</div>
  <div class="kpi-sub">Somatório</div>
  <div class="kpi-line"></div>
</div>""", unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("#### 📄 Histórico de vendas (com estoque atual)")
        if not vendas_prod.empty:
            vendas_prod_hist = vendas_prod.copy()
            vendas_prod_hist = add_estoque_atual(vendas_prod_hist, col_produto="PRODUTO", nome_col="ESTOQUE_ATUAL")
            vendas_prod_hist["DATA"] = vendas_prod_hist["DATA"].dt.strftime("%d/%m/%Y")
            vendas_prod_hist["CUSTO_UNIT"] = vendas_prod_hist["CUSTO_TOTAL"] / vendas_prod_hist["QTD"].replace(0, pd.NA)
            vendas_prod_hist["VALOR_TOTAL"] = vendas_prod_hist["VALOR_TOTAL"].map(format_reais)
            vendas_prod_hist["CUSTO_TOTAL"] = vendas_prod_hist["CUSTO_TOTAL"].map(format_reais)
            vendas_prod_hist["LUCRO"] = vendas_prod_hist["LUCRO"].map(format_reais)
            vendas_prod_hist["CUSTO_UNIT"] = vendas_prod_hist["CUSTO_UNIT"].map(format_reais)

            cols_hist = ["DATA","QTD","VALOR_TOTAL","CUSTO_TOTAL","CUSTO_UNIT","LUCRO","ESTOQUE_ATUAL","MES_ANO"]
            cols_hist = [c for c in cols_hist if c in vendas_prod_hist.columns]
            st.dataframe(vendas_prod_hist[cols_hist].sort_values("DATA", ascending=False).head(40), use_container_width=True)
        else:
            st.info("Sem vendas registradas para esse produto.")

        st.markdown("---")
        st.markdown("#### 🧾 Histórico de compras ENTREGUE")
        compras_prod = df_compras.copy()
        compras_prod.columns = [c.strip().upper() for c in compras_prod.columns]
        if "PRODUTO" in compras_prod.columns:
            compras_prod = compras_prod[compras_prod["PRODUTO"] == prod_sel].copy()
        else:
            compras_prod = pd.DataFrame()

        if not compras_prod.empty and "STATUS" in compras_prod.columns:
            compras_prod = compras_prod[compras_prod["STATUS"].astype(str).str.upper() == "ENTREGUE"].copy()

        if compras_prod.empty:
            st.info("Nenhuma compra ENTREGUE registrada para esse produto.")
        else:
            compras_prod["DATA"] = pd.to_datetime(compras_prod["DATA"], errors="coerce", dayfirst=True)
            compras_prod = compras_prod.sort_values("DATA", ascending=False)
            compras_prod["DATA_FMT"] = compras_prod["DATA"].dt.strftime("%d/%m/%Y")
            compras_prod["QUANTIDADE"] = compras_prod["QUANTIDADE"].apply(parse_money).astype(float)
            compras_prod["CUSTO UNITÁRIO"] = compras_prod["CUSTO UNITÁRIO"].apply(parse_money).astype(float)
            compras_prod["CUSTO_TOTAL"] = compras_prod["QUANTIDADE"] * compras_prod["CUSTO UNITÁRIO"]

            compras_prod["CUSTO_UNIT_FMT"] = compras_prod["CUSTO UNITÁRIO"].map(format_reais)
            compras_prod["CUSTO_TOTAL_FMT"] = compras_prod["CUSTO_TOTAL"].map(format_reais)

            cols_comp = ["DATA_FMT","STATUS","QUANTIDADE","CUSTO_UNIT_FMT","CUSTO_TOTAL_FMT"]
            st.dataframe(
                compras_prod[cols_comp].rename(columns={
                    "DATA_FMT":"Data","STATUS":"Status","QUANTIDADE":"Qtd",
                    "CUSTO_UNIT_FMT":"Custo unit.","CUSTO_TOTAL_FMT":"Custo total"
                }).head(50),
                use_container_width=True
            )

# --------------------------------------------------
# TAB 3 – ALERTAS
# --------------------------------------------------
with tab_alerts:
    st.markdown('<div class="section-title">⚠️ Alertas de estoque</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Vende bem x estoque baixo e estoque parado.</div>', unsafe_allow_html=True)

    if df_estoque.empty:
        st.info("Sem dados de estoque para gerar alertas.")
    else:
        LIM_VENDE_BEM = st.slider("Vende bem a partir de (unid.)", 5, 50, 10, 1)
        LIM_ESTOQUE_BAIXO = st.slider("Considerar estoque baixo abaixo de (unid.)", 1, 20, 3, 1)
        LIM_DIAS_PARADO = st.slider("Parado há mais de (dias)", 7, 180, 30, 1)

        vendas_tot = (
            df_fifo.groupby("PRODUTO", as_index=False)["QTD"]
            .sum()
            .rename(columns={"QTD": "QTD_VENDIDA_TOTAL"})
        )
        base_alerta = df_estoque.merge(vendas_tot, on="PRODUTO", how="left")
        base_alerta["QTD_VENDIDA_TOTAL"] = base_alerta["QTD_VENDIDA_TOTAL"].fillna(0)

        st.markdown("### 🔥 Vendendo bem e com pouco estoque")
        vb = base_alerta[
            (base_alerta["QTD_VENDIDA_TOTAL"] >= LIM_VENDE_BEM)
            & (base_alerta["SALDO_QTD"] > 0)
            & (base_alerta["SALDO_QTD"] <= LIM_ESTOQUE_BAIXO)
        ].copy()

        if vb.empty:
            st.info("Nenhum produto com vendas fortes e estoque muito baixo pelos critérios atuais.")
        else:
            vb["VALOR_ESTOQUE_FMT"] = vb["VALOR_ESTOQUE"].map(format_reais)
            vb = vb.sort_values(["SALDO_QTD", "QTD_VENDIDA_TOTAL"], ascending=[True, False])
            st.dataframe(
                vb[["PRODUTO","SALDO_QTD","QTD_VENDIDA_TOTAL","VALOR_ESTOQUE_FMT"]].rename(columns={
                    "PRODUTO":"Produto","SALDO_QTD":"Estoque atual","QTD_VENDIDA_TOTAL":"Qtd vendida (histórico)","VALOR_ESTOQUE_FMT":"Valor estoque (FIFO)"
                }),
                use_container_width=True
            )

        st.markdown("---")
        st.markdown("### 🐌 Estoque parado (puxando última venda/compra)")

        df_compras_alert = df_compras.copy()
        df_compras_alert.columns = [c.strip().upper() for c in df_compras_alert.columns]
        df_compras_alert = df_compras_alert[df_compras_alert["STATUS"].astype(str).str.upper() == "ENTREGUE"].copy()
        df_compras_alert["DATA"] = pd.to_datetime(df_compras_alert["DATA"], errors="coerce", dayfirst=True)

        df_vendas_alert = df_vendas.copy()
        df_vendas_alert.columns = [c.strip().upper() for c in df_vendas_alert.columns]
        df_vendas_alert["DATA"] = pd.to_datetime(df_vendas_alert["DATA"], errors="coerce", dayfirst=True)

        last_sale = (df_vendas_alert.groupby("PRODUTO", as_index=False)["DATA"].max().rename(columns={"DATA":"ULT_VENDA"})) if not df_vendas_alert.empty else pd.DataFrame(columns=["PRODUTO","ULT_VENDA"])
        last_buy  = (df_compras_alert.groupby("PRODUTO", as_index=False)["DATA"].max().rename(columns={"DATA":"ULT_COMPRA"})) if not df_compras_alert.empty else pd.DataFrame(columns=["PRODUTO","ULT_COMPRA"])

        parado = df_estoque.merge(last_sale, on="PRODUTO", how="left").merge(last_buy, on="PRODUTO", how="left")
        parado = parado[parado["SALDO_QTD"] > 0].copy()

        today = pd.Timestamp.now().normalize()

        def dias_parado(row):
            uv = row.get("ULT_VENDA")
            uc = row.get("ULT_COMPRA")
            if pd.notna(uv):
                return (today - uv.normalize()).days
            if pd.notna(uc):
                return (today - uc.normalize()).days
            return None

        parado["DIAS_PARADO"] = parado.apply(dias_parado, axis=1)
        pf = parado[(parado["DIAS_PARADO"].notna()) & (parado["DIAS_PARADO"] >= LIM_DIAS_PARADO)].copy()

        if pf.empty:
            st.info(f"Nenhum produto com estoque parado há mais de {LIM_DIAS_PARADO} dias.")
        else:
            pf["ULT_VENDA_FMT"] = pf["ULT_VENDA"].dt.strftime("%d/%m/%Y")
            pf["ULT_COMPRA_FMT"] = pf["ULT_COMPRA"].dt.strftime("%d/%m/%Y")
            pf["VALOR_ESTOQUE_FMT"] = pf["VALOR_ESTOQUE"].map(format_reais)
            pf = pf.sort_values("DIAS_PARADO", ascending=False)

            st.dataframe(
                pf[["PRODUTO","SALDO_QTD","VALOR_ESTOQUE_FMT","DIAS_PARADO","ULT_VENDA_FMT","ULT_COMPRA_FMT"]].rename(columns={
                    "PRODUTO":"Produto","SALDO_QTD":"Estoque atual","VALOR_ESTOQUE_FMT":"Valor estoque (FIFO)",
                    "DIAS_PARADO":"Dias parado","ULT_VENDA_FMT":"Última venda","ULT_COMPRA_FMT":"Última compra"
                }),
                use_container_width=True
            )

# --------------------------------------------------
# TAB 4 – COMPRAS
# --------------------------------------------------
with tab_compras:
    st.markdown('<div class="section-title">🧾 Compras</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Compras ENTREGUE com estoque atual do item comprado (linha a linha).</div>', unsafe_allow_html=True)

    dfc = df_compras.copy()
    dfc.columns = [c.strip().upper() for c in dfc.columns]

    if "DATA" not in dfc.columns:
        st.info("A aba COMPRAS precisa ter a coluna DATA.")
    else:
        dfc["DATA"] = pd.to_datetime(dfc["DATA"], errors="coerce", dayfirst=True)
        dfc = dfc[dfc["STATUS"].astype(str).str.upper() == "ENTREGUE"].copy()

        dfc["QUANTIDADE"] = dfc["QUANTIDADE"].apply(parse_money).astype(float)
        dfc["CUSTO UNITÁRIO"] = dfc["CUSTO UNITÁRIO"].apply(parse_money).astype(float)
        dfc["CUSTO_TOTAL"] = dfc["QUANTIDADE"] * dfc["CUSTO UNITÁRIO"]
        dfc["MES_ANO"] = dfc["DATA"].dt.strftime("%Y-%m")

        meses_comp = ["Todos"] + sorted(dfc["MES_ANO"].dropna().unique().tolist(), reverse=True)
        mes_atual = pd.Timestamp.now().strftime("%Y-%m")
        idx_padrao_comp = meses_comp.index(mes_atual) if mes_atual in meses_comp else 0

        mes_sel_comp = st.selectbox("Filtrar compras por mês (AAAA-MM):", meses_comp, index=idx_padrao_comp)

        if mes_sel_comp == "Todos":
            dfc_filt = dfc.copy()
        else:
            dfc_filt = dfc[dfc["MES_ANO"] == mes_sel_comp].copy()

        if dfc_filt.empty:
            st.info("Não há compras no período selecionado.")
        else:
            total_compras = dfc_filt["CUSTO_TOTAL"].sum()
            qtd_total_comp = dfc_filt["QUANTIDADE"].sum()
            custo_medio_geral = total_compras / qtd_total_comp if qtd_total_comp > 0 else 0.0
            num_prod_dif = dfc_filt["PRODUTO"].nunique()

            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.markdown(f"""
<div class="kpi">
  <div class="kpi-label">Total em compras</div>
  <div class="kpi-value">{format_reais(total_compras)}</div>
  <div class="kpi-sub">Somatório no período</div>
  <div class="kpi-line"></div>
</div>""", unsafe_allow_html=True)
            with c2:
                st.markdown(f"""
<div class="kpi">
  <div class="kpi-label">Qtd comprada</div>
  <div class="kpi-value">{int(qtd_total_comp)} unid.</div>
  <div class="kpi-sub">Somatório</div>
  <div class="kpi-line"></div>
</div>""", unsafe_allow_html=True)
            with c3:
                st.markdown(f"""
<div class="kpi">
  <div class="kpi-label">Custo médio</div>
  <div class="kpi-value">{format_reais(custo_medio_geral)}</div>
  <div class="kpi-sub">Custo / Qtd</div>
  <div class="kpi-line"></div>
</div>""", unsafe_allow_html=True)
            with c4:
                st.markdown(f"""
<div class="kpi">
  <div class="kpi-label">Produtos comprados</div>
  <div class="kpi-value">{num_prod_dif}</div>
  <div class="kpi-sub">Itens diferentes</div>
  <div class="kpi-line"></div>
</div>""", unsafe_allow_html=True)

            st.markdown("---")
            st.markdown("#### 📥 Top produtos comprados (com estoque atual)")

            top_comp = (
                dfc_filt.groupby("PRODUTO", as_index=False)
                .agg(QTD_COMP=("QUANTIDADE","sum"), VALOR_COMP=("CUSTO_TOTAL","sum"))
                .sort_values("VALOR_COMP", ascending=False)
            )
            top_comp["ESTOQUE_ATUAL"] = top_comp["PRODUTO"].map(estoque_atual_map).fillna(0).astype(int)
            top_comp["VALOR_COMP_FMT"] = top_comp["VALOR_COMP"].map(format_reais)

            st.dataframe(
                top_comp.rename(columns={
                    "PRODUTO":"Produto","QTD_COMP":"Qtd comprada","VALOR_COMP_FMT":"Valor em compras","ESTOQUE_ATUAL":"Estoque atual"
                })[["Produto","Qtd comprada","Valor em compras","Estoque atual"]].head(25),
                use_container_width=True
            )

            st.markdown("---")
            st.markdown("#### 🧾 Compras detalhadas (com estoque atual)")

            dfc_view = dfc_filt.copy()
            dfc_view = add_estoque_atual(dfc_view, col_produto="PRODUTO", nome_col="ESTOQUE_ATUAL")
            dfc_view["DATA_FMT"] = dfc_view["DATA"].dt.strftime("%d/%m/%Y")
            dfc_view["CUSTO_UNIT_FMT"] = dfc_view["CUSTO UNITÁRIO"].map(format_reais)
            dfc_view["CUSTO_TOTAL_FMT"] = dfc_view["CUSTO_TOTAL"].map(format_reais)

            st.dataframe(
                dfc_view[["DATA_FMT","PRODUTO","STATUS","QUANTIDADE","CUSTO_UNIT_FMT","CUSTO_TOTAL_FMT","ESTOQUE_ATUAL","MES_ANO"]]
                .rename(columns={
                    "DATA_FMT":"Data","PRODUTO":"Produto","STATUS":"Status","QUANTIDADE":"Qtd",
                    "CUSTO_UNIT_FMT":"Custo unit.","CUSTO_TOTAL_FMT":"Custo total","ESTOQUE_ATUAL":"Estoque atual","MES_ANO":"Mês/ano"
                })
                .sort_values("Data", ascending=False),
                use_container_width=True
            )
