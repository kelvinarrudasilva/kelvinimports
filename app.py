# =========================
# Painel de Estoque - Kelvin Arruda (Versão Blindada)
# =========================

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io, os

st.set_page_config(page_title="Painel de Estoque", layout="wide")

st.title("📦 Painel de Estoque")
st.markdown("### **KELVIN ARRUDA**")
st.write("Versão que lê qualquer CSV e renomeia colunas automaticamente.")

# -------------------------
# Função de leitura inteligente
# -------------------------
def load_csv(file):
    encodings = ["utf-8", "latin1"]
    seps = [";", ","]
    for enc in encodings:
        for sep in seps:
            try:
                file.seek(0)
                df = pd.read_csv(file, sep=sep, encoding=enc, skip_blank_lines=True)
                if df.empty:
                    file.seek(0)
                    df = pd.read_csv(file, sep=sep, encoding=enc, header=None)
                df = df.dropna(how="all").dropna(axis=1, how="all")
                if not df.empty:
                    return df
            except Exception:
                continue
    st.error("❌ Não foi possível ler o arquivo. Verifique o formato CSV.")
    st.stop()

# -------------------------
# Upload
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

# -------------------------
# Normaliza e tenta identificar o cabeçalho
# -------------------------
df.columns = [str(c).strip().lower() for c in df.columns]
primeira_linha = df.iloc[0].astype(str).str.lower()

if any(x in " ".join(primeira_linha) for x in ["produto", "estoque", "venda", "compra", "valor"]):
    df.columns = primeira_linha
    df = df.drop(0)
    df.columns = [str(c).strip().lower() for c in df.columns]
else:
    # Se não houver cabeçalho, cria nomes genéricos
    df.columns = [f"col_{i}" for i in range(len(df.columns))]

# -------------------------
# Tenta detectar colunas
# -------------------------
def detectar_coluna(possiveis):
    for p in possiveis:
        for c in df.columns:
            if p in c:
                return c
    return None

col_prod = detectar_coluna(["prod", "nome", "descri", "item"])
col_estoque = detectar_coluna(["estoque", "quant", "qtd"])
col_vendas = detectar_coluna(["venda", "vendido"])
col_preco = detectar_coluna(["preco", "valor", "unit"])
col_compras = detectar_coluna(["compra", "pedido"])

# Se nada encontrado, assume colunas pela posição
if col_prod is None:
    col_prod = df.columns[0]
if col_estoque is None and len(df.columns) > 1:
    col_estoque = df.columns[1]

st.sidebar.subheader("Colunas detectadas (verifique)")
st.sidebar.json({
    "produto": col_prod,
    "estoque": col_estoque,
    "compras": col_compras,
    "preco_venda": col_preco,
    "vendas": col_vendas
})

# -------------------------
# Renomeia para padrão fixo
# -------------------------
rename_map = {
    col_prod: "Produto",
    col_estoque: "Estoque",
    col_compras: "Compras",
    col_preco: "Preco",
    col_vendas: "Vendas"
}
df = df.rename(columns={k: v for k, v in rename_map.items() if k})

# -------------------------
# Limpeza de dados
# -------------------------
for col in ["Estoque", "Compras", "Preco", "Vendas"]:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

if "Produto" not in df.columns:
    df["Produto"] = "Produto_" + df.index.astype(str)

df["Produto"] = df["Produto"].astype(str).str.strip()
df = df[df["Produto"].ne("")]

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
# Tabela completa
# -------------------------
st.divider()
st.subheader("📋 Tabela Completa")
st.dataframe(df, use_container_width=True)
