# app.py — Dashboard final com valores em R$ e Top10 lucro
import streamlit as st
import pandas as pd
import plotly.express as px
import re

st.set_page_config(page_title="Loja Importados – Dashboard", layout="wide")

URL_PLANILHA = "https://docs.google.com/spreadsheets/d/1TsRjsfw1TVfeEWBBvhKvsGQ5YUCktn2b/export?format=xlsx"

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
# LIMPEZA DE ABAS
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
# CARREGAR PLANILHA
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
    "VENDAS": ["DATA", "PRODUTO", "QTD", "VALOR VENDA", "VALOR TOTAL", "MEDIA CUSTO UNITARIO", "LUCRO UNITARIO", "MAKEUP", "% DE LUCRO SOBRE CUSTO", "STATUS", "CLIENTE", "OBS"],
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
# CONVERSÃO
# ----------------------------
if "ESTOQUE" in dfs:
    df_e = dfs["ESTOQUE"]
    if "Media C. UNITARIO" in df_e.columns:
        df_e["Media C. UNITARIO"] = parse_money_series(df_e["Media C. UNITARIO"])
    if "Valor Venda Sugerido" in df_e.columns:
        df_e["Valor Venda Sugerido"] = parse_money_series(df_e["Valor Venda Sugerido"])
    if "EM ESTOQUE" in df_e.columns:
        df_e["EM ESTOQUE"] = parse_int_series(df_e["EM ESTOQUE"]).fillna(0)
    if "VENDAS" in df_e.columns:
        df_e["VENDAS"] = parse_int_series(df_e["VENDAS"]).fillna(0)
    dfs["ESTOQUE"] = df_e

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

if "COMPRAS" in dfs:
    df_c = dfs["COMPRAS"]
    if "QUANTIDADE" in df_c.columns:
        df_c["QUANTIDADE"] = parse_int_series(df_c["QUANTIDADE"]).fillna(0)
    if "CUSTO UNITÁRIO" in df_c.columns:
        df_c["CUSTO UNITÁRIO"] = parse_money_series(df_c["CUSTO UNITÁRIO"]).fillna(0.0)
    if "QUANTIDADE" in df_c.columns and "CUSTO UNITÁRIO" in df_c.columns:
        df_c["CUSTO TOTAL (RECALC)"] = df_c["QUANTIDADE"] * df_c["CUSTO UNITÁRIO"]
    else:
        df_c["CUSTO TOTAL (RECALC)"] = parse_money_series(df_c["CUSTO TOTAL"]).fillna(0.0) if "CUSTO TOTAL" in df_c.columns else 0.0
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
    if mes == "Todos":
        return df
    if "MES_ANO" in df.columns:
        return df[df["MES_ANO"] == mes].copy()
    return df

vendas_filtradas = filtrar_mes(dfs.get("VENDAS", pd.DataFrame()), mes_selecionado)
compras_filtradas = filtrar_mes(dfs.get("COMPRAS", pd.DataFrame()), mes_selecionado)
estoque_df = dfs.get("ESTOQUE", pd.DataFrame())

# ----------------------------
# Funções de formatação
# ----------------------------
def formatar_reais(df, colunas):
    for c in colunas:
        if c in df.columns:
            df[c] = df[c].apply(lambda x: f"R$ {x:,.2f}")
    return df

def formatar_inteiro(df, colunas):
    for c in colunas:
        if c in df.columns:
            df[c] = df[c].apply(lambda x: f"{int(x):,}")
    return df

# ----------------------------
# KPIs
# ----------------------------
total_vendido = vendas_filtradas["VALOR TOTAL"].sum() if "VALOR TOTAL" in vendas_filtradas.columns else 0.0
total_lucro = (vendas_filtradas["LUCRO UNITARIO"]*vendas_filtradas["QTD"]).sum() if "LUCRO UNITARIO" in vendas_filtradas.columns else 0.0
total_compras = compras_filtradas["CUSTO TOTAL (RECALC)"].sum() if not compras_filtradas.empty else 0.0

k1, k2, k3 = st.columns(3)
k1.metric("💵 Total Vendido (R$)", f"R$ {total_vendido:,.2f}")
k2.metric("🧾 Total Lucro (R$)", f"R$ {total_lucro:,.2f}")
k3.metric("💸 Total Compras (R$)", f"R$ {total_compras:,.2f}")

# ----------------------------
# Abas
# ----------------------------
tabs = st.tabs(["🛒 VENDAS", "🏆 TOP10 (VALOR)", "🏅 TOP10 (QUANTIDADE)", "📦 CONSULTAR ESTOQUE"])

# Aba VENDAS
with tabs[0]:
    st.subheader("Vendas (período selecionado)")
    df_vendas_exibir = vendas_filtradas.copy()
    monetarias = ["VALOR VENDA","VALOR TOTAL","MEDIA CUSTO UNITARIO","LUCRO UNITARIO"]
    df_vendas_exibir = formatar_reais(df_vendas_exibir, monetarias)
    df_vendas_exibir = formatar_inteiro(df_vendas_exibir, ["QTD"])
    st.dataframe(df_vendas_exibir, use_container_width=True)

# Aba TOP10 VALOR + LUCRO
with tabs[1]:
    st.subheader("Top 10 — por VALOR (R$)")
    if not vendas_filtradas.empty:
        dfv = vendas_filtradas.copy()
        if "VALOR TOTAL" not in dfv.columns:
            dfv["VALOR TOTAL"] = dfv["VALOR VENDA"]*dfv["QTD"]
        top_val = dfv.groupby("PRODUTO")["VALOR TOTAL"].sum().reset_index().sort_values("VALOR TOTAL", ascending=False).head(10)
        fig = px.bar(top_val, x="PRODUTO", y="VALOR TOTAL",
                     text=top_val["VALOR TOTAL"].map(lambda x: f"R$ {x:,.2f}"))
        fig.update_traces(textposition="inside")
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(formatar_reais(top_val.copy(), ["VALOR TOTAL"]))

        # Top 10 LUCRO
        st.subheader("Top 10 — por LUCRO (R$)")
        top_lucro = (dfv.assign(LUCRO_TOTAL=dfv["LUCRO UNITARIO"]*dfv["QTD"])
                     .groupby("PRODUTO")["LUCRO_TOTAL"].sum()
                     .reset_index().sort_values("LUCRO_TOTAL", ascending=False).head(10))
        fig_l = px.bar(top_lucro, x="PRODUTO", y="LUCRO_TOTAL",
                       text=top_lucro["LUCRO_TOTAL"].map(lambda x: f"R$ {x:,.2f}"))
        fig_l.update_traces(textposition="inside")
        st.plotly_chart(fig_l, use_container_width=True)
        st.dataframe(formatar_reais(top_lucro.copy(), ["LUCRO_TOTAL"]))

# Aba TOP10 QUANTIDADE
with tabs[2]:
    st.subheader("Top 10 — por QUANTIDADE")
    if not vendas_filtradas.empty:
        dfv = vendas_filtradas.copy()
        top_q = dfv.groupby("PRODUTO")["QTD"].sum().reset_index().sort_values("QTD", ascending=False).head(10)
        fig2 = px.bar(top_q, x="PRODUTO", y="QTD",
                      text=top_q["QTD"].map(lambda x: f"{int(x):,}"))
        fig2.update_traces(textposition="inside")
        st.plotly_chart(fig2, use_container_width=True)
        st.dataframe(formatar_inteiro(top_q.copy(), ["QTD"]))

# Aba ESTOQUE
with tabs[3]:
    st.subheader("Consulta completa do Estoque")
    if not estoque_df.empty:
        df_e = estoque_df.copy()
        monetarias = [c for c in ["Media C. UNITARIO","Valor Venda Sugerido"] if c in df_e.columns]
        inteiros = [c for c in ["EM ESTOQUE","VENDAS","COMPRAS"] if c in df_e.columns]
        df_e = formatar_reais(df_e, monetarias)
        df_e = formatar_inteiro(df_e, inteiros)
        st.dataframe(df_e.sort_values("PRODUTO").reset_index(drop=True), use_container_width=True)

st.success("✅ Dashboard carregado com sucesso!")
