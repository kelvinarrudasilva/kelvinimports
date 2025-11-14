# app.py — Dashboard final (link fixo, filtro por mês, top10, correção compras)
import streamlit as st
import pandas as pd
import plotly.express as px
import re
from io import BytesIO

st.set_page_config(page_title="Dashboard Loja Importados", layout="wide")

# --------------------------
# Config visual (simples)
# --------------------------
st.markdown(
    """
    <style>
      :root { --gold:#FFD700; }
      body, .stApp { background-color:#0b0b0b; color:#EEE; }
      h1,h2,h3,h4 { color: var(--gold); }
      .stMetric { background:#111; padding:10px; border-radius:8px; border:1px solid #333; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("📊 Dashboard – Loja Importados")

# --------------------------
# Link fixo do Google Drive
# --------------------------
URL_PLANILHA = "https://drive.google.com/uc?export=download&id=1TsRjsfw1TVfeEWBBvhKvsGQ5YUCktn2b"

# --------------------------
# Helpers de limpeza/parse
# --------------------------
def parse_money_series(s):
    """Tenta transformar uma série em float monetário robustamente."""
    if s is None:
        return pd.Series(dtype="float64")
    # converter tudo para str
    s2 = s.astype(str).fillna("")
    # remover símbolos de moeda e espaços
    s2 = s2.str.replace(r"[^\d,\-\.]", "", regex=True)
    # se existir padrão com '.' como thousand and ',' as decimal (ex: 1.234,56)
    # detectamos se contém both '.' e ',' and last ',' has 2 digits -> assume BR format
    def parse_val(x):
        if x is None or x == "" or x.lower() == "nan":
            return float("nan")
        x = str(x).strip()
        # if contains both . and , and comma appears in last 3 chars -> brazilian format
        if "." in x and "," in x:
            # replace dots (thousands) and comma to decimal
            x = x.replace(".", "")
            x = x.replace(",", ".")
        else:
            # if only dots and more than one dot -> likely thousands separators, remove them
            if x.count(".") > 1:
                x = x.replace(".", "")
            # if only comma, replace comma with dot
            if "," in x and "." not in x:
                x = x.replace(",", ".")
        # final cleanup: remove any leftover non-digit except dot and minus
        x = re.sub(r"[^\d\.\-]", "", x)
        try:
            return float(x) if x not in ("", ".", "-") else float("nan")
        except:
            return float("nan")
    return s2.map(parse_val)

def parse_int_series(s):
    """Transforma série em int, tentando remover texto e separators."""
    if s is None:
        return pd.Series(dtype="Int64")
    s2 = s.astype(str).fillna("")
    s2 = s2.str.replace(r"[^\d\-\.,]", "", regex=True)
    # remove thousand separators
    s2 = s2.str.replace(r"\.", "", regex=True)
    s2 = s2.str.replace(",", ".", regex=True)
    def to_int(x):
        try:
            if x is None or x == "" or x.lower() == "nan":
                return pd.NA
            # convert to float then to int if it is integer-valued
            v = float(x)
            return int(v)
        except:
            return pd.NA
    return s2.map(to_int).astype("Int64")

# --------------------------
# Carregar arquivo Excel (mantemos seu método)
# --------------------------
def carregar_xls(url):
    try:
        xls = pd.ExcelFile(url)
        return xls, None
    except Exception as e:
        return None, str(e)

xls, erro = carregar_xls(URL_PLANILHA)
if erro:
    st.error("Erro ao abrir planilha do Google Drive.")
    st.code(erro)
    st.stop()

# ignorar aba EXCELENTEJOAO
abas = [a for a in xls.sheet_names if a.upper() != "EXCELENTEJOAO"]

# =========================
# Funções de limpeza (usadas anteriormente)
# =========================
def detectar_linha_cabecalho(df, chave):
    linha_cab = None
    for i in range(len(df)):
        linha = df.iloc[i].astype(str).str.upper().tolist()
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
    # remover colunas Unnamed
    df = df.loc[:, ~df.columns.astype(str).str.contains("Unnamed")]
    df = df.reset_index(drop=True)
    # limpar nomes de colunas: strip
    df.columns = [str(c).strip() for c in df.columns]
    return df

def converter_moedas_e_numeros(dfs_dict):
    # Estoque
    if "ESTOQUE" in dfs_dict:
        df = dfs_dict["ESTOQUE"]
        if "Media C. UNITARIO" in df.columns:
            df["Media C. UNITARIO"] = parse_money_series(df["Media C. UNITARIO"])
        if "Valor Venda Sugerido" in df.columns:
            df["Valor Venda Sugerido"] = parse_money_series(df["Valor Venda Sugerido"])
        if "EM ESTOQUE" in df.columns:
            df["EM ESTOQUE"] = parse_int_series(df["EM ESTOQUE"])
        if "VENDAS" in df.columns:
            df["VENDAS"] = parse_int_series(df["VENDAS"])
        dfs_dict["ESTOQUE"] = df

    # Vendas
    if "VENDAS" in dfs_dict:
        df = dfs_dict["VENDAS"]
        if "VALOR VENDA" in df.columns:
            df["VALOR VENDA"] = parse_money_series(df["VALOR VENDA"])
        if "VALOR TOTAL" in df.columns:
            df["VALOR TOTAL"] = parse_money_series(df["VALOR TOTAL"])
        if "MEDIA CUSTO UNITARIO" in df.columns:
            df["MEDIA CUSTO UNITARIO"] = parse_money_series(df["MEDIA CUSTO UNITARIO"])
        if "LUCRO UNITARIO" in df.columns:
            df["LUCRO UNITARIO"] = parse_money_series(df["LUCRO UNITARIO"])
        if "QTD" in df.columns:
            df["QTD"] = parse_int_series(df["QTD"])
        dfs_dict["VENDAS"] = df

    # Compras
    if "COMPRAS" in dfs_dict:
        df = dfs_dict["COMPRAS"]
        # garantir QUANTIDADE numérica
        if "QUANTIDADE" in df.columns:
            df["QUANTIDADE"] = parse_int_series(df["QUANTIDADE"])
        # custo unitário
        if "CUSTO UNITÁRIO" in df.columns:
            df["CUSTO UNITÁRIO"] = parse_money_series(df["CUSTO UNITÁRIO"])
        # recalcular CUSTO TOTAL de forma segura
        if "QUANTIDADE" in df.columns and "CUSTO UNITÁRIO" in df.columns:
            df["CUSTO TOTAL (RECALC)"] = (df["QUANTIDADE"].fillna(0).astype(float) *
                                         df["CUSTO UNITÁRIO"].fillna(0.0))
        else:
            # tentar converter coluna existente
            if "CUSTO TOTAL" in df.columns:
                df["CUSTO TOTAL (RECALC)"] = parse_money_series(df["CUSTO TOTAL"])
            else:
                df["CUSTO TOTAL (RECALC)"] = pd.NA
        dfs_dict["COMPRAS"] = df

    return dfs_dict

# =========================
# Ler e processar as abas (mantendo seu fluxo)
# =========================
colunas_esperadas = {
    "ESTOQUE": [
        "PRODUTO", "EM ESTOQUE", "COMPRAS",
        "Media C. UNITARIO", "Valor Venda Sugerido", "VENDAS"
    ],
    "VENDAS": [
        "DATA", "PRODUTO", "QTD", "VALOR VENDA", "VALOR TOTAL",
        "MEDIA CUSTO UNITARIO", "LUCRO UNITARIO", "MAKEUP",
        "% DE LUCRO SOBRE CUSTO", "STATUS", "CLIENTE", "OBS"
    ],
    "COMPRAS": [
        "DATA", "PRODUTO", "STATUS",
        "QUANTIDADE", "CUSTO UNITÁRIO", "CUSTO TOTAL"
    ]
}

dfs = {}
for aba in colunas_esperadas.keys():
    if aba not in abas:
        continue
    bruto = pd.read_excel(URL_PLANILHA, sheet_name=aba, header=None)
    limpo = limpar_aba_raw(bruto, aba)
    if limpo is None:
        continue
    # manter colunas originais e ajustar
    dfs[aba] = limpo

# converter campos monetários/numeros e recalcular custos
dfs = converter_moedas_e_numeros(dfs)

# -------------------------------------------------------
# Criar colunas auxiliares: DATA como datetime, MES_ANO
# -------------------------------------------------------
if "VENDAS" in dfs:
    df_v = dfs["VENDAS"]
    if "DATA" in df_v.columns:
        df_v["DATA"] = pd.to_datetime(df_v["DATA"], errors="coerce")
        df_v["MES_ANO"] = df_v["DATA"].dt.strftime("%Y-%m")
    else:
        df_v["MES_ANO"] = pd.NA
    dfs["VENDAS"] = df_v

if "COMPRAS" in dfs:
    df_c = dfs["COMPRAS"]
    if "DATA" in df_c.columns:
        df_c["DATA"] = pd.to_datetime(df_c["DATA"], errors="coerce")
        df_c["MES_ANO"] = df_c["DATA"].dt.strftime("%Y-%m")
    else:
        df_c["MES_ANO"] = pd.NA
    dfs["COMPRAS"] = df_c

# --------------------------
# FILTRO POR MÊS (único control)
# --------------------------
# lista de meses válidos da aba vendas (se houver), ordenados desc
meses_disponiveis = []
if "VENDAS" in dfs:
    meses_disponiveis = sorted(df_v["MES_ANO"].dropna().unique().tolist(), reverse=True)
# incluir uma opção "Todos"
meses_opcoes = ["Todos"] + meses_disponiveis
mes_selecionado = st.selectbox("Filtrar por mês (ano-mês):", meses_opcoes, index=0)

def filtrar_por_mes(df, mes):
    if mes is None or mes == "Todos":
        return df
    if "MES_ANO" in df.columns:
        return df[df["MES_ANO"] == mes].copy()
    return df

vendas_filtradas = filtrar_por_mes(dfs.get("VENDAS", pd.DataFrame()), mes_selecionado)
compras_filtradas = filtrar_por_mes(dfs.get("COMPRAS", pd.DataFrame()), mes_selecionado)
estoque_df = dfs.get("ESTOQUE", pd.DataFrame())

# --------------------------
# KPIs: total vendido (R$) e total lucro (R$) no período
# --------------------------
def calcular_totais_vendas(df):
    if df is None or df.empty:
        return 0.0, 0.0
    # total vendido em R$
    total_vendido = 0.0
    if "VALOR TOTAL" in df.columns:
        total_vendido = df["VALOR TOTAL"].fillna(0.0).sum()
    elif "VALOR VENDA" in df.columns and "QTD" in df.columns:
        total_vendido = (df["VALOR VENDA"].fillna(0.0) * df["QTD"].fillna(0)).sum()

    # total lucro
    lucro_total = 0.0
    if "LUCRO UNITARIO" in df.columns and "QTD" in df.columns:
        lucro_total = (df["LUCRO UNITARIO"].fillna(0.0) * df["QTD"].fillna(0)).sum()
    elif "LUCRO UNITARIO" in df.columns:
        lucro_total = df["LUCRO UNITARIO"].fillna(0.0).sum()
    else:
        # fallback: VALOR_TOTAL - CUSTO aproximado
        if "VALOR TOTAL" in df.columns and "MEDIA CUSTO UNITARIO" in df.columns and "QTD" in df.columns:
            custo_estim = (df["MEDIA CUSTO UNITARIO"].fillna(0.0) * df["QTD"].fillna(0)).sum()
            lucro_total = df["VALOR TOTAL"].sum() - custo_estim

    return float(total_vendido), float(lucro_total)

total_vendido, total_lucro = calcular_totais_vendas(vendas_filtradas)

# total gasto em compras (usar coluna recalc)
total_compras = 0.0
if not compras_filtradas.empty and "CUSTO TOTAL (RECALC)" in compras_filtradas.columns:
    total_compras = compras_filtradas["CUSTO TOTAL (RECALC)"].fillna(0.0).sum()
elif not compras_filtradas.empty and "CUSTO TOTAL" in compras_filtradas.columns:
    total_compras = parse_money_series(compras_filtradas["CUSTO TOTAL"]).fillna(0.0).sum()

# Exibir KPIs no topo
k1, k2, k3 = st.columns(3)
k1.metric("💵 Total Vendido (R$)", f"R$ {total_vendido:,.2f}")
k2.metric("🧾 Total Lucro (R$)", f"R$ {total_lucro:,.2f}")
k3.metric("🧾 Total Compras (R$)", f"R$ {total_compras:,.2f}")

# --------------------------
# Top 10 Produtos Mais Vendidos (por VALOR TOTAL)
# --------------------------
st.subheader("🏆 Top 10 Produtos Mais Vendidos (por Valor)")
if vendas_filtradas is None or vendas_filtradas.empty:
    st.info("Sem dados de vendas para o período selecionado.")
else:
    # garantir colunas
    dfv = vendas_filtradas.copy()
    if "VALOR TOTAL" not in dfv.columns and "VALOR VENDA" in dfv.columns and "QTD" in dfv.columns:
        dfv["VALOR TOTAL"] = dfv["VALOR VENDA"].fillna(0.0) * dfv["QTD"].fillna(0)

    # agrupar por produto
    if "PRODUTO" in dfv.columns:
        top = (dfv.groupby("PRODUTO")["VALOR TOTAL"]
               .sum()
               .reset_index()
               .sort_values("VALOR TOTAL", ascending=False)
               .head(10))
        fig_top = px.bar(top, x="PRODUTO", y="VALOR TOTAL", title="Top 10 - Vendas (R$)")
        st.plotly_chart(fig_top, use_container_width=True)

        # tabela com Qtd vendida e lucro por produto (apoiando detalhes)
        detalhes = (dfv.groupby("PRODUTO")
                    .agg(QTD_TOTAL=pd.NamedAgg(column="QTD", aggfunc="sum"),
                         VALOR_TOTAL=pd.NamedAgg(column="VALOR TOTAL", aggfunc="sum"),
                         LUCRO_TOTAL=pd.NamedAgg(column="LUCRO_UNITARIO" if "LUCRO_UNITARIO" in dfv.columns else "VALOR_TOTAL",
                                                 aggfunc=lambda x: (x.fillna(0) * dfv.loc[x.index, "QTD"].fillna(0)).sum()
                                                 if "LUCRO_UNITARIO" in dfv.columns and "QTD" in dfv.columns else x.sum())))
        detalhes = detalhes.reset_index().sort_values("VALOR_TOTAL", ascending=False).head(10)
        # ajustar nomes das colunas e exibir
        if "LUCRO_TOTAL" in detalhes.columns:
            detalhes["LUCRO_TOTAL"] = detalhes["LUCRO_TOTAL"].fillna(0.0)
        st.dataframe(detalhes.style.format({"VALOR_TOTAL": "R$ {:,.2f}", "LUCRO_TOTAL": "R$ {:,.2f}", "QTD_TOTAL": "{:,.0f}"}))
    else:
        st.warning("Coluna 'PRODUTO' não encontrada nas vendas.")

# --------------------------
# Gráficos adicionais por aba (opcionais)
# --------------------------
st.subheader("📈 Evolução do Faturamento (período selecionado)")
if not vendas_filtradas.empty and "DATA" in vendas_filtradas.columns and "VALOR TOTAL" in vendas_filtradas.columns:
    series_fat = (vendas_filtradas.groupby("DATA")["VALOR TOTAL"].sum().reset_index().sort_values("DATA"))
    fig_fat = px.line(series_fat, x="DATA", y="VALOR TOTAL", title="Faturamento Diário")
    st.plotly_chart(fig_fat, use_container_width=True)
else:
    st.info("Sem dados de faturamento por data para exibir.")

# --------------------------
# Compras: corrigir valores e mostrar série
# --------------------------
st.subheader("📥 Compras (período selecionado)")
if not compras_filtradas.empty:
    dfc = compras_filtradas.copy()
    # exibir coluna recalcada e limpar valores extremos
    if "CUSTO TOTAL (RECALC)" in dfc.columns:
        dfc["CUSTO TOTAL (RECALC)"] = pd.to_numeric(dfc["CUSTO TOTAL (RECALC)"], errors="coerce").fillna(0.0)
        # limitar valores absurdos: se > 1e12 consideramos inválido -> NaN
        dfc.loc[dfc["CUSTO TOTAL (RECALC)"] > 1e12, "CUSTO TOTAL (RECALC)"] = pd.NA

        st.metric("Total Compras (recalculado)", f"R$ {dfc['CUSTO TOTAL (RECALC)'].sum():,.2f}")

        # série de compras
        if "DATA" in dfc.columns:
            serie_comp = dfc.groupby("DATA")["CUSTO TOTAL (RECALC)"].sum().reset_index().sort_values("DATA")
            fig_comp = px.line(serie_comp, x="DATA", y="CUSTO TOTAL (RECALC)", title="Gastos com Compras")
            st.plotly_chart(fig_comp, use_container_width=True)
    else:
        st.info("Coluna de custo não encontrada ou não foi possível recalcular.")
    st.dataframe(dfc, use_container_width=True)
else:
    st.info("Sem dados de compras para o período selecionado.")

# --------------------------
# Estoque (resumo)
# --------------------------
st.subheader("📦 Estoque")
if not estoque_df.empty:
    df_e = estoque_df.copy()
    # garantir EM ESTOQUE numérico
    if "EM ESTOQUE" in df_e.columns:
        df_e["EM ESTOQUE"] = parse_int_series(df_e["EM ESTOQUE"]).fillna(0)
    # exibir top com menor estoque
    if "EM ESTOQUE" in df_e.columns and "PRODUTO" in df_e.columns:
        criticos = df_e.sort_values("EM ESTOQUE").head(10)
        st.write("Produtos com menor estoque")
        st.dataframe(criticos[["PRODUTO", "EM ESTOQUE"]], use_container_width=True)
    else:
        st.dataframe(df_e, use_container_width=True)
else:
    st.info("Aba ESTOQUE não encontrada ou vazia.")

st.success("✅ Dashboard atualizado")
