# app.py — Dashboard final completo
import streamlit as st
import pandas as pd
import plotly.express as px
import re

st.set_page_config(page_title="Loja Importados – Dashboard", layout="wide")

# ----------------------------
# LINK FIXO (XLSX com múltiplas abas)
# ----------------------------
URL_PLANILHA = "https://docs.google.com/spreadsheets/d/1TsRjsfw1TVfeEWBBvhKvsGQ5YUCktn2b/export?format=xlsx"

# ----------------------------
# VISUAL
# ----------------------------
st.markdown(
    """
    <style>
      :root { --gold:#FFD700; }
      body, .stApp { background-color:#0b0b0b; color:#EEE; }
      h1,h2,h3,h4 { color: var(--gold); }
    </style>
    """,
    unsafe_allow_html=True,
)
st.title("📊 Loja Importados — Dashboard")

# ----------------------------
# FUNÇÕES DE PARSE
# ----------------------------
def parse_money_value(x):
    try:
        if pd.isna(x):
            return float("nan")
    except:
        pass
    s = str(x).strip()
    if s == "" or s.lower() == "nan":
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
        return float(s) if s not in ("", ".", "-") else float("nan")
    except:
        return float("nan")

def parse_money_series(serie):
    return serie.astype(str).map(lambda x: parse_money_value(x)).astype("float64")

def parse_int_series(serie):
    def to_int(x):
        try:
            if pd.isna(x):
                return pd.NA
        except:
            pass
        s = str(x)
        s = re.sub(r"[^\d\-]", "", s)
        if s == "" or s == "-" or s.lower() == "nan":
            return pd.NA
        try:
            return int(float(s))
        except:
            return pd.NA
    return serie.map(to_int).astype("Int64")

# ----------------------------
# CABEÇALHO / LIMPEZA
# ----------------------------
def detectar_linha_cabecalho(df_raw, chave):
    linha_cab = None
    for i in range(len(df_raw)):
        linha = df_raw.iloc[i].astype(str).str.upper().tolist()
        if chave in " ".join(linha):
            linha_cab = i
            break
    return linha_cab

def limpar_aba_raw(df_raw, nome_aba):
    busca = "PRODUTO" if nome_aba not in ("VENDAS", "COMPRAS") else "DATA"
    linha = detectar_linha_cabecalho(df_raw, busca)
    if linha is None:
        return None
    df_raw.columns = df_raw.iloc[linha]
    df = df_raw.iloc[linha+1:].copy()
    df = df.loc[:, ~df.columns.astype(str).str.contains("Unnamed")]
    df = df.reset_index(drop=True)
    df.columns = [str(c).strip() for c in df.columns]
    return df

# ----------------------------
# CARREGAR XLSX E ABAS
# ----------------------------
try:
    xls = pd.ExcelFile(URL_PLANILHA)
except Exception as e:
    st.error("Erro ao carregar planilha XLSX do Google Drive.")
    st.code(str(e))
    st.stop()

abas_all = [a for a in xls.sheet_names if a.upper() != "EXCELENTEJOAO"]

colunas_esperadas = {
    "ESTOQUE": ["PRODUTO", "EM ESTOQUE", "COMPRAS", "Media C. UNITARIO", "Valor Venda Sugerido", "VENDAS"],
    "VENDAS": ["DATA", "PRODUTO", "QTD", "VALOR VENDA", "VALOR TOTAL", "MEDIA CUSTO UNITARIO",
               "LUCRO UNITARIO", "MAKEUP", "% DE LUCRO SOBRE CUSTO", "STATUS", "CLIENTE", "OBS"],
    "COMPRAS": ["DATA", "PRODUTO", "STATUS", "QUANTIDADE", "CUSTO UNITÁRIO", "CUSTO TOTAL"]
}

dfs = {}
for aba in colunas_esperadas.keys():
    if aba not in abas_all:
        continue
    bruto = pd.read_excel(URL_PLANILHA, sheet_name=aba, header=None)
    limpo = limpar_aba_raw(bruto, aba)
    if limpo is None:
        st.warning(f"Aba {aba}: cabeçalho não encontrado corretamente — pulando.")
        continue
    dfs[aba] = limpo

# ----------------------------
# CONVERSÃO CAMPOS
# ----------------------------
# Estoque
if "ESTOQUE" in dfs:
    df_e = dfs["ESTOQUE"]
    if "Media C. UNITARIO" in df_e.columns:
        df_e["Media C. UNITARIO"] = parse_money_series(df_e["Media C. UNITARIO"])
    if "Valor Venda Sugerido" in df_e.columns:
        df_e["Valor Venda Sugerido"] = parse_money_series(df_e["Valor Venda Sugerido"])
    for col in ["EM ESTOQUE","VENDAS","COMPRAS"]:
        if col in df_e.columns:
            df_e[col] = parse_int_series(df_e[col]).fillna(0)
    dfs["ESTOQUE"] = df_e

# Vendas
if "VENDAS" in dfs:
    df_v = dfs["VENDAS"]
    for col in ["VALOR VENDA","VALOR TOTAL","MEDIA CUSTO UNITARIO","LUCRO UNITARIO"]:
        if col in df_v.columns:
            df_v[col] = parse_money_series(df_v[col])
    if "QTD" in df_v.columns:
        df_v["QTD"] = parse_int_series(df_v["QTD"]).fillna(0)
    if "DATA" in df_v.columns:
        df_v["DATA"] = pd.to_datetime(df_v["DATA"], errors="coerce")
        df_v["MES_ANO"] = df_v["DATA"].dt.strftime("%Y-%m")
    else:
        df_v["MES_ANO"] = pd.NA
    dfs["VENDAS"] = df_v

# Compras
if "COMPRAS" in dfs:
    df_c = dfs["COMPRAS"]
    if "QUANTIDADE" in df_c.columns:
        df_c["QUANTIDADE"] = parse_int_series(df_c["QUANTIDADE"]).fillna(0)
    if "CUSTO UNITÁRIO" in df_c.columns:
        df_c["CUSTO UNITÁRIO"] = parse_money_series(df_c["CUSTO UNITÁRIO"]).fillna(0.0)
    if "QUANTIDADE" in df_c.columns and "CUSTO UNITÁRIO" in df_c.columns:
        df_c["CUSTO TOTAL (RECALC)"] = df_c["QUANTIDADE"].astype(float) * df_c["CUSTO UNITÁRIO"]
    else:
        if "CUSTO TOTAL" in df_c.columns:
            df_c["CUSTO TOTAL (RECALC)"] = parse_money_series(df_c["CUSTO TOTAL"]).fillna(0.0)
        else:
            df_c["CUSTO TOTAL (RECALC)"] = 0.0
    if "DATA" in df_c.columns:
        df_c["DATA"] = pd.to_datetime(df_c["DATA"], errors="coerce")
        df_c["MES_ANO"] = df_c["DATA"].dt.strftime("%Y-%m")
    else:
        df_c["MES_ANO"] = pd.NA
    dfs["COMPRAS"] = df_c

# ----------------------------
# FILTRO MÊS
# ----------------------------
meses_venda = []
if "VENDAS" in dfs:
    meses_venda = sorted(dfs["VENDAS"]["MES_ANO"].dropna().unique().tolist(), reverse=True)
mes_opcoes = ["Todos"] + meses_venda
mes_selecionado = st.selectbox("Filtrar por mês (YYYY-MM):", mes_opcoes, index=0)

def filtrar_mes(df, mes):
    if df is None or df.empty:
        return pd.DataFrame()
    if mes == "Todos" or mes is None:
        return df
    if "MES_ANO" in df.columns:
        return df[df["MES_ANO"] == mes].copy()
    return df

vendas_filtradas = filtrar_mes(dfs.get("VENDAS", pd.DataFrame()), mes_selecionado)
compras_filtradas = filtrar_mes(dfs.get("COMPRAS", pd.DataFrame()), mes_selecionado)
estoque_df = dfs.get("ESTOQUE", pd.DataFrame())

# ----------------------------
# KPIs
# ----------------------------
def calcular_totais_vendas(df):
    if df is None or df.empty:
        return 0.0, 0.0
    total_vendido = (df["VALOR TOTAL"].fillna(0.0).sum() 
                     if "VALOR TOTAL" in df.columns else
                     (df["VALOR VENDA"].fillna(0.0) * df["QTD"].fillna(0)).sum())
    total_lucro = (df["LUCRO UNITARIO"].fillna(0.0) * df["QTD"].fillna(0)).sum() if "LUCRO UNITARIO" in df.columns else 0.0
    return float(total_vendido), float(total_lucro)

total_vendido, total_lucro = calcular_totais_vendas(vendas_filtradas)

total_compras = 0.0
if not compras_filtradas.empty and "CUSTO TOTAL (RECALC)" in compras_filtradas.columns:
    total_compras = compras_filtradas["CUSTO TOTAL (RECALC)"].sum()

k1, k2, k3 = st.columns(3)
k1.metric("💵 Total Vendido (R$)", f"R$ {total_vendido:,.2f}")
k2.metric("🧾 Total Lucro (R$)", f"R$ {total_lucro:,.2f}")
k3.metric("💸 Total Compras (R$)", f"R$ {total_compras:,.2f}")

# ----------------------------
# Abas
# ----------------------------
tabs = st.tabs(["🛒 VENDAS", "🏆 TOP10 (VALOR)", "🏅 TOP10 (QUANTIDADE)", "💰 TOP10 (LUCRO)", "📦 CONSULTAR ESTOQUE"])

# ----------------------------
# Vendas completa
with tabs[0]:
    st.subheader("Vendas (período selecionado)")
    if vendas_filtradas.empty:
        st.info("Sem dados de vendas para o período selecionado.")
    else:
        df_show = vendas_filtradas.copy()
        for col in ["VALOR VENDA","VALOR TOTAL","MEDIA CUSTO UNITARIO","LUCRO UNITARIO"]:
            if col in df_show.columns:
                df_show[col] = df_show[col].map(lambda x: f"R$ {x:,.2f}")
        st.dataframe(df_show, use_container_width=True)

# ----------------------------
# Top 10 VALOR
with tabs[1]:
    st.subheader("Top 10 — por VALOR (R$)")
    if vendas_filtradas.empty:
        st.info("Sem dados de vendas para o período selecionado.")
    else:
        dfv = vendas_filtradas.copy()
        if "VALOR TOTAL" not in dfv.columns and "VALOR VENDA" in dfv.columns and "QTD" in dfv.columns:
            dfv["VALOR TOTAL"] = dfv["VALOR VENDA"] * dfv["QTD"]
        top_val = dfv.groupby("PRODUTO")["VALOR TOTAL"].sum().reset_index().sort_values("VALOR TOTAL", ascending=False).head(10)
        top_val["VALOR_TOTAL_FMT"] = top_val["VALOR TOTAL"].map(lambda x: f"R$ {x:,.2f}")
        fig = px.bar(top_val, x="PRODUTO", y="VALOR TOTAL", text="VALOR_TOTAL_FMT")
        fig.update_traces(textposition="inside")
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(top_val.drop(columns=["VALOR_TOTAL_FMT"]).style.format({"VALOR TOTAL":"R$ {:,.2f}"}))

# ----------------------------
# Top 10 QUANTIDADE
with tabs[2]:
    st.subheader("Top 10 — por QUANTIDADE")
    if vendas_filtradas.empty:
        st.info("Sem dados de vendas para o período selecionado.")
    else:
        dfv = vendas_filtradas.copy()
        if "QTD" in dfv.columns and "PRODUTO" in dfv.columns:
            top_q = dfv.groupby("PRODUTO")["QTD"].sum().reset_index().sort_values("QTD", ascending=False).head(10)
            top_q["QTD_TEXT"] = top_q["QTD"].astype(int).astype(str)
            fig2 = px.bar(top_q, x="PRODUTO", y="QTD", text="QTD_TEXT")
            fig2.update_traces(textposition="inside")
            st.plotly_chart(fig2, use_container_width=True)
            st.dataframe(top_q.drop(columns=["QTD_TEXT"]).style.format({"QTD":"{:,.0f}"}))

# ----------------------------
# Top 10 LUCRO
with tabs[3]:
    st.subheader("Top 10 — por LUCRO (R$)")
    if vendas_filtradas.empty:
        st.info("Sem dados de vendas para o período selecionado.")
    else:
        dfv = vendas_filtradas.copy()
        if "LUCRO UNITARIO" in dfv.columns and "QTD" in dfv.columns:
            dfv["LUCRO_TOTAL"] = dfv["LUCRO UNITARIO"] * dfv["QTD"]
            top_lucro = dfv.groupby("PRODUTO")["LUCRO_TOTAL"].sum().reset_index().sort_values("LUCRO_TOTAL", ascending=False).head(10)
            top_lucro["LUCRO_TOTAL_FMT"] = top_lucro["LUCRO_TOTAL"].map(lambda x: f"R$ {x:,.2f}")
            fig3 = px.bar(top_lucro, x="PRODUTO", y="LUCRO_TOTAL", text="LUCRO_TOTAL_FMT")
            fig3.update_traces(textposition="inside")
            st.plotly_chart(fig3, use_container_width=True)
            st.dataframe(top_lucro.drop(columns=["LUCRO_TOTAL_FMT"]).style.format({"LUCRO_TOTAL":"R$ {:,.2f}"}))

# ----------------------------
# Consultar Estoque
with tabs[4]:
    st.subheader("Consulta completa do Estoque")
    if estoque_df.empty:
        st.info("Aba ESTOQUE não encontrada ou vazia.")
    else:
        df_show = estoque_df.copy()
        # remover colunas totalmente NAN
        df_show = df_show.dropna(axis=1, how='all')
        # formatar valores monetários
        for col in ["Media C. UNITARIO","Valor Venda Sugerido"]:
            if col in df_show.columns:
                df_show[col] = df_show[col].map(lambda x: f"R$ {x:,.2f}")
        # formatar inteiros
        for col in ["EM ESTOQUE","COMPRAS","VENDAS"]:
            if col in df_show.columns:
                df_show[col] = df_show[col].astype(int)
        st.dataframe(df_show.sort_values(by="PRODUTO").reset_index(drop=True), use_container_width=True)

st.success("✅ Dashboard carregado com sucesso!")
