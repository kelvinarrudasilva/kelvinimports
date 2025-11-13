# =========================
# Painel de Estoque - Kelvin Arruda
# =========================

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io, os

st.set_page_config(page_title="Painel de Estoque", layout="wide")

st.title("📦 Painel de Estoque")
st.markdown("### **KELVIN ARRUDA**")
st.write("Leitura inteligente de estoque com detecção automática de colunas.")

# -------------------------
# Função de leitura robusta
# -------------------------
def load_csv(file):
    encodings = ["utf-8", "latin1"]
    seps = [";", ","]
    for enc in encodings:
        for sep in seps:
            try:
                file.seek(0)
                df = pd.read_csv(file, sep=sep, encoding=enc, skip_blank_lines=True)
                # remove colunas totalmente vazias
                df = df.dropna(axis=1, how="all")
                # remove linhas vazias
                df = df.dropna(how="all")
                if len(df.columns) > 1:
                    return df
            except Exception:
                continue
    st.error("Não foi possível ler o arquivo. Verifique o formato CSV.")
    st.stop()

# -------------------------
# Upload de arquivo
# -------------------------
st.sidebar.header("Dados")
file = st.sidebar.file_uploader("📁 Envie o arquivo CSV do estoque", type=["csv"])

if file is not None:
    df = load_csv(file)
else:
    DEFAULT = "LOJA IMPORTADOS(ESTOQUE).csv"
    if os.path.exists(DEFAULT):
        df = load_csv(open(DEFAULT, "rb"))
    else:
        st.info("Envie um arquivo CSV para continuar.")
        st.stop()

# Normaliza nomes
df.columns = [str(c).strip().lower() for c in df.columns]

# -------------------------
# Detecta colunas automaticamente
# -------------------------
def detectar_coluna(possiveis):
    for p in possiveis:
        for c in df.columns:
            if p in c:
                return c
    return None

col_prod = detectar_coluna(["prod", "nome", "descri"])
col_estoque = detectar_coluna(["estoque", "quantidade", "qtd"])
col_vendas = detectar_coluna(["venda", "vendido"])
col_preco = detectar_coluna(["preco", "valor"])
col_compras = detectar_coluna(["compra"])

# tenta usar a primeira coluna não numérica como produto
if col_prod is None:
    for c in df.columns:
        if not pd.api.types.is_numeric_dtype(df[c]):
            col_prod = c
            break

# Mostra colunas detectadas
st.sidebar.subheader("Colunas detectadas (verifique)")
st.sidebar.json({
    "produto": col_prod,
    "estoque": col_estoque,
    "compras": col_compras,
    "preco_venda": col_preco,
    "vendas": col_vendas
})

# -------------------------
# Limpa e padroniza dataframe
# -------------------------
rename_map = {
    col_prod: "Produto",
    col_estoque: "Estoque",
    col_compras: "Compras",
    col_preco: "Preco",
    col_vendas: "Vendas"
}

df = df.rename(columns={k: v for k, v in rename_map.items() if k})
for col in ["Estoque", "Compras", "Preco", "Vendas"]:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

# remove linhas sem produto
if "Produto" not in df.columns:
    df["Produto"] = df.index.astype(str)
df = df[df["Produto"].astype(str).str.strip().ne("")]

# -------------------------
# Indicadores
# -------------------------
st.divider()
st.subheader("📊 Indicadores")

col1, col2, col3 = st.columns(3)
col1.metric("Produtos", len(df))
col2.metric("Estoque Total", int(df["Estoque"].sum()) if "Estoque" in df.columns else 0)
col3.metric("Total Vendas", int(df["Vendas"].sum()) if "Vendas" in df.columns else 0)

# -------------------------
# Alertas
# -------------------------
st.divider()
st.subheader("⚠️ Produtos com estoque baixo (≤5)")
if "Estoque" in df.columns:
    low = df[df["Estoque"] <= 5]
    if len(low):
        st.warning(f"{len(low)} produtos com estoque baixo.")
        st.dataframe(low[["Produto", "Estoque"]])
    else:
        st.success("Nenhum produto com estoque crítico.")
else:
    st.info("Coluna de estoque não encontrada.")

# -------------------------
# Gráficos
# -------------------------
st.divider()
st.subheader("📈 Estoque por Produto")
if "Estoque" in df.columns:
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.bar(df["Produto"], df["Estoque"], color="#007acc")
    plt.xticks(rotation=90, fontsize=8)
    st.pyplot(fig)

st.subheader("💸 Vendas por Produto")
if "Vendas" in df.columns:
    fig2, ax2 = plt.subplots(figsize=(10, 4))
    ax2.bar(df["Produto"], df["Vendas"], color="#2ca02c")
    plt.xticks(rotation=90, fontsize=8)
    st.pyplot(fig2)

# -------------------------
# Tabela final
# -------------------------
st.divider()
st.subheader("📋 Tabela Completa")
st.dataframe(df, use_container_width=True)
