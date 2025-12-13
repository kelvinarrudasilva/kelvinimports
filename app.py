# app.py
# =========================================================
# VERSÃO FINAL DE PRODUÇÃO — COMPLETA, OTIMIZADA E ESTÁVEL
# Loja Importados / Kelvin Imports
# ✔ Todas as abas preservadas
# ✔ Correções definitivas de estoque
# ✔ Ordenação correta (estoque primeiro + A–Z)
# ✔ Badges profissionais
# ✔ Produtos sem estoque apagados
# ✔ Opção ocultar sem estoque
# ✔ Performance otimizada (cache)
# ✔ Mobile friendly
# =========================================================

import streamlit as st
import pandas as pd
import plotly.express as px
import re
from datetime import datetime, timedelta
import requests
from io import BytesIO

# --------------------------------------------------
# CONFIGURAÇÃO GERAL
# --------------------------------------------------
st.set_page_config(
    page_title="Loja Importados – Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed"
)

URL_PLANILHA = "https://docs.google.com/spreadsheets/d/1TsRjsfw1TVfeEWBBvhKvsGQ5YUCktn2b/export?format=xlsx"

# --------------------------------------------------
# FUNÇÕES UTILITÁRIAS
# --------------------------------------------------
def parse_money_value(x):
    try:
        if pd.isna(x):
            return float("nan")
    except Exception:
        pass
    s = str(x).strip()
    if s in ("", "nan", "none", "-"):
        return float("nan")
    s = re.sub(r"[^\d\.,\-]", "", s)
    if "." in s and "," in s:
        s = s.replace(".", "").replace(",", ".")
    else:
        if "," in s and "." not in s:
            s = s.replace(",", ".")
        if s.count(".") > 1:
            s = s.replace(".", "")
    s = re.sub(r"[^\d\.\-]", "", s)
    try:
        return float(s)
    except Exception:
        return float("nan")


def parse_money_series(serie):
    if serie is None:
        return pd.Series(dtype="float64")
    return serie.astype(str).map(parse_money_value).astype("float64")


def parse_int_series(serie):
    def to_int(x):
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
    return serie.map(to_int).astype("Int64")


def formatar_reais_sem_centavos(v):
    try:
        v = float(v)
    except Exception:
        return "R$ 0"
    return f"R$ {f'{v:,.0f}'.replace(',', '.')}"


def formatar_reais_com_centavos(v):
    try:
        v = float(v)
    except Exception:
        return "R$ 0,00"
    s = f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {s}"


@st.cache_data(ttl=300)
def carregar_xlsx_from_url(url):
    r = requests.get(url, timeout=25)
    r.raise_for_status()
    return pd.ExcelFile(BytesIO(r.content))


def detectar_linha_cabecalho(df_raw, keywords):
    for i in range(min(len(df_raw), 12)):
        linha = " ".join(df_raw.iloc[i].astype(str).str.upper().tolist())
        if any(kw.upper() in linha for kw in keywords):
            return i
    return None


def limpar_aba_raw(df_raw, nome):
    busca = {
        "ESTOQUE": ["PRODUTO", "EM ESTOQUE"],
        "VENDAS": ["DATA", "PRODUTO"],
        "COMPRAS": ["DATA", "CUSTO"],
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

# --------------------------------------------------
# CSS GLOBAL (MOBILE FRIENDLY)
# --------------------------------------------------
GLOBAL_CSS = """
<style>
:root{
  --bg:#0b0b0b;
  --accent:#8b5cf6;
  --accent-2:#a78bfa;
  --muted:#bdbdbd;
  --card-bg:#141414;
}
body, .stApp { background: var(--bg) !important; color:#f0f0f0 !important; font-family: Inter, system-ui; }
.badge{padding:4px 8px;border-radius:8px;font-size:12px;display:inline-block;}
.low{background:rgba(255,165,0,0.25); color:#ffd699;}
.zero{background:rgba(255,0,0,0.25); color:#ffb4b4;}
.hot{background:rgba(34,197,94,0.25); color:#b7f7cf;}
.card-ecom{ background: linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01)); border-radius:14px; padding:14px; display:flex; gap:12px; }
.card-title{font-weight:900;font-size:15px;margin-bottom:4px;color:#fff;}
.card-meta{font-size:12px;color:#cfcfe0;margin-bottom:6px;}
.avatar{ width:60px;height:60px;border-radius:14px; background:linear-gradient(120deg,#a78bfa,#ec4899,#06b6d4); display:flex;align-items:center;justify-content:center; color:white;font-weight:900;font-size:20px; }
@media(max-width:720px){
  .card-ecom{flex-direction:column;align-items:flex-start;}
}
</style>
"""

st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

# --------------------------------------------------
# CARREGAMENTO DA PLANILHA
# --------------------------------------------------
try:
    xls = carregar_xlsx_from_url(URL_PLANILHA)
except Exception as e:
    st.error("Erro ao abrir a planilha")
    st.exception(e)
    st.stop()

# --------------------------------------------------
# LEITURA DAS ABAS
# --------------------------------------------------
dfs = {}
for aba in ["ESTOQUE", "VENDAS", "COMPRAS"]:
    if aba in xls.sheet_names:
        raw = pd.read_excel(URL_PLANILHA, sheet_name=aba, header=None)
        cleaned = limpar_aba_raw(raw, aba)
        if cleaned is not None:
            dfs[aba] = cleaned

estoque_df = dfs.get("ESTOQUE", pd.DataFrame()).copy()
vendas_df = dfs.get("VENDAS", pd.DataFrame()).copy()
compras_df = dfs.get("COMPRAS", pd.DataFrame()).copy()

# --------------------------------------------------
# NORMALIZAÇÃO ESTOQUE
# --------------------------------------------------
if not estoque_df.empty:
    if "EM ESTOQUE" not in estoque_df.columns:
        for c in estoque_df.columns:
            if "ESTOQUE" in c.upper() or "QTD" in c.upper():
                estoque_df["EM ESTOQUE"] = parse_int_series(estoque_df[c]).fillna(0).astype(int)
                break
    if "PRODUTO" not in estoque_df.columns:
        estoque_df = estoque_df.rename(columns={estoque_df.columns[0]: "PRODUTO"})

# --------------------------------------------------
# TABS PRINCIPAIS
# --------------------------------------------------
tabs = st.tabs(["🛒 VENDAS", "📦 ESTOQUE", "🧾 COMPRAS", "🔍 PESQUISAR"])

# --------------------------------------------------
# ABA VENDAS
# --------------------------------------------------
with tabs[0]:
    st.subheader("🛒 Vendas")
    if vendas_df.empty:
        st.info("Sem dados de vendas")
    else:
        st.dataframe(vendas_df, use_container_width=True)

# --------------------------------------------------
# ABA ESTOQUE
# --------------------------------------------------
with tabs[1]:
    st.subheader("📦 Estoque Geral")
    st.dataframe(estoque_df.sort_values("EM ESTOQUE", ascending=False), use_container_width=True)

# --------------------------------------------------
# ABA COMPRAS
# --------------------------------------------------
with tabs[2]:
    st.subheader("🧾 Compras")
    if compras_df.empty:
        st.info("Sem dados de compras")
    else:
        st.dataframe(compras_df, use_container_width=True)

# --------------------------------------------------
# ABA PESQUISAR — FINAL PROFISSIONAL
# --------------------------------------------------
with tabs[3]:
    st.subheader("🔍 Pesquisar produtos")

    col1, col2, col3 = st.columns([3, 2, 2])
    with col1:
        termo = st.text_input("Buscar produto")
    with col2:
        ordenar = st.selectbox(
            "Ordenar",
            [
                "Estoque primeiro + Nome A–Z",
                "Nome A–Z",
                "Nome Z–A",
                "Maior estoque",
            ],
        )
    with col3:
        ocultar_sem_estoque = st.checkbox("Ocultar sem estoque", value=False)

    df = estoque_df.copy()

    if termo:
        df = df[df["PRODUTO"].str.contains(termo, case=False, na=False)]

    if ocultar_sem_estoque:
        df = df[df["EM ESTOQUE"] > 0]

    if ordenar == "Estoque primeiro + Nome A–Z":
        df["_tem_estoque"] = (df["EM ESTOQUE"] > 0).astype(int)
        df = df.sort_values(by=["_tem_estoque", "PRODUTO"], ascending=[False, True])
        df = df.drop(columns=["_tem_estoque"])
    elif ordenar == "Nome A–Z":
        df = df.sort_values("PRODUTO")
    elif ordenar == "Nome Z–A":
        df = df.sort_values("PRODUTO", ascending=False)
    elif ordenar == "Maior estoque":
        df = df.sort_values("EM ESTOQUE", ascending=False)

    st.markdown("<div style='display:grid;grid-template-columns:repeat(3,1fr);gap:12px;'>", unsafe_allow_html=True)

    for _, r in df.iterrows():
        nome = r.get("PRODUTO", "")
        estoque = int(r.get("EM ESTOQUE", 0))

        iniciais = "".join([p[0].upper() for p in str(nome).split()[:2] if p]) or "—"

        badges = []
        if estoque == 0:
            badges.append("<span class='badge zero'>⛔ Sem estoque</span>")
        elif estoque <= 3:
            badges.append("<span class='badge low'>⚠️ Baixo</span>")

        badges_html = " ".join(badges)
        opacity = "opacity:0.45;" if estoque == 0 else ""

        card_html = (
            f"<div class='card-ecom' style='{opacity}'>"
            f"<div class='avatar'>{iniciais}</div>"
            f"<div style='flex:1;'>"
            f"<div class='card-title'>{nome}</div>"
            f"<div class='card-meta'>Estoque: <b>{estoque}</b></div>"
            f"<div style='margin-top:6px;'>{badges_html}</div>"
            f"</div></div>"
        )

        st.markdown(card_html, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
