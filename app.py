import streamlit as st
import pandas as pd
import plotly.express as px

# ======================================
# CONFIGURAÇÃO GERAL
# ======================================
st.set_page_config(page_title="Dashboard Loja Importados", layout="wide")
st.markdown("""
    <style>
        body { background-color: #0e1117; color: #f1c40f; }
        [data-testid="stAppViewContainer"] { background-color: #0e1117; }
        [data-testid="stHeader"] { background: none; }
        .kpi-card {
            background-color: #1e1e1e; padding: 15px; border-radius: 10px;
            text-align: center; box-shadow: 0 0 8px #00000055;
        }
        .kpi-value { font-size: 26px; color: #f1c40f; font-weight: bold; }
        .kpi-label { font-size: 14px; color: #aaa; }
    </style>
""", unsafe_allow_html=True)

# ======================================
# FUNÇÃO DE LEITURA SEGURA
# ======================================
@st.cache_data
def load_data():
    try:
        xls = pd.ExcelFile("LOJA IMPORTADOS.xlsx")

        def read_sheet(name, header_guess=2):
            try:
                df = pd.read_excel(xls, sheet_name=name, header=header_guess)
                df = df.loc[:, ~df.columns.str.contains("^Unnamed")]
                df.columns = [str(c).strip().upper() for c in df.columns]
                return df
            except Exception as e:
                st.warning(f"⚠️ Erro ao ler aba {name}: {e}")
                return pd.DataFrame()

        estoque = read_sheet("ESTOQUE")
        vendas = read_sheet("VENDAS")
        compras = read_sheet("COMPRAS")

        return estoque, vendas, compras

    except Exception as e:
        st.error(f"❌ Falha ao carregar o arquivo: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

# ======================================
# CARREGAR DADOS
# ======================================
estoque, vendas, compras = load_data()

if vendas.empty and compras.empty and estoque.empty:
    st.stop()

# ======================================
# AJUSTES E CÁLCULOS
# ======================================
def safe_numeric(df, cols):
    for col in cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
        else:
            st.warning(f"⚠️ Coluna ausente: {col}")
            df[col] = 0
    return df

if not vendas.empty:
    vendas = safe_numeric(vendas, ["QTD", "VALOR VENDA", "MEDIA CUSTO UNITARIO"])
    vendas["LUCRO_CALC"] = (vendas["VALOR VENDA"] - vendas["MEDIA CUSTO UNITARIO"]) * vendas["QTD"]
    total_vendas = (vendas["VALOR VENDA"] * vendas["QTD"]).sum()
    lucro_estimado = vendas["LUCRO_CALC"].sum()
else:
    total_vendas, lucro_estimado = 0, 0

if not compras.empty:
    compras = safe_numeric(compras, ["VALOR TOTAL"])
    total_compras = compras["VALOR TOTAL"].sum()
else:
    total_compras = 0

if not estoque.empty:
    estoque = safe_numeric(estoque, ["QTD"])
    qtd_estoque = estoque["QTD"].sum()
else:
    qtd_estoque = 0

# ======================================
# LAYOUT KPIs
# ======================================
st.markdown("<h2 style='color:#f1c40f;text-align:center;'>📊 Painel Gerencial - Loja Importados</h2>", unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)
col1.markdown(f"<div class='kpi-card'><div class='kpi-value'>R$ {total_vendas:,.2f}</div><div class='kpi-label'>💰 Total de Vendas</div></div>", unsafe_allow_html=True)
col2.markdown(f"<div class='kpi-card'><div class='kpi-value'>R$ {total_compras:,.2f}</div><div class='kpi-label'>🧾 Total de Compras</div></div>", unsafe_allow_html=True)
col3.markdown(f"<div class='kpi-card'><div class='kpi-value'>R$ {lucro_estimado:,.2f}</div><div class='kpi-label'>📈 Lucro Estimado</div></div>", unsafe_allow_html=True)
col4.markdown(f"<div class='kpi-card'><div class='kpi-value'>{qtd_estoque:,}</div><div class='kpi-label'>📦 Qtde em Estoque</div></div>", unsafe_allow_html=True)

st.markdown("---")

# ======================================
# GRÁFICOS
# ======================================
aba = st.sidebar.radio("📂 Escolha uma aba", ["Vendas", "Compras", "Estoque", "Diagnóstico"])

if aba == "Vendas" and not vendas.empty:
    st.subheader("💵 Vendas por Produto")
    graf_vendas = vendas.groupby("PRODUTO")["VALOR VENDA"].sum().sort_values(ascending=False).reset_index()
    fig = px.bar(graf_vendas, x="PRODUTO", y="VALOR VENDA", title="Ranking de Vendas", color="VALOR VENDA", color_continuous_scale="gold")
    fig.update_layout(template="plotly_dark", plot_bgcolor="#0e1117", paper_bgcolor="#0e1117", font_color="white")
    st.plotly_chart(fig, use_container_width=True)

elif aba == "Compras" and not compras.empty:
    st.subheader("🧾 Compras por Produto")
    if "PRODUTO" in compras.columns and "VALOR TOTAL" in compras.columns:
        graf_compras = compras.groupby("PRODUTO")["VALOR TOTAL"].sum().reset_index()
        fig = px.bar(graf_compras, x="PRODUTO", y="VALOR TOTAL", title="Compras por Produto", color="VALOR TOTAL", color_continuous_scale="gold")
        fig.update_layout(template="plotly_dark", plot_bgcolor="#0e1117", paper_bgcolor="#0e1117", font_color="white")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("⚠️ Colunas de produto ou valor não encontradas em COMPRAS.")

elif aba == "Estoque" and not estoque.empty:
    st.subheader("📦 Estoque Atual")
    fig = px.bar(estoque, x="PRODUTO", y="QTD", title="Quantidade em Estoque", color="QTD", color_continuous_scale="gold")
    fig.update_layout(template="plotly_dark", plot_bgcolor="#0e1117", paper_bgcolor="#0e1117", font_color="white")
    st.plotly_chart(fig, use_container_width=True)

elif aba == "Diagnóstico":
    st.subheader("🔍 Diagnóstico de Colunas Detectadas")
    st.write("**ESTOQUE:**", list(estoque.columns))
    st.write("**VENDAS:**", list(vendas.columns))
    st.write("**COMPRAS:**", list(compras.columns))
