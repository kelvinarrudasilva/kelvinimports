# app.py — Dashboard Loja Importados (Roxo Minimalista) — Dark Theme Mobile
import streamlit as st
import pandas as pd
import plotly.express as px
import re
from datetime import datetime, timedelta
import requests
from io import BytesIO

st.set_page_config(page_title="Loja Importados – Dashboard", layout="wide", initial_sidebar_state="collapsed")

URL_PLANILHA = "https://docs.google.com/spreadsheets/d/1TsRjsfw1TVfeEWBBvhKvsGQ5YUCktn2b/export?format=xlsx"

# =============================
# CSS - Dark Theme + CARTÕES PESQUISA
# =============================
st.markdown("""
<style>
:root{
  --bg:#0b0b0b;
  --accent:#8b5cf6;
  --accent-2:#a78bfa;
  --card-bg:#141414;
  --muted:#bdbdbd;
}
body, .stApp { background: var(--bg) !important; color:#f0f0f0 !important; font-family: Inter, system-ui; }

/* CARD PESQUISA */
.search-card {
    background:#151515;
    border-radius:14px;
    padding:16px;
    border:1px solid #272727;
    box-shadow:0 6px 18px rgba(0,0,0,0.55);
    transition:0.18s;
}
.search-card:hover {
    transform: translateY(-4px);
    border-color: var(--accent-2);
}
.card-title {
    font-size:16px;
    font-weight:800;
    color:var(--accent-2);
    margin-bottom:6px;
}
.badge {
    display:inline-block;
    background:#222;
    padding:4px 10px;
    font-size:11px;
    border-radius:8px;
    border:1px solid #444;
}
.badge.low { background:#360000; border-color:#ff5b5b; }
.badge.hot { background:#341144; border-color:#c77dff; }

/* GRID COM 2 COLUNAS NO PC E 1 NO MOBILE */
.card-grid {
    display:grid;
    grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
    gap:16px;
    margin-top:16px;
}
</style>
""", unsafe_allow_html=True)

# =============================
# Top Bar
# =============================
st.markdown("""
<div style="display:flex; align-items:center; gap:12px; margin-bottom:10px;">
  <div style="width:44px; height:44px; background:linear-gradient(135deg,#8b5cf6,#a78bfa); border-radius:12px; display:flex; align-items:center; justify-content:center;">
    <svg viewBox="0 0 24 24" fill="none" width="26" height="26">
      <rect x="3" y="3" width="18" height="18" rx="4" stroke="white" stroke-opacity="0.7"/>
    </svg>
  </div>
  <div>
    <div style="font-size:20px; font-weight:800; color:#a78bfa;">Loja Importados — Dashboard</div>
    <div style="font-size:12px; color:#bdbdbd;">Visão rápida de vendas e estoque</div>
  </div>
</div>
""", unsafe_allow_html=True)

# =============================
# Helpers
# =============================
def parse_money_value(x):
    try:
        if pd.isna(x): return float("nan")
    except: pass
    s=str(x).strip()
    if s in ("","nan","none","-"): return float("nan")
    s=re.sub(r"[^\d\.,\-]","",s)
    if "." in s and "," in s:
        s=s.replace(".","").replace(",",".")
    else:
        if "," in s and "." not in s: s=s.replace(",",".")
        if s.count(".")>1: s=s.replace(".","")
    try: return float(s)
    except: return float("nan")

def parse_money_series(serie):
    return serie.astype(str).map(parse_money_value).astype("float64") if serie is not None else pd.Series(dtype="float64")

def parse_int_series(serie):
    def to_int(x):
        try:
            if pd.isna(x): return pd.NA
        except: pass
        s=re.sub(r"[^\d\-]","",str(x))
        if s in ("","-","nan"): return pd.NA
        try: return int(float(s))
        except: return pd.NA
    return serie.map(to_int).astype("Int64")

def formatar_reais_sem_centavos(v):
    try: v=float(v)
    except: return "R$ 0"
    return f"R$ {f'{v:,.0f}'.replace(',', '.')}"

def formatar_reais_com_centavos(v):
    try: v=float(v)
    except: return "R$ 0,00"
    s=f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {s}"

# =============================
# Carregar planilha
# =============================
def carregar_xlsx_from_url(url):
    r=requests.get(url, timeout=25)
    r.raise_for_status()
    return pd.ExcelFile(BytesIO(r.content))

xls = carregar_xlsx_from_url(URL_PLANILHA)
abas_all = xls.sheet_names
dfs = {}

def detectar_linha_cabecalho(df_raw, keywords):
    for i in range(min(len(df_raw), 12)):
        ln=" ".join(df_raw.iloc[i].astype(str).str.upper().tolist())
        if any(k.upper() in ln for k in keywords):
            return i
    return None

def limpar_aba_raw(df_raw, nome):
    busca={"ESTOQUE":["PRODUTO","ESTOQUE"],"VENDAS":["DATA","PRODUTO"],"COMPRAS":["DATA","CUSTO"]}.get(nome,["PRODUTO"])
    linha=detectar_linha_cabecalho(df_raw, busca)
    if linha is None: return None
    tmp=df_raw.copy()
    tmp.columns=tmp.iloc[linha]
    df=tmp.iloc[linha+1:].copy()
    df.columns=[str(c).strip() for c in df.columns]
    return df.loc[:, ~df.isna().all()].reset_index(drop=True)

for aba in ["ESTOQUE","VENDAS","COMPRAS"]:
    if aba in abas_all:
        raw=pd.read_excel(URL_PLANILHA, sheet_name=aba, header=None)
        clean=limpar_aba_raw(raw, aba)
        if clean is not None:
            dfs[aba]=clean

# =============================
# Ajustar ESTOQUE
# =============================
if "ESTOQUE" in dfs:
    df_e = dfs["ESTOQUE"].copy()
    for alt in ["Media C. UNITARIO","MEDIA CUSTO UNITARIO","MEDIA C. UNIT"]:
        if alt in df_e.columns:
            df_e["Media C. UNITARIO"]=parse_money_series(df_e[alt]).fillna(0)
    for alt in ["Valor Venda Sugerido","VALOR VENDA SUGERIDO","VALOR VENDA"]:
        if alt in df_e.columns:
            df_e["Valor Venda Sugerido"]=parse_money_series(df_e[alt]).fillna(0)
    for alt in ["EM ESTOQUE","ESTOQUE","QTD"]:
        if alt in df_e.columns:
            df_e["EM ESTOQUE"]=parse_int_series(df_e[alt]).fillna(0).astype(int)
    if "PRODUTO" not in df_e.columns:
        df_e = df_e.rename(columns={df_e.columns[0]:"PRODUTO"})
    dfs["ESTOQUE"]=df_e

# =============================
# Ajustar VENDAS
# =============================
if "VENDAS" in dfs:
    df_v = dfs["VENDAS"].copy()
    df_v.columns=[str(c).strip() for c in df_v.columns]

    map_money={
        "VALOR VENDA":["VALOR VENDA","VALOR_VENDA"],
        "VALOR TOTAL":["VALOR TOTAL","VALOR_TOTAL"],
        "MEDIA CUSTO UNITARIO":["MEDIA CUSTO UNITARIO","MEDIA C. UNITARIO"],
        "LUCRO UNITARIO":["LUCRO UNITARIO"]
    }
    for dest, srcs in map_money.items():
        for s in srcs:
            if s in df_v.columns:
                df_v[dest]=parse_money_series(df_v[s])
                break

    qtd_cols=[c for c in df_v.columns if c.upper() in ("QTD","QUANTIDADE")]
    if qtd_cols:
        df_v["QTD"]=parse_int_series(df_v[qtd_cols[0]]).fillna(0).astype(int)

    if "DATA" in df_v.columns:
        df_v["DATA"]=pd.to_datetime(df_v["DATA"], errors="coerce")
        df_v["MES_ANO"]=df_v["DATA"].dt.strftime("%Y-%m")

    dfs["VENDAS"]=df_v.sort_values("DATA", ascending=False).reset_index(drop=True)

# =============================
# Ajustar COMPRAS
# =============================
if "COMPRAS" in dfs:
    df_c = dfs["COMPRAS"].copy()
    q=[c for c in df_c.columns if "QUANT" in c.upper()]
    if q:
        df_c["QUANTIDADE"]=parse_int_series(df_c[q[0]]).fillna(0).astype(int)
    cu=[c for c in df_c.columns if "CUSTO" in c.upper()]
    if cu:
        df_c["CUSTO UNITÁRIO"]=parse_money_series(df_c[cu[0]]).fillna(0)
    df_c["CUSTO TOTAL (RECALC)"]=df_c.get("QUANTIDADE",0)*df_c.get("CUSTO UNITÁRIO",0)
    if "DATA" in df_c.columns:
        df_c["DATA"]=pd.to_datetime(df_c["DATA"], errors="coerce")
        df_c["MES_ANO"]=df_c["DATA"].dt.strftime("%Y-%m")
    dfs["COMPRAS"]=df_c

# =============================
# INDICADORES
# =============================
estoque_df=dfs.get("ESTOQUE", pd.DataFrame()).copy()
if not estoque_df.empty:
    custo_total=(estoque_df["Media C. UNITARIO"]*estoque_df["EM ESTOQUE"]).sum()
    venda_total=(estoque_df["Valor Venda Sugerido"]*estoque_df["EM ESTOQUE"]).sum()
else:
    custo_total=venda_total=0

meses=["Todos"]
if "VENDAS" in dfs:
    meses+=sorted(dfs["VENDAS"]["MES_ANO"].dropna().unique().tolist(), reverse=True)

mes_atual=datetime.now().strftime("%Y-%m")
index_padrao=meses.index(mes_atual) if mes_atual in meses else 0

col_filter, col_kpis=st.columns([1,3])
with col_filter:
    mes_sel=st.selectbox("Filtrar por mês:", meses, index=index_padrao)

def filtrar(df, mes):
    if df is None or df.empty: return df
    return df if mes=="Todos" else df[df["MES_ANO"]==mes]

df_v_f=filtrar(dfs.get("VENDAS"), mes_sel)
df_c_f=filtrar(dfs.get("COMPRAS"), mes_sel)

# KPIs
total_vendido=df_v_f.get("VALOR TOTAL", pd.Series()).fillna(0).sum()
total_lucro=(df_v_f.get("LUCRO UNITARIO",0)*df_v_f.get("QTD",0)).sum()
total_compras=df_c_f.get("CUSTO TOTAL (RECALC)", pd.Series()).fillna(0).sum()

with col_kpis:
    st.markdown(f"""
    <div style="display:flex; gap:12px; flex-wrap:wrap;">
      <div class="kpi"><h3>Total Vendido</h3><div class="value">{formatar_reais_sem_centavos(total_vendido)}</div></div>
      <div class="kpi"><h3>Total Lucro</h3><div class="value">{formatar_reais_sem_centavos(total_lucro)}</div></div>
      <div class="kpi"><h3>Total Compras</h3><div class="value">{formatar_reais_sem_centavos(total_compras)}</div></div>
      <div class="kpi"><h3>Custo Estoque</h3><div class="value">{formatar_reais_sem_centavos(custo_total)}</div></div>
      <div class="kpi"><h3>Sugestão Venda Estoque</h3><div class="value">{formatar_reais_sem_centavos(venda_total)}</div></div>
    </div>
    """, unsafe_allow_html=True)

# =============================
# TABS
# =============================
tabs = st.tabs(["🛒 VENDAS", "📦 ESTOQUE", "🔍 PESQUISAR"])

# =============================
# VENDAS
# =============================
with tabs[0]:
    if df_v_f.empty:
        st.info("Nenhuma venda no período.")
    else:
        df_v_t=df_v_f.copy()
        df_v_t["DATA"]=pd.to_datetime(df_v_t["DATA"])
        st.dataframe(df_v_t, use_container_width=True)

# =============================
# ESTOQUE
# =============================
with tabs[1]:
    if estoque_df.empty:
        st.info("Sem estoque.")
    else:
        st.dataframe(estoque_df, use_container_width=True)

# =============================
# PESQUISAR — NOVA VERSÃO 2 COLUNAS
# =============================
with tabs[2]:
    st.subheader("🔍 Buscar produtos")

    termo = st.text_input("Digite parte do nome:")

    if termo.strip():
        df_s = estoque_df[estoque_df["PRODUTO"].str.contains(termo, case=False, na=False)]

        if df_s.empty:
            st.warning("Nenhum produto encontrado.")
        else:
            st.markdown("<div class='card-grid'>", unsafe_allow_html=True)

            for _, row in df_s.iterrows():

                nome = row["PRODUTO"]
                estoque = int(row["EM ESTOQUE"])
                custo = formatar_reais_com_centavos(row["Media C. UNITARIO"])
                venda = formatar_reais_com_centavos(row["Valor Venda Sugerido"])

                # BADGES inteligentes (sem margem)
                badge_html = ""
                if estoque <= 3:
                    badge_html = "<span class='badge low'>⚠️ Baixo estoque</span>"
                elif row["Valor Venda Sugerido"] >= estoque_df["Valor Venda Sugerido"].quantile(0.85):
                    badge_html = "<span class='badge hot'>🔥 Premium</span>"

                st.markdown(f"""
                <div class='search-card'>
                    <div class='card-title'>{nome}</div>

                    <div style="margin-bottom:6px;">{badge_html}</div>

                    <p style="font-size:14px; line-height:1.5; margin:0;">
                        <strong>Estoque:</strong> {estoque}<br>
                        <strong>Preço Custo:</strong> {custo}<br>
                        <strong>Preço Venda:</strong> {venda}<br>
                    </p>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

# =============================
# Rodapé
# =============================
st.markdown("""<div style='margin-top:20px;font-size:12px;color:#777;'>Kelvin Imports ©</div>""", unsafe_allow_html=True)
