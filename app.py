# ================================================
# app.py – VERSÃO CORRIGIDA (detecção automática PRODUTO/QTD)
# Loja Importados – Dashboard Dark Roxo
# ================================================

import streamlit as st
import pandas as pd
import plotly.express as px
import re
from datetime import datetime, timedelta
import requests
from io import BytesIO

# -------------------------
# Config
# -------------------------
st.set_page_config(page_title="Loja Importados – Dashboard", layout="wide")
URL_PLANILHA = "https://docs.google.com/spreadsheets/d/1TsRjsfw1TVfeEWBBvhKvsGQ5YUCktn2b/export?format=xlsx"

# -------------------------
# CSS
# -------------------------
st.markdown("""
<style>
:root{--bg:#0b0b0b;--card:#141414;--accent:#8b5cf6;--accent2:#a78bfa;--text:#f2f2f2;}
body, .stApp { background:var(--bg) !important; color:var(--text) !important; font-family: Inter; }
.kpi-box{ background:var(--card); padding:14px 18px; border-radius:14px; border-left:5px solid var(--accent); box-shadow:0 4px 14px rgba(0,0,0,0.45); }
.dataframe tbody tr td{ color:white !important; }
</style>
""", unsafe_allow_html=True)

# -------------------------
# Helpers
# -------------------------
def baixar_planilha(url):
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    return pd.ExcelFile(BytesIO(r.content))

def limpar_moeda(x):
    if pd.isna(x): return 0.0
    s = str(x)
    s = s.replace("R$","").replace(".","").replace(",",".")
    s = re.sub(r"[^0-9.\-]","",s)
    try: return float(s)
    except: return 0.0

def formatar_reais(v):
    try:
        v = float(v)
    except:
        return "R$ 0"
    return f"R$ {v:,.0f}".replace(",", ".")

def aplicar_tema_dark(fig):
    fig.update_layout(plot_bgcolor="#0b0b0b", paper_bgcolor="#0b0b0b", font_color="#f2f2f2")
    return fig

def detectar_coluna_por_nome(df, candidatos):
    """Retorna o nome da primeira coluna do df que contém qualquer string em candidatos (case-insensitive)."""
    if df is None or df.empty: return None
    cols = list(df.columns)
    for c in cols:
        cu = str(c).upper()
        for cand in candidatos:
            if cand.upper() in cu:
                return c
    return None

def detectar_coluna_produto(df):
    candidatos = ["PRODUTO","PROD","PRODUCT","ITEM","NOME","DESCRI","DESC","TITLE"]
    col = detectar_coluna_por_nome(df, candidatos)
    if col: return col
    # fallback: primeira coluna string/object que não seja data/valor
    for c in df.columns:
        if df[c].dtype == object:
            return c
    return None

def detectar_coluna_qtd(df):
    candidatos = ["QTD","QUANT","QTY","QTD_VENDA","QUANTITY","UNIDADES"]
    col = detectar_coluna_por_nome(df, candidatos)
    if col: return col
    # fallback: any numeric integer-like column that's not a date/price
    for c in df.columns:
        if pd.api.types.is_integer_dtype(df[c]) or pd.api.types.is_float_dtype(df[c]):
            # ignore if looks like money (contains many decimals and large values?) - cannot be perfect
            return c
    return None

def detectar_coluna_valor_unitario(df):
    candidatos = ["VALORVENDA","VALOR VENDA","VALOR","PRECO","PRICE","UNIT"]
    return detectar_coluna_por_nome(df, candidatos)

def detectar_coluna_valor_total(df):
    candidatos = ["VALOR TOTAL","VALOR_TOTAL","TOTAL","VALORTOTAL"]
    return detectar_coluna_por_nome(df, candidatos)

# -------------------------
# Carregar planilha
# -------------------------
try:
    xls = baixar_planilha(URL_PLANILHA)
except Exception as e:
    st.error("Erro ao carregar planilha:")
    st.exception(e)
    st.stop()

dfs = {}
for aba in ["VENDAS","COMPRAS","ESTOQUE"]:
    if aba in xls.sheet_names:
        dfs[aba] = pd.read_excel(xls, aba)

# -------------------------
# Preprocess VENDAS (robusto)
# -------------------------
if "VENDAS" in dfs:
    vendas = dfs["VENDAS"].copy()

    # detectar DATA
    col_data = detectar_coluna_por_nome(vendas, ["DATA","DT","DIA","DATE"])
    if col_data is None:
        # tentar inferir por conversão de primeira coluna
        for c in vendas.columns:
            try:
                teste = pd.to_datetime(vendas[c], errors="coerce")
                if teste.notna().sum() > 0:
                    col_data = c
                    break
            except:
                pass
    if col_data:
        vendas = vendas.rename(columns={col_data: "DATA"})
        vendas["DATA"] = pd.to_datetime(vendas["DATA"], errors="coerce")
    else:
        # cria coluna vazia para evitar crashes - mas avisamos
        vendas["DATA"] = pd.NaT
        st.warning("Atenção: não detectei coluna de DATA em VENDAS; algumas visualizações usarão o histórico, se houver.")

    # detectar produto e qtd e valores
    prod_col = detectar_coluna_produto(vendas)
    qtd_col = detectar_coluna_qtd(vendas)
    unit_col = detectar_coluna_valor_unitario(vendas)
    total_col = detectar_coluna_valor_total(vendas)

    # normalizar QTD
    if qtd_col:
        try:
            vendas["QTD"] = pd.to_numeric(vendas[qtd_col], errors="coerce").fillna(0).astype(int)
        except:
            vendas["QTD"] = pd.to_numeric(vendas[qtd_col].astype(str).str.replace(",","."), errors="coerce").fillna(0).astype(int)
    else:
        vendas["QTD"] = 0

    # normalizar valores
    if total_col:
        vendas["VALOR_TOTAL_DETECT"] = vendas[total_col].map(limpar_moeda)
    else:
        vendas["VALOR_TOTAL_DETECT"] = pd.NA

    if unit_col:
        vendas["VALOR_UNIT_DETECT"] = vendas[unit_col].map(limpar_moeda)
    else:
        vendas["VALOR_UNIT_DETECT"] = pd.NA

    # criar VALOR TOTAL definitivo
    if vendas["VALOR_TOTAL_DETECT"].notna().any():
        vendas["VALOR TOTAL"] = vendas["VALOR_TOTAL_DETECT"].fillna(0)
    elif "VALOR_UNIT_DETECT" in vendas.columns and vendas["VALOR_UNIT_DETECT"].notna().any():
        vendas["VALOR TOTAL"] = vendas["VALOR_UNIT_DETECT"].fillna(0) * vendas["QTD"].fillna(0)
    else:
        vendas["VALOR TOTAL"] = 0.0

    # garantir coluna PRODUTO com nome padronizado
    if prod_col:
        vendas = vendas.rename(columns={prod_col: "PRODUTO"})
    else:
        # tentar encontrar primeira coluna string
        possible = None
        for c in vendas.columns:
            if vendas[c].dtype == object:
                possible = c
                break
        if possible:
            vendas = vendas.rename(columns={possible: "PRODUTO"})
        else:
            vendas["PRODUTO"] = "SEM_PRODUTO_DETECTADO"
            st.warning("Nenhuma coluna de PRODUTO detectada; exibir como 'SEM_PRODUTO_DETECTADO'.")

    # mes_ano
    vendas["MES_ANO"] = vendas["DATA"].dt.strftime("%Y-%m")
else:
    vendas = pd.DataFrame()

# -------------------------
# Preprocess COMPRAS (simples)
# -------------------------
if "COMPRAS" in dfs:
    compras = dfs["COMPRAS"].copy()
    col_data_c = detectar_coluna_por_nome(compras, ["DATA","DT","DIA"])
    if col_data_c:
        compras = compras.rename(columns={col_data_c: "DATA"})
        compras["DATA"] = pd.to_datetime(compras["DATA"], errors="coerce")
    # custo e qtd
    col_custo_c = detectar_coluna_por_nome(compras, ["CUSTO","PRECO","VALOR","UNIT"])
    col_qtd_c = detectar_coluna_por_nome(compras, ["QTD","QUANT","QTY"])
    compras["CUSTO_UNIT"] = compras[col_custo_c].map(limpar_moeda) if col_custo_c else 0
    compras["QUANTIDADE"] = compras[col_qtd_c].fillna(0).astype(int) if col_qtd_c else 0
    compras["CUSTO TOTAL"] = compras["CUSTO_UNIT"] * compras["QUANTIDADE"]
    compras["MES_ANO"] = compras["DATA"].dt.strftime("%Y-%m") if "DATA" in compras else pd.NA
else:
    compras = pd.DataFrame()

# -------------------------
# Preprocess ESTOQUE (simples)
# -------------------------
if "ESTOQUE" in dfs:
    estoque = dfs["ESTOQUE"].copy()
    col_prod_e = detectar_coluna_produto(estoque)
    if col_prod_e:
        estoque = estoque.rename(columns={col_prod_e: "PRODUTO"})
    col_qtd_e = detectar_coluna_por_nome(estoque, ["ESTOQUE","QTD","QUANT"])
    estoque["EM_ESTOQUE"] = estoque[col_qtd_e].fillna(0).astype(int) if col_qtd_e else 0
    col_custo_e = detectar_coluna_por_nome(estoque, ["CUSTO","PRECO","VALOR","UNIT"])
    estoque["CUSTO_UNIT"] = estoque[col_custo_e].map(limpar_moeda) if col_custo_e else 0
    col_venda_e = detectar_coluna_por_nome(estoque, ["VENDA","PRECO","VALOR","PRICE"])
    estoque["PRECO_VENDA"] = estoque[col_venda_e].map(limpar_moeda) if col_venda_e else 0
    estoque["VALOR_CUSTO_TOTAL"] = estoque["CUSTO_UNIT"] * estoque["EM_ESTOQUE"]
    estoque["VALOR_VENDA_TOTAL"] = estoque["PRECO_VENDA"] * estoque["EM_ESTOQUE"]
else:
    estoque = pd.DataFrame()

# -------------------------
# Filtro mês
# -------------------------
meses = ["Todos"]
if not vendas.empty:
    meses += sorted(vendas["MES_ANO"].dropna().unique().tolist(), reverse=True)
mes_padrao = datetime.now().strftime("%Y-%m")
idx = meses.index(mes_padrao) if mes_padrao in meses else 0
mes_selecionado = st.selectbox("Filtrar por mês (YYYY-MM):", meses, index=idx)

def filtrar_mes(df, mes):
    if df is None or df.empty: return pd.DataFrame()
    if mes == "Todos": return df
    if "MES_ANO" in df.columns:
        return df[df["MES_ANO"] == mes].copy()
    return df

vendas_filtradas = filtrar_mes(vendas, mes_selecionado)
compras_filtradas = filtrar_mes(compras, mes_selecionado)

# -------------------------
# KPIs
# -------------------------
total_vendido = vendas_filtradas["VALOR TOTAL"].sum() if not vendas_filtradas.empty else 0
total_qtd = vendas_filtradas["QTD"].sum() if not vendas_filtradas.empty else 0
total_compras = compras_filtradas["CUSTO TOTAL"].sum() if not compras_filtradas.empty else 0
valor_venda_estoque = estoque["VALOR_VENDA_TOTAL"].sum() if not estoque.empty else 0
valor_custo_estoque = estoque["VALOR_CUSTO_TOTAL"].sum() if not estoque.empty else 0

c1,c2,c3,c4,c5 = st.columns(5)
c1.markdown(f"<div class='kpi-box'><h4>💵 Total Vendido</h4><h2>{formatar_reais(total_vendido)}</h2></div>", unsafe_allow_html=True)
c2.markdown(f"<div class='kpi-box'><h4>📦 Qtde Vendida</h4><h2>{int(total_qtd)}</h2></div>", unsafe_allow_html=True)
c3.markdown(f"<div class='kpi-box'><h4>💸 Compras</h4><h2>{formatar_reais(total_compras)}</h2></div>", unsafe_allow_html=True)
c4.markdown(f"<div class='kpi-box'><h4>🏷 Estoque Venda</h4><h2>{formatar_reais(valor_venda_estoque)}</h2></div>", unsafe_allow_html=True)
c5.markdown(f"<div class='kpi-box'><h4>📥 Estoque Custo</h4><h2>{formatar_reais(valor_custo_estoque)}</h2></div>", unsafe_allow_html=True)

# -------------------------
# Abas (sem TOP10)
# -------------------------
tab_vendas, tab_estoque, tab_pesquisar = st.tabs(["🛒 VENDAS", "📦 ESTOQUE", "🔍 PESQUISAR"])

# -------------------------
# ABA VENDAS (Top5 + Semanal + Tabela)
# -------------------------
with tab_vendas:
    st.subheader("Vendas — Top 5 produtos (últimos 90 dias)")

    # garantir colunas existentes
    prod_col_name = "PRODUTO" if "PRODUTO" in vendas.columns else None
    qtd_col_name = "QTD" if "QTD" in vendas.columns else None

    # construir histórico dos últimos 90 dias
    if not vendas.empty and prod_col_name and qtd_col_name:
        cutoff = datetime.now() - timedelta(days=90)
        df_hist = vendas.copy()
        if "DATA" in df_hist.columns:
            df_hist = df_hist[df_hist["DATA"] >= cutoff]
        # agrupar - proteção extra
        if prod_col_name in df_hist.columns and qtd_col_name in df_hist.columns:
            top5 = df_hist.groupby("PRODUTO", dropna=False)["QTD"].sum().reset_index().sort_values("QTD", ascending=False).head(5)
            if not top5.empty:
                fig_top5 = px.bar(top5, x="QTD", y="PRODUTO", orientation="h", text="QTD", color_discrete_sequence=["#8b5cf6"], height=380)
                fig_top5.update_traces(textposition="inside")
                aplicar_tema_dark(fig_top5)
                st.plotly_chart(fig_top5, use_container_width=True, config={"displayModeBar": False})
            else:
                st.info("Não há vendas nos últimos 90 dias.")
        else:
            st.warning("Não foi possível identificar colunas PRODUTO e/ou QTD para calcular Top 5.")
    else:
        st.warning("Dados insuficientes para calcular Top 5 (verifique se há colunas de produto e quantidade).")

    # Faturamento semanal (usando vendas_filtradas)
    st.markdown("### 📅 Faturamento Semanal")
    if vendas_filtradas.empty or "DATA" not in vendas_filtradas.columns:
        st.info("Sem dados para gráfico semanal.")
    else:
        df_sem = vendas_filtradas.copy()
        df_sem["DATA"] = pd.to_datetime(df_sem["DATA"], errors="coerce")
        df_sem = df_sem.dropna(subset=["DATA"])
        if df_sem.empty:
            st.info("Sem dados com DATA válidos para o período.")
        else:
            df_sem["SEMANA"] = df_sem["DATA"].dt.isocalendar().week
            df_sem["ANO"] = df_sem["DATA"].dt.year
            df_week = df_sem.groupby(["ANO","SEMANA"], dropna=False)["VALOR TOTAL"].sum().reset_index()
            def intervalo_sem(row):
                try:
                    ini = datetime.fromisocalendar(int(row["ANO"]), int(row["SEMANA"]), 1)
                    fim = ini + timedelta(days=6)
                    return f"{ini.strftime('%d/%m')} → {fim.strftime('%d/%m')}"
                except:
                    return "N/A"
            df_week["INTERVALO"] = df_week.apply(intervalo_sem, axis=1)
            df_week["LABEL"] = df_week["VALOR TOTAL"].apply(formatar_reais)
            fig_week = px.bar(df_week, x="INTERVALO", y="VALOR TOTAL", text="LABEL", color_discrete_sequence=["#8b5cf6"], height=380)
            fig_week.update_traces(textposition="inside")
            aplicar_tema_dark(fig_week)
            st.plotly_chart(fig_week, use_container_width=True, config={"displayModeBar": False})

    st.markdown("### 📄 Tabela de Vendas (últimas entradas)")
    if vendas_filtradas.empty:
        st.info("Sem vendas para exibir.")
    else:
        # exibir colunas úteis sem explodir
        display_cols = [c for c in ["DATA","PRODUTO","QTD","VALOR TOTAL"] if c in vendas_filtradas.columns]
        st.dataframe(vendas_filtradas[display_cols].sort_values("DATA", ascending=False).reset_index(drop=True), use_container_width=True)

# -------------------------
# ABA ESTOQUE
# -------------------------
with tab_estoque:
    st.subheader("Estoque")
    if estoque.empty:
        st.info("Nenhum dado de estoque.")
    else:
        df_e = estoque.copy()
        if "PRODUTO" not in df_e.columns:
            st.warning("Estoque sem coluna PRODUTO identificada.")
        st.dataframe(df_e.sort_values("EM_ESTOQUE", ascending=False).reset_index(drop=True), use_container_width=True)

# -------------------------
# ABA PESQUISAR
# -------------------------
with tab_pesquisar:
    st.subheader("Pesquisar produto no estoque")
    termo = st.text_input("Digite parte do nome do produto:")
    if termo:
        if estoque.empty or "PRODUTO" not in estoque.columns:
            st.warning("Sem dados de estoque ou coluna PRODUTO ausente.")
        else:
            resultado = estoque[estoque["PRODUTO"].astype(str).str.contains(termo, case=False, na=False)]
            if resultado.empty:
                st.info("Nenhum produto encontrado.")
            else:
                st.dataframe(resultado.reset_index(drop=True), use_container_width=True)
