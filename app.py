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
  --bg-card:#111111;
  --bg-card-soft:#111111;
  --bg-card-softer:#0c0c0c;
  --border-color:#262626;
  --border-soft:#1f2937;
  --text-primary:#f9fafb;
  --text-muted:#9ca3af;
  --accent:#facc15;
  --accent-soft:rgba(250,204,21,0.16);
  --accent-strong:#facc15;
  --danger:#f97373;
  --success:#22c55e;
  --shadow-soft:0 18px 45px rgba(0,0,0,0.60);
}

html, body, [class^="stApp"]{
  background-color:var(--bg);
  color:var(--text-primary);
}

.stApp {
  background: radial-gradient(circle at top left, #111827 0, #020617 45%, #020617 100%);
}

section.main > div {
  padding-top:0.5rem;
}

.stTabs [data-baseweb="tab-list"] {
  gap: 0.5rem;
}

.stTabs [data-baseweb="tab"] {
  background-color: #020617;
  border-radius: 999px;
  padding: 0.35rem 0.9rem;
  color: var(--text-muted);
  border: 1px solid #111827;
}

.stTabs [data-baseweb="tab"][aria-selected="true"] {
  background: linear-gradient(135deg, #facc15, #f97316);
  color:#020617;
  font-weight:600;
  border-color:transparent;
}

.stTabs [data-baseweb="tab"] p {
  font-size:0.80rem;
}

/* Cards */
.block-container{
  padding-top:1.4rem;
  padding-bottom:2rem;
}

div[data-testid="stMetric"]{
  background-color:var(--bg-card);
  border-radius:1rem;
  padding:1rem 1rem;
  border:1px solid var(--border-soft);
  box-shadow:var(--shadow-soft);
}

/* Remove fundo branco padrão dos plots */
.js-plotly-plot .plotly{
  background-color:transparent !important;
}

/* Dataframe */
[data-testid="stDataFrame"] {
  border-radius: 0.75rem;
  border:1px solid var(--border-soft);
  overflow:hidden;
  box-shadow:0 18px 38px rgba(0,0,0,0.55);
}

[data-testid="stDataFrame"] div[role="columnheader"] {
  background-color:#020617 !important;
  color:#e5e7eb !important;
  font-weight:500;
}

[data-testid="stDataFrame"] div[role="gridcell"] {
  background-color:#020617 !important;
  color:#e5e7eb !important;
  font-size:0.80rem;
}

/* Títulos de seção */
.section-title{
  font-size:1.05rem;
  font-weight:600;
  margin-bottom:0.15rem;
}

.section-sub{
  font-size:0.80rem;
  color:var(--text-muted);
  margin-bottom:0.8rem;
}

/* KPIs personalizados */
.kpi-row{
  display:grid;
  grid-template-columns:repeat(4,minmax(0,1fr));
  gap:0.75rem;
}

.kpi-card{
  background:radial-gradient(circle at top left,#111827 0,var(--bg-card) 55%);
  border-radius:1.1rem;
  padding:0.9rem 1rem;
  border:1px solid rgba(55,65,81,0.8);
  box-shadow:0 20px 40px rgba(0,0,0,0.75);
  position:relative;
  overflow:hidden;
}

.kpi-label{
  font-size:0.75rem;
  color:var(--text-muted);
  margin-bottom:0.35rem;
}

.kpi-value{
  font-size:1.25rem;
  font-weight:600;
  letter-spacing:0.01em;
  margin-bottom:0.25rem;
}

.kpi-pill{
  display:inline-flex;
  align-items:center;
  gap:0.25rem;
  padding:0.15rem 0.55rem;
  border-radius:999px;
  font-size:0.70rem;
  border:1px solid rgba(75,85,99,0.9);
  color:#9ca3af;
  background:rgba(15,23,42,0.9);
}

/* Destaque pequeno */
.badge-soft{
  display:inline-flex;
  align-items:center;
  gap:0.35rem;
  padding:0.15rem 0.45rem;
  border-radius:999px;
  border:1px solid rgba(55,65,81,0.9);
  font-size:0.70rem;
  color:#9ca3af;
  background:rgba(15,23,42,0.9);
}

/* Caixas laterais */
.side-card{
  background:radial-gradient(circle at top left,#111827 0,#020617 55%);
  border-radius:1.1rem;
  padding:1rem 1.1rem;
  border:1px solid #1f2937;
  box-shadow:0 20px 38px rgba(0,0,0,0.8);
}

/* Slider */
.stSlider > div > div > div {
  color:var(--text-primary) !important;
}

/* Inputs */
.stTextInput>div>div>input,
.stNumberInput input{
  background-color:#020617;
  border-radius:0.6rem;
  border:1px solid #1f2937;
  color:#e5e7eb;
  font-size:0.85rem;
}

.stSelectbox > div > div {
  background-color:#020617;
  border-radius:0.6rem;
  border:1px solid #1f2937;
}

/* Botões */
.stButton>button{
  border-radius:999px;
  padding:0.4rem 0.9rem;
  font-size:0.85rem;
  border:1px solid #374151;
  background:linear-gradient(135deg,#facc15,#f97316);
  color:#111827;
  font-weight:600;
  box-shadow:0 18px 40px rgba(0,0,0,0.9);
}

.stButton>button:hover{
  filter:brightness(1.08);
}

/* Expander */
.st-expander{
  border-radius:0.85rem;
  border:1px solid #1f2937;
  background-color:#020617;
}

/* Tooltipzinho helper */
.helper{
  font-size:0.75rem;
  color:#9ca3af;
  margin-top:0.15rem;
}

/* Rodapé discreto */
.footer-note{
  font-size:0.7rem;
  color:#4b5563;
  margin-top:1rem;
  text-align:right;
}
</style>
"""
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


# --------------------------------------------------
# FUNÇÕES UTILITÁRIAS
# --------------------------------------------------
@st.cache_data(ttl=60 * 5)
def carregar_planilha():
    return pd.read_excel(URL_PLANILHA, sheet_name=None)


def limpar_aba(xls, nome_aba: str) -> pd.DataFrame:
    """
    Lê a aba e corrige casos onde o Excel tem um título na primeira linha
    (ex: 'COMPRAS') e os cabeçalhos verdadeiros estão na primeira linha de dados.
    """
    if isinstance(xls, dict):
        df = xls.get(nome_aba)
    else:
        df = pd.read_excel(xls, sheet_name=nome_aba)

    if df is None:
        st.error(f"Aba '{nome_aba}' não encontrada na planilha.")
        st.stop()

    df = df.copy()

    # Tenta detectar se as colunas atuais são genéricas (ex: COMPRAS, Unnamed: 1...)
    cols_original = [str(c).strip() for c in df.columns]
    cols_upper = [c.upper() for c in cols_original]

    # Marcadores típicos de cabeçalho real
    marcadores = [
        "DATA",
        "PRODUTO",
        "STATUS",
        "QUANTIDADE",
        "CUSTO UNITÁRIO",
        "QTD",
        "VALOR TOTAL",
    ]

    def lista_tem_marcador(lista):
        return any(m in lista for m in marcadores)

    # Se as colunas atuais NÃO têm nenhum dos marcadores,
    # tentamos promover a primeira linha a cabeçalho
    if not lista_tem_marcador(cols_upper) and not df.empty:
        primeira_linha = df.iloc[0].astype(str).str.strip()
        primeira_upper = [s.upper() for s in primeira_linha]

        if lista_tem_marcador(primeira_upper):
            # Usa a primeira linha como cabeçalho
            df = df.iloc[1:].copy()
            df.columns = primeira_linha

    # Ajuste final de nomes de coluna
    df.columns = [str(c).strip() for c in df.columns]

    # Remove linhas de TOTAL
    if not df.empty:
        df = df[~df.iloc[:, 0].astype(str).str.contains("TOTAL", case=False, na=False)]

    return df


def parse_money(x):
    if pd.isna(x):
        return 0.0
    if isinstance(x, (int, float)):
        return float(x)
    s = str(x)
    s = s.replace("R$", "").replace(" ", "")
    s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except Exception:
        return 0.0


def format_reais(v: float) -> str:
    try:
        return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ 0,00"


# --------------------------------------------------
# CARREGAR DADOS BÁSICOS
# --------------------------------------------------
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
        if qtd_venda <= 0:
            continue

        if produto not in estoque:
            continue

        qtd_restante = qtd_venda
        custo_total = 0.0
        valor_total = float(row["VALOR TOTAL"])
        data_venda = row["DATA"]

        while qtd_restante > 0 and estoque[produto]:
            lote = estoque[produto][0]
            qtd_lote = lote["qtd"]
            custo_unit = lote["custo"]

            if qtd_lote <= qtd_restante:
                custo_total += qtd_lote * custo_unit
                qtd_restante -= qtd_lote
                estoque[produto].pop(0)
            else:
                custo_total += qtd_restante * custo_unit
                estoque[produto][0]["qtd"] = qtd_lote - qtd_restante
                qtd_restante = 0

        if qtd_restante > 0:
            continue

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
    if mask_insano.any():
        df_fifo = df_fifo[~mask_insano].copy()

    if df_fifo.empty:
        st.warning("Todas as vendas ficaram inválidas após o filtro de custo unitário.")
        return pd.DataFrame(), pd.DataFrame()

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
# APLICAÇÃO
# --------------------------------------------------
st.title("📦 Loja Importados – Visão Real (FIFO)")

st.markdown(
    """
<div class="badge-soft">
  📌 Painel focado em lucro real, reposição inteligente e saúde do estoque.
</div>
""",
    unsafe_allow_html=True,
)

st.markdown("")

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
    st.warning("Não há dados suficientes para montar o painel (vendas/estoque vazio).")
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
<div class="section-sub">Resumo financeiro real, já considerando custo das compras via FIFO.</div>
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

    if df_fifo_filt.empty:
        st.info("Nenhuma venda encontrada para o período selecionado.")
        st.stop()

    receita_total = df_fifo_filt["VALOR_TOTAL"].sum()
    custo_total = df_fifo_filt["CUSTO_TOTAL"].sum()
    lucro_total = df_fifo_filt["LUCRO"].sum()

    margem_pct = (lucro_total / receita_total * 100) if receita_total != 0 else 0

    if not df_estoque.empty:
        valor_estoque_total = df_estoque["VALOR_ESTOQUE"].sum()
    else:
        valor_estoque_total = 0.0

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(
            f"""
<div class="kpi-card">
  <div class="kpi-label">Faturamento do período</div>
  <div class="kpi-value">{format_reais(receita_total)}</div>
  <div class="kpi-pill">Somatório de vendas do período</div>
</div>
""",
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f"""
<div class="kpi-card">
  <div class="kpi-label">Custo real (FIFO)</div>
  <div class="kpi-value">{format_reais(custo_total)}</div>
  <div class="kpi-pill">Custo das unidades efetivamente vendidas</div>
</div>
""",
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            f"""
<div class="kpi-card">
  <div class="kpi-label">Lucro líquido</div>
  <div class="kpi-value">{format_reais(lucro_total)}</div>
  <div class="kpi-pill">Receita - custo real (FIFO)</div>
</div>
""",
            unsafe_allow_html=True,
        )

    with col4:
        st.markdown(
            f"""
<div class="kpi-card">
  <div class="kpi-label">Margem do período</div>
  <div class="kpi-value">{margem_pct:,.1f}%</div>
  <div class="kpi-pill">Lucro / receita</div>
</div>
""",
            unsafe_allow_html=True,
        )

    st.markdown("---")

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

        top_prod["PRECO_MEDIO_VENDA"] = top_prod["RECEITA"] / top_prod["QTD_VENDIDA"].replace(0, pd.NA)
        top_prod["CUSTO_MEDIO_VENDIDO"] = top_prod["CUSTO"] / top_prod["QTD_VENDIDA"].replace(0, pd.NA)
        top_prod["MARGEM_PCT"] = (
            (top_prod["LUCRO"] / top_prod["RECEITA"]) * 100
        ).replace([pd.NA, float("inf")], 0)

        top6 = top_prod.sort_values("QTD_VENDIDA", ascending=False).head(6).copy()

        if top6.empty:
            st.info("Nenhum produto com vendas suficientes para o ranking.")
        else:
            fig = px.bar(
                top6,
                x="PRODUTO",
                y="QTD_VENDIDA",
                text="QTD_VENDIDA",
            )
            fig.update_traces(
                textposition="outside",
            )
            fig.update_layout(
                height=360,
                xaxis_title="Produto",
                yaxis_title="Qtd vendida (período)",
                margin=dict(l=10, r=10, t=10, b=10),
                plot_bgcolor="#020617",
                paper_bgcolor="#020617",
                font=dict(color="#e5e7eb"),
            )
            st.plotly_chart(fig, use_container_width=True)

            st.markdown("##### Detalhes dos TOP 6 produtos")
            df_top_view = top6[
                [
                    "PRODUTO",
                    "QTD_VENDIDA",
                    "RECEITA",
                    "CUSTO",
                    "LUCRO",
                    "PRECO_MEDIO_VENDA",
                    "CUSTO_MEDIO_VENDIDO",
                    "MARGEM_PCT",
                    "SALDO_QTD",
                ]
            ].copy()
            df_top_view["RECEITA"] = df_top_view["RECEITA"].map(format_reais)
            df_top_view["CUSTO"] = df_top_view["CUSTO"].map(format_reais)
            df_top_view["LUCRO"] = df_top_view["LUCRO"].map(format_reais)
            df_top_view["PRECO_MEDIO_VENDA"] = df_top_view["PRECO_MEDIO_VENDA"].map(format_reais)
            df_top_view["CUSTO_MEDIO_VENDIDO"] = df_top_view["CUSTO_MEDIO_VENDIDO"].map(format_reais)
            df_top_view["MARGEM_PCT"] = df_top_view["MARGEM_PCT"].map(lambda v: f"{v:,.1f}%")

            df_top_view = df_top_view.rename(
                columns={
                    "PRODUTO": "Produto",
                    "QTD_VENDIDA": "Qtd vendida (período)",
                    "RECEITA": "Receita",
                    "CUSTO": "Custo real (FIFO)",
                    "LUCRO": "Lucro",
                    "PRECO_MEDIO_VENDA": "Preço médio venda",
                    "CUSTO_MEDIO_VENDIDO": "Custo médio vendido",
                    "MARGEM_PCT": "Margem",
                    "SALDO_QTD": "Estoque atual",
                }
            )

            st.dataframe(df_top_view, use_container_width=True)

    st.markdown("---")

    st.markdown(
        """
<div class="section-title">📈 Evolução mensal de faturamento x lucro</div>
<div class="section-sub">Com base em todas as vendas registradas, agrupadas por mês.</div>
""",
        unsafe_allow_html=True,
    )

    df_mes = (
        df_fifo.groupby("MES_ANO", as_index=False)
        .agg(
            RECEITA=("VALOR_TOTAL", "sum"),
            CUSTO=("CUSTO_TOTAL", "sum"),
            LUCRO=("LUCRO", "sum"),
        )
        .sort_values("MES_ANO")
    )

    df_mes["MARGEM"] = (df_mes["LUCRO"] / df_mes["RECEITA"].replace(0, pd.NA)) * 100

    if df_mes.empty:
        st.info("Não há dados suficientes para montar a evolução mensal.")
    else:
        fig = px.bar(
            df_mes,
            x="MES_ANO",
            y="RECEITA",
            text="RECEITA",
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

    st.markdown(
        """
<div class="section-title">🧾 Vendas detalhadas (com custo FIFO)</div>
<div class="section-sub">
Visualize cada venda com custo FIFO aplicado, para entender onde o lucro está nascendo – e onde está morrendo.
</div>
""",
        unsafe_allow_html=True,
    )

    df_view = df_fifo_filt.copy()
    df_view["DATA"] = pd.to_datetime(df_view["DATA"], errors="coerce")
    df_view["DATA_FMT"] = df_view["DATA"].dt.strftime("%d/%m/%Y")

    df_view["VALOR_TOTAL_FMT"] = df_view["VALOR_TOTAL"].map(format_reais)
    df_view["CUSTO_TOTAL_FMT"] = df_view["CUSTO_TOTAL"].map(format_reais)
    df_view["LUCRO_FMT"] = df_view["LUCRO"].map(format_reais)
    df_view["CUSTO_UNIT_FMT"] = df_view["CUSTO_UNIT"].map(format_reais)

    cols = [
        "DATA_FMT",
        "PRODUTO",
        "QTD",
        "VALOR_TOTAL_FMT",
        "CUSTO_TOTAL_FMT",
        "LUCRO_FMT",
        "CUSTO_UNIT_FMT",
    ]
    cols = [c for c in cols if c in df_view.columns]

    st.dataframe(
        df_view[cols]
        .rename(
            columns={
                "DATA_FMT": "Data",
                "QTD": "Qtd",
                "VALOR_TOTAL_FMT": "Valor total",
                "CUSTO_TOTAL_FMT": "Custo total",
                "LUCRO_FMT": "Lucro",
                "CUSTO_UNIT_FMT": "Custo unitário (FIFO)",
            }
        )
        .sort_values("Data", ascending=False),
        use_container_width=True,
    )


# --------------------------------------------------
# TAB 2 – PESQUISA DE PRODUTO
# --------------------------------------------------
with tab_search:
    st.markdown(
        """
<div class="section-title">🔎 Pesquisa detalhada de produto</div>
<div class="section-sub">
Veja custo médio FIFO, histórico de vendas e comportamento do produto ao longo do tempo.
</div>
""",
        unsafe_allow_html=True,
    )

    produtos_unicos = sorted(df_fifo["PRODUTO"].dropna().unique().tolist())

    produto_sel = st.selectbox("Escolha o produto:", produtos_unicos)

    df_prod = df_fifo[df_fifo["PRODUTO"] == produto_sel].copy()
    if df_prod.empty:
        st.info("Nenhuma venda encontrada para esse produto.")
    else:
        df_prod["DATA"] = pd.to_datetime(df_prod["DATA"], errors="coerce")
        df_prod = df_prod.sort_values("DATA")

        qtd_total_vendida = df_prod["QTD"].sum()
        receita_prod = df_prod["VALOR_TOTAL"].sum()
        custo_prod = df_prod["CUSTO_TOTAL"].sum()
        lucro_prod = df_prod["LUCRO"].sum()
        preco_medio = receita_prod / qtd_total_vendida if qtd_total_vendida != 0 else 0.0
        custo_medio = custo_prod / qtd_total_vendida if qtd_total_vendida != 0 else 0.0
        margem_pct_prod = (lucro_prod / receita_prod * 100) if receita_prod != 0 else 0

        saldo_estoque_prod = 0
        custo_medio_fifo_prod = 0.0
        if not df_estoque.empty and produto_sel in df_estoque["PRODUTO"].values:
            row_est = df_estoque[df_estoque["PRODUTO"] == produto_sel].iloc[0]
            saldo_estoque_prod = row_est["SALDO_QTD"]
            custo_medio_fifo_prod = row_est["CUSTO_MEDIO_FIFO"]

        colA, colB, colC, colD = st.columns(4)
        with colA:
            st.markdown(
                f"""
<div class="kpi-card">
  <div class="kpi-label">Receita total do produto</div>
  <div class="kpi-value">{format_reais(receita_prod)}</div>
  <div class="kpi-pill">Somatório de vendas</div>
</div>
""",
                unsafe_allow_html=True,
            )
        with colB:
            st.markdown(
                f"""
<div class="kpi-card">
  <div class="kpi-label">Lucro total do produto</div>
  <div class="kpi-value">{format_reais(lucro_prod)}</div>
  <div class="kpi-pill">Receita - custo real (FIFO)</div>
</div>
""",
                unsafe_allow_html=True,
            )
        with colC:
            st.markdown(
                f"""
<div class="kpi-card">
  <div class="kpi-label">Margem percentual</div>
  <div class="kpi-value">{margem_pct_prod:,.1f}%</div>
  <div class="kpi-pill">Lucro / receita</div>
</div>
""",
                unsafe_allow_html=True,
            )
        with colD:
            st.markdown(
                f"""
<div class="kpi-card">
  <div class="kpi-label">Estoque atual (unidades)</div>
  <div class="kpi-value">{int(saldo_estoque_prod)}</div>
  <div class="kpi-pill">Custo médio FIFO: {format_reais(custo_medio_fifo_prod)}</div>
</div>
""",
                unsafe_allow_html=True,
            )

        st.markdown("---")

        st.markdown(
            """
<div class="section-title">📊 Evolução de vendas e preço médio</div>
<div class="section-sub">Veja como o produto se comportou ao longo do tempo.</div>
""",
            unsafe_allow_html=True,
        )

        df_prod["MES_ANO"] = df_prod["DATA"].dt.strftime("%Y-%m")
        df_mes_prod = (
            df_prod.groupby("MES_ANO", as_index=False)
            .agg(
                QTD_MES=("QTD", "sum"),
                RECEITA_MES=("VALOR_TOTAL", "sum"),
                CUSTO_MES=("CUSTO_TOTAL", "sum"),
            )
            .sort_values("MES_ANO")
        )
        df_mes_prod["PRECO_MEDIO_MES"] = df_mes_prod["RECEITA_MES"] / df_mes_prod[
            "QTD_MES"
        ].replace(0, pd.NA)

        if df_mes_prod.empty:
            st.info("Sem histórico mensal consolidado para esse produto.")
        else:
            fig2 = px.bar(
                df_mes_prod,
                x="MES_ANO",
                y="QTD_MES",
                text="QTD_MES",
            )
            fig2.update_traces(textposition="outside")
            fig2.update_layout(
                height=320,
                xaxis_title="Mês",
                yaxis_title="Qtd vendida",
                plot_bgcolor="#020617",
                paper_bgcolor="#020617",
                font=dict(color="#e5e7eb"),
            )
            st.plotly_chart(fig2, use_container_width=True)

        st.markdown("---")

        st.markdown("#### 🕒 Última venda")
        ultima = df_prod.sort_values("DATA", ascending=False).iloc[0]
        data_ultima = ultima["DATA"]
        preco_unit_ultima = ultima["VALOR_TOTAL"] / ultima["QTD"]

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

        df_hist = df_prod.copy()
        df_hist["DATA_FMT"] = df_hist["DATA"].dt.strftime("%d/%m/%Y")
        df_hist["VALOR_TOTAL_FMT"] = df_hist["VALOR_TOTAL"].map(format_reais)
        df_hist["CUSTO_TOTAL_FMT"] = df_hist["CUSTO_TOTAL"].map(format_reais)
        df_hist["LUCRO_FMT"] = df_hist["LUCRO"].map(format_reais)
        df_hist["CUSTO_UNIT_FMT"] = df_hist["CUSTO_UNIT"].map(format_reais)

        cols_hist = [
            "DATA_FMT",
            "QTD",
            "VALOR_TOTAL_FMT",
            "CUSTO_TOTAL_FMT",
            "LUCRO_FMT",
            "CUSTO_UNIT_FMT",
        ]
        cols_hist = [c for c in cols_hist if c in df_hist.columns]

        st.dataframe(
            df_hist[cols_hist]
            .rename(
                columns={
                    "DATA_FMT": "Data",
                    "QTD": "Qtd",
                    "VALOR_TOTAL_FMT": "Valor total",
                    "CUSTO_TOTAL_FMT": "Custo total",
                    "LUCRO_FMT": "Lucro",
                    "CUSTO_UNIT_FMT": "Custo unitário (FIFO)",
                }
            )
            .sort_values("Data", ascending=False),
            use_container_width=True,
        )


# --------------------------------------------------
# TAB 3 – ALERTAS
# --------------------------------------------------
with tab_alerts:
    st.markdown(
        """
<div class="section-title">⚠️ Alertas de estoque e saúde da loja</div>
<div class="section-sub">
Foque onde dói: produtos que vendem muito e podem faltar, itens parados e concentração de estoque.
</div>
""",
        unsafe_allow_html=True,
    )

    if df_estoque.empty:
        st.info("Sem dados de estoque para gerar alertas.")
    else:
        df_estoque_alert = df_estoque.copy()
        df_estoque_alert["VALOR_ESTOQUE_FMT"] = df_estoque_alert["VALOR_ESTOQUE"].map(
            format_reais
        )

        df_venda_hist = (
            df_fifo.groupby("PRODUTO", as_index=False)
            .agg(
                QTD_VENDIDA_TOTAL=("QTD", "sum"),
                RECEITA_TOTAL=("VALOR_TOTAL", "sum"),
            )
            .sort_values("QTD_VENDIDA_TOTAL", ascending=False)
        )

        base_alerta = df_estoque_alert.merge(
            df_venda_hist, on="PRODUTO", how="left"
        ).fillna({"QTD_VENDIDA_TOTAL": 0, "RECEITA_TOTAL": 0})

        st.markdown(
            """
<div class="section-title">🎯 Ajuste dos critérios</div>
<div class="section-sub">
Personalize os números que definem quando algo é “bom demais para faltar” ou “parado demais para ficar”.
</div>
""",
            unsafe_allow_html=True,
        )

        colA1, colA2, colA3 = st.columns(3)
        with colA1:
            LIM_VENDE_BEM = st.number_input(
                "Vende bem a partir de quantas unid. no histórico?",
                min_value=1,
                value=20,
                step=1,
            )
        with colA2:
            LIM_ESTOQUE_BAIXO = st.number_input(
                "Estoque muito baixo a partir de quantas unid.?",
                min_value=1,
                value=5,
                step=1,
            )
        with colA3:
            LIM_DIAS_PARADO = st.number_input(
                "Considerar parado há quantos dias sem vender?",
                min_value=15,
                value=60,
                step=5,
            )

        st.markdown("---")

        st.markdown(
            """
<div class="section-title">🔥 Vendendo forte com estoque perigoso</div>
<div class="section-sub">
Produtos que giram bem, mas já estão com poucas unidades – risco real de ruptura se não repor.
</div>
""",
            unsafe_allow_html=True,
        )

        df_fifo_alert = df_fifo.copy()
        df_fifo_alert["DATA"] = pd.to_datetime(df_fifo_alert["DATA"], errors="coerce")

        corte_data = pd.Timestamp.now() - pd.Timedelta(days=LIM_DIAS_PARADO)

        vendas_recentes = (
            df_fifo_alert[df_fifo_alert["DATA"] >= corte_data]
            .groupby("PRODUTO", as_index=False)["QTD"]
            .sum()
            .rename(columns={"QTD": "QTD_VENDIDA_RECENTE"})
        )

        vendendo_bem_baixo_estoque = base_alerta.merge(
            vendas_recentes, on="PRODUTO", how="left"
        ).fillna({"QTD_VENDIDA_RECENTE": 0})

        vendendo_bem_baixo_estoque = vendendo_bem_baixo_estoque[
            (vendendo_bem_baixo_estoque["QTD_VENDIDA_RECENTE"] >= LIM_VENDE_BEM)
            & (vendendo_bem_baixo_estoque["SALDO_QTD"] > 0)
            & (vendendo_bem_baixo_estoque["SALDO_QTD"] <= LIM_ESTOQUE_BAIXO)
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

        df_compras_alert["DATA"] = pd.to_datetime(
            df_compras_alert["DATA"], errors="coerce", dayfirst=True
        )

        df_ult_compra = (
            df_compras_alert.groupby("PRODUTO", as_index=False)["DATA"]
            .max()
            .rename(columns={"DATA": "DATA_ULTIMA_COMPRA"})
        )

        df_merged_parado = df_estoque_alert.merge(
            df_ult_compra, on="PRODUTO", how="left"
        )

        df_merged_parado["DIAS_DESDE_ULT_COMPRA"] = (
            pd.Timestamp.now() - df_merged_parado["DATA_ULTIMA_COMPRA"]
        ).dt.days

        df_parado = df_merged_parado[
            (df_merged_parado["SALDO_QTD"] > 0)
            & (df_merged_parado["DIAS_DESDE_ULT_COMPRA"] >= LIM_DIAS_PARADO)
        ].copy()

        if df_parado.empty:
            st.info("Nenhum produto parado pelo critério de dias sem comprar.")
        else:
            df_parado["VALOR_ESTOQUE_FMT"] = df_parado["VALOR_ESTOQUE"].map(format_reais)
            df_parado = df_parado.sort_values(
                ["DIAS_DESDE_ULT_COMPRA", "VALOR_ESTOQUE"], ascending=[False, False]
            )

            st.dataframe(
                df_parado[
                    [
                        "PRODUTO",
                        "SALDO_QTD",
                        "VALOR_ESTOQUE_FMT",
                        "DIAS_DESDE_ULT_COMPRA",
                    ]
                ].rename(
                    columns={
                        "PRODUTO": "Produto",
                        "SALDO_QTD": "Estoque atual",
                        "VALOR_ESTOQUE_FMT": "Valor em estoque (FIFO)",
                        "DIAS_DESDE_ULT_COMPRA": "Dias desde última compra",
                    }
                ),
                use_container_width=True,
            )

        st.markdown("### 🧱 Concentração de estoque (risco)")

        if df_estoque_alert.empty:
            st.info("Sem dados de estoque para essa análise.")
        else:
            df_risco = df_estoque_alert.copy()
            df_risco = df_risco.sort_values("VALOR_ESTOQUE", ascending=False)
            total_estoque = df_risco["VALOR_ESTOQUE"].sum()
            df_risco["PCT_ESTOQUE"] = (
                df_risco["VALOR_ESTOQUE"] / total_estoque * 100
                if total_estoque > 0
                else 0
            )

            top5 = df_risco.head(5).copy()
            pct_estoque_top5 = top5["PCT_ESTOQUE"].sum()

            fig_risco = px.bar(
                top5,
                x="PRODUTO",
                y="VALOR_ESTOQUE",
                text="VALOR_ESTOQUE",
            )
            fig_risco.update_traces(
                textposition="outside",
                texttemplate="%{text}",
            )
            fig_risco.update_layout(
                height=320,
                xaxis_title="Produto",
                yaxis_title="Valor em estoque (R$)",
                plot_bgcolor="#020617",
                paper_bgcolor="#020617",
                font=dict(color="#e5e7eb"),
            )
            st.plotly_chart(fig_risco, use_container_width=True)

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
            f"*Critérios atuais:* vende bem ≥ **{LIM_VENDE_BEM} unid. no período recente**, estoque baixo ≤ **{LIM_ESTOQUE_BAIXO} unid.**, parado ≥ **{LIM_DIAS_PARADO} dias**."
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

    # Cópia da aba de compras
    dfc = df_compras.copy()
    dfc.columns = [c.strip().upper() for c in dfc.columns]

    # Precisa ter coluna DATA
    if "DATA" not in dfc.columns:
        st.info("A aba COMPRAS da planilha precisa ter uma coluna 'DATA'.")
    else:
        # Converte DATA
        dfc["DATA"] = pd.to_datetime(dfc["DATA"], errors="coerce", dayfirst=True)

        # Considera só compras ENTREGUE (coerente com o FIFO)
        if "STATUS" in dfc.columns:
            dfc = dfc[dfc["STATUS"].astype(str).str.upper() == "ENTREGUE"].copy()

        # Quantidade
        if "QUANTIDADE" in dfc.columns:
            dfc["QUANTIDADE"] = dfc["QUANTIDADE"].apply(parse_money).astype(float)
        else:
            dfc["QUANTIDADE"] = 0.0

        # Custo unitário
        if "CUSTO UNITÁRIO" in dfc.columns:
            dfc["CUSTO UNITÁRIO"] = dfc["CUSTO UNITÁRIO"].apply(parse_money).astype(float)
        else:
            dfc["CUSTO UNITÁRIO"] = 0.0

        # Custo total (sempre recalculado)
        dfc["CUSTO_TOTAL"] = dfc["QUANTIDADE"] * dfc["CUSTO_UNITÁRIO"]

        # Mês/ano para filtro
        dfc["MES_ANO"] = dfc["DATA"].dt.strftime("%Y-%m")

        if dfc["MES_ANO"].dropna().empty:
            st.info("Não encontrei compras com DATA válida para montar a aba de Compras.")
        else:
            # ------------------------------
            # Filtro de mês (mês atual pré-selecionado)
            # ------------------------------
            meses_comp = ["Todos"]
            meses_disp_comp = sorted(
                dfc["MES_ANO"].dropna().unique().tolist(),
                reverse=True
            )
            meses_comp += meses_disp_comp

            mes_atual = pd.Timestamp.now().strftime("%Y-%m")
            idx_padrao = meses_comp.index(mes_atual) if mes_atual in meses_comp else 0

            mes_sel_comp = st.selectbox(
                "Filtrar compras por mês (AAAA-MM):",
                meses_comp,
                index=idx_padrao,
            )

            if mes_sel_comp == "Todos":
                dfc_filt = dfc.copy()
            else:
                dfc_filt = dfc[dfc["MES_ANO"] == mes_sel_comp].copy()

            if dfc_filt.empty:
                st.info("Não há compras no período selecionado.")
            else:
                # ------------------------------
                # KPIs principais
                # ------------------------------
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

                # ------------------------------
                # Top produtos comprados no período
                # ------------------------------
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

                # ------------------------------
                # Tabela detalhada de compras
                # ------------------------------
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

                # Formatações
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
