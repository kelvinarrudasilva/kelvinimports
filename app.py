# app_final_com_compras_lapidado.py
# Versão lapidada do dashboard com aba COMPRAS — pronta para rodar
# Melhorias aplicadas (resumo):
# - Refatoração modular (helpers, parsing, normalização, visual)
# - Tipagem básica e docstrings para funções importantes
# - Uso de st.cache_data para cachear download da planilha
# - Tratamento de exceções mais robusto e mensagens úteis ao usuário
# - Simplificação e deduplicação de conversões de moeda/inteiro
# - Limpeza de CSS: variáveis organizadas e menos repetição
# - Pequenas melhorias UX: labels consistentes, botão de refresh e download
# Dependências: streamlit, pandas, plotly, requests, openpyxl

import re
from io import BytesIO
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

# ------------------------
# Config
# ------------------------
st.set_page_config(page_title="Loja Importados – Dashboard", layout="wide", initial_sidebar_state="collapsed")

# URL da planilha (export xlsx)
URL_PLANILHA = "https://docs.google.com/spreadsheets/d/1TsRjsfw1TVfeEWBBvhKvsGQ5YUCktn2b/export?format=xlsx"

# ------------------------
# Utilitários: parsing e formatação
# ------------------------

_NUMBER_CLEAN_RE = re.compile(r"[^\d\,\.\-]")


def parse_money_value(x) -> float:
    """Converte strings monetárias (BRL) para float. Retorna NaN em casos inválidos."""
    try:
        if pd.isna(x):
            return float("nan")
    except Exception:
        pass
    s = str(x).strip()
    if s == "" or s.lower() in ("nan", "none", "-"):
        return float("nan")
    # remove caracteres não numéricos exceto , . -
    s = _NUMBER_CLEAN_RE.sub("", s)
    # heurística de separador
    if "." in s and "," in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s and "." not in s:
        s = s.replace(",", ".")
    # se sobrar múltiplos pontos, remove todos menos último
    if s.count(".") > 1:
        parts = s.split(".")
        s = "".join(parts[:-1]) + "." + parts[-1]
    try:
        return float(s)
    except Exception:
        return float("nan")


def parse_money_series(serie: pd.Series) -> pd.Series:
    if serie is None:
        return pd.Series(dtype="float64")
    return serie.astype(str).map(parse_money_value).astype("float64")


def parse_int_series(serie: pd.Series) -> pd.Series:
    def _to_int(x):
        try:
            if pd.isna(x):
                return pd.NA
        except Exception:
            pass
        s = re.sub(r"[^\d\-]", "", str(x))
        if s in ("", "-", "nan"):
            return pd.NA
        try:
            return int(float(s))
        except Exception:
            return pd.NA
    return serie.map(_to_int).astype("Int64")


def formatar_reais_sem_centavos(v) -> str:
    try:
        v = float(v)
    except Exception:
        return "R$ 0"
    # separador de milhar ponto, sem centavos
    return f"R$ {int(round(v)):,.0f}".replace(",", ".")


def formatar_reais_com_centavos(v) -> str:
    try:
        v = float(v)
    except Exception:
        return "R$ 0,00"
    s = f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {s}"

# ------------------------
# Leitura da planilha (cacheada)
# ------------------------

@st.cache_data(ttl=300)
def carregar_xlsx_from_url(url: str) -> pd.ExcelFile:
    """Baixa e retorna um pd.ExcelFile. Cache simples para reduzir requests."""
    r = requests.get(url, timeout=25)
    r.raise_for_status()
    return pd.ExcelFile(BytesIO(r.content))

# ------------------------
# Normalização das abas
# ------------------------

def detectar_linha_cabecalho(df_raw: pd.DataFrame, keywords: List[str]) -> Optional[int]:
    """Tenta encontrar a linha onde surgem as palavras-chave do cabeçalho."""
    max_scan = min(len(df_raw), 12)
    for i in range(max_scan):
        linha = " ".join(df_raw.iloc[i].astype(str).str.upper().tolist())
        if any(kw.upper() in linha for kw in keywords):
            return i
    return None


def limpar_aba_raw(df_raw: pd.DataFrame, nome: str) -> Optional[pd.DataFrame]:
    """Detecta cabeçalho e retorna df com colunas limpas ou None se falhar."""
    busca = {
        "ESTOQUE": ["PRODUTO", "EM ESTOQUE"],
        "VENDAS": ["DATA", "PRODUTO"],
        "COMPRAS": ["DATA", "CUSTO", "FORNEC"],
    }.get(nome, ["PRODUTO"])
    linha = detectar_linha_cabecalho(df_raw, busca)
    if linha is None:
        return None
    df_tmp = df_raw.copy()
    df_tmp.columns = df_tmp.iloc[linha]
    df = df_tmp.iloc[linha + 1 :].copy()
    df.columns = [str(c).strip() for c in df.columns]
    df = df.drop(columns=[c for c in df.columns if str(c).lower() in ("nan", "none", "")], errors="ignore")
    df = df.loc[:, ~df.isna().all()]
    return df.reset_index(drop=True)

# ------------------------
# Funções de negócio
# ------------------------

def compute_top5_global(dfs: Dict[str, pd.DataFrame]) -> List[str]:
    vendas = dfs.get("VENDAS", pd.DataFrame()).copy()
    if vendas.empty or "PRODUTO" not in vendas.columns:
        return []
    if "QTD" not in vendas.columns:
        for c in vendas.columns:
            if c.upper() in ("QTD", "QUANTIDADE", "QTY"):
                vendas["QTD"] = vendas[c]
                break
    vendas["QTD"] = vendas.get("QTD", 0).fillna(0).astype(int)
    top = vendas.groupby("PRODUTO")["QTD"].sum().sort_values(ascending=False).head(5)
    return list(top.index)


def compute_encalhados_global(dfs: Dict[str, pd.DataFrame], limit: int = 10) -> Tuple[List[str], pd.DataFrame]:
    estoque = dfs.get("ESTOQUE", pd.DataFrame()).copy()
    vendas = dfs.get("VENDAS", pd.DataFrame()).copy()
    compras = dfs.get("COMPRAS", pd.DataFrame()).copy()

    if estoque.empty:
        return [], pd.DataFrame()

    if not vendas.empty and "DATA" in vendas.columns:
        vendas["DATA"] = pd.to_datetime(vendas["DATA"], errors="coerce")
    if not compras.empty and "DATA" in compras.columns:
        compras["DATA"] = pd.to_datetime(compras["DATA"], errors="coerce")

    last_sale = vendas.groupby("PRODUTO")["DATA"].max().reset_index().rename(columns={"DATA": "ULT_VENDA"}) if not vendas.empty else pd.DataFrame(columns=["PRODUTO", "ULT_VENDA"])
    last_buy = compras.groupby("PRODUTO")["DATA"].max().reset_index().rename(columns={"DATA": "ULT_COMPRA"}) if not compras.empty else pd.DataFrame(columns=["PRODUTO", "ULT_COMPRA"])

    enc = estoque.merge(last_sale, how="left", on="PRODUTO").merge(last_buy, how="left", on="PRODUTO")
    estoque_col = next((c for c in enc.columns if str(c).upper() in ("EM ESTOQUE", "ESTOQUE", "QTD", "QUANTIDADE")), None)
    if estoque_col is None:
        return [], pd.DataFrame()
    enc = enc[enc[estoque_col] > 0].copy()

    today = pd.Timestamp.now()

    def dias_parado_row(row):
        if pd.notna(row.get("ULT_VENDA")):
            return (today - row["ULT_VENDA"]).days
        if pd.notna(row.get("ULT_COMPRA")):
            return (today - row["ULT_COMPRA"]).days
        return 9999

    enc["DIAS_PARADO"] = enc.apply(dias_parado_row, axis=1)
    enc_sorted = enc.sort_values("DIAS_PARADO", ascending=False).head(limit)
    return enc_sorted["PRODUTO"].tolist(), enc_sorted

# ------------------------
# Visual + CSS (limpo)
# ------------------------
GLOBAL_CSS = """
<style>
:root{ --bg:#0b0b0b; --accent:#8b5cf6; --muted:#bdbdbd; --card-bg:#141414; }
body, .stApp { background: var(--bg) !important; color:#f0f0f0 !important; font-family: Inter, system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial; }
.topbar { display:flex; align-items:center; gap:12px; margin-bottom:8px; }
.logo-wrap { width:44px; height:44px; display:flex; align-items:center; justify-content:center; border-radius:10px; background: linear-gradient(135deg,var(--accent),#a78bfa); }
.title { font-size:20px; font-weight:800; color:#a78bfa; margin:0; line-height:1; }
.subtitle { margin:0; font-size:12px; color:var(--muted); margin-top:2px; }
.kpi-row { display:flex; gap:10px; align-items:center; margin-bottom:20px; flex-wrap:wrap; }
.kpi { background: var(--card-bg); border-radius: 14px; padding: 12px 16px; border-left: 6px solid var(--accent); min-width: 170px; color: #f0f0f0; }
.stDataFrame thead th { background: linear-gradient(90deg, rgba(139,92,246,0.12), rgba(167,139,250,0.04)) !important; color: #f0f0f0 !important; font-weight:700 !important; }
.avatar{ width:56px;height:56px;border-radius:12px; background:linear-gradient(120deg,#a78bfa,#ec4899,#06b6d4); display:flex;align-items:center;justify-content:center; color:white;font-weight:900;font-size:18px; }
.badge{padding:4px 8px;border-radius:8px;font-size:12px;display:inline-block;}
.low{background:rgba(255,0,0,0.18); color:#ffb4b4;}
.hot{background:rgba(150,0,255,0.14); color:#e0b0ff;}
.zero{background:rgba(255,255,255,0.04); color:#fff;}
.card-ecom{ background: linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01)); border-radius:12px; padding:12px; display:flex; gap:12px; align-items:center; }
.card-title{font-weight:900;font-size:15px;margin-bottom:4px;color:#fff;}
.card-meta{font-size:12px;color:#cfcfe0;margin-bottom:6px;}
</style>
"""
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

st.markdown(
    """
    <div class='topbar'>
      <div class='logo-wrap'>
        <svg viewBox='0 0 24 24' fill='none' width='28' height='28'><rect x='3' y='3' width='18' height='18' rx='4' fill='white' fill-opacity='0.06'/><path d='M7 9h10l-1 6H8L7 9z' stroke='white' stroke-opacity='0.95' stroke-width='1.2'/><path d='M9 6l2-2 2 2' stroke='white' stroke-opacity='0.95' stroke-width='1.2'/></svg>
      </div>
      <div>
        <div class='title'>Loja Importados — Dashboard</div>
        <div class='subtitle'>Visão rápida de vendas, compras e estoque</div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ------------------------
# Carregar e normalizar planilha
# ------------------------
try:
    xls = carregar_xlsx_from_url(URL_PLANILHA)
except Exception as e:
    st.error("Erro ao carregar a planilha — verifique a URL e a conexão.")
    st.exception(e)
    st.stop()

abas_all = xls.sheet_names
raw_dfs: Dict[str, pd.DataFrame] = {}
for aba in ["ESTOQUE", "VENDAS", "COMPRAS"]:
    if aba in abas_all:
        raw = pd.read_excel(URL_PLANILHA, sheet_name=aba, header=None)
        cleaned = limpar_aba_raw(raw, aba)
        if cleaned is not None:
            raw_dfs[aba] = cleaned

# Normalizações pontuais (driven by heurísticas)

dfs: Dict[str, pd.DataFrame] = {}

# ESTOQUE
if "ESTOQUE" in raw_dfs:
    df_e = raw_dfs["ESTOQUE"].copy()
    # localizar colunas alternativas
    # custo unitário
    for alt in ["Media C. UNITARIO", "MEDIA C. UNITARIO", "MEDIA CUSTO UNITARIO", "MEDIA C. UNIT"]:
        if alt in df_e.columns:
            df_e["Media C. UNITARIO"] = parse_money_series(df_e[alt]).fillna(0)
            break
    # valor venda sugerido
    for alt in ["Valor Venda Sugerido", "VALOR VENDA SUGERIDO", "VALOR VENDA", "VALOR_VENDA"]:
        if alt in df_e.columns:
            df_e["Valor Venda Sugerido"] = parse_money_series(df_e[alt]).fillna(0)
            break
    # quantidade em estoque
    for alt in ["EM ESTOQUE", "ESTOQUE", "QTD", "QUANTIDADE"]:
        if alt in df_e.columns:
            df_e["EM ESTOQUE"] = parse_int_series(df_e[alt]).fillna(0).astype(int)
            break
    # produto (fallback)
    if "PRODUTO" not in df_e.columns:
        for c in df_e.columns:
            if df_e[c].dtype == object:
                df_e = df_e.rename(columns={c: "PRODUTO"})
                break
    dfs["ESTOQUE"] = df_e

# VENDAS
if "VENDAS" in raw_dfs:
    df_v = raw_dfs["VENDAS"].copy()
    df_v.columns = [str(c).strip() for c in df_v.columns]
    money_map = {
        "VALOR VENDA": ["VALOR VENDA", "VALOR_VENDA", "VALORVENDA"],
        "VALOR TOTAL": ["VALOR TOTAL", "VALOR_TOTAL", "VALORTOTAL"],
        "MEDIA CUSTO UNITARIO": ["MEDIA C. UNITARIO", "MEDIA CUSTO UNITARIO", "MEDIA CUSTO"],
        "LUCRO UNITARIO": ["LUCRO UNITARIO", "LUCRO_UNITARIO"],
    }
    for target, vars_ in money_map.items():
        for v in vars_:
            if v in df_v.columns:
                df_v[target] = parse_money_series(df_v[v])
                break
    # detectar QTD
    qtd_cols = [c for c in df_v.columns if c.upper() in ("QTD", "QUANTIDADE", "QTY")]
    if qtd_cols:
        df_v["QTD"] = parse_int_series(df_v[qtd_cols[0]]).fillna(0).astype(int)
    # datas
    if "DATA" in df_v.columns:
        df_v["DATA"] = pd.to_datetime(df_v["DATA"], errors="coerce")
        df_v["MES_ANO"] = df_v["DATA"].dt.strftime("%Y-%m")
    else:
        df_v["MES_ANO"] = pd.NA
    # recalcula VALOR TOTAL se faltando
    if "VALOR TOTAL" not in df_v.columns and "VALOR VENDA" in df_v.columns:
        df_v["VALOR TOTAL"] = df_v["VALOR VENDA"].fillna(0) * df_v.get("QTD", 0).fillna(0)
    # lucro unitario
    if "LUCRO UNITARIO" not in df_v.columns and ("VALOR VENDA" in df_v.columns and "MEDIA CUSTO UNITARIO" in df_v.columns):
        df_v["LUCRO UNITARIO"] = df_v["VALOR VENDA"].fillna(0) - df_v["MEDIA CUSTO UNITARIO"].fillna(0)
    if "DATA" in df_v.columns:
        df_v = df_v.sort_values("DATA", ascending=False).reset_index(drop=True)
    dfs["VENDAS"] = df_v

# COMPRAS
if "COMPRAS" in raw_dfs:
    df_c = raw_dfs["COMPRAS"].copy()
    qcols = [c for c in df_c.columns if "QUANT" in c.upper()]
    if qcols:
        df_c["QUANTIDADE"] = parse_int_series(df_c[qcols[0]]).fillna(0).astype(int)
    ccols = [c for c in df_c.columns if any(k in c.upper() for k in ("CUSTO", "UNIT", "VALOR"))]
    if ccols:
        df_c["CUSTO UNITÁRIO"] = parse_money_series(df_c[ccols[0]]).fillna(0)
    df_c["CUSTO TOTAL (RECALC)"] = df_c.get("QUANTIDADE", 0) * df_c.get("CUSTO UNITÁRIO", 0)
    if "DATA" in df_c.columns:
        df_c["DATA"] = pd.to_datetime(df_c["DATA"], errors="coerce")
        df_c["MES_ANO"] = df_c["DATA"].dt.strftime("%Y-%m")
    dfs["COMPRAS"] = df_c

# ------------------------
# Calculos globais (top5, encalhados e indicadores)
# ------------------------
_top5_list_global = compute_top5_global(dfs)
_enc_list_global, _enc_df_global = compute_encalhados_global(dfs, limit=10)

estoque_df = dfs.get("ESTOQUE", pd.DataFrame()).copy()
if not estoque_df.empty:
    estoque_df["Media C. UNITARIO"] = estoque_df.get("Media C. UNITARIO", 0).fillna(0).astype(float)
    estoque_df["Valor Venda Sugerido"] = estoque_df.get("Valor Venda Sugerido", 0).fillna(0).astype(float)
    estoque_df["EM ESTOQUE"] = estoque_df.get("EM ESTOQUE", 0).fillna(0).astype(int)
    valor_custo_estoque = (estoque_df["Media C. UNITARIO"] * estoque_df["EM ESTOQUE"]).sum()
    valor_venda_estoque = (estoque_df["Valor Venda Sugerido"] * estoque_df["EM ESTOQUE"]).sum()
    quantidade_total_itens = int(estoque_df["EM ESTOQUE"].sum())
else:
    valor_custo_estoque = 0
    valor_venda_estoque = 0
    quantidade_total_itens = 0

# filtro mês
meses = ["Todos"]
if "VENDAS" in dfs:
    meses += sorted(dfs["VENDAS"]["MES_ANO"].dropna().unique().tolist(), reverse=True)
mes_atual = datetime.now().strftime("%Y-%m")
index_padrao = meses.index(mes_atual) if mes_atual in meses else 0
col_filter, col_kpis = st.columns([1, 3])
with col_filter:
    mes_selecionado = st.selectbox("Filtrar por mês (YYYY-MM):", meses, index=index_padrao)

# helper: filtrar por MES_ANO

def filtrar_mes_df(df: pd.DataFrame, mes: str) -> pd.DataFrame:
    if df is None or df.empty:
        return df
    if mes == "Todos":
        return df
    return df[df["MES_ANO"] == mes].copy() if "MES_ANO" in df.columns else df

vendas_filtradas = filtrar_mes_df(dfs.get("VENDAS", pd.DataFrame()), mes_selecionado)
if not vendas_filtradas.empty and "DATA" in vendas_filtradas.columns:
    vendas_filtradas = vendas_filtradas.sort_values("DATA", ascending=False).reset_index(drop=True)
compras_filtradas = filtrar_mes_df(dfs.get("COMPRAS", pd.DataFrame()), mes_selecionado)

# KPIs
total_vendido = vendas_filtradas.get("VALOR TOTAL", pd.Series()).fillna(0).sum()
total_lucro = (vendas_filtradas.get("LUCRO UNITARIO", 0).fillna(0) * vendas_filtradas.get("QTD", 0).fillna(0)).sum()
total_compras = compras_filtradas.get("CUSTO TOTAL (RECALC)", pd.Series()).fillna(0).sum()

with col_kpis:
    st.markdown(f"""
    <div class="kpi-row">
      <div class="kpi"><h3>💵 Faturamento</h3><div class="value">{formatar_reais_sem_centavos(total_vendido)}</div></div>
      <div class="kpi" style="border-left-color:#34d399;"><h3>🧾 Lucro Liq.</h3><div class="value">{formatar_reais_sem_centavos(total_lucro)}</div></div>
      <div class="kpi" style="border-left-color:#f59e0b;"><h3>💸 Compras</h3><div class="value">{formatar_reais_sem_centavos(total_compras)}</div></div>
      <div class="kpi" style="border-left-color:#8b5cf6;"><h3>📦 Custo Est.</h3><div class="value">{formatar_reais_sem_centavos(valor_custo_estoque)}</div></div>
      <div class="kpi" style="border-left-color:#a78bfa;"><h3>🏷️ Venda Est.</h3><div class="value">{formatar_reais_sem_centavos(valor_venda_estoque)}</div></div>
      <div class="kpi" style="border-left-color:#6ee7b7;"><h3>🔢 Itens</h3><div class="value">{quantidade_total_itens}</div></div>
    </div>
    """, unsafe_allow_html=True)

# Tabs
tabs = st.tabs(["🛒 VENDAS", "📦 ESTOQUE", "🧾 COMPRAS", "🔍 PESQUISAR"])

# ----------------------------
# VENDAS TAB
# ----------------------------
with tabs[0]:
    st.subheader("Vendas — período selecionado")

    if vendas_filtradas.empty:
        st.info("Sem dados de vendas.")
    else:
        df_sem = vendas_filtradas.copy()
        df_sem["DATA"] = pd.to_datetime(df_sem["DATA"], errors="coerce")
        df_sem = df_sem.sort_values("DATA", ascending=False).reset_index(drop=True)
        df_sem["SEMANA"] = df_sem["DATA"].dt.isocalendar().week
        df_sem["ANO"] = df_sem["DATA"].dt.year

        # Faturamento semanal
        def semana_intervalo(row):
            try:
                inicio = datetime.fromisocalendar(int(row["ANO"]), int(row["SEMANA"]), 1)
                fim = inicio + timedelta(days=6)
                return f"{inicio.strftime('%d/%m')} → {fim.strftime('%d/%m')}"
            except Exception:
                return "N/A"

        df_sem_group = df_sem.groupby(["ANO", "SEMANA"], dropna=False)["VALOR TOTAL"].sum().reset_index()
        if not df_sem_group.empty:
            df_sem_group["INTERVALO"] = df_sem_group.apply(semana_intervalo, axis=1)
            df_sem_group["LABEL"] = df_sem_group["VALOR TOTAL"].apply(formatar_reais_com_centavos)
            st.markdown("### 📊 Faturamento Semanal do Mês")
            fig_sem = px.bar(df_sem_group, x="INTERVALO", y="VALOR TOTAL", text="LABEL", color_discrete_sequence=["#8b5cf6"], height=380)
            fig_sem.update_traces(textposition="inside", textfont_size=12)
            st.plotly_chart(fig_sem, use_container_width=True, config=dict(displayModeBar=False))

        # Tabela de vendas
        st.markdown("### 📄 Tabela de Vendas (mais recentes primeiro)")

        def preparar_tabela_vendas(df: pd.DataFrame, estoque_df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
            d = df.copy()
            if "DATA" in d.columns:
                d["DATA"] = d["DATA"].dt.strftime("%d/%m/%Y")
            for c in ["VALOR VENDA", "VALOR TOTAL", "MEDIA CUSTO UNITARIO", "LUCRO UNITARIO", "QTD"]:
                if c not in d.columns:
                    d[c] = 0
            # garantir tipos
            for col in ["VALOR VENDA", "VALOR TOTAL", "MEDIA CUSTO UNITARIO", "LUCRO UNITARIO"]:
                try:
                    d[col] = d[col].astype(float)
                except Exception:
                    pass
            d["VALOR VENDA"] = d["VALOR VENDA"].map(formatar_reais_com_centavos)
            d["VALOR TOTAL"] = d["VALOR TOTAL"].map(formatar_reais_com_centavos)
            d["MEDIA CUSTO UNITARIO"] = d["MEDIA CUSTO UNITARIO"].map(formatar_reais_com_centavos)
            d["LUCRO UNITARIO"] = d["LUCRO UNITARIO"].map(formatar_reais_com_centavos)

            d = d.loc[:, ~d.columns.astype(str).str.contains("^Unnamed|MES_ANO")]

            try:
                d["VALOR VENDA_RAW"] = parse_money_series(df["VALOR VENDA"]).fillna(0)
            except Exception:
                d["VALOR VENDA_RAW"] = pd.to_numeric(df.get("VALOR VENDA", 0), errors="coerce").fillna(0)
            try:
                d["CUSTO_RAW"] = parse_money_series(df.get("MEDIA CUSTO UNITARIO", pd.Series())).fillna(0)
            except Exception:
                d["CUSTO_RAW"] = pd.to_numeric(df.get("MEDIA CUSTO UNITARIO", 0), errors="coerce").fillna(0)
            try:
                d["LUCRO TOTAL"] = (d["VALOR VENDA_RAW"] - d["CUSTO_RAW"]) * d.get("QTD", 0)
            except Exception:
                d["LUCRO TOTAL"] = 0
            d["LUCRO TOTAL"] = d["LUCRO TOTAL"].map(lambda x: formatar_reais_com_centavos(x))

            if estoque_df is not None and not estoque_df.empty and "PRODUTO" in estoque_df.columns:
                try:
                    estoque_for_merge = estoque_df[["PRODUTO", "EM ESTOQUE"]].copy().rename(columns={"EM ESTOQUE": "Estoque"})
                    d = d.merge(estoque_for_merge, on="PRODUTO", how="left")
                    d["Estoque"] = d["Estoque"].fillna(0).astype(int)
                except Exception:
                    pass
            return d

        tabela_vendas_exib = preparar_tabela_vendas(df_sem, estoque_df=estoque_df)

        # sufixo de estoque no nome do produto quando disponível
        try:
            if not tabela_vendas_exib.empty and "PRODUTO" in tabela_vendas_exib.columns and "Estoque" in tabela_vendas_exib.columns:
                def _nome_prod(row):
                    try:
                        est = int(row.get("Estoque", 0))
                    except Exception:
                        est = 0
                    suf = f" (📦 Resta {est} produto{'s' if est!=1 else ''})"
                    return f"{row.get('PRODUTO','')}{suf}"
                tabela_vendas_exib["PRODUTO"] = tabela_vendas_exib.apply(_nome_prod, axis=1)
        except Exception:
            pass

        # limitar colunas
        cols = tabela_vendas_exib.columns.tolist()
        if "OBS" in cols:
            limite = cols.index("OBS") + 1
            tabela_vendas_exib = tabela_vendas_exib[cols[:limite]]

        st.dataframe(tabela_vendas_exib, use_container_width=True)

        # Top 5
        try:
            vendas_all = dfs.get("VENDAS", pd.DataFrame()).copy()
            if not vendas_all.empty and "PRODUTO" in vendas_all.columns:
                top5 = vendas_all.groupby("PRODUTO")["QTD"].sum().reset_index().sort_values("QTD", ascending=False).head(5)
                if not top5.empty:
                    est = dfs.get("ESTOQUE", pd.DataFrame()).copy()
                    if not est.empty and "PRODUTO" in est.columns:
                        top5 = top5.merge(est[["PRODUTO", "EM ESTOQUE"]].rename(columns={"EM ESTOQUE": "Estoque"}), on="PRODUTO", how="left")
                    else:
                        top5["Estoque"] = 0
                    top5["QTD"] = top5["QTD"].fillna(0).astype(int)
                    top5_display = top5.copy()
                    top5_display["Produto"] = top5_display.apply(lambda r: f"{r['PRODUTO']} (📦 Resta {int(r.get('Estoque',0))} produtos)", axis=1)
                    top5_display = top5_display.rename(columns={"QTD": "Unidades"})
                    st.markdown("### 🔥 Top 5 — Produtos bombando (por unidades vendidas)")
                    st.table(top5_display[["Produto", "Unidades"]])
        except Exception:
            pass

        # Produtos encalhados
        try:
            estoque_all = dfs.get("ESTOQUE", pd.DataFrame()).copy()
            vendas_all = dfs.get("VENDAS", pd.DataFrame()).copy()
            compras_all = dfs.get("COMPRAS", pd.DataFrame()).copy()
            if not compras_all.empty:
                compras_all["DATA"] = pd.to_datetime(compras_all["DATA"], errors="coerce")
            if not vendas_all.empty:
                vendas_all["DATA"] = pd.to_datetime(vendas_all["DATA"], errors="coerce")
            if not estoque_all.empty:
                last_sale = vendas_all.groupby("PRODUTO")["DATA"].max().reset_index().rename(columns={"DATA": "ULT_VENDA"}) if not vendas_all.empty else pd.DataFrame(columns=["PRODUTO", "ULT_VENDA"])
                last_buy = compras_all.groupby("PRODUTO")["DATA"].max().reset_index().rename(columns={"DATA": "ULT_COMPRA"}) if not compras_all.empty else pd.DataFrame(columns=["PRODUTO", "ULT_COMPRA"])
                enc = estoque_all.merge(last_sale, how="left", on="PRODUTO").merge(last_buy, how="left", on="PRODUTO")
                estoque_col = next((c for c in enc.columns if str(c).upper() in ("EM ESTOQUE", "ESTOQUE", "QTD", "QUANTIDADE")), None)
                enc = enc[enc[estoque_col] > 0].copy() if estoque_col else enc
                today = pd.Timestamp.now()
                def calc_days(row):
                    if pd.notna(row.get("ULT_VENDA")):
                        return (today - row["ULT_VENDA"]).days
                    if pd.notna(row.get("ULT_COMPRA")):
                        return (today - row["ULT_COMPRA"]).days
                    return 9999
                enc["DIAS_PARADO"] = enc.apply(calc_days, axis=1)
                enc = enc.sort_values("DIAS_PARADO", ascending=False).head(10)
                if not enc.empty:
                    enc_display = enc[["PRODUTO", estoque_col, "ULT_VENDA", "ULT_COMPRA", "DIAS_PARADO"]].copy()
                    enc_display["ULT_VENDA"] = enc_display["ULT_VENDA"].dt.strftime("%d/%m/%Y").fillna("—")
                    enc_display["ULT_COMPRA"] = enc_display["ULT_COMPRA"].dt.strftime("%d/%m/%Y").fillna("—")
                    st.markdown("### ❄️ Produtos encalhados (global)")
                    st.table(enc_display.rename(columns={"PRODUTO": "Produto", estoque_col: "Estoque", "ULT_VENDA": "Última venda", "ULT_COMPRA": "Última compra", "DIAS_PARADO": "Dias parado"}))
        except Exception:
            st.write("Erro ao calcular encalhados")

# ----------------------------
# ESTOQUE TAB
# ----------------------------
with tabs[1]:
    if estoque_df.empty:
        st.info("Sem dados de estoque.")
    else:
        estoque_display = estoque_df.copy()
        estoque_display["VALOR_CUSTO_TOTAL_RAW"] = (estoque_display["Media C. UNITARIO"] * estoque_display["EM ESTOQUE"]).fillna(0)
        estoque_display["VALOR_VENDA_TOTAL_RAW"] = (estoque_display["Valor Venda Sugerido"] * estoque_display["EM ESTOQUE"]).fillna(0)

        st.markdown("### 🥧 Distribuição de estoque — fatias com quantidade")
        top_for_pie = estoque_display.sort_values("EM ESTOQUE", ascending=False).head(10)
        if not top_for_pie.empty:
            fig_pie = px.pie(top_for_pie, names="PRODUTO", values="EM ESTOQUE", hole=0.40)
            fig_pie.update_traces(textinfo="label+value", textposition="inside")
            st.plotly_chart(fig_pie, use_container_width=True, config=dict(displayModeBar=False))

        estoque_clas = estoque_display.copy()
        estoque_clas["CUSTO_UNITARIO_FMT"] = estoque_clas["Media C. UNITARIO"].map(formatar_reais_com_centavos)
        estoque_clas["VENDA_SUGERIDA_FMT"] = estoque_clas["Valor Venda Sugerido"].map(formatar_reais_com_centavos)
        estoque_clas["VALOR_TOTAL_CUSTO_FMT"] = estoque_clas["VALOR_CUSTO_TOTAL_RAW"].map(formatar_reais_sem_centavos)
        estoque_clas["VALOR_TOTAL_VENDA_FMT"] = estoque_clas["VALOR_VENDA_TOTAL_RAW"].map(formatar_reais_sem_centavos)

        display_df = estoque_clas[["PRODUTO", "EM ESTOQUE", "CUSTO_UNITARIO_FMT", "VENDA_SUGERIDA_FMT", "VALOR_TOTAL_CUSTO_FMT", "VALOR_TOTAL_VENDA_FMT"]].rename(columns={"CUSTO_UNITARIO_FMT": "CUSTO UNITÁRIO", "VENDA_SUGERIDA_FMT": "VENDA SUGERIDA", "VALOR_TOTAL_CUSTO_FMT": "VALOR TOTAL CUSTO", "VALOR_TOTAL_VENDA_FMT": "VALOR TOTAL VENDA"})
        display_df = display_df.sort_values("EM ESTOQUE", ascending=False).reset_index(drop=True)
        st.markdown("### 📋 Estoque — visão detalhada")
        st.dataframe(display_df, use_container_width=True)

# ----------------------------
# COMPRAS TAB
# ----------------------------
with tabs[2]:
    st.subheader("Compras — panorama do mês selecionado")
    df_c = dfs.get("COMPRAS", pd.DataFrame()).copy()
    if df_c.empty:
        st.info("Sem dados de compras na planilha.")
    else:
        # detectar colunas úteis
        fornecedor_col = next((c for c in df_c.columns if any(k in str(c).upper() for k in ("FORNEC", "SUPPLIER", "VENDOR"))), None)
        obs_col = next((c for c in df_c.columns if any(k in str(c).upper() for k in ("OBS", "DESCR", "NOTA", "FINAL", "MOTIVO"))), None)

        if "QUANTIDADE" in df_c.columns:
            df_c["QUANTIDADE"] = parse_int_series(df_c["QUANTIDADE"]).fillna(0).astype(int)
        if "CUSTO UNITÁRIO" in df_c.columns:
            df_c["CUSTO UNITÁRIO"] = parse_money_series(df_c["CUSTO UNITÁRIO"]).fillna(0)
        if "CUSTO TOTAL (RECALC)" not in df_c.columns:
            df_c["CUSTO TOTAL (RECALC)"] = df_c.get("QUANTIDADE", 0) * df_c.get("CUSTO UNITÁRIO", 0)

        compras_mes = filtrar_mes_df(df_c, mes_selecionado)
        compras_mes = compras_mes.sort_values("DATA", ascending=False).reset_index(drop=True)

        total_comp_mes = compras_mes["CUSTO TOTAL (RECALC)"].fillna(0).sum()
        n_comp_mes = len(compras_mes)

        marketing_keywords = ["ANUN", "DIVULG", "ADS", "FACEBOOK", "INSTAGRAM", "GOOGLE", "META", "PROMO", "CAMPANHA", "MARKETING", "INFLUENCIADOR"]

        def is_marketing_row(row) -> bool:
            text = ""
            if obs_col and pd.notna(row.get(obs_col, "")):
                text += " " + str(row.get(obs_col, ""))
            for c in compras_mes.columns:
                if any(k in str(c).upper() for k in ("DESCR", "OBS", "NOTA", "FINAL", "MOTIVO")) and pd.notna(row.get(c, "")):
                    text += " " + str(row.get(c, ""))
            text = text.upper()
            return any(kw in text for kw in marketing_keywords)

        compras_mes["_MARKETING"] = compras_mes.apply(is_marketing_row, axis=1)

        marketing_total = compras_mes.loc[compras_mes["_MARKETING"], "CUSTO TOTAL (RECALC)"].fillna(0).sum()
        marketing_count = compras_mes["_MARKETING"].sum()
        marketing_pct = (marketing_total / total_comp_mes * 100) if total_comp_mes else 0

        # gráfico barras
        st.markdown("### 📈 Visão rápida das compras (gráfico por produto/fornecedor)")
        group_by_for = fornecedor_col if fornecedor_col is not None else "PRODUTO"
        group_col = group_by_for if group_by_for in compras_mes.columns else "PRODUTO"
        pivot = compras_mes.groupby(group_col)["CUSTO TOTAL (RECALC)"].sum().reset_index().sort_values("CUSTO TOTAL (RECALC)", ascending=False)
        pivot["CUSTO_FMT"] = pivot["CUSTO TOTAL (RECALC)"].map(formatar_reais_sem_centavos)
        if not pivot.empty:
            fig_bar = px.bar(pivot.head(12), x="CUSTO TOTAL (RECALC)", y=group_col, orientation="h", text="CUSTO_FMT", height=420)
            fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_bar, use_container_width=True, config=dict(displayModeBar=False))

        st.markdown("### 🔹 Distribuição (treemap)")
        category_col = next((c for c in df_c.columns if any(k in str(c).upper() for k in ("CATEG", "FINAL", "TIPO", "DEST", "USO"))), None)
        treemap_col = category_col if category_col in compras_mes.columns else "PRODUTO"
        try:
            tm = compras_mes.groupby(treemap_col)["CUSTO TOTAL (RECALC)"].sum().reset_index().sort_values("CUSTO TOTAL (RECALC)", ascending=False)
            if not tm.empty:
                fig_tm = px.treemap(tm, path=[treemap_col], values="CUSTO TOTAL (RECALC)", height=420)
                st.plotly_chart(fig_tm, use_container_width=True, config=dict(displayModeBar=False))
        except Exception:
            st.write("Sem dados suficientes para treemap.")

        st.markdown("### 🧾 KPIs de Compras")
        k1, k2, k3, k4 = st.columns([1, 1, 1, 1])
        k1.metric("Total compras (mês)", formatar_reais_sem_centavos(total_comp_mes))
        k2.metric("Nº de compras", f"{n_comp_mes}")
        k3.metric("Gasto marketing", formatar_reais_sem_centavos(marketing_total))
        k4.metric("Pct marketing", f"{marketing_pct:.1f}%")

        st.markdown("### 📄 Últimas compras (tabela)")
        display_cols = ["DATA", "PRODUTO", "QUANTIDADE", "CUSTO UNITÁRIO", "CUSTO TOTAL (RECALC)"]
        display_cols = [c for c in display_cols if c in compras_mes.columns]
        tbl = compras_mes.copy()
        for c in ["CUSTO UNITÁRIO", "CUSTO TOTAL (RECALC)"]:
            if c in tbl.columns:
                tbl[c + "_FMT"] = tbl[c].map(formatar_reais_com_centavos)
        if "DATA" in tbl.columns:
            tbl["DATA"] = pd.to_datetime(tbl["DATA"], errors="coerce").dt.strftime("%d/%m/%Y").fillna("—")
        show_cols = []
        if "DATA" in tbl.columns:
            show_cols.append("DATA")
        if "PRODUTO" in tbl.columns:
            show_cols.append("PRODUTO")
        if fornecedor_col:
            show_cols.insert(1, fornecedor_col)
        if "QUANTIDADE" in tbl.columns:
            show_cols.append("QUANTIDADE")
        if "CUSTO UNITÁRIO_FMT" in tbl.columns:
            show_cols.append("CUSTO UNITÁRIO_FMT")
        if "CUSTO TOTAL (RECALC)_FMT" in tbl.columns:
            show_cols.append("CUSTO TOTAL (RECALC)_FMT")
        if obs_col:
            show_cols.append(obs_col)
        if show_cols:
            st.dataframe(tbl[show_cols + ["_MARKETING"]].rename(columns={c: c.replace("_FMT", "") for c in show_cols}), use_container_width=True)
        else:
            st.dataframe(tbl.head(50), use_container_width=True)

        csv_bytes = compras_mes.to_csv(index=False).encode('utf-8')
        st.download_button("Baixar CSV das compras filtradas", data=csv_bytes, file_name=f"compras_{mes_selecionado}.csv", mime="text/csv")

        st.markdown("### 💡 Insights rápidos (meta-resumo)")
        insights = []
        if marketing_total > 0:
            insights.append(f"Você gastou {formatar_reais_sem_centavos(marketing_total)} em itens relacionados a marketing neste mês — {marketing_count} compras identificadas.")
        else:
            insights.append("Nenhuma compra claramente marcada como 'marketing' encontrada — verifique colunas de descrição/observação para identificar gastos em anúncios/divulgação.")
        if not pivot.empty:
            top_conc = pivot["CUSTO TOTAL (RECALC)"].iloc[0]
            if total_comp_mes > 0 and top_conc / total_comp_mes > 0.4:
                insights.append("Alerta: >40% dos custos do mês concentrados em 1 fornecedor/produto — risco de dependência.")
        insights.append("Sugestões: agrupe compras de anúncios em uma categoria 'Marketing', registre a finalidade em 'OBS' e monitore ROI por campanha.")
        for ins in insights:
            st.write("- " + ins)

# ----------------------------
# PESQUISAR TAB
# ----------------------------
with tabs[3]:
    col_a, col_b = st.columns([3, 2])
    with col_a:
        termo = st.text_input("🔎 Buscar produto", value="", placeholder="Digite o nome do produto...")
    with col_b:
        cols = st.columns([1, 1, 1, 1])
        with cols[0]:
            itens_pagina = st.selectbox("Itens/pg", [6, 9, 12, 24, 36, 48, 60, 100, 200], index=2)
        with cols[1]:
            ordenar = st.selectbox("Ordenar por", ["Nome A–Z", "Nome Z–A", "Menor preço", "Maior preço", "Mais vendidos", "Maior estoque"], index=0)
        with cols[2]:
            grid_cols = st.selectbox("Colunas", [2, 3, 4], index=1)
        with cols[3]:
            ver_tudo = st.checkbox("Ver tudo (sem paginação)", value=False)

    filtro_baixo = st.checkbox("⚠️ Baixo estoque (≤3)", value=False)
    filtro_alto = st.checkbox("📦 Alto estoque (≥20)", value=False)
    filtro_vendidos = st.checkbox("🔥 Com vendas", value=False)
    filtro_sem_venda = st.checkbox("❄️ Sem vendas", value=False)

    df = estoque_df.copy()
    vendas_df = dfs.get("VENDAS", pd.DataFrame()).copy()
    if not vendas_df.empty and "QTD" in vendas_df.columns:
        vend = vendas_df.groupby("PRODUTO")["QTD"].sum().reset_index().rename(columns={"QTD": "TOTAL_QTD"})
        df = df.merge(vend, how="left", on="PRODUTO").fillna({"TOTAL_QTD": 0})
    else:
        df["TOTAL_QTD"] = 0

    compras_df = dfs.get("COMPRAS", pd.DataFrame()).copy()
    ultima_compra = {}
    if not compras_df.empty and "DATA" in compras_df.columns and "PRODUTO" in compras_df.columns:
        compras_df = compras_df.dropna(subset=["PRODUTO"])
        compras_df["DATA"] = pd.to_datetime(compras_df["DATA"], errors="coerce")
        tmp = compras_df.groupby("PRODUTO")["DATA"].max().reset_index()
        ultima_compra = dict(zip(tmp["PRODUTO"], tmp["DATA"].dt.strftime("%d/%m/%Y")))

    if termo and termo.strip():
        df = df[df["PRODUTO"].str.contains(termo, case=False, na=False)]
    if filtro_baixo:
        df = df[df["EM ESTOQUE"] <= 3]
    if filtro_alto:
        df = df[df["EM ESTOQUE"] >= 20]
    if filtro_vendidos:
        df = df[df["TOTAL_QTD"] > 0]
    if filtro_sem_venda:
        df = df[df["TOTAL_QTD"] == 0]

    df["CUSTO_FMT"] = df.get("Media C. UNITARIO", 0).map(formatar_reais_com_centavos)
    df["VENDA_FMT"] = df.get("Valor Venda Sugerido", 0).map(formatar_reais_com_centavos)

    if ordenar == "Nome A–Z":
        df = df.sort_values("PRODUTO", ascending=True)
    elif ordenar == "Nome Z–A":
        df = df.sort_values("PRODUTO", ascending=False)
    elif ordenar == "Menor preço":
        df = df.sort_values("Valor Venda Sugerido", ascending=True)
    elif ordenar == "Maior preço":
        df = df.sort_values("Valor Venda Sugerido", ascending=False)
    elif ordenar == "Mais vendidos":
        if "TOTAL_QTD" in df.columns:
            df = df.sort_values("TOTAL_QTD", ascending=False)
    elif ordenar == "Maior estoque":
        df = df.sort_values("EM ESTOQUE", ascending=False)

    total = len(df)
    if ver_tudo:
        itens_pagina = total if total > 0 else 1
    else:
        itens_pagina = int(itens_pagina)
    total_paginas = max(1, (total + itens_pagina - 1) // itens_pagina)
    if "pagina" not in st.session_state:
        st.session_state["pagina"] = 1
    st.session_state["pagina"] = max(1, min(st.session_state["pagina"], total_paginas))
    coln1, coln2, coln3 = st.columns([1, 2, 1])
    with coln1:
        if st.button("⬅️ Voltar"):
            st.session_state["pagina"] = max(1, st.session_state["pagina"] - 1)
    with coln2:
        st.markdown(f"**Página {st.session_state['pagina']} de {total_paginas} — {total} resultados**")
    with coln3:
        if st.button("Avançar ➡️"):
            st.session_state["pagina"] = min(total_paginas, st.session_state["pagina"] + 1)

    pagina = st.session_state["pagina"]
    inicio = (pagina - 1) * itens_pagina
    fim = inicio + itens_pagina
    df_page = df.iloc[inicio:fim].reset_index(drop=True)

    css_grid = f"""
    <style>
    .card-grid-ecom{{ display:grid; grid-template-columns: repeat({grid_cols},1fr); gap:12px; }}
    @media(max-width:720px){{ .card-grid-ecom{{grid-template-columns:1fr;}} }}
    </style>
    """
    st.markdown(css_grid, unsafe_allow_html=True)
    st.markdown("<div class='card-grid-ecom'>", unsafe_allow_html=True)

    for _, r in df_page.iterrows():
        nome = r.get("PRODUTO", "")
        estoque = int(r.get("EM ESTOQUE", 0)) if pd.notna(r.get("EM ESTOQUE", 0)) else 0
        venda = r.get("VENDA_FMT", "R$ 0")
        custo = r.get("CUSTO_FMT", "R$ 0")
        vendidos = int(r.get("TOTAL_QTD", 0)) if pd.notna(r.get("TOTAL_QTD", 0)) else 0
        iniciais = "".join([p[0].upper() for p in str(nome).split()[:2] if p]) or "—"
        badges = []
        if estoque <= 3:
            badges.append(f"<span class='badge low'>⚠️ Baixo</span>")
        if vendidos >= 15:
            badges.append(f"<span class='badge hot'>🔥 Saindo</span>")
        if nome in _enc_list_global:
            badges.append("<span class='badge zero'>🐌 Encalhado</span>")
        if nome in _top5_list_global:
            badges.append("<span class='badge hot'>🥇 Campeão</span>")

        badges_html = " ".join(badges)
        ultima = ultima_compra.get(nome, "—")
        avatar_html = f"<div class='avatar'>{iniciais}</div>"
        card_html = (
            f"<div class='card-ecom'>"
            f"{avatar_html}"
            f"<div style='flex:1;'>"
            f"<div class='card-title'>{nome}</div>"
            f"<div class='card-meta'>Estoque: <b>{estoque}</b> • Vendidos: <b>{vendidos}</b></div>"
            f"<div style='margin-top:6px; line-height:1.25;'><div style='font-size:13px; font-weight:700;'>💲 Venda: <span style='color:#a78bfa;'>{venda}</span></div><div style='font-size:12px;'>💰 Custo: <span style='color:#ffb4b4;'>{custo}</span></div></div>"
            f"<div style='font-size:11px;color:#9ca3af;margin-top:4px;'>🕒 Última compra: <b>{ultima}</b></div>"
            f"<div style='margin-top:6px;'>{badges_html}</div>"
            f"</div></div>"
        )
        st.markdown(card_html, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

# FIM
print("Dashboard carregado com sucesso")
