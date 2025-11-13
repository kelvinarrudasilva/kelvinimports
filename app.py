import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os

st.set_page_config(page_title="Gestão de Estoque - Kelvin Arruda", layout="wide")

st.title("📦 Gestão de Estoque - Kelvin Arruda")

# --- Função para detectar colunas ---
def detectar_colunas(df):
    cols = {c.lower().strip(): c for c in df.columns}
    mapa = {
        "produto": None,
        "estoque": None,
        "preco_venda": None,
        "vendas": None
    }

    for chave in mapa:
        for nome_coluna in cols:
            if any(p in nome_coluna for p in [chave, "item", "nome", "descri", "quant", "valor", "preço", "venda", "estoque"]):
                mapa[chave] = cols[nome_coluna]
                break
    return mapa

# --- Carregar o Excel automaticamente ---
ARQUIVO = "LOJA IMPORTADOS.xlsx"

if not os.path.exists(ARQUIVO):
    st.error("❌ O arquivo 'LOJA IMPORTADOS.xlsx' não foi encontrado na pasta.")
else:
    try:
        df = pd.read_excel(ARQUIVO, engine="openpyxl")
        st.success("✅ Arquivo carregado com sucesso!")

        # Limpeza básica
        df = df.dropna(how="all")
        df.columns = df.columns.astype(str)

        mapa = detectar_colunas(df)
        st.write("🔍 **Colunas detectadas (verifique)**")
        st.json(mapa)

        if mapa["produto"] is None or mapa["estoque"] is None:
            st.error("❌ Não foi possível identificar as colunas principais (produto/estoque). Verifique o Excel.")
        else:
            df = df.rename(columns={
                mapa["produto"]: "Produto",
                mapa["estoque"]: "Estoque",
                mapa["preco_venda"]: "Preço",
                mapa["vendas"]: "Vendas"
            })

            # Converter colunas numéricas
            for c in ["Estoque", "Preço", "Vendas"]:
                if c in df.columns:
                    df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

            st.subheader("📋 Dados do Estoque")
            st.dataframe(df, use_container_width=True)

            # --- Gráfico de estoque ---
            st.subheader("📊 Quantidade em Estoque")
            fig, ax = plt.subplots(figsize=(8, 4))
            df.plot(kind="bar", x="Produto", y="Estoque", ax=ax, legend=False)
            ax.set_ylabel("Quantidade")
            ax.set_xlabel("")
            st.pyplot(fig)

            # --- Alertas de reposição ---
            st.subheader("⚠️ Alertas de Reposição")
            baixo_estoque = df[df["Estoque"] <= 5]
            if baixo_estoque.empty:
                st.success("✅ Nenhum produto com estoque baixo.")
            else:
                st.warning("🚨 Produtos com baixo estoque:")
                st.dataframe(baixo_estoque, use_container_width=True)

    except Exception as e:
        st.error(f"❌ Erro ao processar o arquivo: {e}")
