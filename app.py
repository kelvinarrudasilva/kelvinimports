import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from urllib.parse import quote
import re
import unicodedata
import html
from difflib import SequenceMatcher

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
  white-space:normal;
}
.compact-grid td{
  padding:7px 10px;
  border-bottom:1px solid #121212;
  vertical-align:middle;
  white-space:normal;
}
.compact-grid tbody tr:nth-child(odd) td{ background:#050505; }
.compact-grid tbody tr:nth-child(even) td{ background:#0a0a0a; }
.compact-grid tbody tr:hover td{ background:#111827 !important; }
.compact-grid .prodcell{ display:flex; align-items:center; gap:8px; }
.compact-grid a.lens{ text-decoration:none; font-size:13px; }
.compact-grid a.lens:hover{ filter:brightness(1.2); }
.compact-grid .muted{ color:var(--muted); }

.hint-row{display:flex;flex-wrap:wrap;gap:8px;margin:6px 0 14px 0;}
.hint-chip{display:inline-flex;align-items:center;gap:6px;padding:7px 10px;border-radius:999px;border:1px solid var(--border-soft);background:#0b0b0b;color:#d4d4d8;font-size:12px;}
.hint-icon,.mini-hover{
  display:inline-flex;align-items:center;justify-content:center;
  width:18px;height:18px;border-radius:999px;
  background:#151515;border:1px solid #2a2a2a;color:#facc15;
  font-size:11px;cursor:help;line-height:1;
}
.mini-hover{width:20px;height:20px;color:#93c5fd;border-color:#1f2937;background:#0f172a;}
.hover-cell{display:inline-flex;align-items:center;gap:6px;}
.help-inline{display:inline-flex;align-items:center;gap:6px;white-space:nowrap;}
.badge-action{display:inline-flex;align-items:center;justify-content:center;padding:5px 10px;border-radius:999px;font-size:11px;font-weight:700;letter-spacing:.02em;border:1px solid transparent;white-space:nowrap;}
.badge-buy{background:rgba(34,197,94,.14);color:#86efac;border-color:rgba(34,197,94,.28);}
.badge-plan{background:rgba(59,130,246,.14);color:#93c5fd;border-color:rgba(59,130,246,.28);}
.badge-test{background:rgba(168,85,247,.14);color:#d8b4fe;border-color:rgba(168,85,247,.28);}
.badge-watch{background:rgba(245,158,11,.14);color:#fcd34d;border-color:rgba(245,158,11,.28);}
.badge-skip{background:rgba(239,68,68,.14);color:#fca5a5;border-color:rgba(239,68,68,.28);}
.badge-hold{background:rgba(107,114,128,.18);color:#d1d5db;border-color:rgba(107,114,128,.30);}
.pill-soft{display:inline-flex;align-items:center;justify-content:center;padding:4px 8px;border-radius:999px;border:1px solid var(--border-soft);background:#0b0b0b;color:#d4d4d8;font-size:11px;white-space:nowrap;}

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
        must_have = ["DATA", "PRODUTO", "QTD", "VALOR", "STATUS", "CLIENTE"]
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
    cols_vendas_obrig = ["DATA", "PRODUTO", "QTD", "VALOR TOTAL", "STATUS", "CLIENTE"]

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


def calcular_lotes_remanescentes_fifo(df_compras_raw: pd.DataFrame, df_vendas_raw: pd.DataFrame) -> pd.DataFrame:
    compras = df_compras_raw.copy()
    vendas = df_vendas_raw.copy()

    compras.columns = [c.strip().upper() for c in compras.columns]
    vendas.columns = [c.strip().upper() for c in vendas.columns]

    cols_compras_obrig = ["DATA", "PRODUTO", "STATUS", "QUANTIDADE", "CUSTO UNITÁRIO"]
    cols_vendas_obrig = ["DATA", "PRODUTO", "QTD"]

    if any(c not in compras.columns for c in cols_compras_obrig) or any(c not in vendas.columns for c in cols_vendas_obrig):
        return pd.DataFrame(columns=["PRODUTO", "QTD_REMANESCENTE", "DATA_LOTE", "CUSTO_UNIT", "VALOR_LOTE", "DIAS_PARADO_LOTE"])

    compras = compras[compras["STATUS"].astype(str).str.upper() == "ENTREGUE"].copy()
    if compras.empty:
        return pd.DataFrame(columns=["PRODUTO", "QTD_REMANESCENTE", "DATA_LOTE", "CUSTO_UNIT", "VALOR_LOTE", "DIAS_PARADO_LOTE"])

    compras["DATA"] = pd.to_datetime(compras["DATA"], errors="coerce", dayfirst=True)
    vendas["DATA"] = pd.to_datetime(vendas["DATA"], errors="coerce", dayfirst=True)

    compras["QUANTIDADE"] = compras["QUANTIDADE"].apply(parse_money).astype(float)
    compras["CUSTO UNITÁRIO"] = compras["CUSTO UNITÁRIO"].apply(parse_money).astype(float)
    compras["CUSTO TOTAL"] = compras["QUANTIDADE"] * compras["CUSTO UNITÁRIO"]
    compras["CUSTO_UNIT_CALC"] = compras["CUSTO TOTAL"] / compras["QUANTIDADE"].replace(0, pd.NA)
    compras = compras[
        (compras["CUSTO_UNIT_CALC"].notna())
        & (compras["CUSTO_UNIT_CALC"] >= 0)
        & (compras["CUSTO_UNIT_CALC"] <= CUSTO_MAX_PLAUSIVEL)
        & (compras["QUANTIDADE"] > 0)
        & (compras["DATA"].notna())
    ].sort_values(["PRODUTO", "DATA"]).copy()

    vendas["QTD"] = vendas["QTD"].apply(parse_money).astype(float)
    vendas = vendas[(vendas["QTD"] > 0) & (vendas["DATA"].notna())].sort_values(["PRODUTO", "DATA"]).copy()

    estoque = {}
    for _, row in compras.iterrows():
        produto = str(row["PRODUTO"])
        estoque.setdefault(produto, []).append({
            "qtd": float(row["QUANTIDADE"]),
            "custo": float(row["CUSTO_UNIT_CALC"]),
            "data": row["DATA"],
        })

    for _, row in vendas.iterrows():
        produto = str(row["PRODUTO"])
        restante = float(row["QTD"])
        lotes = estoque.get(produto, [])
        while restante > 0 and lotes:
            lote = lotes[0]
            if lote["qtd"] <= restante:
                restante -= lote["qtd"]
                lotes.pop(0)
            else:
                lote["qtd"] -= restante
                restante = 0

    today = pd.Timestamp.now().normalize()
    registros = []
    for produto, lotes in estoque.items():
        for lote in lotes:
            qtd = float(lote.get("qtd", 0))
            if qtd <= 0:
                continue
            data_lote = lote.get("data")
            dias = (today - data_lote.normalize()).days if pd.notna(data_lote) else pd.NA
            custo_unit = float(lote.get("custo", 0))
            registros.append({
                "PRODUTO": produto,
                "QTD_REMANESCENTE": qtd,
                "DATA_LOTE": data_lote,
                "CUSTO_UNIT": custo_unit,
                "VALOR_LOTE": qtd * custo_unit,
                "DIAS_PARADO_LOTE": dias,
            })

    return pd.DataFrame(registros)


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
df_lotes_fifo = calcular_lotes_remanescentes_fifo(df_compras, df_vendas)

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


def _attr_safe(s):
    if s is None:
        return ""
    s = html.escape(str(s), quote=True)
    s = s.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "&#10;")
    return s



def _hint_icon(text, icon="⚠️"):
    return f'<span class="hint-icon" title="{_attr_safe(text)}">{icon}</span>'


def _mini_hover(text, icon="🧠"):
    return f'<span class="mini-hover" title="{_attr_safe(text)}">{icon}</span>'


def _acao_badge(acao):
    acao = "" if acao is None else str(acao)
    mapa = {
        "Comprar já": "badge-buy",
        "Planejar compra": "badge-plan",
        "Teste leve": "badge-test",
        "Monitorar": "badge-watch",
        "Não comprar agora": "badge-skip",
        "Segurar estoque": "badge-hold",
    }
    cls = mapa.get(acao, "badge-hold")
    return f'<span class="badge-action {cls}">{_safe(acao)}</span>'


def _painel_resultado_text(row):
    produto = _safe(row.get("PRODUTO", "")) or "Produto"
    acao = _safe(row.get("ACAO", "Monitorar")) or "Monitorar"

    qtd_total = float(row.get("QTD_VENDIDA_TOTAL", 0) or 0)
    v30 = float(row.get("V30", 0) or 0)
    v60 = float(row.get("V60", 0) or 0)
    v90 = float(row.get("V90", 0) or 0)

    estoque = float(row.get("ESTOQUE_ATUAL", 0) or 0)

    hoje = pd.Timestamp.now().normalize()
    ultima_venda_data = pd.to_datetime(row.get("ULTIMA_VENDA"), errors="coerce")
    dias_desde_ult_venda = None
    dias_ate_prox_venda = None
    if pd.notna(ultima_venda_data):
        ultima_norm = ultima_venda_data.normalize()
        diff = int((hoje - ultima_norm).days)
        if diff >= 0:
            dias_desde_ult_venda = diff
        else:
            dias_ate_prox_venda = abs(diff)

    dias_para_vender = row.get("DIAS_PRIMEIRA_COMPRA_ATE_PRIMEIRA_VENDA")

    pontos = []
    if qtd_total <= 1:
        pontos.append("vendeu pouco")
    elif v30 > 0:
        pontos.append("tem venda recente")
    elif v60 > 0 or v90 > 0:
        pontos.append("tem algum histórico de venda")
    else:
        pontos.append("não teve venda recente")

    if qtd_total >= 4 or v30 >= 2:
        pontos.append("histórico bom para tomar decisão")
    elif qtd_total >= 2:
        pontos.append("histórico razoável, mas ainda observando")
    else:
        pontos.append("histórico ainda fraco para cravar compra")

    if acao == "Comprar já":
        pontos.append("vale comprar agora")
    elif acao == "Planejar compra":
        pontos.append("vale planejar a próxima compra")
    elif acao == "Teste leve":
        pontos.append("melhor repor pouco e testar")
    elif acao == "Monitorar":
        pontos.append("melhor não comprar agora")
    elif acao == "Não comprar agora":
        pontos.append("não vale repor neste momento")
    elif acao == "Segurar estoque":
        pontos.append("já tem estoque suficiente por enquanto")

    extras = []
    if dias_desde_ult_venda is not None:
        extras.append(f"Última venda há {dias_desde_ult_venda} dias")
    elif dias_ate_prox_venda is not None:
        extras.append(f"Há venda lançada para daqui a {dias_ate_prox_venda} dias")

    try:
        if pd.notna(dias_para_vender):
            extras.append(f"Demorou cerca de {int(round(float(dias_para_vender)))} dias da compra até vender")
    except Exception:
        pass

    if estoque <= 0:
        extras.append("Estoque atual zerado")

    linhas = [
        "📦 Resultado no painel",
        "",
        f"Produto: {produto}",
        "",
        f"Ação: {acao}",
        "",
    ]

    for p in pontos[:3]:
        linhas.append(f"• {p}")

    if extras:
        linhas.append("")
        linhas.extend(extras[:2])

    return "\n".join(linhas)



def _nivel_confianca(row):
    qtd = float(row.get("QTD_VENDIDA_TOTAL", 0) or 0)
    v30 = float(row.get("V30", 0) or 0)
    v60 = float(row.get("V60", 0) or 0)
    intervalo = row.get("INTERVALO_ESPERADO")
    lag = row.get("DIAS_PRIMEIRA_COMPRA_ATE_PRIMEIRA_VENDA")
    sim = float(row.get("V30_SIMILARES", 0) or 0)
    pontos = 0
    if qtd >= 6:
        pontos += 45
    elif qtd >= 4:
        pontos += 36
    elif qtd >= 2:
        pontos += 24
    elif qtd >= 1:
        pontos += 10
    if v30 >= 3:
        pontos += 25
    elif v60 >= 4:
        pontos += 18
    elif v60 >= 2:
        pontos += 10
    if pd.notna(intervalo):
        pontos += 15
    if pd.notna(lag) and float(lag) >= 90:
        pontos -= 18
    elif pd.notna(lag) and float(lag) >= 60:
        pontos -= 10
    if qtd <= 1:
        pontos -= 18
    if qtd <= 1 and sim > 0:
        pontos -= 8
    pontos = max(0, min(100, int(round(pontos))))
    if pontos >= 70:
        return "Alta"
    if pontos >= 45:
        return "Média"
    return "Baixa"


def _risco_analise(row):
    conf = _nivel_confianca(row)
    qtd = float(row.get("QTD_VENDIDA_TOTAL", 0) or 0)
    sim = float(row.get("V30_SIMILARES", 0) or 0)
    if conf == "Alta":
        risco = "Baixo"
    elif conf == "Média":
        risco = "Médio"
    else:
        risco = "Alto"
    if qtd <= 1 and sim > 0:
        risco = "Alto"
    return risco


def normalize_name(s):
    s = "" if s is None else str(s)
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("utf-8")
    s = s.lower().strip()
    s = re.sub(r"[^a-z0-9]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


STOPWORDS_NOME = {
    "de", "do", "da", "dos", "das", "para", "pro", "plus", "com", "sem", "e", "a", "o",
    "wireless", "bluetooth", "usb", "rgb", "led", "gamer", "fone", "mouse", "teclado", "caixa",
    "som", "tws", "pro", "max", "mini", "ultra", "novo", "nova"
}


def tokenizar_produto(s):
    s = normalize_name(s)
    tokens = [t for t in s.split() if t and t not in STOPWORDS_NOME and not t.isdigit()]
    return tokens


def similaridade_produto(a, b):
    ta = set(tokenizar_produto(a))
    tb = set(tokenizar_produto(b))
    if not ta or not tb:
        na, nb = normalize_name(a), normalize_name(b)
        if not na or not nb:
            return 0.0
        return 1.0 if na == nb else 0.0
    inter = len(ta & tb)
    union = len(ta | tb)
    jacc = inter / union if union else 0.0
    prefix_bonus = 0.15 if normalize_name(a)[:10] == normalize_name(b)[:10] else 0.0
    return min(1.0, jacc + prefix_bonus)


def top_similares(produto, universo, limite=3, min_score=0.34):
    sims = []
    for other in universo:
        if other == produto:
            continue
        score = similaridade_produto(produto, other)
        if score >= min_score:
            sims.append((other, score))
    sims.sort(key=lambda x: (-x[1], x[0]))
    return sims[:limite]


def _score_busca_produto(produto, consulta):
    produto_norm = normalize_name(produto)
    consulta_norm = normalize_name(consulta)
    if not consulta_norm:
        return 0.0

    tokens_consulta = [t for t in consulta_norm.split() if t]
    tokens_produto = [t for t in produto_norm.split() if t]
    if not tokens_produto:
        return 0.0

    score = 0.0

    if consulta_norm == produto_norm:
        score += 200
    if consulta_norm in produto_norm:
        score += 90
        if produto_norm.startswith(consulta_norm):
            score += 20

    if tokens_consulta:
        matches = sum(1 for t in tokens_consulta if any(t in tp for tp in tokens_produto))
        score += matches * 28
        cobertura = matches / len(tokens_consulta)
        score += cobertura * 30

    for t in tokens_consulta:
        if len(t) >= 3 and any(tp.startswith(t) for tp in tokens_produto):
            score += 8

    score += SequenceMatcher(None, consulta_norm, produto_norm).ratio() * 35
    return score


def buscar_produtos_relacionados(consulta, produtos, estoque_map, limite=80):
    produtos = list(produtos or [])
    consulta_norm = normalize_name(consulta)

    resultados = []
    for prod in produtos:
        estoque = float(estoque_map.get(prod, 0) or 0)
        score = _score_busca_produto(prod, consulta_norm) if consulta_norm else 0.0
        if consulta_norm and score < 18:
            continue
        resultados.append({
            'PRODUTO': prod,
            'ESTOQUE': estoque,
            'TEM_ESTOQUE': 1 if estoque > 0 else 0,
            'SCORE': score,
        })

    if not resultados and consulta_norm:
        for prod in produtos:
            estoque = float(estoque_map.get(prod, 0) or 0)
            resultados.append({
                'PRODUTO': prod,
                'ESTOQUE': estoque,
                'TEM_ESTOQUE': 1 if estoque > 0 else 0,
                'SCORE': SequenceMatcher(None, consulta_norm, normalize_name(prod)).ratio() * 35,
            })

    df_res = pd.DataFrame(resultados)
    if df_res.empty:
        return df_res

    df_res = df_res.sort_values(
        ['TEM_ESTOQUE', 'SCORE', 'ESTOQUE', 'PRODUTO'],
        ascending=[False, False, False, True]
    ).head(limite).reset_index(drop=True)
    return df_res


def label_produto_busca(produto, estoque_map):
    estoque = float(estoque_map.get(produto, 0) or 0)
    status = 'com estoque' if estoque > 0 else 'sem estoque'
    qtd = int(round(estoque)) if float(estoque).is_integer() else round(estoque, 2)
    return f'{produto} — {status} ({qtd})'


def _media_intervalo_em_dias(df_vendas_prod):
    if df_vendas_prod is None or df_vendas_prod.empty or "DATA" not in df_vendas_prod.columns:
        return np.nan
    datas = (
        pd.to_datetime(df_vendas_prod["DATA"], errors="coerce")
        .dropna()
        .sort_values()
        .dt.normalize()
        .drop_duplicates()
    )
    if len(datas) <= 1:
        return np.nan
    diffs = datas.diff().dt.days.dropna()
    if diffs.empty:
        return np.nan
    return float(diffs.mean())


def _dias_entre_compra_e_venda(c_df, v_df):
    """Mede quanto tempo o item levou para começar a girar.
    Para cada compra, procura a primeira venda no mesmo dia ou depois.
    Retorna média e mediana em dias, quando existir histórico suficiente.
    """
    if c_df is None or v_df is None or c_df.empty or v_df.empty or "DATA" not in c_df.columns or "DATA" not in v_df.columns:
        return np.nan, np.nan

    compras_datas = pd.to_datetime(c_df["DATA"], errors="coerce").dropna().sort_values().dt.normalize().tolist()
    vendas_datas = pd.to_datetime(v_df["DATA"], errors="coerce").dropna().sort_values().dt.normalize().tolist()
    if not compras_datas or not vendas_datas:
        return np.nan, np.nan

    diffs = []
    for dc in compras_datas:
        prox_venda = next((dv for dv in vendas_datas if dv >= dc), None)
        if prox_venda is not None:
            diffs.append((prox_venda - dc).days)

    if not diffs:
        return np.nan, np.nan
    return float(np.mean(diffs)), float(np.median(diffs))


def build_reposicao_inteligente(df_fifo, df_estoque, df_compras):
    produtos = sorted(set(df_fifo.get("PRODUTO", pd.Series(dtype=str)).dropna().astype(str).tolist()) |
                      set(df_estoque.get("PRODUTO", pd.Series(dtype=str)).dropna().astype(str).tolist()) |
                      set(df_compras.get("PRODUTO", pd.Series(dtype=str)).dropna().astype(str).tolist()))
    if not produtos:
        return pd.DataFrame()

    fifo = df_fifo.copy()
    fifo = ensure_datetime_series(fifo, "DATA")
    fifo["QTD"] = fifo.get("QTD", 0).apply(parse_money).astype(float)
    fifo["VALOR_TOTAL"] = fifo.get("VALOR_TOTAL", 0).apply(parse_money).astype(float)
    fifo["CUSTO_TOTAL"] = fifo.get("CUSTO_TOTAL", 0).apply(parse_money).astype(float)
    fifo["LUCRO"] = fifo.get("LUCRO", 0).apply(parse_money).astype(float)

    compras = df_compras.copy()
    compras.columns = [str(c).strip().upper() for c in compras.columns]
    compras = ensure_datetime_series(compras, "DATA")
    if "STATUS" in compras.columns:
        compras = compras[compras["STATUS"].astype(str).str.upper() == "ENTREGUE"].copy()
    compras["QUANTIDADE"] = compras.get("QUANTIDADE", 0).apply(parse_money).astype(float)
    compras["CUSTO UNITÁRIO"] = compras.get("CUSTO UNITÁRIO", 0).apply(parse_money).astype(float)
    compras["CUSTO_TOTAL"] = compras["QUANTIDADE"] * compras["CUSTO UNITÁRIO"]

    estoque = df_estoque.copy() if isinstance(df_estoque, pd.DataFrame) else pd.DataFrame()
    if not estoque.empty:
        estoque["SALDO_QTD"] = estoque.get("SALDO_QTD", 0).apply(parse_money).astype(float)
        estoque["VALOR_ESTOQUE"] = estoque.get("VALOR_ESTOQUE", 0).apply(parse_money).astype(float)
        estoque["CUSTO_MEDIO_FIFO"] = estoque.get("CUSTO_MEDIO_FIFO", 0).apply(parse_money).astype(float)

    hoje = pd.Timestamp.now().normalize()
    linhas = []

    for prod in produtos:
        v = fifo[fifo["PRODUTO"] == prod].copy()
        c = compras[compras["PRODUTO"] == prod].copy() if "PRODUTO" in compras.columns else pd.DataFrame()
        e = estoque[estoque["PRODUTO"] == prod].copy() if not estoque.empty and "PRODUTO" in estoque.columns else pd.DataFrame()

        estoque_atual = float(e["SALDO_QTD"].iloc[0]) if not e.empty else 0.0
        valor_estoque = float(e["VALOR_ESTOQUE"].iloc[0]) if not e.empty else 0.0
        custo_fifo = float(e["CUSTO_MEDIO_FIFO"].iloc[0]) if not e.empty else 0.0

        qtd_vendida = float(v["QTD"].sum()) if not v.empty else 0.0
        receita_total = float(v["VALOR_TOTAL"].sum()) if not v.empty else 0.0
        lucro_total = float(v["LUCRO"].sum()) if not v.empty else 0.0
        qtd_comprada = float(c["QUANTIDADE"].sum()) if not c.empty else 0.0

        primeira_venda = v["DATA"].min() if not v.empty else pd.NaT
        ultima_venda = v["DATA"].max() if not v.empty else pd.NaT
        primeira_compra = c["DATA"].min() if not c.empty else pd.NaT
        ultima_compra = c["DATA"].max() if not c.empty else pd.NaT

        media_dias_compra_venda, mediana_dias_compra_venda = _dias_entre_compra_e_venda(c, v)
        dias_primeira_compra_ate_primeira_venda = int((primeira_venda.normalize() - primeira_compra.normalize()).days) if pd.notna(primeira_compra) and pd.notna(primeira_venda) and primeira_venda >= primeira_compra else np.nan
        dias_ultima_compra_ate_ultima_venda = int((ultima_venda.normalize() - ultima_compra.normalize()).days) if pd.notna(ultima_compra) and pd.notna(ultima_venda) and ultima_venda >= ultima_compra else np.nan

        dias_com_historico = max(1, int(((hoje - primeira_venda.normalize()).days + 1)) if pd.notna(primeira_venda) else 1)
        dias_desde_ult_venda = max(0, int((hoje - ultima_venda.normalize()).days)) if pd.notna(ultima_venda) else 9999
        dias_desde_ult_compra = max(0, int((hoje - ultima_compra.normalize()).days)) if pd.notna(ultima_compra) else 9999

        v30 = v[v["DATA"] >= (hoje - pd.Timedelta(days=30))]["QTD"].sum() if not v.empty else 0.0
        v60 = v[v["DATA"] >= (hoje - pd.Timedelta(days=60))]["QTD"].sum() if not v.empty else 0.0
        v90 = v[v["DATA"] >= (hoje - pd.Timedelta(days=90))]["QTD"].sum() if not v.empty else 0.0

        vel_30 = v30 / 30.0
        vel_60 = v60 / 60.0
        vel_90 = v90 / 90.0
        vel_hist = qtd_vendida / dias_com_historico if dias_com_historico else 0.0
        intervalo_medio_vendas = _media_intervalo_em_dias(v)
        intervalo_esperado = float(intervalo_medio_vendas) if pd.notna(intervalo_medio_vendas) else np.nan

        velocidade_base = (vel_30 * 0.50) + (vel_60 * 0.22) + (vel_90 * 0.13) + (vel_hist * 0.15)

        fator_recencia = 1.0
        if pd.notna(intervalo_esperado) and intervalo_esperado > 0:
            relacao = dias_desde_ult_venda / max(intervalo_esperado, 1.0)
            if relacao >= 3.0:
                fator_recencia = 0.35
            elif relacao >= 2.0:
                fator_recencia = 0.55
            elif relacao >= 1.2:
                fator_recencia = 0.80
            elif relacao <= 0.5:
                fator_recencia = 1.12
        else:
            if dias_desde_ult_venda > 90:
                fator_recencia = 0.40
            elif dias_desde_ult_venda > 45:
                fator_recencia = 0.65

        similares = top_similares(prod, produtos, limite=3, min_score=0.34)
        similares_txt = ", ".join([f"{nome} ({score:.0%})" for nome, score in similares])
        boost_similares = 0.0
        ultima_venda_similar = pd.NaT
        ultima_compra_similar = pd.NaT
        intervalo_similar = np.nan
        v30_similares = 0.0

        for nome, score in similares:
            vv = fifo[fifo["PRODUTO"] == nome].copy()
            cc = compras[compras["PRODUTO"] == nome].copy() if "PRODUTO" in compras.columns else pd.DataFrame()
            if not vv.empty:
                vv30 = vv[vv["DATA"] >= (hoje - pd.Timedelta(days=30))]["QTD"].sum() / 30.0
                boost_similares += vv30 * score
                v30_similares += vv[vv["DATA"] >= (hoje - pd.Timedelta(days=30))]["QTD"].sum() * score
                cand_ult_venda = vv["DATA"].max()
                if pd.notna(cand_ult_venda) and (pd.isna(ultima_venda_similar) or cand_ult_venda > ultima_venda_similar):
                    ultima_venda_similar = cand_ult_venda
                cand_intervalo = _media_intervalo_em_dias(vv)
                if pd.notna(cand_intervalo):
                    if pd.isna(intervalo_similar):
                        intervalo_similar = cand_intervalo * score
                    else:
                        intervalo_similar += cand_intervalo * score
            if not cc.empty:
                cand_ult_compra = cc["DATA"].max()
                if pd.notna(cand_ult_compra) and (pd.isna(ultima_compra_similar) or cand_ult_compra > ultima_compra_similar):
                    ultima_compra_similar = cand_ult_compra

        demanda_ajustada = velocidade_base * fator_recencia
        if boost_similares > 0:
            sem_saida_recente = (v30 <= 0 and v60 <= 0)
            if sem_saida_recente and estoque_atual <= 0:
                demanda_ajustada += boost_similares * 0.35
            elif sem_saida_recente:
                demanda_ajustada += boost_similares * 0.18
            else:
                demanda_ajustada += boost_similares * 0.10

        cobertura_dias = (estoque_atual / demanda_ajustada) if demanda_ajustada > 0 else 999.0
        preco_medio = (receita_total / qtd_vendida) if qtd_vendida > 0 else 0.0
        margem_pct = (lucro_total / receita_total) if receita_total > 0 else 0.0
        sell_through = (qtd_vendida / qtd_comprada) if qtd_comprada > 0 else 0.0
        dias_desde_ult_venda_similar = max(0, int((hoje - ultima_venda_similar.normalize()).days)) if pd.notna(ultima_venda_similar) else 9999
        dias_desde_ult_compra_similar = max(0, int((hoje - ultima_compra_similar.normalize()).days)) if pd.notna(ultima_compra_similar) else 9999

        if pd.isna(intervalo_esperado) and pd.notna(intervalo_similar):
            intervalo_esperado = float(intervalo_similar)

        linhas.append({
            "PRODUTO": prod,
            "ESTOQUE_ATUAL": estoque_atual,
            "VALOR_ESTOQUE": valor_estoque,
            "CUSTO_MEDIO_FIFO": custo_fifo,
            "QTD_VENDIDA_TOTAL": qtd_vendida,
            "QTD_COMPRADA_TOTAL": qtd_comprada,
            "RECEITA_TOTAL": receita_total,
            "LUCRO_TOTAL": lucro_total,
            "PRECO_MEDIO": preco_medio,
            "MARGEM_PCT": margem_pct,
            "SELL_THROUGH": sell_through,
            "PRIMEIRA_VENDA": primeira_venda,
            "ULTIMA_VENDA": ultima_venda,
            "PRIMEIRA_COMPRA": primeira_compra,
            "ULTIMA_COMPRA": ultima_compra,
            "ULTIMA_VENDA_SIMILAR": ultima_venda_similar,
            "ULTIMA_COMPRA_SIMILAR": ultima_compra_similar,
            "DIAS_DESDE_ULT_VENDA": dias_desde_ult_venda,
            "DIAS_DESDE_ULT_COMPRA": dias_desde_ult_compra,
            "MEDIA_DIAS_COMPRA_VENDA": media_dias_compra_venda,
            "MEDIANA_DIAS_COMPRA_VENDA": mediana_dias_compra_venda,
            "DIAS_PRIMEIRA_COMPRA_ATE_PRIMEIRA_VENDA": dias_primeira_compra_ate_primeira_venda,
            "DIAS_ULTIMA_COMPRA_ATE_ULTIMA_VENDA": dias_ultima_compra_ate_ultima_venda,
            "DIAS_DESDE_ULT_VENDA_SIMILAR": dias_desde_ult_venda_similar,
            "DIAS_DESDE_ULT_COMPRA_SIMILAR": dias_desde_ult_compra_similar,
            "INTERVALO_MEDIO_VENDAS": intervalo_medio_vendas,
            "INTERVALO_MEDIO_SIMILAR": intervalo_similar,
            "INTERVALO_ESPERADO": intervalo_esperado,
            "V30": v30,
            "V60": v60,
            "V90": v90,
            "V30_SIMILARES": v30_similares,
            "VEL_DIA": velocidade_base,
            "FATOR_RECENCIA": fator_recencia,
            "DEMANDA_AJUSTADA_DIA": demanda_ajustada,
            "COBERTURA_DIAS": cobertura_dias,
            "SIMILARES": similares_txt,
            "SCORE_SIMILARES": boost_similares,
        })

    return pd.DataFrame(linhas)


def classificar_reposicao(row, alvo_dias=30, lead_time=10, seguranca=0.20):
    demanda = float(row.get("DEMANDA_AJUSTADA_DIA", 0.0) or 0.0)
    estoque = float(row.get("ESTOQUE_ATUAL", 0.0) or 0.0)
    cobertura = float(row.get("COBERTURA_DIAS", 999.0) or 999.0)
    dias_sem_vender = float(row.get("DIAS_DESDE_ULT_VENDA", 9999) or 9999)
    dias_sem_vender_similar = float(row.get("DIAS_DESDE_ULT_VENDA_SIMILAR", 9999) or 9999)
    dias_sem_comprar = float(row.get("DIAS_DESDE_ULT_COMPRA", 9999) or 9999)
    margem = float(row.get("MARGEM_PCT", 0.0) or 0.0)
    sell_through = float(row.get("SELL_THROUGH", 0.0) or 0.0)
    qtd_vendida_total = float(row.get("QTD_VENDIDA_TOTAL", 0.0) or 0.0)
    qtd_comprada_total = float(row.get("QTD_COMPRADA_TOTAL", 0.0) or 0.0)
    v30 = float(row.get("V30", 0.0) or 0.0)
    v60 = float(row.get("V60", 0.0) or 0.0)
    v90 = float(row.get("V90", 0.0) or 0.0)
    v30_similares = float(row.get("V30_SIMILARES", 0.0) or 0.0)
    intervalo_esperado = float(row.get("INTERVALO_ESPERADO", np.nan)) if pd.notna(row.get("INTERVALO_ESPERADO", np.nan)) else np.nan
    media_dias_compra_venda = float(row.get("MEDIA_DIAS_COMPRA_VENDA", np.nan)) if pd.notna(row.get("MEDIA_DIAS_COMPRA_VENDA", np.nan)) else np.nan
    mediana_dias_compra_venda = float(row.get("MEDIANA_DIAS_COMPRA_VENDA", np.nan)) if pd.notna(row.get("MEDIANA_DIAS_COMPRA_VENDA", np.nan)) else np.nan
    dias_primeira_compra_ate_primeira_venda = float(row.get("DIAS_PRIMEIRA_COMPRA_ATE_PRIMEIRA_VENDA", np.nan)) if pd.notna(row.get("DIAS_PRIMEIRA_COMPRA_ATE_PRIMEIRA_VENDA", np.nan)) else np.nan
    dias_ultima_compra_ate_ultima_venda = float(row.get("DIAS_ULTIMA_COMPRA_ATE_ULTIMA_VENDA", np.nan)) if pd.notna(row.get("DIAS_ULTIMA_COMPRA_ATE_ULTIMA_VENDA", np.nan)) else np.nan

    # Base de venda mensal: primeiro olha janela recente, mas sem se deixar enganar por 1 venda isolada.
    venda_mensal_bruta = max(v30, v60 / 2.0, v90 / 3.0, demanda * 30.0)
    historico_fraco = qtd_vendida_total <= 1.0 or qtd_comprada_total <= 1.0
    historico_muito_fraco = qtd_vendida_total <= 1.0 and qtd_comprada_total <= 2.0
    venda_isolada_recente = historico_muito_fraco and v30 > 0 and v90 <= 1.0

    lag_compra_venda_ref = np.nan
    for cand in [mediana_dias_compra_venda, media_dias_compra_venda, dias_ultima_compra_ate_ultima_venda, dias_primeira_compra_ate_primeira_venda]:
        if pd.notna(cand):
            lag_compra_venda_ref = float(cand)
            break

    giro_lote_lento = pd.notna(lag_compra_venda_ref) and lag_compra_venda_ref >= 60
    giro_lote_muito_lento = pd.notna(lag_compra_venda_ref) and lag_compra_venda_ref >= 90

    if venda_isolada_recente and pd.notna(lag_compra_venda_ref):
        venda_mensal_ref = min(venda_mensal_bruta, 30.0 / max(lag_compra_venda_ref, 1.0))
    elif historico_muito_fraco and pd.notna(lag_compra_venda_ref):
        venda_mensal_ref = min(venda_mensal_bruta, 30.0 / max(lag_compra_venda_ref, 1.0))
    else:
        venda_mensal_ref = venda_mensal_bruta

    estoque_meses = (estoque / venda_mensal_ref) if venda_mensal_ref > 0 else (999.0 if estoque > 0 else 0.0)
    similar_quente = v30_similares > 1.5 and dias_sem_vender_similar <= 35

    lento = (
        (pd.notna(intervalo_esperado) and intervalo_esperado >= 45)
        or (v90 <= 2 and dias_sem_vender >= 45)
        or venda_mensal_ref < 1.2
        or giro_lote_lento
    )
    muito_lento = (
        (pd.notna(intervalo_esperado) and intervalo_esperado >= 75)
        or (v90 <= 1 and dias_sem_vender >= 80)
        or venda_mensal_ref < 0.55
        or giro_lote_muito_lento
    )
    bom_giro = (
        v30 >= 3
        or venda_mensal_ref >= 3.2
        or (pd.notna(intervalo_esperado) and intervalo_esperado <= 14 and qtd_vendida_total >= 3)
    )
    otimo_giro = (
        v30 >= 6
        or venda_mensal_ref >= 6
        or (pd.notna(intervalo_esperado) and intervalo_esperado <= 7 and qtd_vendida_total >= 4)
    )
    excesso = (
        estoque > 0
        and (
            cobertura >= max(alvo_dias * 2.2, 75)
            or estoque_meses >= 3.0
            or (lento and estoque >= max(2.0, venda_mensal_ref * 2.5))
        )
    )

    janela_planejada = max(7, int(alvo_dias + lead_time))
    janela_enxuta = max(lead_time + 7, int(alvo_dias * 0.65) + lead_time)
    if muito_lento:
        janela_repor = max(lead_time + 5, min(janela_enxuta, 20))
    elif lento:
        janela_repor = max(lead_time + 7, min(janela_enxuta, 28))
    else:
        janela_repor = janela_planejada

    estoque_seguranca = demanda * janela_repor * seguranca
    ponto_pedido = (demanda * lead_time) + estoque_seguranca
    estoque_alvo = (demanda * janela_repor) + estoque_seguranca
    comprar = max(0.0, estoque_alvo - estoque)

    urgencia = 0.0
    motivo = []

    if bom_giro:
        urgencia += 18.0
        motivo.append("tem giro real")
    if otimo_giro:
        urgencia += 12.0
        motivo.append("gira rápido")
    if margem >= 0.22:
        urgencia += 5.0
        motivo.append("margem boa")
    if sell_through >= 0.75 and qtd_comprada_total >= 3:
        urgencia += 5.0
        motivo.append("vende boa parte do que compra")
    if estoque <= 0 and bom_giro:
        urgencia += 22.0
        motivo.append("zerou mas continua com saída")
    if cobertura <= max(lead_time, 7) and venda_mensal_ref >= 2:
        urgencia += 20.0
        motivo.append("estoque curto para o ritmo atual")
    elif cobertura <= max(alvo_dias * 0.55, lead_time + 7) and venda_mensal_ref >= 1.2:
        urgencia += 10.0
    if dias_sem_comprar >= 45 and venda_mensal_ref >= 2 and qtd_vendida_total >= 3:
        urgencia += 6.0
        motivo.append("faz tempo que não recompra")
    if similar_quente and estoque <= 0 and not bom_giro and not historico_muito_fraco:
        urgencia += 8.0
        motivo.append("itens parecidos seguem vendendo")

    if pd.notna(intervalo_esperado) and intervalo_esperado > 0:
        relacao = dias_sem_vender / max(intervalo_esperado, 1.0)
        if relacao >= 2.8:
            urgencia -= 24.0
            motivo.append("já passou muito do ritmo normal de venda")
        elif relacao >= 1.8:
            urgencia -= 14.0
            motivo.append("venda recente esfriou")
        elif relacao >= 1.2:
            urgencia -= 6.0
    else:
        if dias_sem_vender > 60:
            urgencia -= 10.0
        if dias_sem_vender > 120:
            urgencia -= 14.0

    if lento:
        urgencia -= 10.0
        motivo.append("giro lento")
    if muito_lento:
        urgencia -= 16.0
        motivo.append("vende muito devagar")
    if giro_lote_lento:
        urgencia -= 16.0
        motivo.append("demorou muito para girar depois da compra")
    if giro_lote_muito_lento:
        urgencia -= 20.0
        motivo.append("primeiro giro do lote foi muito demorado")
    if historico_fraco:
        urgencia -= 8.0
        motivo.append("histórico ainda fraco")
    if historico_muito_fraco:
        urgencia -= 10.0
    if venda_isolada_recente:
        urgencia -= 14.0
        motivo.append("1 venda isolada recente não prova giro")
    if excesso:
        urgencia -= 30.0
        motivo.append("já tem estoque suficiente por bastante tempo")
        comprar = 0.0

    if estoque <= 0 and muito_lento and not similar_quente:
        comprar = 0.0
    elif estoque <= 0 and lento and not bom_giro:
        comprar = 0.0 if historico_muito_fraco else min(comprar, 1.0)
    elif lento:
        comprar = min(comprar, max(0.0, round(venda_mensal_ref * 0.8)))

    if historico_muito_fraco and giro_lote_muito_lento:
        comprar = 0.0
    if venda_isolada_recente and giro_lote_lento:
        comprar = 0.0
    if not bom_giro and similar_quente and estoque <= 0 and comprar <= 0 and not historico_muito_fraco:
        comprar = 1.0

    urgencia = max(0.0, min(100.0, urgencia))

    if excesso:
        acao = "Não comprar agora"
        urgencia = min(urgencia, 18.0)
        comprar = 0.0
    elif historico_muito_fraco and giro_lote_muito_lento:
        acao = "Não comprar agora"
        urgencia = min(urgencia, 10.0)
        comprar = 0.0
        motivo.append("zerou, mas levou meses para vender")
    elif estoque <= 0 and muito_lento and not similar_quente:
        acao = "Não comprar agora"
        urgencia = min(urgencia, 15.0)
        comprar = 0.0
        motivo.append("zerou, mas o histórico é fraco")
    elif estoque <= 0 and bom_giro and not giro_lote_lento:
        acao = "Comprar já"
        comprar = max(comprar, max(1.0, round(venda_mensal_ref * 0.9)))
        urgencia = max(urgencia, 82.0)
    elif cobertura <= max(lead_time, 7) and bom_giro and not giro_lote_lento:
        acao = "Comprar já"
        urgencia = max(urgencia, 76.0)
    elif cobertura <= max(alvo_dias * 0.55, lead_time + 7) and venda_mensal_ref >= 1.2 and not giro_lote_muito_lento:
        acao = "Planejar compra"
        urgencia = max(urgencia, 56.0)
    elif estoque <= 0 and similar_quente and not historico_muito_fraco:
        acao = "Teste leve"
        comprar = max(1.0, min(2.0, comprar if comprar > 0 else 1.0))
        urgencia = max(urgencia, 40.0)
    elif lento and estoque > 0:
        acao = "Segurar estoque"
        comprar = 0.0
        urgencia = min(urgencia, 28.0)
    else:
        acao = "Monitorar"

    leitura = []
    if estoque <= 0:
        leitura.append("sem estoque hoje")
    else:
        leitura.append(f"estoque atual de {int(round(estoque))} unid.")

    if v30 > 0:
        leitura.append(f"vendeu {int(round(v30))} unid. nos últimos 30 dias")
    elif v90 > 0:
        leitura.append(f"vendeu {int(round(v90))} unid. nos últimos 90 dias")
    else:
        leitura.append("sem venda recente no histórico")

    if pd.notna(intervalo_esperado) and qtd_vendida_total >= 2:
        leitura.append(f"este item costuma sair a cada {float(intervalo_esperado):.0f} dias")
    if pd.notna(lag_compra_venda_ref):
        leitura.append(f"levou cerca de {float(lag_compra_venda_ref):.0f} dias da compra até vender")
    if dias_sem_vender < 9999:
        leitura.append(f"última venda há {int(dias_sem_vender)} dias")
    if dias_sem_comprar < 9999:
        leitura.append(f"última compra há {int(dias_sem_comprar)} dias")
    if similar_quente:
        leitura.append("há item parecido com saída recente")
    if excesso:
        leitura.append("já tem estoque para vários meses")

    resumo = " • ".join(leitura[:6]) if leitura else "sem histórico suficiente"
    motivo_txt = ", ".join(dict.fromkeys(motivo)) if motivo else "combinação de estoque, giro e recência"

    return pd.Series({
        "PONTO_PEDIDO": ponto_pedido,
        "ESTOQUE_ALVO": estoque_alvo,
        "QTD_RECOMENDADA": int(max(0, round(comprar))),
        "URGENCIA": urgencia,
        "ACAO": acao,
        "RESUMO_IA": resumo,
        "MOTIVO_IA": motivo_txt,
    })


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

NAV_OPTS = ["📊 Dashboard", "🔎 Pesquisa de produto", "⚠️ Alertas", "🧠 IA de reposição", "🧾 Compras"]
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

        st.markdown("<div style="height:10px"></div>", unsafe_allow_html=True)

        # Top produtos com maior lucro total
        st.markdown(
            """
<div class="section-title">💰 Top produtos com maior lucro</div>
<div class="section-sub">Top 6 por lucro total real do produto no período. Aqui a quantidade já entra na conta: se vendeu mais unidades e somou mais lucro, ele sobe no ranking.</div>
""",
            unsafe_allow_html=True,
        )

        lucro_view = top_prod.sort_values(["LUCRO", "QTD_VENDIDA", "RECEITA"], ascending=[False, False, False]).head(6).copy()
        lucro_view["LUCRO_POR_UNID"] = lucro_view["LUCRO"] / lucro_view["QTD_VENDIDA"].replace(0, pd.NA)

        lucro_view["CUSTO_MEDIO_FIFO_FMT"] = lucro_view["CUSTO_MEDIO_FIFO"].map(format_reais)
        lucro_view["PRECO_MEDIO_VENDA_FMT"] = lucro_view["PRECO_MEDIO_VENDA"].map(format_reais)
        lucro_view["LUCRO_FMT"] = lucro_view["LUCRO"].map(format_reais)
        lucro_view["RECEITA_FMT"] = lucro_view["RECEITA"].map(format_reais)
        lucro_view["LUCRO_POR_UNID_FMT"] = lucro_view["LUCRO_POR_UNID"].fillna(0).map(format_reais)

        tabela_lucro = lucro_view[
            [
                "PRODUTO",
                "QTD_VENDIDA",
                "SALDO_QTD",
                "LUCRO_POR_UNID_FMT",
                "RECEITA_FMT",
                "LUCRO_FMT",
            ]
        ].rename(
            columns={
                "PRODUTO": "Produto",
                "QTD_VENDIDA": "Qtd vendida",
                "SALDO_QTD": "Estoque atual",
                "LUCRO_POR_UNID_FMT": "Lucro por unid.",
                "RECEITA_FMT": "Receita total",
                "LUCRO_FMT": "Lucro total (FIFO)",
            }
        )

        headers_lucro = ["Produto", "Qtd", "Estoque", "Lucro/unid.", "Receita", "Lucro total"]
        rows_lucro = []
        for _, r in tabela_lucro.iterrows():
            prod = _safe(r.get("Produto", ""))
            link = f"?produto={quote(prod)}"
            prod_html = f'<div class="prodcell"><a class="lens" href="{link}" target="_self" title="Abrir na Pesquisa">🔍</a><span>{prod}</span></div>'
            rows_lucro.append(
                "<tr>"
                + _td(prod_html)
                + _td(_safe(int(r.get("Qtd vendida", 0))))
                + _td(_safe(int(r.get("Estoque atual", 0))))
                + _td(_safe(r.get("Lucro por unid.", "")))
                + _td(_safe(r.get("Receita total", "")))
                + _td(_safe(r.get("Lucro total (FIFO)", "")))
                + "</tr>"
            )

        st.markdown(_render_compact_table(rows_lucro, headers_lucro), unsafe_allow_html=True)

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
<div class="section-sub">Digite parte do nome, apelido ou palavra-chave. Ex.: <b>fone</b>, <b>mouse</b>, <b>iphone</b>. Os itens com estoque aparecem primeiro.</div>
""",
        unsafe_allow_html=True,
    )

    if df_fifo.empty and df_estoque.empty:
        st.info("Sem dados de estoque ou vendas para pesquisar.")
    else:
        produtos_estoque = df_estoque["PRODUTO"].unique().tolist() if not df_estoque.empty else []
        produtos_vendas = df_fifo["PRODUTO"].unique().tolist() if not df_fifo.empty else []
        produtos_compras = df_compras["PRODUTO"].dropna().astype(str).unique().tolist() if "PRODUTO" in df_compras.columns else []
        todos_produtos = sorted(set(produtos_estoque) | set(produtos_vendas) | set(produtos_compras))

        busca_inicial = ""
        if st.session_state.get("produto_pesquisa"):
            busca_inicial = str(st.session_state.get("produto_pesquisa"))

        busca_produto = st.text_input(
            "Buscar produto",
            value=busca_inicial if not st.session_state.get("busca_produto_digitada") else st.session_state.get("busca_produto_digitada", ""),
            placeholder="Ex.: fone, cabo iphone, mouse, caixa de som...",
            help="Pode digitar só um pedaço. A lista entende termos parecidos e joga os itens com estoque para cima.",
            key="busca_produto_digitada",
        )

        resultado_busca = buscar_produtos_relacionados(busca_produto, todos_produtos, estoque_atual_map, limite=120)

        if resultado_busca.empty:
            st.warning("Nada apareceu nessa busca. Tenta uma palavra mais curta ou mais genérica.")
            prod_sel = "(selecione)"
        else:
            qtd_match = len(resultado_busca)
            qtd_com_estoque = int((resultado_busca["ESTOQUE"] > 0).sum())
            st.caption(f"{qtd_match} produto(s) encontrado(s) • {qtd_com_estoque} com estoque agora")

            top_atalhos = resultado_busca.head(8)["PRODUTO"].tolist()
            if top_atalhos:
                st.markdown("**Achados mais prováveis**")
                cols = st.columns(min(4, len(top_atalhos)))
                escolhido_atalho = None
                for i, prod in enumerate(top_atalhos):
                    with cols[i % len(cols)]:
                        estoque_txt = int(round(float(estoque_atual_map.get(prod, 0) or 0)))
                        rotulo_btn = f"{prod[:34]}{'…' if len(prod) > 34 else ''} ({estoque_txt})"
                        if st.button(rotulo_btn, key=f"atalho_busca_{i}", use_container_width=True):
                            escolhido_atalho = prod
                if escolhido_atalho:
                    st.session_state.produto_pesquisa = escolhido_atalho

            opcoes_filtradas = resultado_busca["PRODUTO"].tolist()
            idx_default = 0
            atual = st.session_state.get("produto_pesquisa")
            if atual in opcoes_filtradas:
                idx_default = opcoes_filtradas.index(atual)

            prod_sel = st.selectbox(
                "Produto encontrado",
                options=opcoes_filtradas,
                index=idx_default,
                format_func=lambda p: label_produto_busca(p, estoque_atual_map),
                help="A lista já vem ordenada com quem tem estoque primeiro e sem estoque por último.",
            )

        if prod_sel and prod_sel != "(selecione)":
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

            relacionados = buscar_produtos_relacionados(busca_produto, todos_produtos, estoque_atual_map, limite=12) if busca_produto else pd.DataFrame()
            if not relacionados.empty:
                relacionados = relacionados[relacionados["PRODUTO"] != prod_sel].head(5)
                if not relacionados.empty:
                    sugestoes = " • ".join([label_produto_busca(p, estoque_atual_map) for p in relacionados["PRODUTO"].tolist()])
                    st.caption(f"Talvez você também esteja procurando: {sugestoes}")

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
                vendas_prod_hist["DATA_ORD"] = vendas_prod_hist["DATA"]
                vendas_prod_hist["DATA"] = vendas_prod_hist["DATA"].dt.strftime("%d/%m/%Y").fillna("")
                vendas_prod_hist["VALOR_TOTAL"] = vendas_prod_hist["VALOR_TOTAL"].map(format_reais)
                vendas_prod_hist["CUSTO_TOTAL"] = vendas_prod_hist["CUSTO_TOTAL"].map(format_reais)
                vendas_prod_hist["LUCRO"] = vendas_prod_hist["LUCRO"].map(format_reais)
                vendas_prod_hist["CUSTO_UNIT"] = vendas_prod_hist["CUSTO_UNIT"].map(format_reais)

                cols_hist = [
                    "DATA",
                    "CLIENTE",
                    "STATUS",
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
                    vendas_prod_hist.sort_values("DATA_ORD", ascending=False)[cols_hist].head(30),
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
- Agora a busca aceita palavra solta e também ajuda a achar família de produto sem exigir nome exato.
- Olhando o **histórico de compras**, você enxerga:
  - se está pagando mais caro ou mais barato ao longo do tempo,
  - se vale negociar de novo com o fornecedor,
  - e se não está enchendo estoque de um item que não gira tanto assim.
                """
            )
        else:
            st.info("Digite algo para filtrar e escolha um produto para ver os detalhes baseados no FIFO.")

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
        max_dias_fifo_parado = 0
        if "df_lotes_fifo" in globals() and not df_lotes_fifo.empty and "DIAS_PARADO_LOTE" in df_lotes_fifo.columns:
            max_dias_fifo_parado = int(pd.to_numeric(df_lotes_fifo["DIAS_PARADO_LOTE"], errors="coerce").fillna(0).max())

        if max_dias_fifo_parado >= 30:
            topo_redondo = (max_dias_fifo_parado // 30) * 30
            opcoes_dias_parado = list(range(30, topo_redondo + 1, 30)) if topo_redondo >= 30 else []
            if not opcoes_dias_parado or opcoes_dias_parado[-1] != max_dias_fifo_parado:
                opcoes_dias_parado.append(max_dias_fifo_parado)
        elif max_dias_fifo_parado > 0:
            opcoes_dias_parado = [max_dias_fifo_parado]
        else:
            opcoes_dias_parado = [30]

        def _label_dias_parado(dias):
            dias = int(dias)
            meses = max(1, dias // 30)
            if max_dias_fifo_parado > 0 and dias == max_dias_fifo_parado and dias % 30 != 0:
                meses_txt = f"{meses} meses" if meses > 1 else "1 mês"
                return f"{meses_txt} ou mais (máx. atual: {dias} dias)"
            if dias == 30:
                return "1 mês ou mais"
            if dias % 30 == 0:
                return f"{meses} meses ou mais"
            return f"{dias} dias ou mais"

        LIM_DIAS_PARADO = st.select_slider(
            "Estoque parado a partir de",
            options=opcoes_dias_parado,
            value=opcoes_dias_parado[-1],
            format_func=_label_dias_parado,
        )

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

        valor_estoque_total_geral = float(df_estoque["VALOR_ESTOQUE"].sum()) if (not df_estoque.empty and "VALOR_ESTOQUE" in df_estoque.columns) else 0.0
        st.markdown("### 🐌 Estoque parado há muito tempo")
        st.caption("FIFO do saldo atual: a venda consome os lotes mais antigos primeiro, então o tempo parado olha só para o que realmente sobrou no estoque.")
        st.caption(f"Corte em blocos de 30 dias, indo até o máximo encontrado no saldo remanescente por FIFO: {max_dias_fifo_parado} dias.")

        if df_lotes_fifo.empty:
            parado_filtrado = pd.DataFrame()
            st.info("Sem lotes remanescentes para analisar no estoque parado.")
        else:
            lotes_alerta = df_lotes_fifo.copy()
            lotes_alerta = lotes_alerta[
                (lotes_alerta["QTD_REMANESCENTE"] > 0)
                & (lotes_alerta["DIAS_PARADO_LOTE"].notna())
            ].copy()

            if lotes_alerta.empty:
                parado_filtrado = pd.DataFrame()
                st.info("Sem lotes remanescentes válidos para analisar.")
            else:
                lotes_alerta["DATA_LOTE"] = pd.to_datetime(lotes_alerta["DATA_LOTE"], errors="coerce")
                lotes_filtrados = lotes_alerta[lotes_alerta["DIAS_PARADO_LOTE"] >= LIM_DIAS_PARADO].copy()

                if lotes_filtrados.empty:
                    parado_filtrado = pd.DataFrame()
                    st.info(f"Nenhum produto com saldo remanescente parado a partir de {LIM_DIAS_PARADO} dias pelo FIFO.")
                else:
                    resumo_parado = (
                        lotes_filtrados.groupby("PRODUTO", as_index=False)
                        .agg(
                            SALDO_QTD=("QTD_REMANESCENTE", "sum"),
                            VALOR_ESTOQUE=("VALOR_LOTE", "sum"),
                            DIAS_PARADO=("DIAS_PARADO_LOTE", "max"),
                            DIAS_MEDIO_PONDERADO=("DIAS_PARADO_LOTE", lambda s: 0),
                            LOTES_ABERTOS=("QTD_REMANESCENTE", "size"),
                            DATA_LOTE_ANTIGO=("DATA_LOTE", "min"),
                            DATA_LOTE_RECENTE=("DATA_LOTE", "max"),
                        )
                    )

                    media_ponderada = (
                        lotes_filtrados.assign(PESO_DIAS=lotes_filtrados["QTD_REMANESCENTE"] * lotes_filtrados["DIAS_PARADO_LOTE"])
                        .groupby("PRODUTO", as_index=False)
                        .agg(PESO_DIAS=("PESO_DIAS", "sum"), QTD_TOTAL=("QTD_REMANESCENTE", "sum"))
                    )
                    media_ponderada["DIAS_MEDIO_PONDERADO"] = (
                        media_ponderada["PESO_DIAS"] / media_ponderada["QTD_TOTAL"].replace(0, pd.NA)
                    )

                    parado_filtrado = resumo_parado.drop(columns=["DIAS_MEDIO_PONDERADO"]).merge(
                        media_ponderada[["PRODUTO", "DIAS_MEDIO_PONDERADO"]],
                        on="PRODUTO",
                        how="left",
                    )
                    parado_filtrado["PCT_ESTOQUE_TOTAL"] = (
                        parado_filtrado["VALOR_ESTOQUE"] / max(valor_estoque_total_geral, 1e-9) * 100
                        if 'valor_estoque_total_geral' in locals() else 0.0
                    )

                    def faixa_parado(dias):
                        if dias >= 120:
                            return "Crítico"
                        if dias >= 90:
                            return "Alto"
                        if dias >= 60:
                            return "Atenção"
                        return "Moderado"

                    parado_filtrado["FAIXA"] = parado_filtrado["DIAS_PARADO"].apply(faixa_parado)
                    parado_filtrado["VALOR_ESTOQUE_FMT"] = parado_filtrado["VALOR_ESTOQUE"].map(format_reais)
                    parado_filtrado["DATA_LOTE_ANTIGO_FMT"] = parado_filtrado["DATA_LOTE_ANTIGO"].dt.strftime("%d/%m/%Y")
                    parado_filtrado["DATA_LOTE_RECENTE_FMT"] = parado_filtrado["DATA_LOTE_RECENTE"].dt.strftime("%d/%m/%Y")
                    parado_filtrado["DIAS_MEDIO_PONDERADO"] = parado_filtrado["DIAS_MEDIO_PONDERADO"].fillna(0).round(0).astype(int)
                    parado_filtrado["PCT_ESTOQUE_TOTAL"] = parado_filtrado["PCT_ESTOQUE_TOTAL"].fillna(0)
                    parado_filtrado = parado_filtrado.sort_values(["DIAS_PARADO", "VALOR_ESTOQUE"], ascending=[False, False])

                    total_parado_valor = float(parado_filtrado["VALOR_ESTOQUE"].sum())
                    total_parado_qtd = float(parado_filtrado["SALDO_QTD"].sum())
                    pct_total_parado = (total_parado_valor / valor_estoque_total_geral * 100) if valor_estoque_total_geral > 0 else 0.0
                    item_mais_antigo = parado_filtrado.iloc[0]

                    a1, a2, a3, a4 = st.columns(4)
                    with a1:
                        st.markdown(f"""
<div class="kpi-card">
  <div class="kpi-label">Valor parado na tela</div>
  <div class="kpi-value">{format_reais(total_parado_valor)}</div>
  <div class="kpi-pill">Soma dos lotes que passaram do corte atual</div>
</div>
""", unsafe_allow_html=True)
                    with a2:
                        st.markdown(f"""
<div class="kpi-card">
  <div class="kpi-label">Unidades paradas</div>
  <div class="kpi-value">{int(round(total_parado_qtd))}</div>
  <div class="kpi-pill">Quantidade remanescente analisada por FIFO</div>
</div>
""", unsafe_allow_html=True)
                    with a3:
                        st.markdown(f"""
<div class="kpi-card">
  <div class="kpi-label">Peso no estoque</div>
  <div class="kpi-value">{pct_total_parado:,.1f}%</div>
  <div class="kpi-pill">Parte do valor total do estoque presa nessa lista</div>
</div>
""", unsafe_allow_html=True)
                    with a4:
                        st.markdown(f"""
<div class="kpi-card">
  <div class="kpi-label">Mais antigo</div>
  <div class="kpi-value">{int(item_mais_antigo['DIAS_PARADO'])} dias</div>
  <div class="kpi-pill">{item_mais_antigo['PRODUTO']}</div>
</div>
""", unsafe_allow_html=True)

                    st.dataframe(
                        parado_filtrado[
                            [
                                "PRODUTO",
                                "SALDO_QTD",
                                "VALOR_ESTOQUE_FMT",
                                "DIAS_PARADO",
                                "DIAS_MEDIO_PONDERADO",
                                "LOTES_ABERTOS",
                                "FAIXA",
                                "PCT_ESTOQUE_TOTAL",
                                "DATA_LOTE_ANTIGO_FMT",
                                "DATA_LOTE_RECENTE_FMT",
                            ]
                        ].rename(
                            columns={
                                "PRODUTO": "Produto",
                                "SALDO_QTD": "Estoque atual",
                                "VALOR_ESTOQUE_FMT": "Valor parado (FIFO)",
                                "DIAS_PARADO": "Maior idade",
                                "DIAS_MEDIO_PONDERADO": "Idade média",
                                "LOTES_ABERTOS": "Lotes abertos",
                                "FAIXA": "Faixa",
                                "PCT_ESTOQUE_TOTAL": "% do estoque",
                                "DATA_LOTE_ANTIGO_FMT": "Lote mais antigo",
                                "DATA_LOTE_RECENTE_FMT": "Lote mais recente",
                            }
                        ),
                        use_container_width=True,
                        column_config={
                            "% do estoque": st.column_config.NumberColumn(format="%.1f%%")
                        },
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

elif nav == "🧠 IA de reposição":
    st.markdown(
        """
<div class="section-title">🧠 IA de reposição de estoque</div>
<div class="section-sub">
Agora a leitura ficou mais humana: estoque zerado não significa comprar no automático, e estoque alto também não. A IA tenta separar o que gira bem do que só ocupa espaço, olhando tempo entre vendas, última compra, última venda, estoque atual e produtos parecidos.
</div>
""",
        unsafe_allow_html=True,
    )

    base_ia = build_reposicao_inteligente(df_fifo, df_estoque, df_compras)

    if base_ia.empty:
        st.info("Ainda não há base suficiente para sugerir reposição.")
    else:
        st.markdown(
            """
<div class="section-sub">
Passe o mouse nos ícones de atenção para entender cada parte sem poluir a tela.
</div>
""",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"""
<div class="hint-row">
  <span class="hint-chip">Cobertura desejada {_hint_icon('Por quantos dias você quer ficar abastecido nos itens que realmente giram. Quanto menor, mais enxuto fica o estoque.')}</span>
  <span class="hint-chip">Prazo do fornecedor {_hint_icon('Em quantos dias a reposição costuma chegar. Se seu fornecedor demora, o sistema sobe a necessidade de cobertura.')}</span>
  <span class="hint-chip">Reserva extra {_hint_icon('É um colchão de segurança para não faltar produto que vende bem quando a procura aperta.')}</span>
  <span class="hint-chip">Nível mínimo de prioridade {_hint_icon('Serve para esconder itens fracos e mostrar primeiro o que mais merece seu dinheiro agora.')}</span>
  <span class="hint-chip">Importante {_hint_icon('Produto zerado não significa compra automática. Se ele gira devagar ou demorou muito para vender, a IA pode marcar Não comprar agora.')}</span>
</div>
""",
            unsafe_allow_html=True,
        )

        perfis = {
            "Estoque enxuto": {"alvo_dias": 20, "seguranca": 0.10},
            "Equilibrado (recomendado)": {"alvo_dias": 30, "seguranca": 0.20},
            "Protegido (evita faltar)": {"alvo_dias": 45, "seguranca": 0.35},
        }
        prazos = {
            "Rápido — até 7 dias": 7,
            "Normal — até 15 dias": 15,
            "Demorado — até 30 dias": 30,
            "Muito demorado — até 45 dias": 45,
        }
        filtros_prioridade = {
            "Mostrar tudo": 0,
            "Só o que merece atenção": 35,
            "Só o mais urgente": 60,
            "Só compra imediata": 80,
        }

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            perfil_sel = st.selectbox("Estratégia de reposição", list(perfis.keys()), index=0)
        with c2:
            prazo_sel = st.selectbox("Prazo do fornecedor", list(prazos.keys()), index=1)
        with c3:
            cobertura_dias = st.number_input(
                "Cobertura desejada (dias)",
                min_value=10,
                max_value=120,
                value=60,
                step=5,
                help="Quantos dias de estoque você quer ter depois da compra.",
            )
        with c4:
            prioridade_sel = st.selectbox("Nível mínimo de prioridade", list(filtros_prioridade.keys()), index=0)

        c5, c6 = st.columns([1.2, 2.8])
        with c5:
            reserva_extra = st.selectbox(
                "Reserva extra",
                ["Baixa", "Média", "Alta"],
                index=1,
                help="Colchão adicional para evitar falta quando o giro aperta.",
            )
        mapa_reserva = {"Baixa": 0.10, "Média": 0.20, "Alta": 0.35}
        seguranca = max(perfis[perfil_sel]["seguranca"], mapa_reserva[reserva_extra])
        lead_time = prazos[prazo_sel]
        min_urgencia = filtros_prioridade[prioridade_sel]

        with c6:
            st.markdown(
                f"""
<div class="kpi-card" style="min-height:94px; display:flex; flex-direction:column; justify-content:center;">
  <div class="kpi-label">Leitura ativa do motor</div>
  <div class="kpi-pill">Meta de cobertura: <b>{int(cobertura_dias)} dias</b> · Prazo do fornecedor: <b>{lead_time} dias</b> · Reserva extra: <b>{int(seguranca*100)}%</b></div>
</div>
""",
                unsafe_allow_html=True,
            )

        calc = base_ia.apply(
            lambda row: classificar_reposicao(
                row,
                alvo_dias=int(cobertura_dias),
                lead_time=int(lead_time),
                seguranca=float(seguranca),
            ),
            axis=1,
        )
        base_ia = pd.concat([base_ia, calc], axis=1)

        base_ia["SCORE_FINAL"] = (
            base_ia["URGENCIA"]
            + (base_ia["MARGEM_PCT"].clip(lower=0) * 18)
            + (base_ia["SELL_THROUGH"].clip(lower=0, upper=2) * 8)
            + ((base_ia["V30_SIMILARES"].fillna(0) > 0).astype(int) * 4)
        )

        ordem_acoes = ["Comprar já", "Planejar compra", "Teste leve", "Monitorar", "Não comprar agora", "Segurar estoque"]
        ordem_map = {acao: i + 1 for i, acao in enumerate(ordem_acoes)}
        base_ia["ORDEM_ACAO_NUM"] = base_ia["ACAO"].map(ordem_map).fillna(99).astype(int)
        base_ia["ORDEM_ACAO"] = pd.Categorical(base_ia["ACAO"], categories=ordem_acoes, ordered=True)
        base_ia["CONFIANCA_IA"] = base_ia.apply(_nivel_confianca, axis=1)
        base_ia["RISCO_IA"] = base_ia.apply(_risco_analise, axis=1)

        def _numero_seguro(valor, padrao=0.0):
            try:
                n = float(valor)
                if pd.isna(n) or np.isinf(n):
                    return float(padrao)
                return n
            except Exception:
                return float(padrao)

        def _capital_parado_dias(row):
            cobertura = _numero_seguro(row.get("COBERTURA_DIAS", np.nan), np.nan)
            primeira_saida = _numero_seguro(row.get("DIAS_PRIMEIRA_COMPRA_ATE_PRIMEIRA_VENDA", 0), 0)

            if pd.notna(cobertura) and cobertura < 999:
                return int(round(max(cobertura, 0)))
            return int(round(max(primeira_saida, 0)))

        base_ia["CAPITAL_PARADO_DIAS"] = base_ia.apply(_capital_parado_dias, axis=1)

        universo_acoes = ["Todos"] + [a for a in ordem_acoes if a in base_ia["ACAO"].dropna().unique().tolist()]
        f1, f2 = st.columns([1.2, 2.8])
        with f1:
            acao_sel = st.selectbox("Filtrar por ação", universo_acoes, index=0)
        with f2:
            busca = st.text_input("Buscar produto ou família", value="")

        view = base_ia.copy()
        if acao_sel != "Todos":
            view = view[view["ACAO"] == acao_sel].copy()
        if busca.strip():
            termo = normalize_name(busca)
            view = view[view["PRODUTO"].astype(str).apply(lambda x: termo in normalize_name(x))].copy()

        view = view[view["URGENCIA"] >= min_urgencia].copy()

        view = view.sort_values(["ORDEM_ACAO_NUM", "QTD_RECOMENDADA", "URGENCIA", "SCORE_FINAL", "PRODUTO"], ascending=[True, False, False, False, True], kind="mergesort")

        total_para_comprar = int(view["QTD_RECOMENDADA"].fillna(0).sum()) if not view.empty else 0
        produtos_criticos = int((view["ACAO"].isin(["Comprar já"])).sum()) if not view.empty else 0
        capital_estimado = float((view["QTD_RECOMENDADA"].fillna(0) * view["CUSTO_MEDIO_FIFO"].fillna(0)).sum()) if not view.empty else 0.0
        itens_teste = int((view["ACAO"] == "Teste leve").sum()) if not view.empty else 0
        capital_parado_medio = int(view["CAPITAL_PARADO_DIAS"].clip(lower=0).mean()) if not view.empty else 0

        k1, k2, k3, k4, k5 = st.columns(5)
        with k1:
            st.markdown(f"""
<div class="kpi-card">
  <div class="kpi-label">Comprar agora</div>
  <div class="kpi-value">{produtos_criticos}</div>
  <div class="kpi-pill">Itens realmente fortes que pedem recompra imediata</div>
</div>
""", unsafe_allow_html=True)
        with k2:
            st.markdown(f"""
<div class="kpi-card">
  <div class="kpi-label">Qtd sugerida</div>
  <div class="kpi-value">{total_para_comprar} unid.</div>
  <div class="kpi-pill">Soma das recomendações no filtro</div>
</div>
""", unsafe_allow_html=True)
        with k3:
            st.markdown(f"""
<div class="kpi-card">
  <div class="kpi-label">Capital estimado</div>
  <div class="kpi-value">{format_reais(capital_estimado)}</div>
  <div class="kpi-pill">Baseado no custo FIFO atual</div>
</div>
""", unsafe_allow_html=True)
        with k4:
            st.markdown(f"""
<div class="kpi-card">
  <div class="kpi-label">Teste leve</div>
  <div class="kpi-value">{itens_teste}</div>
  <div class="kpi-pill">Produtos sem histórico forte, mas com sinais na família</div>
</div>
""", unsafe_allow_html=True)
        with k5:
            st.markdown(f"""
<div class="kpi-card">
  <div class="kpi-label">Capital parado</div>
  <div class="kpi-value">{capital_parado_medio} dias</div>
  <div class="kpi-pill">Média de quanto o dinheiro tende a ficar preso nesse grupo</div>
</div>
""", unsafe_allow_html=True)

        top_repor = view.head(18).copy()
        st.markdown("---")
        st.markdown(
            """
<div class="section-title">🎯 Prioridade de compra</div>
<div class="section-sub">
A ordem olha quatro coisas ao mesmo tempo: o que vendeu, há quantos dias vendeu, há quanto tempo você não recompra e quanto ainda sobrou em estoque hoje.
</div>
""",
            unsafe_allow_html=True,
        )

        if top_repor.empty:
            st.info("Nenhum item bateu o filtro atual. Hoje o estoque conseguiu dormir sem susto.")
        else:
            tabela = top_repor.copy()
            tabela["ESTOQUE_ATUAL"] = tabela["ESTOQUE_ATUAL"].round(0).astype(int)
            tabela["QTD_RECOMENDADA"] = tabela["QTD_RECOMENDADA"].round(0).astype(int)
            tabela["COBERTURA_DIAS_FMT"] = tabela["COBERTURA_DIAS"].apply(lambda x: f"{x:,.1f} dias" if x < 999 else "sem giro")
            tabela["ULTIMA_COMPRA_FMT"] = pd.to_datetime(tabela["ULTIMA_COMPRA"], errors="coerce").dt.strftime("%d/%m/%Y").fillna("—")
            tabela["ULTIMA_VENDA_FMT"] = pd.to_datetime(tabela["ULTIMA_VENDA"], errors="coerce").dt.strftime("%d/%m/%Y").fillna("—")
            tabela["LEITURA_FMT"] = tabela["RESUMO_IA"].fillna("")
            tabela["PRIORIDADE_FMT"] = tabela["URGENCIA"].apply(lambda x: f"{float(x):.0f}/100")

            headers = ["Ação sugerida", "Produto", "Prioridade", "Sugestão", "Estoque", "Cobertura", "Leitura da IA"]
            rows = []
            for _, r in tabela.iterrows():
                prod = _safe(r.get("PRODUTO", ""))
                link = f"?produto={quote(prod)}"
                prod_html = f'<div class="prodcell"><a class="lens" href="{link}" target="_self" title="Abrir na Pesquisa">🔍</a><span>{prod}</span></div>'
                leitura_hover = f'<span class="hover-cell">{_mini_hover(_painel_resultado_text(r), icon="🧠")}<span class="muted">passar mouse</span></span>'
                rows.append(
                    "<tr>"
                    + _td(_acao_badge(r.get("ACAO", "")))
                    + _td(prod_html)
                    + _td(_safe(r.get("PRIORIDADE_FMT", "")), "muted")
                    + _td(_safe(r.get("QTD_RECOMENDADA", 0)))
                    + _td(_safe(r.get("ESTOQUE_ATUAL", 0)))
                    + _td(_safe(r.get("COBERTURA_DIAS_FMT", "")), "muted")
                    + _td(leitura_hover, "muted")
                    + "</tr>"
                )
            st.markdown(_render_compact_table(rows, headers), unsafe_allow_html=True)

        st.markdown("---")
        st.markdown(
            """
<div class="section-title">🧬 Explicação item por item</div>
<div class="section-sub">
Aqui o sistema abre o raciocínio em português claro, para você bater o olho e entender o porquê da sugestão.
</div>
""",
            unsafe_allow_html=True,
        )

        detalhe_cols = [
            "PRODUTO", "ACAO", "QTD_RECOMENDADA", "URGENCIA", "ESTOQUE_ATUAL", "V30", "V60",
            "DIAS_DESDE_ULT_VENDA", "DIAS_DESDE_ULT_COMPRA", "DIAS_DESDE_ULT_VENDA_SIMILAR",
            "INTERVALO_ESPERADO", "COBERTURA_DIAS", "SIMILARES", "MOTIVO_IA", "RESUMO_IA", "ORDEM_ACAO", "ORDEM_ACAO_NUM",
            "CAPITAL_PARADO_DIAS"
        ]
        detalhe = view[detalhe_cols].copy() if not view.empty else pd.DataFrame(columns=detalhe_cols)
        if not detalhe.empty:
            detalhe = detalhe.sort_values(
                ["ORDEM_ACAO_NUM", "QTD_RECOMENDADA", "URGENCIA", "PRODUTO"],
                ascending=[True, False, False, True],
                kind="mergesort"
            ).copy()
            detalhe["PRIORIDADE_FMT"] = detalhe["URGENCIA"].apply(lambda x: f"{float(x):.0f}/100")
            detalhe["QTD_FMT"] = detalhe["QTD_RECOMENDADA"].round(0).astype(int)
            detalhe["ESTOQUE_FMT"] = detalhe["ESTOQUE_ATUAL"].round(0).astype(int)
            detalhe["V30_FMT"] = detalhe["V30"].round(0).astype(int)
            detalhe["V60_FMT"] = detalhe["V60"].round(0).astype(int)
            detalhe["DIAS_VENDA_FMT"] = detalhe["DIAS_DESDE_ULT_VENDA"].apply(lambda x: "—" if pd.isna(x) or float(x) >= 9999 else int(round(float(x))))
            detalhe["DIAS_COMPRA_FMT"] = detalhe["DIAS_DESDE_ULT_COMPRA"].apply(lambda x: "—" if pd.isna(x) or float(x) >= 9999 else int(round(float(x))))
            detalhe["DIAS_SIMILAR_FMT"] = detalhe["DIAS_DESDE_ULT_VENDA_SIMILAR"].apply(lambda x: "—" if pd.isna(x) or float(x) >= 9999 else int(round(float(x))))
            detalhe["INTERVALO_FMT"] = detalhe["INTERVALO_ESPERADO"].apply(lambda x: "—" if pd.isna(x) else round(float(x), 1))
            detalhe["COBERTURA_FMT"] = detalhe["COBERTURA_DIAS"].apply(lambda x: "sem giro" if pd.isna(x) or float(x) >= 999 else f"{float(x):.1f} dias")

            headers = ["Ação", "Produto", "Prioridade", "Est./Sug.", "Movimento", "Datas", "Ritmo", "Motivo", "IA"]
            rows = []
            for _, r in detalhe.iterrows():
                prod = _safe(r.get("PRODUTO", ""))
                link = f"?produto={quote(prod)}"
                prod_html = f'<div class="prodcell"><a class="lens" href="{link}" target="_self" title="Abrir na Pesquisa">🔍</a><span>{prod}</span></div>'
                motivo_hover = f'<span class="hover-cell">{_mini_hover(r.get("MOTIVO_IA", "Sem motivo disponível"), icon="⚠️")}<span class="muted">ver</span></span>'
                resumo_hover = f'<span class="hover-cell">{_mini_hover(_painel_resultado_text(r), icon="🧠")}<span class="muted">ver</span></span>'
                estoque_sug_html = (
                    f'<div style="line-height:1.25">'
                    f'<div><strong>{_safe(r.get("ESTOQUE_FMT", 0))}</strong> em estoque</div>'
                    f'<div class="muted">sugestão: {_safe(r.get("QTD_FMT", 0))}</div>'
                    f'</div>'
                )
                movimento_html = (
                    f'<div style="line-height:1.25">'
                    f'<div>30d: <strong>{_safe(r.get("V30_FMT", 0))}</strong></div>'
                    f'<div class="muted">60d: {_safe(r.get("V60_FMT", 0))}</div>'
                    f'</div>'
                )
                datas_html = (
                    f'<div style="line-height:1.25">'
                    f'<div>venda: <strong>{_safe(r.get("DIAS_VENDA_FMT", "—"))}</strong>d</div>'
                    f'<div class="muted">compra: {_safe(r.get("DIAS_COMPRA_FMT", "—"))}d • parecido: {_safe(r.get("DIAS_SIMILAR_FMT", "—"))}d</div>'
                    f'</div>'
                )
                ritmo_html = (
                    f'<div style="line-height:1.25">'
                    f'<div>médio: <strong>{_safe(r.get("INTERVALO_FMT", "—"))}</strong>d</div>'
                    f'<div class="muted">cobertura: {_safe(r.get("COBERTURA_FMT", ""))}</div>'
                    f'</div>'
                )
                rows.append(
                    "<tr>"
                    + _td(_acao_badge(r.get("ACAO", "")))
                    + _td(prod_html)
                    + _td(_safe(r.get("PRIORIDADE_FMT", "")), "muted")
                    + _td(estoque_sug_html)
                    + _td(movimento_html)
                    + _td(datas_html, "muted")
                    + _td(ritmo_html, "muted")
                    + _td(motivo_hover, "muted")
                    + _td(resumo_hover, "muted")
                    + "</tr>"
                )
            st.markdown(_render_compact_table(rows, headers), unsafe_allow_html=True)
        else:
            st.info("Nada para detalhar com o filtro atual.")

        st.markdown("---")
        st.markdown(
            """
<div class="section-title">🪄 Como essa IA pensa</div>
<div class="section-sub">
Nada de mágica de fumaça: ela segue sinais reais da sua operação.
</div>
""",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"""
- **O que vende de verdade:** usa vendas dos últimos 30, 60 e 90 dias, dando mais peso ao que aconteceu agora.  
- **Tempo entre vendas:** tenta descobrir em quantos dias aquele item costuma girar. Se já passou muito desse ritmo, ela esfria a recomendação.  
- **Última venda x última compra:** compara há quantos dias vendeu pela última vez e há quantos dias você não recompra. Isso evita comprar cedo demais ou tarde demais.  
- **Produtos parecidos:** quando um item tem pouco histórico, a IA olha a família parecida como pista extra — não manda no resultado sozinha, só ajuda a iluminar a trilha.  
- **Estoque atual hoje:** se a cobertura não aguenta o prazo do fornecedor e sua meta de {int(cobertura_dias)} dias, a compra sobe na fila.  
- **Leitura da IA:** passe o mouse no ícone para ver o resumo do raciocínio sem ocupar espaço na tela.  
- **Capital parado:** o painel estima quantos dias seu dinheiro tende a ficar preso naquele item para ajudar no estoque enxuto.  
- **Reserva extra:** foi configurada em **{int(seguranca*100)}%**, para segurar o tranco se a procura apertar.  
"""
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
