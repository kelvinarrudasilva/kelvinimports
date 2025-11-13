import streamlit as st
import pandas as pd
from pathlib import Path

# ==============================
# ⚙️ CONFIGURAÇÃO
# ==============================
st.set_page_config(page_title="Visualização de Abas - Loja Importados", layout="wide")

st.markdown(
    """
    <style>
        body {background-color: #0e0e0e; color: #FFD700;}
        .stMarkdown h1, h2, h3, h4 {color: #FFD700;}
        .block-container {padding-top: 1rem;}
    </style>
    """,
    unsafe_allow_html=True
)

st.title("📘 Visualização das Abas - Loja Importados")

# ==============================
# 🔍 DETECTA CABEÇALHO AUTOMATICAMENTE
# ==============================
def detect_header(path, sheet_name):
    temp = pd.read_excel(path, sheet_name=sheet_name, header=None)
    for i in range(len(temp)):
        if "PRODUTO" in str(temp.iloc[i].values).upper():
            df = pd.read_excel(path, sheet_name=sheet_name, header=i)
            st.write(f"✅ Cabeçalho detectado na linha {i+1} da aba **{sheet_name}**")
            return df
    st.warning(f"⚠️ Nenhum cabeçalho com 'PRODUTO' detectado na aba **{sheet_name}**")
    return pd.read_excel(path, sheet_name=sheet_name)


# ==============================
# 📂 LEITURA DO ARQUIVO
# ==============================
file_path = "LOJA IMPORTADOS.xlsx"

if not Path(file_path).exists():
    st.error("❌ O arquivo 'LOJA IMPORTADOS.xlsx' não foi encontrado no diretório atual.")
else:
    xls = pd.ExcelFile(file_path)
    abas_validas = ["ESTOQUE", "VENDAS", "COMPRAS"]
    abas_encontradas = [a for a in xls.sheet_names if a in abas_validas]

    st.write("📄 Abas encontradas:", abas_encontradas)

    for aba in abas_validas:
        if aba in abas_encontradas:
            st.subheader(f"📊 Aba: {aba}")
            df = detect_header(file_path, aba)

            # Mostra as primeiras linhas e info
            st.write("🧱 **Colunas detectadas:**", list(df.columns))
            st.dataframe(df.head(10))
            st.markdown("---")
        else:
            st.warning(f"❌ Aba '{aba}' não encontrada no arquivo.")
