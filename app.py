# app.py — Dashboard Loja Importados (Roxo Minimalista) — Dark Theme Mobile
# Versão corrigida: tratamento de colunas ausentes + extras (atualizar, download CSV, pizza destacada)

import streamlit as st
import pandas as pd
import plotly.express as px
import re
from datetime import datetime, timedelta
import requests
from io import BytesIO

st.set_page_config(page_title="Loja Importados – Dashboard", layout="wide", initial_sidebar_state="collapsed")

URL_PLANILHA = "https://docs.google.com/spreadsheets/d/1TsRjsfw1TVfeEWBBvhKvsGQ5YUCktn2b/export?format=xlsx"

# -------------------------
# CSS — Tabelas 100% dark
# -------------------------
st.markdown("""
<style>
:root{
  --bg:#0b0b0b;
  --accent:#8b5cf6;
  --accent-2:#a78bfa;
  --muted:#bdbdbd;
  --card-bg:#141414;
  --table-bg:#111;
  --table-head:#202020;
  --table-row:#181818;
}
body, .stApp { background: var(--bg) !important; color:#f0f0f0 !important; font-family: Inter, system-ui, -apple-system; }

/* Tabelas completamente escuras */
.stDataFrame, .stTable, .dataframe {
    background: var(--table-bg) !important;
    color: #f0f0f0 !important;
}
.stDataFrame thead th, .dataframe thead th {
    background: var(--table-head) !important;
    color: #fff !important;
    font-weight:700 !important;
    border-bottom:1px solid #333 !important;
}
.stDataFrame tbody tr td, .dataframe tbody tr td {
    background: var(--table-row) !important;
    color:#eaeaea !important;
    border-bottom:1px solid rgba(255,255,255,0.06) !important;
}

/* Scrollbars escuros */
::-webkit-scrollbar { width: 8px; height:8px; }
::-webkit-scrollbar-track { background:#111; }
::-webkit-scrollbar-thumb { background:#333; border-radius:10px; }

/* KPIs / estética */
.topbar { display:flex; gap:12px; margin-bottom:8px; align-items:center; }
.logo-wrap { width:44px; height:44px; display:flex; align-items:center; justify-content:center; border-radius:10px; background: linear-gradient(135deg,var(--accent),var(--accent-2)); box-shadow:0 6px 18px rgba(0,0,0,0.5); }
.title { font-size:20px; font-weight:800; color:var(--accent-2); margin:0; }
.subtitle { font-size:12px; color:var(--muted); margin:0; margin-top:2px; }
.kpi-row { display:flex; gap:10px; flex-wrap:wrap; margin-bottom:20px; }
.kpi { background:var(--card-bg); border-radius:10px; padding:10px 14px; box-shadow:0 6px 16px rgba(0,0,0,0.45); border-left:6px solid var(--accent); min-width:160px; }
.kpi h3 { margin:0; font-size:12px; color:var(--accent-2); font-weight:800; }
.kpi .value { margin-top:6px; font-size:20px; font-weight:900; }
.stTabs button { background:#1e1e1e !important; border:1px solid #333 !important; border-radius:12px !important; padding:8px 14px !important; margin-right:8px !important; color:var(--accent-2) !important; font-weight:700 !important; }
</style>
""", unsafe_allow_html=True)

# -------------------------
# Top bar
# -------------------------
st.markdown("""
<div class="topbar">
  <div class="logo-wrap">
    <svg viewBox="0 0 24 24" fill="none">
      <rect x="3" y="3" width="18" height="18" rx="4" fill="white" fill-opacity="0.06"/>
      <path d="M7 9h10l-1 6H8L7 9z" stroke="white" stroke-opacity="0.95" stroke-width="1.2"/>
      <path d="M9 6l2-2 2 2" stroke="white" stroke-opacity="0.95" stroke-width="1.2"/>
    </svg>
  </div>
  <div>
    <div class="title">Loja Importados — Dashboard</div>
    <div class="subtitle">Visão rápida de vendas e estoque</div>
  </div>
</div>
""", unsafe_allow_html=True)

# -------------------------
# Helpers robustos
# -------------------------
def find_col(df, candidates):
    """Procura a primeira coluna do dataframe que casa com qualquer string em candidates (case-insensitive)."""
    cols = df.columns.astype(str)
    for cand in candidates:
        for c in cols:
            if c.strip().upper() == cand.strip().upper():
                return c
    # tenta contains
    for cand in candidates:
        for c in cols:
            if cand.strip().upper() in c.strip().upper():
                return c
    return None

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
        if "," in s and "." not in s:
            s=s.replace(",",".")
        if s.count(".")>1:
            s=s.replace(".","")
    s=re.sub(r"[^\d\.\-]","",s)
    try:
        return float(s)
    except:
        return float("nan")

def parse_money_series(s):
    if s is None:
        return pd.Series(dtype="float64")
    return s.astype(str).map(parse_money_value).astype(float)

def parse_int_series(s):
    if s is None:
        return pd.Series(dtype="Int64")
    def conv(x):
        try:
            if pd.isna(x): return 0
        except: pass
        ss=re.sub(r"[^\d]","",str(x))
        if ss=="": return 0
        try: return int(ss)
        except: return 0
    return s.map(conv).astype("Int64")

def formatar_reais_sem_centavos(v):
    try:
        v=float(v)
    except:
        return "R$ 0"
    return f"R$ {f'{v:,.0f}'.replace(',','.')}" 

# -------------------------
# Carregar Excel (cacheável)
# -------------------------
@st.cache_data(ttl=300)
def carregar_xlsx_from_url(url):
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return pd.ExcelFile(BytesIO(r.content))

# botão para atualizar (limpa cache e rerun)
col_refresh, _ = st.columns([1,9])
with col_refresh:
    if st.button("🔁 Atualizar planilha (forçar)"):
        st.cache_data.clear()
        st.experimental_rerun()

# tenta carregar
try:
    xls = carregar_xlsx_from_url(URL_PLANILHA)
except Exception as e:
    st.error("Erro ao carregar planilha. Confira o link e a conexão.")
    st.exception(e)
    st.stop()

# -------------------------
# Ler abas com tolerância
# -------------------------
dfs = {}
for aba in ["ESTOQUE","VENDAS","COMPRAS"]:
    if aba in xls.sheet_names:
        tmp = pd.read_excel(URL_PLANILHA, sheet_name=aba, header=0)
        # normaliza nome colunas (strip)
        tmp.columns = [str(c).strip() for c in tmp.columns]
        dfs[aba] = tmp

# -------------------------
# Preparar ESTOQUE com nomes flexíveis
# -------------------------
e = dfs.get("ESTOQUE", pd.DataFrame()).copy()

# mapear colunas possíveis
col_prod = find_col(e, ["PRODUTO","Produto","produto","NOME","ITEM"])
col_media = find_col(e, ["Media C. UNITARIO","MEDIA C. UNITARIO","Media C UNITARIO","MEDIA CUSTO UNITARIO","Media C. UNIT"])
col_venda_sug = find_col(e, ["Valor Venda Sugerido","Valor Venda","VALOR VENDA SUGERIDO","VALOR VENDA","PRECO VENDA"])
col_estoque = find_col(e, ["EM ESTOQUE","ESTOQUE","QTD","QUANTIDADE","QTDE","QTY"])

# renomear para padrão interno (se existirem)
if not e.empty:
    rename_map = {}
    if col_prod: rename_map[col_prod] = "PRODUTO"
    if col_media: rename_map[col_media] = "Media C. UNITARIO"
    if col_venda_sug: rename_map[col_venda_sug] = "Valor Venda Sugerido"
    if col_estoque: rename_map[col_estoque] = "EM ESTOQUE"
    if rename_map:
        e = e.rename(columns=rename_map)

    # garantir colunas numéricas seguras
    if "Media C. UNITARIO" in e.columns:
        e["Media C. UNITARIO"] = parse_money_series(e["Media C. UNITARIO"]).fillna(0)
    else:
        e["Media C. UNITARIO"] = 0.0
    if "Valor Venda Sugerido" in e.columns:
        e["Valor Venda Sugerido"] = parse_money_series(e["Valor Venda Sugerido"]).fillna(0)
    else:
        e["Valor Venda Sugerido"] = 0.0
    if "EM ESTOQUE" in e.columns:
        e["EM ESTOQUE"] = parse_int_series(e["EM ESTOQUE"]).fillna(0).astype(int)
    else:
        e["EM ESTOQUE"] = 0

    if "PRODUTO" not in e.columns:
        # tenta primeira coluna string
        for c in e.columns:
            if e[c].dtype == object:
                e = e.rename(columns={c:"PRODUTO"})
                break
else:
    # garantir DataFrame com colunas esperadas
    e = pd.DataFrame(columns=["PRODUTO","Media C. UNITARIO","Valor Venda Sugerido","EM ESTOQUE"])

# -------------------------
# Preparar VENDAS com nomes flexíveis
# -------------------------
v = dfs.get("VENDAS", pd.DataFrame()).copy()
if not v.empty:
    # detectar colunas-chave
    col_prod_v = find_col(v, ["PRODUTO","Produto","produto","ITEM"])
    col_val_venda = find_col(v, ["VALOR VENDA","VALOR_VENDA","Valor Venda","PRECO"])
    col_val_total = find_col(v, ["VALOR TOTAL","VALOR_TOTAL","Valor Total"])
    col_qtd = find_col(v, ["QTD","QUANTIDADE","QTY","QTDE"])
    col_data = find_col(v, ["DATA","Data","data"])
    col_media_custo = find_col(v, ["MEDIA C. UNITARIO","MEDIA CUSTO UNITARIO","CUSTO UNITARIO"])

    # rename
    rmap_v = {}
    if col_prod_v: rmap_v[col_prod_v] = "PRODUTO"
    if col_val_venda: rmap_v[col_val_venda] = "VALOR VENDA"
    if col_val_total: rmap_v[col_val_total] = "VALOR TOTAL"
    if col_qtd: rmap_v[col_qtd] = "QTD"
    if col_data: rmap_v[col_data] = "DATA"
    if col_media_custo: rmap_v[col_media_custo] = "MEDIA CUSTO UNITARIO"
    if rmap_v:
        v = v.rename(columns=rmap_v)

    # parse
    if "VALOR VENDA" in v.columns:
        v["VALOR VENDA"] = parse_money_series(v["VALOR VENDA"]).fillna(0)
    if "VALOR TOTAL" in v.columns:
        v["VALOR TOTAL"] = parse_money_series(v["VALOR TOTAL"]).fillna(0)
    else:
        # calc from valor venda * qtd if possible
        if "VALOR VENDA" in v.columns and "QTD" in v.columns:
            v["VALOR TOTAL"] = v["VALOR VENDA"].fillna(0) * parse_int_series(v["QTD"]).fillna(0)
        else:
            v["VALOR TOTAL"] = 0
    if "QTD" in v.columns:
        v["QTD"] = parse_int_series(v["QTD"]).fillna(0).astype(int)
    else:
        v["QTD"] = 0
    if "DATA" in v.columns:
        v["DATA"] = pd.to_datetime(v["DATA"], errors="coerce")
        v["MES_ANO"] = v["DATA"].dt.strftime("%Y-%m")
    else:
        v["MES_ANO"] = pd.NA

    # lucro unitário (se possível)
    if "VALOR VENDA" in v.columns and "MEDIA CUSTO UNITARIO" in v.columns:
        v["LUCRO UNITARIO"] = v["VALOR VENDA"].fillna(0) - parse_money_series(v["MEDIA CUSTO UNITARIO"]).fillna(0)
    else:
        if "LUCRO UNITARIO" not in v.columns:
            v["LUCRO UNITARIO"] = 0.0
else:
    v = pd.DataFrame(columns=["PRODUTO","VALOR VENDA","VALOR TOTAL","QTD","DATA","MES_ANO","LUCRO UNITARIO"])

# -------------------------
# Preparar COMPRAS com nomes flexíveis
# -------------------------
c = dfs.get("COMPRAS", pd.DataFrame()).copy()
if not c.empty:
    col_q_c = find_col(c, ["QUANTIDADE","QTD","QTY"])
    # find custo column
    custo_col = find_col(c, ["CUSTO","CUSTO UNITÁRIO","CUSTO_UNITARIO","CUSTO TOTAL"])
    if col_q_c: c = c.rename(columns={col_q_c:"QUANTIDADE"})
    if custo_col: c = c.rename(columns={custo_col:"CUSTO_UNITARIO"})
    if "QUANTIDADE" in c.columns and "CUSTO_UNITARIO" in c.columns:
        c["QUANTIDADE"] = parse_int_series(c["QUANTIDADE"]).fillna(0).astype(int)
        c["CUSTO_UNITARIO"] = parse_money_series(c["CUSTO_UNITARIO"]).fillna(0)
        c["CUSTO TOTAL (RECALC)"] = c["QUANTIDADE"] * c["CUSTO_UNITARIO"]
    else:
        c["CUSTO TOTAL (RECALC)"] = 0
else:
    c = pd.DataFrame()

# -------------------------
# KPIs de estoque (imutáveis ao filtro)
# -------------------------
# evita KeyError: usamos .get e garantimos colunas acima
valor_custo = float((e.get("Media C. UNITARIO", pd.Series(dtype=float)) * e.get("EM ESTOQUE", pd.Series(dtype=int))).sum()) if not e.empty else 0.0
valor_venda = float((e.get("Valor Venda Sugerido", pd.Series(dtype=float)) * e.get("EM ESTOQUE", pd.Series(dtype=int))).sum()) if not e.empty else 0.0
total_itens = int(e.get("EM ESTOQUE", pd.Series(dtype=int)).sum()) if not e.empty else 0
top5 = e.sort_values("EM ESTOQUE", ascending=False).head(5) if not e.empty else pd.DataFrame()

# -------------------------
# Filtro mês (aplica somente em VENDAS/COMPRAS)
# -------------------------
meses = ["Todos"]
if "MES_ANO" in v.columns:
    meses += sorted(v["MES_ANO"].dropna().unique().tolist(), reverse=True)
atual = datetime.now().strftime("%Y-%m")
index_pad = meses.index(atual) if atual in meses else 0

col_f, col_k = st.columns([1,3])
with col_f:
    mes_sel = st.selectbox("Filtrar por mês (YYYY-MM):", meses, index=index_pad)

def filtrar_df(df):
    if df is None or df.empty or mes_sel == "Todos": return df
    if "MES_ANO" not in df.columns: return df
    return df[df["MES_ANO"] == mes_sel].copy()

v_f = filtrar_df(v)
c_f = filtrar_df(c)

# -------------------------
# KPIs Gerias (vendas/compras)
# -------------------------
total_vendido = float(v_f.get("VALOR TOTAL", pd.Series(dtype=float)).fillna(0).sum()) if not v_f.empty else 0.0
total_lucro = float(((v_f.get("LUCRO UNITARIO", pd.Series(dtype=float)).fillna(0)) * (v_f.get("QTD", pd.Series(dtype=int)).fillna(0))).sum()) if not v_f.empty else 0.0

# calcula total compras com tolerância: tenta CUSTO TOTAL (RECALC) ou qualquer coluna contendo 'CUSTO'
total_compras = 0.0
if not c_f.empty:
    if "CUSTO TOTAL (RECALC)" in c_f.columns:
        total_compras = float(c_f["CUSTO TOTAL (RECALC)"].sum())
    else:
        custo_cols = [col for col in c_f.columns if "CUSTO" in col.upper()]
        if custo_cols:
            total_compras = float(c_f[custo_cols[0]].astype(float).sum())

# -------------------------
# Mostrar KPIs
# -------------------------
with col_k:
    st.markdown(f"""
    <div class="kpi-row">
      <div class="kpi"><h3>💵 Total Vendido</h3><div class="value">{formatar_reais_sem_centavos(total_vendido)}</div></div>
      <div class="kpi" style="border-left-color:#34d399;"><h3>🧾 Total Lucro</h3><div class="value">{formatar_reais_sem_centavos(total_lucro)}</div></div>
      <div class="kpi" style="border-left-color:#f59e0b;"><h3>💸 Total Compras</h3><div class="value">{formatar_reais_sem_centavos(total_compras)}</div></div>

      <div class="kpi" style="border-left-color:#8b5cf6;"><h3>📦 Valor Custo Estoque</h3><div class="value">{formatar_reais_sem_centavos(valor_custo)}</div></div>
      <div class="kpi" style="border-left-color:#a78bfa;"><h3>🏷️ Valor Venda Estoque</h3><div class="value">{formatar_reais_sem_centavos(valor_venda)}</div></div>
      <div class="kpi" style="border-left-color:#6ee7b7;"><h3>🔢 Qtde Total Itens</h3><div class="value">{total_itens}</div></div>
    </div>
    """, unsafe_allow_html=True)

# -------------------------
# Top5: pizza colorida, com destaque e percentuais
# -------------------------
st.markdown("### 🥧 Top 5 — Itens com mais estoque")
if top5.empty:
    st.info("Nenhum dado de estoque disponível.")
else:
    # preparar dados seguros
    pie_df = top5[["PRODUTO","EM ESTOQUE"]].copy()
    pie_df = pie_df.groupby("PRODUTO", dropna=False)["EM ESTOQUE"].sum().reset_index()
    fig_pie = px.pie(pie_df, names="PRODUTO", values="EM ESTOQUE", hole=0.35, color_discrete_sequence=px.colors.qualitative.Set3)
    # destacar a maior fatia
    pulls = [0.12 if i==0 else 0 for i in range(len(pie_df))]
    fig_pie.update_traces(textinfo='percent+label', pull=pulls, marker=dict(line=dict(color='#0b0b0b', width=1)))
    fig_pie.update_layout(plot_bgcolor="#0b0b0b", paper_bgcolor="#0b0b0b", font_color="#fff", margin=dict(t=20,b=20))
    st.plotly_chart(fig_pie, use_container_width=True)
    # download CSV do top5
    csv_top5 = pie_df.to_csv(index=False, sep=';').encode('utf-8')
    st.download_button("⬇️ Baixar Top5 (CSV)", csv_top5, file_name="top5_estoque.csv", mime="text/csv")

# -------------------------
# Tabs principais
# -------------------------
tabs = st.tabs(["🛒 VENDAS","🏆 TOP10 (VALOR)","🏅 TOP10 (QTD)","📦 ESTOQUE","🔍 PESQUISAR"])

with tabs[0]:
    st.subheader("Vendas — período selecionado")
    if v_f.empty:
        st.info("Sem dados de vendas para o período.")
    else:
        # formatar algumas colunas para visualização (não altera dados originais)
        disp = v_f.copy()
        if "VALOR TOTAL" in disp.columns:
            disp["VALOR TOTAL"] = disp["VALOR TOTAL"].map(lambda x: formatar_reais_sem_centavos(x))
        if "VALOR VENDA" in disp.columns:
            disp["VALOR VENDA"] = disp["VALOR VENDA"].map(lambda x: formatar_reais_sem_centavos(x))
        st.dataframe(disp.reset_index(drop=True), use_container_width=True)
        # export CSV
        csv_vendas = v_f.to_csv(index=False, sep=';').encode('utf-8')
        st.download_button("⬇️ Baixar VENDAS (CSV)", csv_vendas, file_name="vendas_filtradas.csv", mime="text/csv")

with tabs[1]:
    st.subheader("Top 10 — por VALOR")
    if v_f.empty:
        st.info("Sem dados.")
    else:
        g = v_f.groupby("PRODUTO", dropna=False).agg(VALOR_TOTAL=("VALOR TOTAL","sum")).reset_index().sort_values("VALOR_TOTAL", ascending=False).head(10)
        fig = px.bar(g, x="PRODUTO", y="VALOR_TOTAL", text=g["VALOR_TOTAL"].map(lambda x: formatar_reais_sem_centavos(x)), color_discrete_sequence=["#8b5cf6"])
        fig.update_layout(plot_bgcolor="#0b0b0b", paper_bgcolor="#0b0b0b", font_color="#fff")
        fig.update_traces(textposition="inside")
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(g.reset_index(drop=True), use_container_width=True)

with tabs[2]:
    st.subheader("Top 10 — por QUANTIDADE")
    if v_f.empty:
        st.info("Sem dados.")
    else:
        gq = v_f.groupby("PRODUTO", dropna=False).agg(QTD_TOTAL=("QTD","sum")).reset_index().sort_values("QTD_TOTAL", ascending=False).head(10)
        fig = px.bar(gq, x="PRODUTO", y="QTD_TOTAL", text=gq["QTD_TOTAL"].astype(str), color_discrete_sequence=["#8b5cf6"])
        fig.update_layout(plot_bgcolor="#0b0b0b", paper_bgcolor="#0b0b0b", font_color="#fff")
        fig.update_traces(textposition="inside")
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(gq.reset_index(drop=True), use_container_width=True)

with tabs[3]:
    st.subheader("Estoque Atual (valores calculados independentes do filtro)")
    if e.empty:
        st.info("Sem dados de estoque.")
    else:
        # cria colunas calculadas seguras para exibição
        disp_e = e.copy()
        disp_e["VALOR_CUSTO_TOTAL"] = (disp_e.get("Media C. UNITARIO", 0) * disp_e.get("EM ESTOQUE", 0)).fillna(0)
        disp_e["VALOR_VENDA_TOTAL"] = (disp_e.get("Valor Venda Sugerido", 0) * disp_e.get("EM ESTOQUE", 0)).fillna(0)
        # formata
        for col in ["Media C. UNITARIO","Valor Venda Sugerido","VALOR_CUSTO_TOTAL","VALOR_VENDA_TOTAL"]:
            if col in disp_e.columns:
                disp_e[col] = disp_e[col].map(lambda x: formatar_reais_sem_centavos(x))
        # colunas de interesse
        cols_order = [c for c in ["PRODUTO","EM ESTOQUE","Media C. UNITARIO","Valor Venda Sugerido","VALOR_CUSTO_TOTAL","VALOR_VENDA_TOTAL"] if c in disp_e.columns]
        st.dataframe(disp_e[cols_order].reset_index(drop=True), use_container_width=True)
        # download estoque
        csv_estoque = e.to_csv(index=False, sep=';').encode('utf-8')
        st.download_button("⬇️ Baixar ESTOQUE (CSV)", csv_estoque, file_name="estoque.csv", mime="text/csv")

with tabs[4]:
    st.subheader("Pesquisar produtos")
    termo = st.text_input("Digite parte do nome do produto")
    if termo.strip():
        res = e[e["PRODUTO"].astype(str).str.contains(termo, case=False, na=False)]
        if res.empty:
            st.warning("Nenhum produto encontrado.")
        else:
            # formata exibição
            res_disp = res.copy()
            if "Media C. UNITARIO" in res_disp.columns:
                res_disp["Media C. UNITARIO"] = res_disp["Media C. UNITARIO"].map(lambda x: formatar_reais_sem_centavos(x))
            if "Valor Venda Sugerido" in res_disp.columns:
                res_disp["Valor Venda Sugerido"] = res_disp["Valor Venda Sugerido"].map(lambda x: formatar_reais_sem_centavos(x))
            st.dataframe(res_disp.reset_index(drop=True), use_container_width=True)

# -------------------------
# Rodapé
# -------------------------
st.markdown("""
<div style="margin-top:12px; color:#bdbdbd; font-size:12px;">
  <em>Nota:</em> O app tenta localizar automaticamente colunas com nomes variados (ex.: \"Media C. UNITARIO\", \"Media CUSTO UNITARIO\", etc.).\
  Os KPIs de estoque não são afetados pelo filtro de mês. Use o botão \"Atualizar planilha\" para forçar recarga do arquivo externo.
</div>
""", unsafe_allow_html=True)
