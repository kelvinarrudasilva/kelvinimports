import streamlit as st
import pandas as pd

# =========================================
# CONFIGURAÇÕES BÁSICAS
# =========================================
st.set_page_config(page_title="Teste de Importação", layout="wide")

st.title("🔍 Teste de Carregamento da Planilha")

URL_PLANILHA = "https://drive.google.com/uc?export=download&id=1TsRjsfw1TVfeEWBBvhKvsGQ5YUCktn2b"

# =========================================
# FUNÇÃO PARA CARREGAR COM TRATAMENTO DE ERROS
# =========================================
@st.cache_data
def carregar_planilha(url):
    try:
        df = pd.read_excel(url)
        return df, None
    except Exception as e:
        return None, str(e)

df, erro = carregar_planilha(URL_PLANILHA)

if erro:
    st.error("❌ ERRO AO CARREGAR A PLANILHA")
    st.code(erro)
    st.stop()

st.success("✅ Planilha carregada com sucesso!")

# =========================================
# VERIFICAR SE ABA EXISTE
# =========================================
abas_necessarias = ["ESTOQUE", "VENDAS", "COMPRAS"]
carregadas = {}

try:
    xls = pd.ExcelFile(URL_PLANILHA)
    abas = xls.sheet_names
    st.write("📄 **Abas encontradas:**", abas)

    for aba in abas_necessarias:
        if aba in abas:
            loaded_df = pd.read_excel(URL_PLANILHA, sheet_name=aba)
            carregadas[aba] = loaded_df
        else:
            st.error(f"❌ A aba **{aba}** não foi encontrada na planilha!")

except Exception as e:
    st.error("❌ Erro ao abrir as abas:")
    st.code(str(e))
    st.stop()

# =========================================
# FUNÇÃO PARA VALIDAR COLUNAS
# =========================================
def validar_colunas(nome_aba, df, colunas_esperadas):
    colunas_encontradas = df.columns.tolist()

    st.subheader(f"📌 Verificando aba: **{nome_aba}**")

    faltando = [c for c in colunas_esperadas if c not in colunas_encontradas]
    extras = [c for c in colunas_encontradas if c not in colunas_esperadas]

    if faltando:
        st.error(f"❌ Colunas faltando em **{nome_aba}**:")
        st.write(faltando)
    else:
        st.success(f"✅ Todas as colunas esperadas estão presentes em **{nome_aba}**")

    if extras:
        st.warning(f"⚠️ Colunas extras encontradas em **{nome_aba}**:")
        st.write(extras)

    st.dataframe(df)

# =========================================
# VALIDAR CADA ABA
# =========================================
validar_colunas(
    "ESTOQUE",
    carregadas.get("ESTOQUE", pd.DataFrame()),
    ["PRODUTO", "EM ESTOQUE", "COMPRAS", "Media C. UNITARIO",
     "Valor Venda Sugerido", "VENDAS"]
)

validar_colunas(
    "VENDAS",
    carregadas.get("VENDAS", pd.DataFrame()),
    ["DATA", "PRODUTO", "QTD", "VALOR VENDA", "VALOR TOTAL",
     "MEDIA CUSTO UNITARIO", "LUCRO UNITARIO", "MAKEUP",
     "% DE LUCRO SOBRE CUSTO", "STATUS", "CLIENTE", "OBS"]
)

validar_colunas(
    "COMPRAS",
    carregadas.get("COMPRAS", pd.DataFrame()),
    ["DATA", "PRODUTO", "STATUS", "QUANTIDADE", "CUSTO UNITÁRIO", "CUSTO TOTAL"]
)

# =========================================
# FORMATAR VALORES MONETÁRIOS
# =========================================
def formatar_moeda(df, colunas):
    for col in colunas:
        if col in df.columns:
            try:
                df[col] = pd.to_numeric(df[col], errors="coerce")
            except:
                st.error(f"Erro ao converter coluna monetária: {col}")
    return df

if "VENDAS" in carregadas:
    carregadas["VENDAS"] = formatar_moeda(
        carregadas["VENDAS"],
        ["VALOR VENDA", "VALOR TOTAL", "MEDIA CUSTO UNITARIO", "LUCRO UNITARIO"]
    )

if "COMPRAS" in carregadas:
    carregadas["COMPRAS"] = formatar_moeda(
        carregadas["COMPRAS"],
        ["CUSTO UNITÁRIO", "CUSTO TOTAL"]
    )

if "ESTOQUE" in carregadas:
    carregadas["ESTOQUE"] = formatar_moeda(
        carregadas["ESTOQUE"],
        ["Media C. UNITARIO", "Valor Venda Sugerido"]
    )

st.success("💰 Conversão de valores monetários concluída!")

# Mostrar dataframes formatados
for nome, tabela in carregadas.items():
    st.subheader(f"📄 Dados formatados: {nome}")
    st.dataframe(tabela)
