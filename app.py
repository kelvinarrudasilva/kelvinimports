# ============================================
#  app.py — Dashboard Loja Importados (v. Busca Premium)
#  Kelvin Edition — Dark Purple Vision
# ============================================

import streamlit as st
import pandas as pd
import plotly.express as px
import re
from datetime import datetime, timedelta
import numpy as np
import requests
from io import BytesIO

# -------------------------------------------------
# CONFIG INICIAL
# -------------------------------------------------
st.set_page_config(
    page_title="Loja Importados – Dashboard IA",
    layout="wide",
    initial_sidebar_state="collapsed"
)

URL_PLANILHA = "https://docs.google.com/spreadsheets/d/1TsRjsfw1TVfeEWBBvhKvsGQ5YUCktn2b/export?format=xlsx"

# -------------------------------------------------
# CSS — Dark Theme + Busca Premium
# -------------------------------------------------
st.markdown("""
<style>
:root {
  --bg: #0b0b0b;
  --accent: #8b5cf6;
  --accent-2: #a78bfa;
  --muted: #bdbdbd;
  --card-bg: #141414;
}
body, .stApp { background: var(--bg) !important; color: #f0f0f0 !important; }

/* KPIs */
.kpi-row { display:flex; gap:12px; flex-wrap:wrap; margin-top:20px; }
.kpi {
  background: var(--card-bg); padding:14px 18px; border-radius:12px;
  box-shadow:0 6px 16px rgba(0,0,0,0.45); border-left:6px solid var(--accent);
  min-width:170px;
}
.kpi h3 { margin:0; font-size:12px; color:var(--accent-2); }
.kpi .value { margin-top:6px; font-size:22px; font-weight:900; }

/* TABS */
.stTabs button {
  background:#1e1e1e !important; border:1px solid #333 !important;
  border-radius:12px !important; padding:8px 14px !important;
  font-weight:700 !important; color:var(--accent-2) !important;
  margin-right:8px !important;
}

/* Busca Premium */
.search-box input {
    background: rgba(255,255,255,0.06) !important;
    padding: 12px 14px !important;
    border-radius: 10px !important;
    border: 1px solid #333 !important;
    font-size: 15px !important;
    color: #fff !important;
}
.filter-pill {
    display:inline-block;
    padding:6px 14px;
    background:#1b1b1b;
    border:1px solid #333;
    color:#dcdcdc;
    border-radius:50px;
    margin-right:6px;
    font-size:12px;
    cursor:pointer;
}
.filter-pill:hover {
    background:#262626;
    border-color:#555;
}
.card-grid {
    display:grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap:16px;
    margin-top:20px;
}
.product-card {
    background:#141414;
    padding:16px;
    border-radius:14px;
    box-shadow:0 4px 14px rgba(0,0,0,0.55);
    border:1px solid rgba(255,255,255,0.05);
}
.product-title {
    font-size:16px;
    font-weight:800;
    color:#a78bfa;
}
.card-badge {
    display:inline-block;
    padding:4px 10px;
    background:#222;
    border-radius:8px;
    margin-right:5px;
    font-size:11px;
}
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------
# FUNÇÕES AUXILIARES
# -------------------------------------------------
def parse_money_value(x):
    try:
        if pd.isna(x): return float("nan")
    except: pass
    s = str(x).strip()
    s = re.sub(r"[^\d\.,\-]", "", s)
    if "." in s and "," in s: s = s.replace(".","").replace(",",".")
    else:
        if "," in s: s = s.replace(",",".")
    try: return float(s)
    except: return float("nan")

def parse_money_series(s):
    return s.astype(str).map(parse_money_value)

def formatar_reais_com_centavos(v):
    try: v=float(v)
    except: return "R$ 0,00"
    s=f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {s}"

def formatar_reais_sem_centavos(v):
    try: v=float(v)
    except: return "R$ 0"
    s=f"{v:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {s}"

def carregar_xlsx_from_url(url):
    r=requests.get(url, timeout=25)
    r.raise_for_status()
    return pd.ExcelFile(BytesIO(r.content))

def detectar_linha_cabecalho(df_raw, keywords):
    for i in range(12):
        linha = " ".join(df_raw.iloc[i].astype(str).str.upper().tolist())
        if any(k.upper() in linha for k in keywords):
            return i
    return None

def limpar_aba_raw(df_raw, nome):
    busca = {"ESTOQUE":["PRODUTO","ESTOQUE"],"VENDAS":["DATA","PRODUTO"],"COMPRAS":["DATA","CUSTO"]}.get(nome,["PRODUTO"])
    linha = detectar_linha_cabecalho(df_raw, busca)
    if linha is None: return None
    tmp = df_raw.copy()
    tmp.columns = tmp.iloc[linha]
    df = tmp.iloc[linha+1:].copy()
    df.columns = [str(c).strip() for c in df.columns]
    df = df.loc[:, ~df.columns.astype(str).str.contains("Unnamed")]
    return df.reset_index(drop=True)

# -------------------------------------------------
# CARREGAR PLANILHA
# -------------------------------------------------
try:
    xls = carregar_xlsx_from_url(URL_PLANILHA)
except:
    st.error("Não foi possível carregar a planilha.")
    st.stop()

abas = xls.sheet_names
dfs = {}

for aba in ["ESTOQUE","VENDAS","COMPRAS"]:
    if aba in abas:
        raw = pd.read_excel(URL_PLANILHA, sheet_name=aba, header=None)
        dfs[aba] = limpar_aba_raw(raw, aba)
# -------------------------------------------------
# AJUSTAR ESTOQUE
# -------------------------------------------------
if "ESTOQUE" in dfs and dfs["ESTOQUE"] is not None:
    df_e = dfs["ESTOQUE"].copy()

    col_map = {
        "Media C. UNITARIO": ["Media C. UNITARIO","MEDIA CUSTO UNITARIO","CUSTO"],
        "Valor Venda Sugerido": ["Valor Venda Sugerido","VALOR VENDA","VENDA"],
        "EM ESTOQUE": ["EM ESTOQUE","ESTOQUE","QTD","QUANTIDADE"]
    }

    for target, opts in col_map.items():
        for op in opts:
            if op in df_e.columns:

                # -------------- PATCH DEFINITIVO ANTI ERRO ----------------
                if "VALOR" in target.upper() or "C." in target:
                    df_e[target] = parse_money_series(df_e[op]).fillna(0)
                else:
                    df_e[target] = (
                        pd.to_numeric(df_e[op], errors="coerce")
                        .fillna(0)
                        .astype(int)
                    )
                # -----------------------------------------------------------

                break

    if "PRODUTO" not in df_e.columns:
        df_e.rename(columns={df_e.columns[0]:"PRODUTO"}, inplace=True)

    # Cálculos de totais
    df_e["VALOR_CUSTO_TOTAL"] = df_e["Media C. UNITARIO"] * df_e["EM ESTOQUE"]
    df_e["VALOR_VENDA_TOTAL"] = df_e["Valor Venda Sugerido"] * df_e["EM ESTOQUE"]

    dfs["ESTOQUE"] = df_e

# -------------------------------------------------
# AJUSTAR VENDAS
# -------------------------------------------------
if "VENDAS" in dfs and dfs["VENDAS"] is not None:
    df_v = dfs["VENDAS"].copy()

    colmap = {
        "VALOR VENDA":["VALOR VENDA","VALOR_VENDA"],
        "VALOR TOTAL":["VALOR TOTAL","VALOR_TOTAL"],
        "MEDIA CUSTO UNITARIO":["MEDIA CUSTO UNITARIO","MEDIA C. UNITARIO"],
        "LUCRO UNITARIO":["LUCRO UNITARIO","LUCRO_UNITARIO"],
        "QTD":["QTD","QUANTIDADE"]
    }

    for target, opts in colmap.items():
        for op in opts:
            if op in df_v.columns:

                if "VALOR" in target.upper() or "CUSTO" in target or "LUCRO" in target:
                    df_v[target] = parse_money_series(df_v[op]).fillna(0)
                else:
                    df_v[target] = (
                        pd.to_numeric(df_v[op], errors="coerce")
                        .fillna(0)
                        .astype(int)
                    )
                break

    if "DATA" in df_v.columns:
        df_v["DATA"] = pd.to_datetime(df_v["DATA"], errors="coerce")
        df_v["MES_ANO"] = df_v["DATA"].dt.strftime("%Y-%m")

    # Calcular total caso não exista
    if "VALOR TOTAL" not in df_v.columns:
        df_v["VALOR TOTAL"] = df_v["VALOR VENDA"] * df_v["QTD"]

    # Calcular lucro total
    if "LUCRO TOTAL" not in df_v.columns and "LUCRO UNITARIO" in df_v.columns:
        df_v["LUCRO TOTAL"] = df_v["LUCRO UNITARIO"] * df_v["QTD"]

    df_v = df_v.sort_values("DATA", ascending=False)
    dfs["VENDAS"] = df_v

# -------------------------------------------------
# AJUSTAR COMPRAS
# -------------------------------------------------
if "COMPRAS" in dfs and dfs["COMPRAS"] is not None:
    df_c = dfs["COMPRAS"].copy()

    # quantidade
    qcols = [c for c in df_c.columns if "QUANT" in c.upper()]
    if qcols:
        df_c["QUANTIDADE"] = (
            pd.to_numeric(df_c[qcols[0]], errors="coerce")
            .fillna(0)
            .astype(int)
        )

    # custo unitário
    ccols = [c for c in df_c.columns if any(x in c.upper() for x in ["CUSTO","UNIT"])]
    if ccols:
        df_c["CUSTO UNITÁRIO"] = parse_money_series(df_c[ccols[0]]).fillna(0)

    df_c["CUSTO TOTAL"] = df_c.get("QUANTIDADE",0) * df_c.get("CUSTO UNITÁRIO",0)

    if "DATA" in df_c.columns:
        df_c["DATA"] = pd.to_datetime(df_c["DATA"], errors="coerce")
        df_c["MES_ANO"] = df_c["DATA"].dt.strftime("%Y-%m")

    dfs["COMPRAS"] = df_c

# -------------------------------------------------
# KPI PRINCIPAL — CABEÇALHO INTELIGENTE
# -------------------------------------------------
st.title("📊 Painel Geral — Inteligência Comercial")

df_v = dfs.get("VENDAS", pd.DataFrame())

if not df_v.empty:

    total_vendido = df_v["VALOR TOTAL"].sum()
    total_lucro = df_v.get("LUCRO TOTAL", pd.Series()).sum()
    qtd_itens = df_v["QTD"].sum()

    k1, k2, k3 = st.columns(3)

    with k1:
        st.markdown(f"""
        <div class='kpi'><h3>Total Vendido</h3>
        <div class='value'>{formatar_reais_sem_centavos(total_vendido)}</div></div>
        """, unsafe_allow_html=True)

    with k2:
        st.markdown(f"""
        <div class='kpi'><h3>Lucro Total</h3>
        <div class='value'>{formatar_reais_sem_centavos(total_lucro)}</div></div>
        """, unsafe_allow_html=True)

    with k3:
        st.markdown(f"""
        <div class='kpi'><h3>Itens Vendidos</h3>
        <div class='value'>{qtd_itens}</div></div>
        """, unsafe_allow_html=True)
# -------------------------------------------------
# GRÁFICOS PRINCIPAIS — ANÁLISE DO NEGÓCIO
# -------------------------------------------------
st.subheader("📈 Panorama Geral do Negócio")

if not df_v.empty:

    colA, colB = st.columns(2)

    # -------------------------
    # GRÁFICO 1 — Vendas por mês
    # -------------------------
    vendas_mes = df_v.groupby("MES_ANO")["VALOR TOTAL"].sum().reset_index()

    fig1 = px.line(
        vendas_mes,
        x="MES_ANO", y="VALOR TOTAL",
        markers=True,
        title="Evolução das Vendas Mensais",
    )
    fig1.update_traces(line_width=3)
    fig1.update_layout(
        height=350,
        xaxis_title="Mês",
        yaxis_title="R$",
        hovermode="x unified",
        showlegend=False
    )

    with colA:
        st.plotly_chart(fig1, use_container_width=True)

    # -------------------------
    # GRÁFICO 2 — Itens mais vendidos (quantidade)
    # -------------------------
    top_itens = (
        df_v.groupby("PRODUTO")["QTD"]
        .sum()
        .sort_values(ascending=False)
        .head(5)
        .reset_index()
    )

    fig2 = px.bar(
        top_itens,
        x="QTD", y="PRODUTO",
        orientation="h",
        title="Top 5 Produtos Mais Vendidos",
    )
    fig2.update_layout(height=350, xaxis_title="Quantidade")

    with colB:
        st.plotly_chart(fig2, use_container_width=True)

    # -------------------------
    # IA — Insights Automáticos
    # -------------------------
    st.markdown("### 🤖 Inteligência Comercial — Insights Automáticos")

    ultimomes = vendas_mes.iloc[-1]["VALOR TOTAL"] if len(vendas_mes) > 0 else 0
    mespassado = vendas_mes.iloc[-2]["VALOR TOTAL"] if len(vendas_mes) > 1 else 0

    dif = ultimomes - mespassado
    perc = (dif / mespassado * 100) if mespassado > 0 else 0

    tendencia = (
        "📈 Crescimento forte" if perc > 15 else
        "📉 Queda acentuada" if perc < -15 else
        "🟣 Estabilidade"
    )

    st.info(f"""
**Tendência do mês:** {tendencia}  
• Vendas deste mês: **{formatar_reais_sem_centavos(ultimomes)}**  
• Mês anterior: **{formatar_reais_sem_centavos(mespassado)}**  
• Variação: **{perc:.1f}%**
""")

    # -------------------------
    # Projeção IA — média móvel
    # -------------------------
    vendas_mes["MM3"] = vendas_mes["VALOR TOTAL"].rolling(3).mean()

    if vendas_mes["MM3"].notna().any():
        proximo = vendas_mes["MM3"].iloc[-1]
        st.success(f"🧠 **Projeção de vendas do próximo mês:** {formatar_reais_sem_centavos(proximo)}")

# -------------------------------------------------
# ABAS DO SISTEMA
# -------------------------------------------------
st.markdown("---")
tabs = st.tabs(["📦 Estoque", "💰 Vendas", "🧾 Compras", "🔍 Pesquisar (IA)"])
# ==============================================================
# 📦 ABA — ESTOQUE
# ==============================================================
with tabs[0]:
    st.subheader("📦 Estoque Atual")

    df_e = dfs.get("ESTOQUE", pd.DataFrame())

    if not df_e.empty:

        # Ordenar por estoque baixo
        df_e_sorted = df_e.sort_values("EM ESTOQUE")

        st.dataframe(
            df_e_sorted[["PRODUTO","EM ESTOQUE","Media C. UNITARIO","Valor Venda Sugerido","VALOR_CUSTO_TOTAL","VALOR_VENDA_TOTAL"]],
            use_container_width=True
        )

        # Estoque crítico
        crit = df_e[df_e["EM ESTOQUE"] <= 3]

        if not crit.empty:
            st.warning("⚠️ Produtos com estoque crítico:")
            st.dataframe(crit[["PRODUTO","EM ESTOQUE","Valor Venda Sugerido"]], use_container_width=True)

# ==============================================================
# 💰 ABA — VENDAS
# ==============================================================
with tabs[1]:
    st.subheader("💰 Vendas")

    df_v = dfs.get("VENDAS", pd.DataFrame())

    if not df_v.empty:

        # Filtro por período
        meses = df_v["MES_ANO"].unique().tolist()
        meses_sel = st.multiselect("Filtrar por mês:", meses, default=meses[:1])

        df_filtrado = df_v[df_v["MES_ANO"].isin(meses_sel)] if meses_sel else df_v

        st.dataframe(df_filtrado, use_container_width=True)

        # Gráfico diário
        df_dia = df_filtrado.groupby("DATA")["VALOR TOTAL"].sum().reset_index()

        fig3 = px.bar(df_dia, x="DATA", y="VALOR TOTAL", title="Vendas por Dia")
        fig3.update_layout(height=350, xaxis_title="Data", yaxis_title="R$")

        st.plotly_chart(fig3, use_container_width=True)

# ==============================================================
# 🧾 ABA — COMPRAS
# ==============================================================
with tabs[2]:
    st.subheader("🧾 Compras")

    df_c = dfs.get("COMPRAS", pd.DataFrame())

    if not df_c.empty:
        st.dataframe(df_c, use_container_width=True)

        # Gráfico compras
        df_comp = df_c.groupby("DATA")["CUSTO TOTAL"].sum().reset_index()
        fig4 = px.line(df_comp, x="DATA", y="CUSTO TOTAL", markers=True, title="Custo diário de compras")
        fig4.update_layout(height=350, xaxis_title="Data", yaxis_title="R$")
        st.plotly_chart(fig4, use_container_width=True)

# ==============================================================
# 🔍 PESQUISAR (IA) — BUSCA PREMIUM
# ==============================================================

with tabs[3]:
    st.subheader("🔍 Buscar Produto — Inteligência Comercial")

    df_e = dfs.get("ESTOQUE", pd.DataFrame())
    df_v = dfs.get("VENDAS", pd.DataFrame())

    if df_e.empty:
        st.error("Nenhum dado de estoque disponível.")
        st.stop()

    # Campo de busca estilizado
    st.markdown("#### 🔎 Pesquisa")
    col_b1, col_b2 = st.columns([4,1])

    with col_b1:
        termo = st.text_input(
            " ",
            placeholder="Digite parte do nome do produto...",
            key="search_box",
            label_visibility="collapsed"
        )
    with col_b2:
        buscar = st.button("🔍 Buscar", use_container_width=True)

    # Filtros premium (pills)
    st.markdown("#### 🎛️ Filtros inteligentes")

    colf = st.columns(5)
    filtros = {
        "estoque_baixo": colf[0].checkbox("📉 Estoque baixo"),
        "estoque_alto": colf[1].checkbox("📦 Estoque alto"),
        "preco_baixo": colf[2].checkbox("💸 Mais barato"),
        "preco_alto": colf[3].checkbox("💰 Mais caro"),
        "alphabetico": colf[4].checkbox("🔤 A–Z"),
    }

    # Aplicar busca
    df_busca = df_e.copy()

    if buscar and termo.strip() != "":
        df_busca = df_busca[df_busca["PRODUTO"].str.contains(termo, case=False, na=False)]

    # Aplicar filtros
    if filtros["estoque_baixo"]:
        df_busca = df_busca[df_busca["EM ESTOQUE"] <= 3]

    if filtros["estoque_alto"]:
        df_busca = df_busca[df_busca["EM ESTOQUE"] >= 20]

    if filtros["preco_baixo"]:
        df_busca = df_busca.sort_values("Valor Venda Sugerido", ascending=True)

    if filtros["preco_alto"]:
        df_busca = df_busca.sort_values("Valor Venda Sugerido", ascending=False)

    if filtros["alphabetico"]:
        df_busca = df_busca.sort_values("PRODUTO")

    # IA — Determinar movimentação do produto
    def tag_movimentacao(prod):
        if df_v.empty:
            return "🟣 Sem dados"
        vendas_prod = df_v[df_v["PRODUTO"].str.lower() == prod.lower()]
        qtd = vendas_prod["QTD"].sum()

        if qtd >= 20:
            return "🔥 Alta procura"
        elif qtd >= 5:
            return "🟡 Estável"
        elif qtd == 0:
            return "❄️ Sem saída"
        else:
            return "⚠️ Baixa movimentação"

    # Mostrar em grade de cards
    if not df_busca.empty:

        st.markdown("### 📦 Resultados")

        st.markdown("<div class='card-grid'>", unsafe_allow_html=True)

        for _, row in df_busca.iterrows():

            badge = tag_movimentacao(row["PRODUTO"])
            preco = formatar_reais_sem_centavos(row["Valor Venda Sugerido"])
            custo = formatar_reais_sem_centavos(row["Media C. UNITARIO"])

            st.markdown(f"""
            <div class='product-card'>
                <div class='product-title'>{row["PRODUTO"]}</div>
                <div style='margin-top:6px;'>
                    <span class='card-badge'>{badge}</span>
                </div>

                <p style='margin-top:12px;'>
                <strong>Estoque:</strong> {int(row["EM ESTOQUE"])}<br>
                <strong>Preço venda:</strong> {preco}<br>
                <strong>Custo médio:</strong> {custo}<br>
                <strong>Total venda:</strong> {formatar_reais_sem_centavos(row["VALOR_VENDA_TOTAL"])}<br>
                </p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    else:
        st.info("🔍 Nenhum produto encontrado.")

