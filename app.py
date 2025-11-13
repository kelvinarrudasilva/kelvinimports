import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import chardet
import io

st.set_page_config(page_title="Painel de Estoque - Kelvin Arruda", layout="wide")

st.title("📦 Painel de Estoque - Kelvin Arruda")

st.sidebar.header("📂 Carregue seu arquivo CSV")
file = st.sidebar.file_uploader("Selecione o arquivo de estoque (.csv)", type=["csv"])

if file:
    try:
        # Detectar encoding
        raw_data = file.read()
        encoding = chardet.detect(raw_data)["encoding"] or "utf-8"
        file.seek(0)

        # Tentar detectar separador automaticamente
        sample = raw_data.decode(encoding, errors="ignore")[:1000]
        if ";" in sample:
            sep = ";"
        elif "\t" in sample:
            sep = "\t"
        else:
            sep = ","

        # Ler CSV com tratamento de erros
        df = pd.read_csv(
            io.BytesIO(raw_data),
            encoding=encoding,
            sep=sep,
            on_bad_lines="skip",
            engine="python"
        )

        st.sidebar.success(f"Arquivo lido com sucesso! ({len(df)} linhas)")

        # Normalizar nomes das colunas
        df.columns = [c.strip().lower() for c in df.columns]

        # Detectar colunas automaticamente
        def detectar_coluna(possiveis):
            for nome in df.columns:
                for p in possiveis:
                    if p in nome:
                        return nome
            return None

        col_produto = detectar_coluna(["produto", "item", "descr"])
        col_estoque = detectar_coluna(["estoque", "quant"])
        col_compras = detectar_coluna(["compra"])
        col_preco = detectar_coluna(["valor", "preço", "venda"])
        col_vendas = detectar_coluna(["venda", "vendida", "qtd vendida"])

        # Evitar duplicação
        if col_vendas == col_preco:
            col_vendas = None

        # Mostrar colunas detectadas
        st.write("### 🔍 Colunas detectadas:")
        st.json({
            "produto": col_produto,
            "estoque": col_estoque,
            "compras": col_compras,
            "preco_venda": col_preco,
            "vendas": col_vendas,
        })

        if not col_produto or not col_estoque:
            st.error("❌ Não foi possível identificar as colunas principais. Verifique o cabeçalho do CSV.")
            st.stop()

        # Limpar dados
        df = df.dropna(subset=[col_produto])
        df = df[df[col_produto].astype(str).str.strip() != ""]

        # Converter numéricos
        for col in [col_estoque, col_compras, col_preco, col_vendas]:
            if col and col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

        # Métricas principais
        total_itens = len(df)
        total_estoque = df[col_estoque].sum()
        valor_total = (df[col_estoque] * df[col_preco]).sum()

        col1, col2, col3 = st.columns(3)
        col1.metric("Produtos Cadastrados", total_itens)
        col2.metric("Quantidade Total em Estoque", f"{total_estoque:,.0f}".replace(",", "."))
        col3.metric("Valor Total do Estoque (R$)", f"{valor_total:,.2f}".replace(".", ","))

        st.divider()

        # Gráfico de barras - Top 15 produtos em estoque
        top_produtos = df.sort_values(by=col_estoque, ascending=False).head(15)
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.barh(top_produtos[col_produto], top_produtos[col_estoque])
        ax.invert_yaxis()
        ax.set_xlabel("Quantidade em Estoque")
        ax.set_ylabel("Produto")
        ax.set_title("Top 15 Produtos em Estoque")
        st.pyplot(fig)

        st.divider()

        # Tabela de alertas (estoque baixo)
        limite = st.slider("Defina o limite para alerta de reposição", 0, 50, 5)
        alerta = df[df[col_estoque] <= limite]
        st.subheader("⚠️ Alertas de Reposição")
        if not alerta.empty:
            st.dataframe(alerta[[col_produto, col_estoque]])
        else:
            st.success("✅ Nenhum produto abaixo do limite definido.")

        st.divider()

        # Exibição completa
        with st.expander("📋 Ver tabela completa"):
            st.dataframe(df)

    except Exception as e:
        st.error(f"❌ Erro ao ler o arquivo: {e}")

else:
    st.info("⬅️ Envie um arquivo CSV para visualizar o painel.")
