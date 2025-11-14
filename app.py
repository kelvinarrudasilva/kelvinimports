# app.py
# Dashboard Premium com seletor C1 minimalista + KPIs aprimorados
# OBS: Substitua a URL_DO_DRIVE_PELO_SEU_LINK abaixo

import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from io import BytesIO

# ============================
# CONFIG VISUAL
# ============================
st.set_page_config(page_title="Painel - Loja Importados", layout="wide")

st.markdown(
    """
    <style>
      :root { --gold:#FFD700; --bg:#000000; --card:#0f0f0f; --muted:#bbbbbb; --white:#FFFFFF; }
      .stApp { background-color: var(--bg); color: var(--gold); }
      .title { color: var(--gold); font-weight:700; font-size:22px; }
      .subtitle { color: var(--muted); font-size:12px; margin-bottom:12px; }

      /* KPI ESTILIZADA */
      .kpi { background: linear-gradient(90deg, #151515, #0b0b0b); padding:16px; border-radius:14px; text-align:center; box-shadow:0 0 10px rgba(255,215,0,0.15); }
      .kpi-value { color: #FFD700; font-size:28px; font-weight:800; }
      .kpi-label { color:#e6e6e6; font-size:15px; font-weight:600; }

      /* SELECTBOX MINIMALISTA PREMIUM C1 */
      .minimal-selectbox .stSelectbox>div>div { background:#0b0b0b !important; border:1px solid #FFD700 !important; color:#FFD700 !important; border-radius:10px !important; padding:6px 10px !important; font-size:14px !important; font-weight:600 !important; }
      .minimal-selectbox .stSelectbox>div>div:hover { border-color:#fff176 !important; }
      .minimal-selectbox label { color:#FFD700 !important; font-weight:700; font-size:14px; }

      .table-card { background: linear-gradient(90deg,#0b0b0b,#111111); border: 1px solid rgba(255,215,0,0.08); padding:12px; border-radius:10px; }
      .table-card h4 { color: var(--gold); margin:0 0 8px 0; }

    </style>
    """,
    unsafe_allow_html=True,
)

# ============================
# FUNÇÃO PARA BAIXAR DO GOOGLE DRIVE
# ============================
def carregar_excel_drive(url):
    try:
      r = requests.get(url)
      return pd.read_excel(BytesIO(r.content))
    except:
      st.error("❌ Erro ao carregar planilha do Google Drive.")
      return None

# ============================
# URL DO DRIVE AQUI
# ============================
url_drive = "https://drive.google.com/uc?id=ID_AQUI"  # coloque seu ID

df = carregar_excel_drive(url_drive)
if df is None:
    st.stop()

# Detectar automaticamente coluna de data
possiveis_datas = ["DATA", "Data", "data", "DATA VENDA", "DIA", "VENDA DATA", "HORARIO", "DT", "DATE"]
col_data = None
for c in df.columns:
    if c.strip().upper() in [x.upper() for x in possiveis_datas]:
        col_data = c
        break

if col_data is None:
    st.error("❌ Nenhuma coluna de data encontrada.")
    st.stop()

# Converter datas
df[col_data] = pd.to_datetime(df[col_data], errors="coerce")
df = df.dropna(subset=[col_data])

# ============================
# SELETOR DE MÊS ESTILO C1
# ============================
with st.container():
    st.markdown("<div class='minimal-selectbox'>", unsafe_allow_html=True)
    meses_unicos = df[col_data].dt.strftime("%m/%Y").unique()
    meses_unicos = sorted(meses_unicos, key=lambda x: (x.split('/')[1], x.split('/')[0]))
    mes_escolhido = st.selectbox("📅 Período", meses_unicos)
    st.markdown("</div>", unsafe_allow_html=True)

# Filtrar mês
mes_num = mes_escolhido.split('/')[0]
ano_num = mes_escolhido.split('/')[1]

filtro_df = df[
    (df[col_data].dt.month == int(mes_num)) &
    (df[col_data].dt.year == int(ano_num))
]

# ============================
# KPIS
# ============================
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("<div class='kpi'>", unsafe_allow_html=True)
    st.markdown(f"<div class='kpi-value'>{len(filtro_df)}</div>")
    st.markdown("<div class='kpi-label'>Vendas no Mês</div>")
    st.markdown("</div>", unsafe_allow_html=True)

with col2:
    total = filtro_df['VALOR TOTAL'].sum() if 'VALOR TOTAL' in df.columns else 0
    st.markdown("<div class='kpi'>", unsafe_allow_html=True)
    st.markdown(f"<div class='kpi-value'>R$ {total:,.2f}</div>")
    st.markdown("<div class='kpi-label'>Faturamento</div>")
    st.markdown("</div>", unsafe_allow_html=True)

with col3:
    lucro = filtro_df['LUCRO'].sum() if 'LUCRO' in df.columns else 0
    st.markdown("<div class='kpi'>", unsafe_allow_html=True)
    st.markdown(f"<div class='kpi-value'>R$ {lucro:,.2f}</div>")
    st.markdown("<div class='kpi-label'>Lucro</div>")
    st.markdown("</div>", unsafe_allow_html=True)

# ============================
# GRÁFICO
# ============================
if 'PRODUTO' in df.columns:
    graf = filtro_df.groupby('PRODUTO').size().reset_index(name='QTD')
    fig = px.bar(graf, x='PRODUTO', y='QTD', title='Produtos Mais Vendidos', text='QTD')
    st.plotly_chart(fig, use_container_width=True)

# ============================
# TABELA DO MÊS
# ============================
st.markdown("<div class='table-card'><h4>📋 Vendas do Período</h4>", unsafe_allow_html=True)
st.dataframe(filtro_df, use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)
