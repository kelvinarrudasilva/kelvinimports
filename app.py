# =========================
# Painel de Estoque - KELVIN ARRUDA (Versão robusta de detecção de colunas)
# =========================

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import io, os

st.set_page_config(page_title="Painel de Estoque", layout="wide")
st.title("📦 Painel de Estoque")
st.markdown("### **KELVIN ARRUDA**")
st.write("Leitura automática de CSV — detectando colunas inteligentemente.")

# -------------------------
# Helpers
# -------------------------
def try_read_file(filelike):
    """Tenta ler o arquivo com combinações de encoding e separador, retorna DataFrame ou levanta exceção."""
    encs = ["latin1", "utf-8"]
    seps = [";", ","]
    last_err = None
    for enc in encs:
        for sep in seps:
            try:
                filelike.seek(0)
                text = filelike.read()
                # if bytes, decode for StringIO
                if isinstance(text, (bytes, bytearray)):
                    text = text.decode(enc, errors="replace")
                buf = io.StringIO(text)
                df = pd.read_csv(buf, sep=sep, skip_blank_lines=True)
                if df is None:
                    continue
                # if reads but only one column and looks like whole line, still accept and try next combo
                if df.empty:
                    continue
                return df
            except Exception as e:
                last_err = e
                continue
    raise last_err if last_err is not None else ValueError("Não foi possível ler o arquivo")

def normalize_cols(df):
    df.columns = [str(c).strip() for c in df.columns]
    return df

def find_best_column(df, keywords):
    """Procura no nome da coluna por palavras-chave; se não encontrar, tenta analisar valores."""
    cols = df.columns.tolist()
    # 1) busca por keywords no nome da coluna
    for k in keywords:
        for c in cols:
            if k.lower() in str(c).lower():
                return c
    # 2) busca por coluna não numérica com muitos valores textuais (provável nome/descrição)
    text_scores = {}
    for c in cols:
        s = df[c].astype(str).replace("nan","").replace("None","")
        non_empty = s[s.str.strip() != ""]
        if len(non_empty) == 0:
            text_scores[c] = 0
            continue
        # percent of values that contain letters
        pct_letters = non_empty.str.contains(r'[A-Za-zÀ-ÿ]').mean()
        text_scores[c] = pct_letters
    # pick column with highest pct_letters (and > 0.3)
    best_col = max(text_scores, key=text_scores.get)
    if text_scores[best_col] >= 0.25:
        return best_col
    # 3) fallback: first column
    return cols[0] if cols else None

def to_number_series(s):
    s = s.fillna('').astype(str)
    s = s.str.replace(r'[^0-9,.\-]', '', regex=True)
    s = s.str.replace(r'\.(?=\d{3}(?!\d))', '', regex=True)
    s = s.str.replace(',', '.', regex=False)
    return pd.to_numeric(s.replace('', pd.NA), errors='coerce').fillna(0)

# -------------------------
# Upload / leitura
# -------------------------
st.sidebar.header("Dados")
uploaded = st.sidebar.file_uploader("Envie o CSV (ou deixe em branco se já estiver no repositório)", type=["csv"])

df_raw = None
if uploaded is not None:
    try:
        df_raw = try_read_file(uploaded)
    except Exception as e:
        st.error(f"Erro ao ler o arquivo enviado: {e}")
        st.stop()
else:
    DEFAULT_CSV = "LOJA IMPORTADOS(ESTOQUE).csv"
    if os.path.exists(DEFAULT_CSV):
        try:
            with open(DEFAULT_CSV, "rb") as f:
                df_raw = try_read_file(f)
        except Exception as e:
            st.error(f"Erro ao ler o arquivo padrão '{DEFAULT_CSV}': {e}")
            st.stop()
    else:
        st.info("Nenhum arquivo enviado e arquivo padrão não encontrado. Faça upload do CSV na barra lateral.")
        st.stop()

# normalize header names spacing
df_raw = normalize_cols(df_raw)

# -------------------------
# Detectar colunas principais
# -------------------------
# palavras-chave prováveis para cada tipo de coluna
product_keywords = ["produto", "prod", "item", "descri", "nome", "description"]
estoque_keywords = ["estoque", "em estoque", "quantidade", "qtd", "quant"]
compras_keywords = ["compra", "compras"]
venda_keywords = ["venda", "preco", "valor", "price"]
vendas_col_keywords = ["vendas", "vendido", "qtd vend", "sold"]

product_col = find_best_column(df_raw, product_keywords)
estoque_col = find_best_column(df_raw, estoque_keywords)
compras_col = find_best_column(df_raw, compras_keywords)
preco_col = find_best_column(df_raw, venda_keywords)
vendas_col = find_best_column(df_raw, vendas_col_keywords)

# show detections
st.sidebar.subheader("Colunas detectadas (verifique)")
st.sidebar.write({
    "produto": product_col,
    "estoque": estoque_col,
    "compras": compras_col,
    "preco_venda": preco_col,
    "vendas": vendas_col
})

# rename to canonical names
mapping = {}
if product_col: mapping[product_col] = "PRODUTO"
if estoque_col: mapping[estoque_col] = "EM_ESTOQUE"
if compras_col: mapping[compras_col] = "COMPRAS"
if preco_col: mapping[preco_col] = "VALOR_VENDA"
if vendas_col: mapping[vendas_col] = "VENDAS"

df = df_raw.rename(columns=mapping)

# ensure product column exists; if not, use first non-numeric column or first column
if "PRODUTO" not in df.columns:
    # try to find first column with many letters
    fallback = find_best_column(df_raw, [])
    if fallback:
        df = df.rename(columns={fallback: "PRODUTO"})
    else:
        # as ultimate fallback, create SKU names
        df.insert(0, "PRODUTO", [f"SKU_{i}" for i in range(len(df))])

# ensure numeric columns exist
for c in ["EM_ESTOQUE", "COMPRAS", "VALOR_VENDA", "VENDAS"]:
    if c in df.columns:
        df[c] = to_number_series(df[c])
    else:
        df[c] = 0

# Remove rows that are clearly header fragments or blank:
# Keep rows where at least one numeric column is non-zero OR product name looks real
mask_real = (
    (df["EM_ESTOQUE"].fillna(0) != 0)
    | (df["COMPRAS"].fillna(0) != 0)
    | (df["VENDAS"].fillna(0) != 0)
    | (df["PRODUTO"].astype(str).str.strip().str.len() > 0)
)
df = df[mask_real].copy()

# also drop rows where PRODUTO is something like 'PRODUTO' (literal header repeated)
df = df[~df["PRODUTO"].astype(str).str.upper().str.contains(r'PRODUT|PRODUTO|ITEM|DESCRI|NOME')].copy()

# final cleanup: fill product names empty with placeholder
df["PRODUTO"] = df["PRODUTO"].fillna("").astype(str).replace("", "SEM_NOME_PRODUTO")

# Derived columns
df["VALOR_ESTOQUE_CUSTO"] = df["EM_ESTOQUE"] * df["VALOR_VENDA"] * 0  # placeholder if no custo; kept 0 to avoid errors
# If there is a custo column name detected (not implemented heuristically here), you'd set it.

# -------------------------
# Exibição e KPIs
# -------------------------
st.write(f"Arquivo lido com sucesso — {len(df)} linhas após limpeza.")
st.markdown("---")

# KPIs
col1, col2, col3, col4 = st.columns(4)
col1.metric("SKUs", int(df["PRODUTO"].nunique()))
col2.metric("Total em estoque", int(df["EM_ESTOQUE"].sum()))
col3.metric("Total vendas (soma)", int(df["VENDAS"].sum()))
col4.metric("Produtos sem nome", int((df["PRODUTO"] == "SEM_NOME_PRODUTO").sum()))

st.markdown("---")
st.subheader("Resumo rápido")
low_stock = df[df["EM_ESTOQUE"] <= 5]
no_sales = df[df["VENDAS"] == 0]
st.write(f"- 🔻 {len(low_stock)} produtos com estoque <= 5")
st.write(f"- 💤 {len(no_sales)} produtos com VENDAS == 0")

# top vendidos
if df["VENDAS"].sum() > 0:
    top_v = df.sort_values("VENDAS", ascending=False).head(10)
    fig, ax = plt.subplots()
    ax.barh(top_v["PRODUTO"][::-1], top_v["VENDAS"][::-1])
    ax.set_xlabel("VENDAS")
    st.pyplot(fig)

st.subheader("Alertas de Reposição")
if low_stock.empty:
    st.success("Nenhum produto crítico por estoque.")
else:
    st.table(low_stock[["PRODUTO", "EM_ESTOQUE", "COMPRAS", "VENDAS"]].head(50))

st.subheader("Tabela completa (filtrável)")
st.dataframe(df.reset_index(drop=True))

st.download_button("Baixar CSV limpo", df.to_csv(index=False).encode("utf-8"), "estoque_limpo.csv", "text/csv")
