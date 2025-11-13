import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import openpyxl
import os

st.set_page_config(page_title="Gestão de Estoque - Kelvin Arruda", layout="wide")
st.title("📦 Gestão de Estoque - Kelvin Arruda")

ARQUIVO = "LOJA IMPORTADOS.xlsx"

def detectar_linha_cabecalho(arquivo):
    wb = openpyxl.load_workbook(arquivo, read_only=True)
    ws = wb.active
    for i, row in enumerate(ws.iter_rows(values_only=True)):
        valores = [str(c).strip().lower() if c else "" for c in row]
        if any("esto" in c or "prod" in c or "descr" in c for c in valores):
            return i
    return 0

def carregar_e_limpar(arquivo):
    header_row = detectar_linha_cabecalho(arquivo)
    df = pd.read_excel(arquivo, engine="openpyxl", header=header_row)
    df.columns = [str(c).strip().lower() for c in df.columns]
    df = df.dropna(how="all")
    df = df.loc[:, ~df.columns.duplicated()]
    return df

def mapear_colunas(df):
    mapa = {"produto": None, "estoque": None, "preco_venda": None, "vendas": None}
    for c in df.columns:
        nome = str(c).lower()
        if any(x in nome for x in ["prod", "descr", "item", "nome"]):
            mapa["produto"] = c
        elif "esto" in nome or "quant" in nome:
            mapa["estoque"] = c
        elif "preç" in nome or "valor" in nome:
            if mapa["preco_venda"] is None:
                mapa["preco_venda"] = c
            else:
                mapa["vendas"] = c
        elif "vend" in nome:
            mapa["vendas"] = c
    return mapa

if not os.path.exists(ARQUIVO):
    st.error("❌ O arquivo 'LOJA IMPORTADOS.xlsx' não foi encontrado.")
else:
    try:
        df = carregar_e_limpar(ARQUIVO)
        mapa = mapear_colunas(df)

        st.write("🔍 **Colunas detectadas (verifique)**")
        st.json(mapa)

        # Se não achar produto, cria uma coluna fictícia
        if mapa["produto"] is None:
            st.warning("⚠️ Nenhuma coluna de produtos detectada. Criando nomes automáticos...")
            df.insert(0, "Produto", [f"Produto {i+1}" for i in range(len(df))])
            mapa["produto"] = "Produto"

        if mapa["estoque"] is None:
            st.error("❌ Nenhuma coluna de estoque encontrada. Corrija o arquivo e tente novamente.")
            st.stop()

        df = df.rename(columns={
            mapa["produto"]: "Produto",
            mapa["estoque"]: "Estoque",
            mapa["preco_venda"]: "Preço",
            mapa["vendas"]: "Vendas"
        })

        df = df.dropna(subset=["Produto"])
        for c in ["Estoque", "Preço", "Vendas"]:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

        st.subheader("📋 Tabela de Estoque")
        st.dataframe(df, use_container_width=True)

        st.subheader("📊 Gráfico de Estoque")
        fig, ax = plt.subplots(figsize=(8, 4))
        df.plot(kind="bar", x="Produto", y="Estoque", ax=ax, legend=False)
        ax.set_ylabel("Quantidade em Estoque")
        ax.set_xlabel("")
        st.pyplot(fig)

        st.subheader("⚠️ Alertas de Reposição")
        baixo = df[df["Estoque"] <= 5]
        if baixo.empty:
            st.success("✅ Nenhum produto com estoque baixo.")
        else:
            st.warning("🚨 Produtos com baixo estoque:")
            st.dataframe(baixo, use_container_width=True)

    except Exception as e:
        st.error(f"❌ Erro ao processar o arquivo: {e}")
