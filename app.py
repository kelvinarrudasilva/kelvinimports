# app.py
import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
import numpy as np
import re

# -------------------------
# Configuração visual
# -------------------------
st.set_page_config(page_title="Controle Loja - Estoque & Vendas", layout="wide")

st.markdown(
    """
    <style>
      :root { --gold: #E8C36A; --bg: #0b0b0b; --card:#121212; --muted:#9e9b8f;}
      .stApp { background-color: var(--bg); color: var(--gold); }
      .kpi { background: linear-gradient(90deg,#0f0f0f,#0b0b0b); padding:12px; border-radius:10px; text-align:center; }
      .kpi-title { color: var(--muted); font-size:13px; }
      .kpi-value { color: var(--gold); font-size:22px; font-weight:700; }
      .small { color: var(--muted); font-size:12px; }
      .stDataFrame table { background-color: #0b0b0b; color: #e6e2d3; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("📊 Controle Loja — Estoque & Vendas")
st.markdown("Tema: Dark • Foco: estoque atual, Top 10 vendidos, vendas e lucro por período.")

# -------------------------
# Helpers: detectar cabeçalho, limpar colunas, encontrar colunas por similaridade
# -------------------------
def detect_header(path, sheet_name):
    """Lê a aba procurando a linha onde aparece 'PRODUTO' e usa essa linha como header."""
    raw = pd.read_excel(path, sheet_name=sheet_name, header=None)
    for i in range(min(len(raw), 10)):
        row_vals = raw.iloc[i].astype(str).str.upper().fillna("")
        if any("PRODUTO" in v for v in row_vals):
            df = pd.read_excel(path, sheet_name=sheet_name, header=i)
            return df, i
    # fallback: header 0
    df = pd.read_excel(path, sheet_name=sheet_name, header=0)
    return df, 0

def clean_df(df):
    """Remove colunas Unnamed e linhas/colunas vazias e padroniza nomes (mantendo originais)."""
    if df is None:
        return None
    # drop unnamed columns
    df = df.loc[:, ~df.columns.str.contains("^Unnamed", na=False)]
    df = df.dropna(axis=1, how="all")
    df = df.dropna(axis=0, how="all").reset_index(drop=True)
    # strip column names
    df.columns = [str(c).strip() for c in df.columns]
    return df

def find_col(df, *candidates):
    """Retorna o nome original da primeira coluna que contém qualquer candidato (case-insensitive)."""
    if df is None:
        return None
    cols = list(df.columns)
    for cand in candidates:
        pattern = re.sub(r"\s+", " ", str(cand)).strip().upper()
        for c in cols:
            if pattern in str(c).upper():
                return c
    return None

def to_num(series):
    return pd.to_numeric(series, errors="coerce").fillna(0)

def fmt_brl(x):
    try:
        return f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "R$ 0,00"

# -------------------------
# Carregar arquivo
# -------------------------
EXCEL = "LOJA IMPORTADOS.xlsx"
if not Path(EXCEL).exists():
    st.error(f"Arquivo '{EXCEL}' não encontrado no diretório do app.")
    st.stop()

# detectar e carregar apenas as 3 abas de interesse
xls = pd.ExcelFile(EXCEL)
available = [s.upper() for s in xls.sheet_names]
# prefer exact names:
sheets = {}
for name in ["ESTOQUE", "VENDAS", "COMPRAS"]:
    if name in available:
        df, hdr = detect_header(EXCEL, name)
        df = clean_df(df)
        sheets[name] = {"df": df, "header_row": hdr}
    else:
        sheets[name] = {"df": None, "header_row": None}

st.sidebar.markdown("### 📂 Fonte")
st.sidebar.write("Abas encontradas:", xls.sheet_names)
st.sidebar.markdown("---")

# pequenos avisos se abas não carregaram
for n in ["ESTOQUE", "VENDAS", "COMPRAS"]:
    if sheets[n]["df"] is None:
        st.warning(f"Aba '{n}' não carregada ou não encontrada. Verifique o Excel.")

estoque = sheets["ESTOQUE"]["df"]
vendas = sheets["VENDAS"]["df"]
compras = sheets["COMPRAS"]["df"]

# -------------------------
# Mapear colunas exatas conforme seus nomes
# -------------------------
# ESTOQUE: PRODUTO, EM ESTOQUE, COMPRAS, Media C. UNITARIO, Valor Venda Sugerido, VENDAS
e_prod = find_col(estoque, "PRODUTO")
e_qtd = find_col(estoque, "EM ESTOQUE", "QUANT", "QTD", "QUANTIDADE")
e_valor_unit = find_col(estoque, "Valor Venda Sugerido", "VALOR VENDA")

# VENDAS: DATA, PRODUTO, QTD, VALOR VENDA, VALOR TOTAL, MEDIA CUSTO UNITARIO, LUCRO
v_data = find_col(vendas, "DATA")
v_prod = find_col(vendas, "PRODUTO")
v_qtd = find_col(vendas, "QTD", "QUANT", "QUANTIDADE")
v_valor_unit = find_col(vendas, "VALOR VENDA", "VALOR_VENDA")
v_valor_total = find_col(vendas, "VALOR TOTAL", "VALOR_TOTAL", "TOTAL")
v_media_custo = find_col(vendas, "MEDIA CUSTO UNITARIO", "MEDIA C. UNITARIO", "CUSTO UNIT")
v_lucro = find_col(vendas, "LUCRO")

# COMPRAS: DATA, PRODUTO, STATUS, QUANTIDADE, CUSTO UNITÁRIO, CUSTO TOTAL, OBSERVAÇÃO
c_data = find_col(compras, "DATA")
c_prod = find_col(compras, "PRODUTO")
c_qtd = find_col(compras, "QUANTIDADE", "QTD", "QUANT")
c_custo_unit = find_col(compras, "CUSTO UNITÁRIO", "CUSTO UNIT")
c_custo_total = find_col(compras, "CUSTO TOTAL", "VALOR TOTAL", "TOTAL")

# Mostrar diagnóstico rápido no topo (colunas detectadas)
with st.expander("🔍 Diagnóstico rápido (colunas detectadas)"):
    st.write("ESTOQUE:", list(estoque.columns) if estoque is not None else "não carregada")
    st.write("VENDAS:", list(vendas.columns) if vendas is not None else "não carregada")
    st.write("COMPRAS:", list(compras.columns) if compras is not None else "não carregada")
    st.write("Mapeamento usado:")
    st.write({
        "ESTOQUE": {"PROD": e_prod, "QTD": e_qtd, "VAL_UNIT_ESTOQUE": e_valor_unit},
        "VENDAS": {"DATA": v_data, "PROD": v_prod, "QTD": v_qtd, "VAL_UNIT_VENDA": v_valor_unit, "VAL_TOTAL": v_valor_total, "MEDIA_CUSTO": v_media_custo, "LUCRO": v_lucro},
        "COMPRAS": {"DATA": c_data, "PROD": c_prod, "QTD": c_qtd, "CUSTO_UNIT": c_custo_unit, "CUSTO_TOTAL": c_custo_total}
    })

# -------------------------
# Preparar dados: garantir colunas numéricas e datas
# -------------------------
# Vendas: parse data, numeric cols
if vendas is not None:
    if v_data in vendas.columns:
        vendas[v_data] = pd.to_datetime(vendas[v_data], errors="coerce")
    # compute VALOR TOTAL if absent
    if v_valor_total not in (vendas.columns if vendas is not None else []):
        if v_valor_unit in (vendas.columns if vendas is not None else []) and v_qtd in (vendas.columns if vendas is not None else []):
            vendas["_VAL_TOTAL_CALC"] = to_num(vendas[v_valor_unit]) * to_num(vendas[v_qtd])
            v_valor_total = "_VAL_TOTAL_CALC"
            vendas[v_valor_total] = vendas[v_valor_total]
    # ensure lucro column: if not present, try calculate using media custo or estoque mapping
    if v_lucro not in (vendas.columns if vendas is not None else []):
        # try to compute
        vendas["_VAL_UNIT_NUM"] = to_num(vendas[v_valor_unit]) if v_valor_unit in vendas.columns else 0
        vendas["_QTD_NUM"] = to_num(vendas[v_qtd]) if v_qtd in vendas.columns else 0
        custo_used = None
        if v_media_custo in (vendas.columns if vendas is not None else []):
            vendas["_CUSTO_UNIT_NUM"] = to_num(vendas[v_media_custo])
            custo_used = "_CUSTO_UNIT_NUM"
        elif estoque is not None and e_prod and e_valor_unit and e_valor_unit in estoque.columns:
            # map from estoque Media C. UNITARIO if exists there
            # try to find 'Media C. UNITARIO' in estoque columns
            e_media = find_col(estoque, "Media C. UNITARIO", "MEDIA C. UNITARIO", "MEDIA C")
            if e_media and e_media in estoque.columns:
                map_media = estoque[[e_prod, e_media]].dropna()
                try:
                    map_media[e_prod] = map_media[e_prod].astype(str).str.strip()
                    mapa = map_media.set_index(e_prod)[e_media].to_dict()
                    vendas["_CUSTO_UNIT_NUM"] = vendas[v_prod].astype(str).str.strip().map(mapa).fillna(0)
                    custo_used = "_CUSTO_UNIT_NUM"
                except Exception:
                    custo_used = None
        # fallback: 0 cost
        if custo_used is None:
            vendas["_CUSTO_UNIT_NUM"] = 0
            custo_used = "_CUSTO_UNIT_NUM"
        vendas["_LUCRO_CALC"] = (vendas["_VAL_UNIT_NUM"].fillna(0) - vendas["_CUSTO_UNIT_NUM"].fillna(0)) * vendas["_QTD_NUM"].fillna(0)
        v_lucro = "_LUCRO_CALC"
        vendas[v_lucro] = vendas["_LUCRO_CALC"]

# Compras: numeric
if compras is not None:
    if c_custo_total in (compras.columns if compras is not None else []):
        compras[c_custo_total] = to_num(compras[c_custo_total])
    if c_custo_unit in (compras.columns if compras is not None else []):
        compras[c_custo_unit] = to_num(compras[c_custo_unit])
    if c_data in (compras.columns if compras is not None else []):
        compras[c_data] = pd.to_datetime(compras[c_data], errors="coerce")

# Estoque: numeric
if estoque is not None:
    if e_qtd in (estoque.columns if estoque is not None else []):
        estoque[e_qtd] = to_num(estoque[e_qtd])
    # Valor unitario vendas (Valor Venda Sugerido) numeric
    if e_valor_unit in (estoque.columns if estoque is not None else []):
        estoque[e_valor_unit] = to_num(estoque[e_valor_unit])

# -------------------------
# Sidebar filters: período (vendas) e produtos
# -------------------------
st.sidebar.header("Filtros")
# Date range filter (based on vendas date)
if vendas is not None and v_data in vendas.columns:
    min_date = vendas[v_data].min()
    max_date = vendas[v_data].max()
    date_range = st.sidebar.date_input("Período (Vendas)", value=(min_date.date() if pd.notna(min_date) else None, max_date.date() if pd.notna(max_date) else None))
else:
    date_range = None

# Product filter (all products from vendas + estoque)
prod_list = set()
if vendas is not None and v_prod in (vendas.columns if vendas is not None else []):
    prod_list.update(vendas[v_prod].dropna().astype(str).unique())
if estoque is not None and e_prod in (estoque.columns if estoque is not None else []):
    prod_list.update(estoque[e_prod].dropna().astype(str).unique())
prod_list = sorted([p for p in prod_list if str(p).strip() != ""])
prod_choice = st.sidebar.multiselect("Produtos (filtrar)", options=prod_list, default=prod_list)

st.sidebar.markdown("---")
st.sidebar.caption("Filtre por período e produto para recalcular KPIs e gráficos.")

# Apply filters to vendas dataset
vendas_filtered = vendas.copy() if vendas is not None else pd.DataFrame()
if date_range and isinstance(date_range, (list, tuple)) and len(date_range) == 2 and v_data in (vendas.columns if vendas is not None else []):
    dfrom, dto = date_range
    try:
        vendas_filtered = vendas_filtered[(vendas_filtered[v_data].dt.date >= dfrom) & (vendas_filtered[v_data].dt.date <= dto)]
    except Exception:
        # ignore filter if fails
        pass
if prod_choice:
    vendas_filtered = vendas_filtered[vendas_filtered[v_prod].astype(str).isin(prod_choice)]

# -------------------------
# KPIs recalculados no período filtrado
# -------------------------
total_vendido_period = vendas_filtered[v_valor_total].sum() if v_valor_total in vendas_filtered.columns else 0
lucro_period = vendas_filtered[v_lucro].sum() if v_lucro in vendas_filtered.columns else 0

# Stock total value: use 'Valor Venda Sugerido' as unit price
valor_total_estoque = 0
if estoque is not None and e_qtd in (estoque.columns if estoque is not None else []) and e_valor_unit in (estoque.columns if estoque is not None else []):
    estoque["_ESTOQUE_VALOR_TOTAL"] = to_num(estoque[e_qtd]) * to_num(estoque[e_valor_unit])
    valor_total_estoque = estoque["_ESTOQUE_VALOR_TOTAL"].sum()
else:
    # fallback: 0
    valor_total_estoque = 0

# display KPIs
k1, k2, k3 = st.columns([1,1,1])
k1.metric("💰 Vendido no Período", fmt_brl(total_vendido_period))
k2.metric("📈 Lucro no Período", fmt_brl(lucro_period))
k3.metric("📦 Valor Total do Estoque", fmt_brl(valor_total_estoque))

st.markdown("---")

# -------------------------
# Top 10 produtos mais vendidos (no período/filtro)
# -------------------------
st.subheader("🏆 Top 10 Produtos Mais Vendidos (período selecionado)")
if v_prod in (vendas_filtered.columns if vendas_filtered is not None else []) and v_qtd in (vendas_filtered.columns if vendas_filtered is not None else []):
    top = vendas_filtered.groupby(v_prod).agg(
        QTDE_SOMADA=(v_qtd, lambda s: to_num(s).sum()),
        VAL_TOTAL=(v_valor_total, lambda s: to_num(s).sum() if v_valor_total in vendas_filtered.columns else (to_num(vendas_filtered[v_valor_unit]) * to_num(vendas_filtered[v_qtd])).groupby(vendas_filtered[v_prod]).sum())
    ).reset_index()
    # if VAL_TOTAL column ended up being a Series of dict (due to lambda), ensure numeric
    if "VAL_TOTAL" in top.columns:
        top["VAL_TOTAL"] = to_num(top["VAL_TOTAL"])
    top = top.sort_values("VAL_TOTAL", ascending=False).head(10)
    # show bar chart horizontal with annotations
    if not top.empty:
        fig_top = px.bar(top, x="VAL_TOTAL", y=v_prod, orientation="h",
                         text="QTDE_SOMADA", title="Top 10 por Valor (mostra qtd à direita)",
                         color="VAL_TOTAL", color_continuous_scale="YlOrBr")
        fig_top.update_traces(texttemplate='%{text:.0f} un', textposition='outside')
        fig_top.update_layout(yaxis={'categoryorder':'total ascending'}, plot_bgcolor="#0b0b0b", paper_bgcolor="#0b0b0b", font_color="#E8C36A")
        st.plotly_chart(fig_top, use_container_width=True)
        # show table with formatted values
        top_display = top.copy()
        top_display["VAL_TOTAL"] = top_display["VAL_TOTAL"].apply(fmt_brl)
        top_display["QTDE_SOMADA"] = top_display["QTDE_SOMADA"].astype(int)
        st.table(top_display[[v_prod, "QTDE_SOMADA", "VAL_TOTAL"]].rename(columns={v_prod:"PRODUTO","QTDE_SOMADA":"QUANTIDADE","VAL_TOTAL":"VALOR TOTAL"}))
    else:
        st.info("Nenhuma venda encontrada no período/filtragem selecionada.")
else:
    st.warning("Colunas de produto/quantidade não encontradas em VENDAS. Verifique no Diagnóstico.")

st.markdown("---")

# -------------------------
# Controle de Estoque Atual (tabela + gráfico)
# -------------------------
st.subheader("📦 Estoque Atual")
if estoque is not None and e_prod in (estoque.columns if estoque is not None else []) and e_qtd in (estoque.columns if estoque is not None else []):
    # create value column if not yet created
    if "_ESTOQUE_VALOR_TOTAL" not in estoque.columns and e_valor_unit in (estoque.columns if estoque is not None else []):
        estoque["_ESTOQUE_VALOR_TOTAL"] = to_num(estoque[e_qtd]) * to_num(estoque[e_valor_unit])
    est_view = estoque[[e_prod, e_qtd, e_valor_unit, "_ESTOQUE_VALOR_TOTAL"]].copy() if e_valor_unit in (estoque.columns if estoque is not None else []) else estoque[[e_prod, e_qtd]].copy()
    est_view.columns = ["PRODUTO", "QUANTIDADE", "PREÇO UNIT (VENDA)","VALOR TOTAL ESTOQUE"] if e_valor_unit in (estoque.columns if estoque is not None else []) else ["PRODUTO","QUANTIDADE"]
    # sort by quantity descending
    est_view = est_view.sort_values("QUANTIDADE", ascending=False)
    # show top N or full depending on size
    st.dataframe(est_view.head(200))
    # chart top 15 by quantity
    top_est = est_view.sort_values("QUANTIDADE", ascending=False).head(15)
    if not top_est.empty:
        fig_e = px.bar(top_est, x="PRODUTO", y="QUANTIDADE", title="Top 15 Estoque (quantidade)", color="QUANTIDADE", color_continuous_scale="YlOrBr")
        fig_e.update_layout(plot_bgcolor="#0b0b0b", paper_bgcolor="#0b0b0b", font_color="#E8C36A")
        st.plotly_chart(fig_e, use_container_width=True)
else:
    st.warning("Aba ESTOQUE ou colunas necessárias não encontradas. Verifique no Diagnóstico.")

st.markdown("---")

# -------------------------
# Vendas no mês (resumo mensal) e lucro mensal (gráfico)
# -------------------------
st.subheader("📅 Vendas & Lucro por Mês")
if vendas is not None and v_data in (vendas.columns if vendas is not None else []):
    tmp = vendas.copy()
    tmp[v_data] = pd.to_datetime(tmp[v_data], errors="coerce")
    tmp["_MES"] = tmp[v_data].dt.to_period("M").astype(str)
    # total por mes
    if v_valor_total in tmp.columns:
        vendas_mes = tmp.groupby("_MES")[v_valor_total].sum().reset_index()
    else:
        # compute if necessary
        tmp["_VAL_TOTAL"] = to_num(tmp[v_valor_unit]) * to_num(tmp[v_qtd]) if v_valor_unit in tmp.columns and v_qtd in tmp.columns else 0
        vendas_mes = tmp.groupby("_MES")["_VAL_TOTAL"].sum().reset_index().rename(columns={"_VAL_TOTAL": "VALOR"})

    # lucro por mes (usar LUCRO da planilha se existir)
    if v_lucro in tmp.columns:
        lucro_mes = tmp.groupby("_MES")[v_lucro].sum().reset_index()
    else:
        # try using computed _LUCRO_CALC if present
        if "_LUCRO_CALC" in tmp.columns:
            lucro_mes = tmp.groupby("_MES")["_LUCRO_CALC"].sum().reset_index().rename(columns={"_LUCRO_CALC":"LUCRO"})
        else:
            lucro_mes = pd.DataFrame()

    fig_vmes = px.bar(vendas_mes, x=vendas_mes.columns[0], y=vendas_mes.columns[1], title="Vendas Mensais", color=vendas_mes.columns[1], color_continuous_scale="YlOrBr")
    fig_vmes.update_layout(plot_bgcolor="#0b0b0b", paper_bgcolor="#0b0b0b", font_color="#E8C36A")
    st.plotly_chart(fig_vmes, use_container_width=True)

    if not lucro_mes.empty:
        fig_lm = px.line(lucro_mes, x=lucro_mes.columns[0], y=lucro_mes.columns[1], title="Lucro Mensal", markers=True)
        fig_lm.update_traces(line=dict(color="#E8C36A"))
        fig_lm.update_layout(plot_bgcolor="#0b0b0b", paper_bgcolor="#0b0b0b", font_color="#E8C36A")
        st.plotly_chart(fig_lm, use_container_width=True)
else:
    st.info("Coluna DATA não encontrada em VENDAS para análise mensal.")

# -------------------------
# Diagnóstico final
# -------------------------
with st.expander("🔧 Diagnóstico completo"):
    st.write("Colunas mapeadas:")
    st.write({
        "ESTOQUE": [e_prod, e_qtd, e_valor_unit],
        "VENDAS": [v_data, v_prod, v_qtd, v_valor_unit, v_valor_total, v_media_custo, v_lucro],
        "COMPRAS": [c_data, c_prod, c_qtd, c_custo_unit, c_custo_total]
    })
    st.write("Amostra VENDAS (10 linhas):")
    if vendas is not None:
        st.dataframe(vendas.head(10))
    st.write("Amostra ESTOQUE (10 linhas):")
    if estoque is not None:
        st.dataframe(estoque.head(10))
    st.write("Amostra COMPRAS (10 linhas):")
    if compras is not None:
        st.dataframe(compras.head(10))

st.caption("Dashboard gerado em Streamlit • Controle de estoque & vendas — Tema: Dark + Dourado")
