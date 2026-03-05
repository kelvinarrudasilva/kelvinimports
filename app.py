import streamlit as st
import pandas as pd
import plotly.express as px
from urllib.parse import quote

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
/* HOVER + COMPACT GRID */
.stDataFrame tbody tr:hover td{
  background:#111827 !important;
}
.stDataFrame td, .stDataFrame th{
  padding:6px 10px !important;
  font-size:12px !important;
  line-height:1.2 !important;
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

/* TABELA HTML COMPACTA (GRID) */
.compact-wrap{ width:100%; overflow:auto; border:1px solid var(--border-soft); border-radius:14px; }
.compact-grid{ width:100%; border-collapse:separate; border-spacing:0; font-size:12px; }
.compact-grid thead th{
  position:sticky; top:0;
  background:#111827;
  color:#e5e7eb;
  text-transform:uppercase;
  letter-spacing:0.12em;
  font-size:11px;
  padding:8px 10px;
  border-bottom:1px solid var(--border-soft);
  text-align:left;
  white-space:nowrap;
}
.compact-grid td{
  padding:7px 10px;
  border-bottom:1px solid #121212;
  vertical-align:middle;
  white-space:nowrap;
}
.compact-grid tbody tr:nth-child(odd) td{ background:#050505; }
.compact-grid tbody tr:nth-child(even) td{ background:#0a0a0a; }
.compact-grid tbody tr:hover td{ background:#111827 !important; }
.compact-grid .prodcell{ display:flex; align-items:center; gap:8px; }
.compact-grid a.lens{ text-decoration:none; font-size:13px; }
.compact-grid a.lens:hover{ filter:brightness(1.2); }
.compact-grid .muted{ color:var(--muted); }

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


def ensure_df(obj):
    """Garante um DataFrame (mesmo se vier torto)."""
    if isinstance(obj, pd.DataFrame):
        return obj
    try:
        return pd.DataFrame(obj)
    except Exception:
        return pd.DataFrame()

def ensure_datetime_series(df: pd.DataFrame, col: str):
    """Converte uma coluna para datetime sem quebrar."""
    df = ensure_df(df)
    if col not in df.columns:
        df[col] = pd.NaT
    try:
        df[col] = pd.to_datetime(df[col], errors="coerce", dayfirst=True)
    except Exception:
        df[col] = pd.to_datetime(pd.Series([pd.NaT] * len(df)), errors="coerce")
    
    return df

def ensure_col_from_aliases(df: pd.DataFrame, target: str, aliases, default=0):
    """Garante df[target]. Se não existir, tenta copiar de aliases, senão cria com default."""
    df = ensure_df(df).copy()
    if target in df.columns:
        return df
    for a in aliases:
        if a in df.columns:
            df[target] = df[a]
            return df
    df[target] = default
    return df

def normalize_sales_like(df: pd.DataFrame):
    """Normaliza nomes/alias comuns em VENDAS ou dataframes derivados."""
    df = ensure_df(df).copy()
    # nomes com espaço -> underscore (apenas alguns críticos)
    df = df.rename(columns={
        "VALOR TOTAL": "VALOR_TOTAL",
        "VALOR TOTAL (R$)": "VALOR_TOTAL",
        "VALOR VENDA": "VALOR_VENDA",
        "LUCRO TOTAL": "LUCRO",
        "QTD.": "QTD",
        "QTDE": "QTD",
        "QUANTIDADE": "QTD",
        "QUANT": "QTD",
        "QNT": "QTD",
    })
    # garante colunas essenciais
    df = ensure_col_from_aliases(df, "DATA", ["DATA", "DATA_VENDA", "DIA"], default=pd.NaT)
    df = ensure_col_from_aliases(df, "PRODUTO", ["PRODUTO", "ITEM", "DESCRICAO"], default="")
    df = ensure_col_from_aliases(df, "QTD", ["QTD", "QTD.", "QTDE", "QUANTIDADE", "QUANT", "QNT", "QTY"], default=0)

    # valor total: prioriza VALOR_TOTAL; fallback em VALOR_VENDA; se existir VALOR (genérico) usa
    if "VALOR_TOTAL" not in df.columns:
        if "VALOR_VENDA" in df.columns:
            df["VALOR_TOTAL"] = df["VALOR_VENDA"]
        elif "VALOR" in df.columns:
            df["VALOR_TOTAL"] = df["VALOR"]
        else:
            df["VALOR_TOTAL"] = 0.0

    # cliente/status (não quebra se não existir)
    df = ensure_col_from_aliases(df, "CLIENTE", ["CLIENTE", "NOME", "COMPRADOR"], default="")
    df = ensure_col_from_aliases(df, "STATUS", ["STATUS", "SITUACAO"], default="")

    # lucro (se faltar, cria 0)
    df = ensure_col_from_aliases(df, "LUCRO", ["LUCRO", "LUCRO_TOTAL", "LUCRO TOTAL"], default=0.0)
    return df


def detectar_linha_cabecalho(df_raw: pd.DataFrame, must_have):
    # procura até 200 linhas
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
        # garante numérico bonitinho
        out[nome_col] = out[nome_col].apply(lambda x: int(round(float(x))) if pd.notna(x) else 0)
    else:
        out[nome_col] = 0
    return out

def _render_compact_table(rows, headers):
    """Renderiza uma tabela HTML compacta com hover e links na coluna Produto."""
    thead = "".join([f"<th>{h}</th>" for h in headers])
    tbody = "".join(rows)
    return f'''
<div class="compact-wrap">
  <table class="compact-grid">
    <thead><tr>{thead}</tr></thead>
    <tbody>{tbody}</tbody>
  </table>
</div>
'''

def _td(txt, cls=""):
    c = f' class="{cls}"' if cls else ""
    return f"<td{c}>{txt}</td>"

def _safe(s):
    if s is None:
        return ""
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")



# --------------------------------------------------
# NAVEGAÇÃO (no lugar de st.tabs, pra permitir ir pra Pesquisa via 🔍)
# --------------------------------------------------
if "nav_tab" not in st.session_state:
    st.session_state.nav_tab = "📊 Dashboard"
if "produto_pesquisa" not in st.session_state:
    st.session_state.produto_pesquisa = None

# Se veio de um link da 🔍 (query param), já abre a Pesquisa com o produto selecionado
try:
    qp = st.query_params
    qp_prod = qp.get("produto", None)
    if isinstance(qp_prod, list):
        qp_prod = qp_prod[0] if qp_prod else None
    if qp_prod:
        st.session_state.produto_pesquisa = str(qp_prod)
        st.session_state["_nav_pending"] = "🔎 Pesquisa de produto"
        # limpa a URL (pra não ficar preso)
        try:
            st.query_params.clear()
        except Exception:
            pass
except Exception:
    pass


# aplica navegação pendente (evita erro de setar session_state do rádio após o widget existir)
if "_nav_pending" in st.session_state:
    st.session_state.nav_tab = st.session_state["_nav_pending"]
    del st.session_state["_nav_pending"]

NAV_OPTS = ["📊 Dashboard", "🔎 Pesquisa de produto", "⚠️ Alertas", "🧾 Compras"]
if st.session_state.nav_tab not in NAV_OPTS:
    st.session_state.nav_tab = "📊 Dashboard"

nav_index = NAV_OPTS.index(st.session_state.nav_tab)

st.radio(
    "Navegação",
    options=NAV_OPTS,
    index=nav_index,
    key="nav_tab",
    horizontal=True,
    label_visibility="collapsed",
)

nav = st.session_state.nav_tab

# --------------------------------------------------
# TELAS
# --------------------------------------------------
if nav == "📊 Dashboard":

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

    
    # --------------------------------------------------
    # GRÁFICO – FATURAMENTO + LUCRO (mês atual e 2 anteriores)
    # --------------------------------------------------
    st.markdown(
        """
<div class="section-title">📈 Faturamento & Lucro – mês atual e 2 anteriores</div>
<div class="section-sub">Dois termômetros do caixa: o que entrou e o que sobrou (lucro FIFO), lado a lado.</div>
""",
        unsafe_allow_html=True,
    )

    df_mes = df_fifo.dropna(subset=["MES_ANO"]).copy()
    if df_mes.empty:
        st.info("Sem dados suficientes para montar o gráfico mensal.")
    else:
        # --- Resumo de VENDAS (faturamento + lucro) por mês ---
        resumo_vendas = (
            df_mes.groupby("MES_ANO", as_index=False)[["VALOR_TOTAL", "LUCRO"]]
            .sum()
            .sort_values("MES_ANO")
        )

        # --- Resumo de COMPRAS (ENTREGUE) por mês ---
        dfc_graf = df_compras.copy()
        if isinstance(dfc_graf, pd.DataFrame) and not dfc_graf.empty:
            dfc_graf.columns = [str(c).strip().upper() for c in dfc_graf.columns]
            if "STATUS" in dfc_graf.columns:
                dfc_graf = dfc_graf[dfc_graf["STATUS"].astype(str).str.upper() == "ENTREGUE"].copy()
            if "DATA" in dfc_graf.columns:
                dfc_graf["DATA"] = pd.to_datetime(dfc_graf["DATA"], errors="coerce", dayfirst=True)
                dfc_graf["MES_ANO"] = dfc_graf["DATA"].dt.strftime("%Y-%m")
            if "QUANTIDADE" in dfc_graf.columns:
                dfc_graf["QUANTIDADE"] = dfc_graf["QUANTIDADE"].apply(parse_money).astype(float)
            if "CUSTO UNITÁRIO" in dfc_graf.columns:
                dfc_graf["CUSTO UNITÁRIO"] = dfc_graf["CUSTO UNITÁRIO"].apply(parse_money).astype(float)
            if "MES_ANO" in dfc_graf.columns:
                dfc_graf["CUSTO_TOTAL"] = dfc_graf.get("QUANTIDADE", 0) * dfc_graf.get("CUSTO UNITÁRIO", 0)
                resumo_compras = (
                    dfc_graf.groupby("MES_ANO", as_index=False)["CUSTO_TOTAL"]
                    .sum()
                    .rename(columns={"CUSTO_TOTAL": "COMPRAS"})
                )
            else:
                resumo_compras = pd.DataFrame(columns=["MES_ANO", "COMPRAS"])
        else:
            resumo_compras = pd.DataFrame(columns=["MES_ANO", "COMPRAS"])

        resumo_mes = resumo_vendas.merge(resumo_compras, on="MES_ANO", how="left")
        resumo_mes["COMPRAS"] = resumo_mes["COMPRAS"].fillna(0.0)

        # --- Escolhe mês atual + 2 anteriores (se existir) ---
        meses_unicos = resumo_mes["MES_ANO"].dropna().tolist()
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

            resumo_mes = resumo_mes[resumo_mes["MES_ANO"].isin(meses_plot)].copy()
            resumo_mes = resumo_mes.sort_values("MES_ANO")

            # --- Rótulo de mês bonito (pt-BR) ---
            _month_map = {
                1: "Jan", 2: "Fev", 3: "Mar", 4: "Abr", 5: "Mai", 6: "Jun",
                7: "Jul", 8: "Ago", 9: "Set", 10: "Out", 11: "Nov", 12: "Dez"
            }
            resumo_mes["_MES_DT"] = pd.to_datetime(resumo_mes["MES_ANO"] + "-01", errors="coerce")
            resumo_mes["MES_LABEL"] = resumo_mes["_MES_DT"].apply(
                lambda d: f"{_month_map.get(int(d.month), '')}/{int(d.year)}" if pd.notna(d) else ""
            )

            # --- Formato longo para plotar 3 métricas ---
            plot_df = resumo_mes.melt(
                id_vars=["MES_ANO", "MES_LABEL"],
                value_vars=["VALOR_TOTAL", "LUCRO", "COMPRAS"],
                var_name="MÉTRICA",
                value_name="VALOR",
            )
            plot_df["MÉTRICA"] = plot_df["MÉTRICA"].map(
                {"VALOR_TOTAL": "Faturamento", "LUCRO": "Lucro (FIFO)", "COMPRAS": "Compras (ENTREGUE)"}
            )
            plot_df["VALOR_FMT"] = plot_df["VALOR"].map(format_reais)

            # Garante ordem correta no eixo X
            ordem_x = resumo_mes["MES_LABEL"].tolist()

            fig = px.bar(
                plot_df,
                x="MES_LABEL",
                y="VALOR",
                color="MÉTRICA",
                barmode="group",
                text="VALOR_FMT",
                labels={"MES_LABEL": "Mês", "VALOR": "Valor (R$)"},
                category_orders={"MES_LABEL": ordem_x},
                color_discrete_map={
                    "Faturamento": "#22c55e",
                    "Lucro (FIFO)": "#14b8a6",
                    "Compras (ENTREGUE)": "#f97316",
                },
            )
            fig.update_traces(
                textposition="inside",
                texttemplate="<b>%{text}</b>",
                insidetextanchor="middle",
                textfont_size=12,
            )
            fig.update_layout(
                height=390,
                yaxis_title="R$",
                xaxis_title="",
                bargap=0.22,
                bargroupgap=0.10,
                uniformtext_minsize=9,
                uniformtext_mode="hide",
                plot_bgcolor="#050505",
                paper_bgcolor="#050505",
                font=dict(
                    family="system-ui, -apple-system, 'Segoe UI', sans-serif",
                    color="#e5e5e5",
                ),
                legend_title_text="",
                margin=dict(l=10, r=10, t=10, b=10),
            )
            fig.update_xaxes(showgrid=False)
            fig.update_yaxes(showgrid=True, gridcolor="#1f2937", zeroline=False)

            st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
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
        # --- Tabela compacta (🔍 abre na Pesquisa) ---
        headers = ["Produto", "Qtd", "Estoque", "Custo FIFO", "Preço médio", "Receita", "Lucro"]
        rows = []
        for _, r in tabela_top.iterrows():
            prod = _safe(r.get("Produto", ""))
            link = f"?produto={quote(prod)}"
            prod_html = f'<div class="prodcell"><a class="lens" href="{link}" target="_self" title="Abrir na Pesquisa">🔍</a><span>{prod}</span></div>'
            rows.append(
                "<tr>"
                + _td(prod_html)
                + _td(_safe(int(r.get("Qtd vendida", 0))))
                + _td(_safe(int(r.get("Estoque atual", 0))))
                + _td(_safe(r.get("Custo médio FIFO (unid.)", "")))
                + _td(_safe(r.get("Preço médio venda (unid.)", "")))
                + _td(_safe(r.get("Receita total", "")))
                + _td(_safe(r.get("Lucro total (FIFO)", "")))
                + "</tr>"
            )

        st.markdown(_render_compact_table(rows, headers), unsafe_allow_html=True)

    st.markdown("---")

    st.markdown("---")

    # Vendas detalhadas + explicação FIFO
    st.markdown(
        """
<div class="section-title">🧾 Vendas detalhadas (com custo FIFO)</div>
<div class="section-sub">Cada linha já traz o custo correto de acordo com o giro do estoque — e agora com o estoque atual do item.</div>
""",
        unsafe_allow_html=True,
    )

    df_fifo_view = df_fifo_filt.copy()
    if not df_fifo_view.empty:
        # Lista compacta de vendas (🔍 abre o produto na Pesquisa)
        df_sales = normalize_sales_like(df_fifo_view).copy()

        # adiciona estoque atual por produto (se não der, segue com 0)
        try:
            df_sales = add_estoque_atual(df_sales, col_produto='PRODUTO', nome_col='ESTOQUE_ATUAL')
        except Exception:
            df_sales['ESTOQUE_ATUAL'] = 0

        # DATA -> datetime antes de qualquer .dt
        df_sales = ensure_datetime_series(df_sales, 'DATA')
        df_sales['DATA_FMT'] = df_sales['DATA'].dt.strftime('%d/%m/%Y').fillna('')

        # numéricos
        df_sales['QTD_NUM'] = df_sales['QTD'].apply(parse_money).astype(float)
        df_sales['QTD_INT'] = df_sales['QTD_NUM'].apply(lambda x: int(round(float(x))) if pd.notna(x) else 0)

        # normaliza ESTOQUE_ATUAL (garante Series)
        if 'ESTOQUE_ATUAL' in df_sales.columns:
            _est = df_sales['ESTOQUE_ATUAL']
        else:
            _est = pd.Series(0, index=df_sales.index)
        df_sales['ESTOQUE_ATUAL'] = _est.apply(lambda x: int(round(float(x))) if pd.notna(x) else 0)

        df_sales['VALOR_TOTAL'] = df_sales['VALOR_TOTAL'].apply(parse_money).astype(float)
        df_sales['LUCRO'] = df_sales['LUCRO'].apply(parse_money).astype(float)

        # custo total e custo unitário FIFO (blindado)
        if 'CUSTO_TOTAL' in df_sales.columns:
            df_sales['CUSTO_TOTAL'] = df_sales['CUSTO_TOTAL'].apply(parse_money).astype(float)
        else:
            df_sales['CUSTO_TOTAL'] = 0.0

        df_sales['CUSTO_UNIT_FIFO'] = df_sales['CUSTO_TOTAL'] / df_sales['QTD_NUM'].replace(0, pd.NA)
        df_sales['CUSTO_UNIT_FIFO'] = df_sales['CUSTO_UNIT_FIFO'].fillna(0.0)

        df_sales['VALOR_FMT'] = df_sales['VALOR_TOTAL'].map(format_reais)
        df_sales['LUCRO_FMT'] = df_sales['LUCRO'].map(format_reais)
        df_sales['CUSTO_UNIT_FIFO_FMT'] = df_sales['CUSTO_UNIT_FIFO'].map(format_reais)

        df_sales = df_sales.sort_values('DATA', ascending=False).head(220)

        headers = ['Data', 'Produto', 'Cliente', 'Status', 'Qtd', 'Estoque', 'Custo un. (FIFO)', 'Valor', 'Lucro']
        rows = []
        for i, r in df_sales.iterrows():
            prod = _safe(r.get('PRODUTO', ''))
            link = f"?produto={quote(prod)}"
            # target _self = mesma janela
            prod_html = f"<div class='prodcell'><a class='lens' href='{link}' target='_self' title='Abrir na Pesquisa'>🔍</a><span>{prod}</span></div>"
            rows.append(
                '<tr>'
                + _td(_safe(r.get('DATA_FMT', '')), 'muted')
                + _td(prod_html)
                + _td(_safe(r.get('CLIENTE', '')))
                + _td(_safe(r.get('STATUS', '')), 'muted')
                + _td(_safe(r.get('QTD_INT', 0)))
                + _td(_safe(r.get('ESTOQUE_ATUAL', 0)), 'muted')
                + _td(_safe(r.get('CUSTO_UNIT_FIFO_FMT', '')), 'muted')
                + _td(_safe(r.get('VALOR_FMT', '')))
                + _td(_safe(r.get('LUCRO_FMT', '')))
                + '</tr>'
            )

        st.markdown(_render_compact_table(rows, headers), unsafe_allow_html=True)

    else:
        st.info("Nenhuma venda no período selecionado.")


elif nav == "🔎 Pesquisa de produto":
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

        # Se veio de uma lupinha, já seleciona o produto automaticamente
        default_idx = 0
        if st.session_state.get("produto_pesquisa") in todos_produtos:
            default_idx = todos_produtos.index(st.session_state.get("produto_pesquisa")) + 1

        prod_sel = st.selectbox(
            "Escolha o produto:",
            options=["(selecione)"] + todos_produtos,
            index=default_idx,
        )
        if prod_sel != "(selecione)":
            st.session_state.produto_pesquisa = prod_sel
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
                vendas_prod_hist = add_estoque_atual(vendas_prod_hist, col_produto="PRODUTO", nome_col="ESTOQUE_ATUAL")

                vendas_prod_hist = ensure_datetime_series(vendas_prod_hist, "DATA")
                vendas_prod_hist["DATA"] = vendas_prod_hist["DATA"].dt.strftime("%d/%m/%Y").fillna("")
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
                    "ESTOQUE_ATUAL",
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

elif nav == "⚠️ Alertas":
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

        valor_estoque_total_alert = df_estoque["VALOR_ESTOQUE"].sum() if "VALOR_ESTOQUE" in df_estoque.columns else 0.0
        valor_estoque_parado = parado_filtrado["VALOR_ESTOQUE"].sum() if "VALOR_ESTOQUE" in parado_filtrado.columns else 0.0
        pct_estoque_parado = (
            (valor_estoque_parado / valor_estoque_total_alert) * 100
            if valor_estoque_total_alert > 0
            else 0.0
        )

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

elif nav == "🧾 Compras":
    st.markdown(
        """
<div class="section-title">🧾 Compras</div>
<div class="section-sub">
Visão das compras da loja por mês, com foco no que realmente importa para o caixa — e com estoque atual do item comprado.
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

                    # adiciona estoque atual do item comprado
                    top_comp["ESTOQUE_ATUAL"] = top_comp["PRODUTO"].map(estoque_atual_map).fillna(0).astype(int)

                    top_comp["VALOR_COMP_FMT"] = top_comp["VALOR_COMP"].map(format_reais)

                    st.dataframe(
                        top_comp.rename(
                            columns={
                                "PRODUTO": "Produto",
                                "QTD_COMP": "Qtd comprada",
                                "VALOR_COMP_FMT": "Valor em compras",
                                "ESTOQUE_ATUAL": "Estoque atual",
                            }
                        )[["Produto", "Qtd comprada", "Valor em compras", "Estoque atual"]]
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
Cada lançamento com data, produto, quantidade e custo — e o estoque atual do item.
</div>
""",
                    unsafe_allow_html=True,
                )

                dfc_view = ensure_df(dfc_filt).copy()

                # Blindagem: se por algum motivo não for DataFrame, não quebra
                if not isinstance(dfc_view, pd.DataFrame):
                    st.error("Erro interno: compras detalhadas inválidas (dfc_view não é DataFrame).")
                    st.stop()

                # adiciona estoque atual em cada linha da compra
                try:
                    dfc_view = add_estoque_atual(dfc_view, col_produto="PRODUTO", nome_col="ESTOQUE_ATUAL")
                except Exception:
                    dfc_view["ESTOQUE_ATUAL"] = 0

                if "DATA" in dfc_view.columns:
                    dfc_view = ensure_datetime_series(dfc_view, "DATA")
                    dfc_view["DATA_FMT"] = dfc_view["DATA"].dt.strftime("%d/%m/%Y").fillna("")
                else:
                    dfc_view["DATA_FMT"] = ""
                dfc_view["CUSTO_UNIT_FMT"] = dfc_view["CUSTO UNITÁRIO"].map(format_reais)
                dfc_view["CUSTO_TOTAL_FMT"] = dfc_view["CUSTO_TOTAL"].map(format_reais)

                cols_comp = ["DATA_FMT"]
                if "PRODUTO" in dfc_view.columns:
                    cols_comp.append("PRODUTO")
                if "STATUS" in dfc_view.columns:
                    cols_comp.append("STATUS")
                cols_comp += ["QUANTIDADE", "CUSTO_UNIT_FMT", "CUSTO_TOTAL_FMT", "ESTOQUE_ATUAL", "MES_ANO"]
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
                            "ESTOQUE_ATUAL": "Estoque atual",
                            "MES_ANO": "Mês/ano",
                        }
                    )
                    .sort_values("Data", ascending=False),
                    use_container_width=True,
                )
