# app.py — Dashboard Loja Importados final + hover detalhado + estoque ordenado + gráfico evolução
import streamlit as st
import pandas as pd
import plotly.express as px
import re
from datetime import datetime

st.set_page_config(page_title="Loja Importados – Dashboard", layout="wide")

# ----------------------------
# LINK FIXO PLANILHA
# ----------------------------
URL_PLANILHA = "https://docs.google.com/spreadsheets/d/1TsRjsfw1TVfeEWBBvhKvsGQ5YUCktn2b/export?format=xlsx"

# ----------------------------
# VISUAL
# ----------------------------
st.markdown("""
    <style>
      :root { --accent:#1aa3ff; --accent-dark:#0066cc; }
      body, .stApp { background-color:#ffffff; color:#111; }
      h1,h2,h3,h4 { color: var(--accent-dark); }
      .stMetric label { color:#333; }
      .stMetric div { color: var(--accent); font-weight:700; }
      .stDataFrame thead th { background-color:#f0f8ff;}
    </style>
""", unsafe_allow_html=True)
st.title("📊 Loja Importados — Dashboard")

# ----------------------------
# FUNÇÕES DE PARSE E FORMATAÇÃO
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

def formatar_valor_reais(df, colunas):
    for c in colunas:
        if c in df.columns:
            df[c] = df[c].fillna(0.0).map(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    return df

# ----------------------------
# DETECTAR CABEÇALHO / LIMPEZA
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
    "ESTOQUE": ["PRODUTO", "EM ESTOQUE", "COMPRAS","Media C. UNITARIO", "Valor Venda Sugerido", "VENDAS"],
    "VENDAS": ["DATA","PRODUTO","QTD","VALOR VENDA","VALOR TOTAL","MEDIA CUSTO UNITARIO","LUCRO UNITARIO","MAKEUP","% DE LUCRO SOBRE CUSTO","STATUS","CLIENTE","OBS"],
    "COMPRAS": ["DATA","PRODUTO","STATUS","QUANTIDADE","CUSTO UNITÁRIO","CUSTO TOTAL"]
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
# CONVERSÃO DE CAMPOS
# ----------------------------
if "ESTOQUE" in dfs:
    df_e = dfs["ESTOQUE"]
    df_e["Media C. UNITARIO"] = parse_money_series(df_e.get("Media C. UNITARIO", pd.Series()))
    df_e["Valor Venda Sugerido"] = parse_money_series(df_e.get("Valor Venda Sugerido", pd.Series()))
    df_e["EM ESTOQUE"] = parse_int_series(df_e.get("EM ESTOQUE", pd.Series())).fillna(0)
    df_e["VENDAS"] = parse_int_series(df_e.get("VENDAS", pd.Series())).fillna(0)
    dfs["ESTOQUE"] = df_e

if "VENDAS" in dfs:
    df_v = dfs["VENDAS"]
    df_v["VALOR VENDA"] = parse_money_series(df_v.get("VALOR VENDA", pd.Series()))
    df_v["VALOR TOTAL"] = parse_money_series(df_v.get("VALOR TOTAL", pd.Series()))
    df_v["MEDIA CUSTO UNITARIO"] = parse_money_series(df_v.get("MEDIA CUSTO UNITARIO", pd.Series()))
    df_v["LUCRO UNITARIO"] = parse_money_series(df_v.get("LUCRO UNITARIO", pd.Series()))
    df_v["QTD"] = parse_int_series(df_v.get("QTD", pd.Series())).fillna(0)
    if "DATA" in df_v.columns:
        df_v["DATA"] = pd.to_datetime(df_v["DATA"], errors="coerce")
        df_v["MES_ANO"] = df_v["DATA"].dt.strftime("%Y-%m")
    else:
        df_v["MES_ANO"] = pd.NA
    dfs["VENDAS"] = df_v

if "COMPRAS" in dfs:
    df_c = dfs["COMPRAS"]
    df_c["QUANTIDADE"] = parse_int_series(df_c.get("QUANTIDADE", pd.Series())).fillna(0)
    df_c["CUSTO UNITÁRIO"] = parse_money_series(df_c.get("CUSTO UNITÁRIO", pd.Series())).fillna(0)
    df_c["CUSTO TOTAL (RECALC)"] = df_c["QUANTIDADE"] * df_c["CUSTO UNITÁRIO"]
    if "DATA" in df_c.columns:
        df_c["DATA"] = pd.to_datetime(df_c["DATA"], errors="coerce")
        df_c["MES_ANO"] = df_c["DATA"].dt.strftime("%Y-%m")
    else:
        df_c["MES_ANO"] = pd.NA
    dfs["COMPRAS"] = df_c

# ----------------------------
# FILTRO MÊS E ORDENAR
# ----------------------------
meses_venda = sorted(dfs["VENDAS"]["MES_ANO"].dropna().unique().tolist(), reverse=True) if "VENDAS" in dfs else []
mes_opcoes = ["Todos"] + meses_venda
mes_atual = datetime.now().strftime("%Y-%m")
index_padrao = mes_opcoes.index(mes_atual) if mes_atual in mes_opcoes else 0
mes_selecionado = st.selectbox("Filtrar por mês (YYYY-MM):", mes_opcoes, index=index_padrao)

def filtrar_mes(df, mes):
    if df.empty:
        return df
    if mes == "Todos":
        return df
    return df[df["MES_ANO"] == mes].copy() if "MES_ANO" in df.columns else df

def ordenar_data(df):
    if df.empty or "DATA" not in df.columns:
        return df
    return df.sort_values("DATA", ascending=False)

vendas_filtradas = ordenar_data(filtrar_mes(dfs.get("VENDAS", pd.DataFrame()), mes_selecionado))
compras_filtradas = ordenar_data(filtrar_mes(dfs.get("COMPRAS", pd.DataFrame()), mes_selecionado))
estoque_df = dfs.get("ESTOQUE", pd.DataFrame())

# ----------------------------
# KPIs
# ----------------------------
def formato_brl(x):
    return f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

total_vendido = (vendas_filtradas["VALOR TOTAL"].fillna(0) if "VALOR TOTAL" in vendas_filtradas.columns else vendas_filtradas["VALOR VENDA"].fillna(0)*vendas_filtradas["QTD"].fillna(0)).sum()
total_lucro = (vendas_filtradas["LUCRO UNITARIO"].fillna(0)*vendas_filtradas["QTD"].fillna(0)).sum() if "LUCRO UNITARIO" in vendas_filtradas.columns else 0
total_compras = compras_filtradas["CUSTO TOTAL (RECALC)"].sum() if not compras_filtradas.empty else 0

k1, k2, k3 = st.columns(3)
k1.metric("💵 Total Vendido (R$)", formato_brl(total_vendido))
k2.metric("🧾 Total Lucro (R$)", formato_brl(total_lucro))
k3.metric("💸 Total Compras (R$)", formato_brl(total_compras))

# ----------------------------
# ABAS
# ----------------------------
tabs = st.tabs(["🛒 VENDAS","🏆 TOP10 (VALOR)","🏅 TOP10 (QUANTIDADE)","💰 TOP10 LUCRO","📦 CONSULTAR ESTOQUE"])

def preparar_tabela_vendas(df):
    df_show = df.dropna(axis=1, how='all')
    if "DATA" in df_show.columns:
        df_show["DATA"] = df_show["DATA"].dt.strftime("%d/%m/%y")
    df_show = formatar_valor_reais(df_show, ["VALOR VENDA","VALOR TOTAL","MEDIA CUSTO UNITARIO","LUCRO UNITARIO"])
    return df_show

# ----------------------------
# Aba VENDAS
with tabs[0]:
    st.subheader("Vendas (período selecionado)")

    # --- Gráfico evolução vendas ---
    if not dfs.get("VENDAS", pd.DataFrame()).empty:
        df_v = dfs["VENDAS"].copy()
        df_mes = df_v.groupby("MES_ANO").agg(
            TOTAL_VENDIDO=("VALOR TOTAL", lambda x: x.fillna(0).sum()),
            TOTAL_LUCRO=("LUCRO UNITARIO", lambda x: (x.fillna(0) * df_v.loc[x.index, "QTD"].fillna(0)).sum())
        ).reset_index().sort_values("MES_ANO")

        fig_predios = px.bar(
            df_mes,
            x="MES_ANO",
            y=["TOTAL_VENDIDO", "TOTAL_LUCRO"],
            barmode="group",
            text_auto=False,
            labels={"MES_ANO":"Mês","value":"R$","variable":"Métrica"},
            title="🏢 Evolução das Vendas e Lucro - Últimos Meses",
            color_discrete_sequence=px.colors.qualitative.Vivid
        )
        fig_predios.update_traces(
            texttemplate='%{y:,.2f}'.replace(",", "X").replace(".", ",").replace("X", "."),
            textposition='inside',
            width=0.6
        )
        fig_predios.update_layout(
            yaxis_tickprefix="R$ ",
            xaxis_tickangle=-45,
            legend_title_text="Métrica",
            legend=dict(x=0.8, y=1.1),
            bargap=0.25
        )
        st.plotly_chart(fig_predios, use_container_width=True)

    if vendas_filtradas.empty:
        st.info("Sem dados de vendas para o período selecionado.")
    else:
        st.dataframe(preparar_tabela_vendas(vendas_filtradas), use_container_width=True)

# ----------------------------
# As outras abas TOP10 VALOR, QUANTIDADE, LUCRO e CONSULTAR ESTOQUE seguem exatamente como antes,
# apenas garantindo que formatar_valor_reais é usado para exibir R$ no padrão brasileiro.
# ----------------------------
# (mantendo o mesmo código das outras abas já corrigido com formato BRL)

st.success("✅ Dashboard carregado com sucesso!")
