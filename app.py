# =========================
# Painel de Estoque - KELVIN ARRUDA (auto detecção de cabeçalho)
# =========================

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import io, os, re

st.set_page_config(page_title="Painel de Estoque", layout="wide")
st.title("📦 Painel de Estoque")
st.markdown("### **KELVIN ARRUDA**")
st.write("Leitura inteligente de CSV com detecção automática de cabeçalho e colunas.")

# -------------------------
# Funções auxiliares
# -------------------------
def detect_real_header(lines):
    """Detecta linha de cabeçalho real (contendo mais textos e menos números)."""
    for i, line in enumerate(lines[:10]):
        letters = sum(c.isalpha() for c in line)
        if letters > 5:  # se tem várias letras, provável cabeçalho
            return i
    return 0

def try_read_file(filelike):
    """Tenta ler CSV com encodings, separadores e detecção de cabeçalho."""
    encs = ["utf-8", "latin1"]
    seps = [";", ","]
    last_err = None
    for enc in encs:
        for sep in seps:
            try:
                filelike.seek(0)
                raw = filelike.read()
                if isinstance(raw, (bytes, bytearray)):
                    text = raw.decode(enc, errors="replace")
                else:
                    text = raw
                lines = text.splitlines()
                header_row = detect_real_header(lines)
                df = pd.read_csv(
                    io.StringIO(text),
                    sep=sep,
                    skiprows=header_row,
                    on_bad_lines="skip"
                )
                if len(df.columns) > 1:
                    return df
            except Exception as e:
                last_err = e
                continue
    raise last_err or ValueError("Não foi possível ler o arquivo")

def normalize_cols(df):
    df.columns = [str(c).strip() for c in df.columns]
    return df

def find_best_column(df, keywords):
    """Procura a melhor coluna com base em palavras-chave ou conteúdo textual."""
    for k in keywords:
        for c in df.columns:
            if k.lower() in str(c).lower():
                return c
    # Se não achou, pega a primeira coluna não numérica
    for c in df.columns:
        if not pd.api.types.is_numeric_dtype(df[c]):
            return c
    return df.columns[0]

def to_number_series(s):
    s = s.fillna('').astype(str)
    s = s.str.replace(r'[^0-9,.\-]', '', regex=True)
    s = s.str.replace(r'\.(?=\d{3}(?!\d))', '', regex=True)
    s = s.str.replace(',', '.', regex=False)
    return pd.to_numeric(s.replace('', pd.NA), errors='coerce').fillna(0)

# -------------------------
# Upload do arquivo
# -------------------------
st.sidebar.header("Dados")
uploaded = st.sidebar.file_uploader("Envie o CSV (ou deixe o arquivo padrão no repositório)", type=["csv"])

if uploaded is not None:
    df_raw = try_read_file(uploaded)
else:
    DEFAULT_CSV = "LOJA IMPORTADOS(ESTOQUE).csv"
    if not os.path.exists(DEFAULT_CSV):
        st.error("Nenhum arquivo enviado e arquivo padrão não encontrado.")
        st.stop()
    with open(DEFAULT_CSV, "rb") as f:
        df_raw = try_read_file(f)

df_raw = normalize_cols(df_raw)

# -------------------------
# Detecção de colunas
# -------------------------
product_col = find_best_column(df_raw, ["produto", "item", "descri", "nome"])
estoque_col = find_best_column(df_raw, ["estoque", "quantidade", "qtd"])
compras_col = find_best_column(df_raw, ["compra"])
preco_col = find_best_column(df_raw, ["preco", "valor", "venda"])
vendas_col = find_best_column(df_raw, ["vendas", "vendido"])

# Exibir detecção
st.sidebar.subheader("Colunas detectadas (verifique)")
st.sidebar.write({
    "produto": product_col,
    "estoque": estoque_col,
    "compras": compras_col,
    "preco_venda": preco_col,
    "vendas": vendas_col
})

# -------------------------
# Padronizar e limpar
# -------------------------
df = df_raw.rename(columns={
    product_col: "PRODUTO",
    estoque_col: "EM_ESTOQUE",
    compras_col: "COMPRAS",
    preco_col: "VALOR_VENDA",
    vendas_col: "VENDAS"
})

# Converter números
for c in ["EM_ESTOQUE", "COMPRAS", "VALOR_VENDA", "VENDAS"]:
    if c in df.columns:
        df[c] = to_number_series(df[c])
    else:
        df[c] = 0

# Garantir existência da coluna PRODUTO
if "PRODUTO" not in df.columns:
    df.insert(0, "PRODUTO", [f"SKU_{i}" for i in range(len(df))])

# Limpeza
df = df.dropna(subset=["PRODUTO"])
df = df[df["PRODUTO"].astype(str).str.strip().ne("")]
df = df[~df["PRODUTO"].astype(str).str.upper().str.contains("UNNAMED|PRODUTO|ITEM|DESCRI")]

# -------------------------
# Painel de dados
# -------------------------
st.write(f"✅ Arquivo lido com sucesso ({len(df)} linhas)")
st.markdown("---")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Produtos únicos", int(df["PRODUTO"].nunique()))
col2.metric("Estoque total", int(df["EM_ESTOQUE"].sum()))
col3.metric("Total de vendas", int(df["VENDAS"].sum()))
col4.metric("Linhas com nome vazio", int((df['PRODUTO'] == '').sum()))

st.subheader("Alertas de Reposição")
low_stock = df[df["EM_ESTOQUE"] <= 5]
if low_stock.empty:
    st.success("Nenhum produto com estoque crítico.")
else:
    st.warning(f"{len(low_stock)} produtos com estoque <= 5.")
    st.dataframe(low_stock[["PRODUTO", "EM_ESTOQUE", "COMPRAS", "VENDAS"]])

st.subheader("Top 10 mais vendidos")
if df["VENDAS"].sum() > 0:
    top_v = df.sort_values("VENDAS", ascending=False).head(10)
    fig, ax = plt.subplots()
    ax.barh(top_v["PRODUTO"][::-1], top_v["VENDAS"][::-1])
    ax.set_xlabel("Vendas")
    st.pyplot(fig)
else:
    st.info("Ainda sem dados de vendas.")

st.subheader("Tabela completa")
st.dataframe(df)

st.download_button("⬇️ Baixar CSV Limpo", df.to_csv(index=False).encode("utf-8"), "estoque_limpo.csv", "text/csv")
