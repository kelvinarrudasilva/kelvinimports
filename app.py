# ================================================
# app.py – Dashboard Loja Importados (compatível com seu Excel)
# - Detecta header na 2ª linha (ignora 1ª linha)
# - Limpa Unnamed
# - Auto-detecta colunas PRODUTO / DATA / QTD / VALORES
# - Top5 (últimos 90 dias) + faturamento semanal + tabela
# - Sem abas TOP10
# ================================================

import streamlit as st
import pandas as pd
import plotly.express as px
import re
from datetime import datetime, timedelta
import requests
from io import BytesIO

st.set_page_config(page_title="Loja Importados – Dashboard", layout="wide")

# ---------- CONFIG ----------
URL_PLANILHA = "https://docs.google.com/spreadsheets/d/1TsRjsfw1TVfeEWBBvhKvsGQ5YUCktn2b/export?format=xlsx"
# se quiser testar localmente, substitua acima pelo caminho do arquivo xlsx: "file:///mnt/data/KELVIN IMPORTADOS 2026.xlsx"

# ---------- CSS (dark roxo) ----------
st.markdown("""
<style>
:root{
  --bg:#0b0b0b; --card:#141414; --accent:#8b5cf6; --accent2:#a78bfa; --text:#f2f2f2;
}
body, .stApp { background:var(--bg) !important; color:var(--text) !important; font-family: Inter, system-ui, -apple-system, 'Segoe UI', Roboto; }
.kpi-box{ background:var(--card); padding:12px 14px; border-radius:12px; border-left:5px solid var(--accent); box-shadow:0 6px 18px rgba(0,0,0,0.45); }
.small { font-size:12px; color:#bdbdbd; }
</style>
""", unsafe_allow_html=True)


# ---------- HELPERS ----------
def baixar_xlsx(url):
    r = requests.get(url, timeout=25)
    r.raise_for_status()
    return BytesIO(r.content)

def detectar_linha_cabecalho(df_raw, keywords):
    """Procura a linha (índice) que contém uma das keywords na concatenação da linha (até 12 primeiras linhas)."""
    for i in range(min(len(df_raw), 12)):
        linha = " ".join(df_raw.iloc[i].astype(str).astype(str).str.upper().tolist())
        if any(kw.upper() in linha for kw in keywords):
            return i
    return None

def carregar_e_limpar_sheet(xls_obj, sheet_name, busca_keywords=None):
    """
    Lê planilha com header=None, detecta a linha de cabeçalho por keywords (ou heurística),
    aplica esse header e devolve dataframe limpo (colunas sem Unnamed).
    """
    raw = pd.read_excel(xls_obj, sheet_name=sheet_name, header=None, dtype=object)
    # heurística: se a segunda linha (index 1) contém strings plausíveis de cabeçalho, use-a
    header_idx = None
    if busca_keywords:
        header_idx = detectar_linha_cabecalho(raw, busca_keywords)
    if header_idx is None:
        # fallback: usar a primeira linha não totalmente vazia que contenha >=2 strings
        for i in range(min(len(raw), 10)):
            non_null = raw.iloc[i].astype(str).replace("nan","").replace("None","").map(lambda s: s.strip()).replace("","").size
            # simpler heuristic: check how many non-empty cells
            nz = (raw.iloc[i].astype(str).str.strip().replace("nan","").replace("None","") != "").sum()
            if nz >= 2:
                header_idx = i
                break
    if header_idx is None:
        header_idx = 0

    df_tmp = raw.copy()
    df_tmp.columns = df_tmp.iloc[header_idx].astype(str).map(lambda x: x.strip())
    df = df_tmp.iloc[header_idx+1:].copy().reset_index(drop=True)

    # drop all-empty columns
    df = df.loc[:, ~df.isna().all()]

    # clean column names: strip, replace multiple spaces, unify to simple strings
    df.columns = [re.sub(r"\s+", " ", str(c)).strip() for c in df.columns]

    # drop columns that are named like 'Unnamed' or empty
    df = df[[c for c in df.columns if not (str(c).strip()=="" or str(c).upper().startswith("UNNAMED"))]]

    return df

def limpar_moeda(x):
    if pd.isna(x): return 0.0
    s = str(x)
    s = s.replace("R$", "").replace(".", "").replace(",", ".")
    s = re.sub(r"[^\d\.\-]", "", s)
    try:
        return float(s)
    except:
        try:
            return float(s.replace(",", "."))
        except:
            return 0.0

def formatar_reais_sem_centavos(v):
    try:
        v = float(v)
    except:
        return "R$ 0"
    s = f"{v:,.0f}".replace(",", ".")
    return f"R$ {s}"

def detectar_coluna_por_candidatos(df, candidatos):
    if df is None or df.empty: return None
    for c in df.columns:
        cu = str(c).upper().replace(" ", "")
        for cand in candidatos:
            if cand.upper().replace(" ", "") in cu:
                return c
    return None

def detectar_produto(df):
    candidatos = ["PRODUTO", "PROD", "PRODUCT", "ITEM", "NOME", "DESCRI", "DESC", "TITLE"]
    col = detectar_coluna_por_candidatos(df, candidatos)
    if col: return col
    # fallback: primeira coluna do tipo object
    for c in df.columns:
        if df[c].dtype == object:
            return c
    return None

def detectar_qtd(df):
    candidatos = ["QTD", "QUANT", "QTY", "UNIDADES", "QTD_VENDA"]
    col = detectar_coluna_por_candidatos(df, candidatos)
    if col: return col
    # fallback: numeric int-like
    for c in df.columns:
        if pd.api.types.is_integer_dtype(df[c]) or pd.api.types.is_float_dtype(df[c]):
            return c
    return None

def detectar_valor_unitario(df):
    candidatos = ["VALORVENDA", "VALOR VENDA", "VALOR", "PRECO", "PRICE", "UNIT"]
    return detectar_coluna_por_candidatos(df, candidatos)

def detectar_valor_total_candidate(df):
    candidatos = ["VALOR TOTAL", "VALOR_TOTAL", "TOTAL", "VALORTOTAL", "VALORTOTAL"]
    return detectar_coluna_por_candidatos(df, candidatos)


# ---------- CARREGAR ARQUIVO ----------
try:
    arquivo_bytes = baixar_xlsx(URL_PLANILHA)
    xls = pd.ExcelFile(arquivo_bytes)
except Exception as e:
    st.error("Erro ao baixar/abrir a planilha. Verifique a URL ou conexão.")
    st.exception(e)
    st.stop()

# Carregar e limpar folhas (usando keywords que vimos na sua planilha)
dfs = {}
if "VENDAS" in xls.sheet_names:
    dfs["VENDAS"] = carregar_e_limpar_sheet(arquivo_bytes, "VENDAS", busca_keywords=["DATA","PRODUTO","QTD"])
if "COMPRAS" in xls.sheet_names:
    dfs["COMPRAS"] = carregar_e_limpar_sheet(arquivo_bytes, "COMPRAS", busca_keywords=["DATA","CUSTO","QUANT"])
if "ESTOQUE" in xls.sheet_names:
    dfs["ESTOQUE"] = carregar_e_limpar_sheet(arquivo_bytes, "ESTOQUE", busca_keywords=["PRODUTO","EM ESTOQUE","MEDIA C. UNITARIO"])

# ---------- NORMALIZAR VENDAS ----------
if "VENDAS" in dfs:
    vendas = dfs["VENDAS"].copy()
    # Trim strings
    vendas.columns = [str(c).strip() for c in vendas.columns]

    # detectar colunas
    col_data = detectar_coluna_por_candidatos(vendas, ["DATA", "DT", "DIA", "DATE"])
    col_prod = detectar_produto(vendas)
    col_qtd = detectar_qtd(vendas)
    col_val_unit = detectar_valor_unitario(vendas)
    col_val_total = detectar_valor_total_candidate(vendas)

    # Renomear para padronizar (se existirem)
    if col_data: vendas = vendas.rename(columns={col_data: "DATA"})
    if col_prod: vendas = vendas.rename(columns={col_prod: "PRODUTO"})
    if col_qtd: vendas = vendas.rename(columns={col_qtd: "QTD"})
    if col_val_unit: vendas = vendas.rename(columns={col_val_unit: "VALOR VENDA"})
    if col_val_total: vendas = vendas.rename(columns={col_val_total: "VALOR TOTAL"})

    # Converter DATA
    if "DATA" in vendas.columns:
        vendas["DATA"] = pd.to_datetime(vendas["DATA"], errors="coerce")
    else:
        vendas["DATA"] = pd.NaT

    # QTD numeric
    if "QTD" in vendas.columns:
        vendas["QTD"] = pd.to_numeric(vendas["QTD"], errors="coerce").fillna(0).astype(int)
    else:
        vendas["QTD"] = 0

    # Valores
    if "VALOR TOTAL" in vendas.columns:
        vendas["VALOR TOTAL"] = vendas["VALOR TOTAL"].map(limpar_moeda)
    else:
        if "VALOR VENDA" in vendas.columns:
            vendas["VALOR VENDA"] = vendas["VALOR VENDA"].map(limpar_moeda)
            vendas["VALOR TOTAL"] = vendas["VALOR VENDA"].fillna(0) * vendas["QTD"].fillna(0)
        else:
            vendas["VALOR TOTAL"] = 0.0

    # coluna PRODUTO check
    if "PRODUTO" not in vendas.columns:
        # tenta nome alternativo
        alt = detectar_produto(vendas)
        if alt:
            vendas = vendas.rename(columns={alt: "PRODUTO"})
        else:
            vendas["PRODUTO"] = "SEM_PRODUTO"

    vendas["MES_ANO"] = vendas["DATA"].dt.strftime("%Y-%m")
else:
    vendas = pd.DataFrame()

# ---------- NORMALIZAR COMPRAS ----------
if "COMPRAS" in dfs:
    compras = dfs["COMPRAS"].copy()
    compras.columns = [str(c).strip() for c in compras.columns]

    col_data_c = detectar_coluna_por_candidatos(compras, ["DATA", "DT", "DIA"])
    col_qtd_c = detectar_coluna_por_candidatos(compras, ["QTD", "QUANT", "QTY"])
    col_custo_c = detectar_coluna_por_candidatos(compras, ["CUSTO", "PRECO", "VALOR", "UNIT"])

    if col_data_c: compras = compras.rename(columns={col_data_c: "DATA"})
    if col_qtd_c: compras = compras.rename(columns={col_qtd_c: "QUANTIDADE"})
    if col_custo_c: compras = compras.rename(columns={col_custo_c: "CUSTO UNITARIO"})

    if "DATA" in compras.columns:
        compras["DATA"] = pd.to_datetime(compras["DATA"], errors="coerce")
    compras["QUANTIDADE"] = pd.to_numeric(compras.get("QUANTIDADE", 0), errors="coerce").fillna(0).astype(int)
    if "CUSTO UNITARIO" in compras.columns:
        compras["CUSTO UNITARIO"] = compras["CUSTO UNITARIO"].map(limpar_moeda)
    else:
        compras["CUSTO UNITARIO"] = 0.0
    compras["CUSTO TOTAL (RECALC)"] = compras["QUANTIDADE"] * compras["CUSTO UNITARIO"]
    if "DATA" in compras.columns:
        compras["MES_ANO"] = compras["DATA"].dt.strftime("%Y-%m")
else:
    compras = pd.DataFrame()

# ---------- NORMALIZAR ESTOQUE ----------
if "ESTOQUE" in dfs:
    estoque = dfs["ESTOQUE"].copy()
    estoque.columns = [str(c).strip() for c in estoque.columns]

    col_prod_e = detectar_produto(estoque)
    col_qtd_e = detectar_coluna_por_candidatos(estoque, ["EM ESTOQUE", "ESTOQUE", "QTD", "QUANT"])
    col_media_custo = detectar_coluna_por_candidatos(estoque, ["MEDIA", "MEDIA C.", "MEDIA C", "CUSTO"])
    col_venda_sugerida = detectar_coluna_por_candidatos(estoque, ["VALOR VENDA", "VALORVENDA", "VENDA", "PRECO"])

    if col_prod_e: estoque = estoque.rename(columns={col_prod_e: "PRODUTO"})
    if col_qtd_e: estoque = estoque.rename(columns={col_qtd_e: "EM ESTOQUE"})
    if col_media_custo: estoque = estoque.rename(columns={col_media_custo: "Media C. UNITARIO"})
    if col_venda_sugerida: estoque = estoque.rename(columns={col_venda_sugerida: "Valor Venda Sugerido"})

    # types
    if "EM ESTOQUE" in estoque.columns:
        estoque["EM ESTOQUE"] = pd.to_numeric(estoque["EM ESTOQUE"], errors="coerce").fillna(0).astype(int)
    else:
        estoque["EM ESTOQUE"] = 0

    if "Media C. UNITARIO" in estoque.columns:
        estoque["Media C. UNITARIO"] = estoque["Media C. UNITARIO"].map(limpar_moeda).fillna(0)
    else:
        estoque["Media C. UNITARIO"] = 0.0

    if "Valor Venda Sugerido" in estoque.columns:
        estoque["Valor Venda Sugerido"] = estoque["Valor Venda Sugerido"].map(limpar_moeda).fillna(0)
    else:
        estoque["Valor Venda Sugerido"] = 0.0

    estoque["VALOR_CUSTO_TOTAL"] = estoque["Media C. UNITARIO"] * estoque["EM ESTOQUE"]
    estoque["VALOR_VENDA_TOTAL"] = estoque["Valor Venda Sugerido"] * estoque["EM ESTOQUE"]
else:
    estoque = pd.DataFrame()

# ---------- FILTRO MÊS (para vendas/compras) ----------
meses = ["Todos"]
if not vendas.empty:
    meses += sorted(vendas["MES_ANO"].dropna().unique().tolist(), reverse=True)
mes_atual = datetime.now().strftime("%Y-%m")
index_padrao = meses.index(mes_atual) if mes_atual in meses else 0
mes_selecionado = st.selectbox("Filtrar por mês (YYYY-MM):", meses, index=index_padrao)

def filtrar_mes(df, mes):
    if df is None or df.empty: return pd.DataFrame()
    if mes == "Todos": return df
    if "MES_ANO" in df.columns:
        return df[df["MES_ANO"] == mes].copy()
    return df

vendas_filtradas = filtrar_mes(vendas, mes_selecionado)
compras_filtradas = filtrar_mes(compras, mes_selecionado)

# ---------- KPIs ----------
valor_total_vendido = vendas_filtradas["VALOR TOTAL"].sum() if not vendas_filtradas.empty else 0
valor_total_lucro_est = 0  # optional - can compute if columns exist
total_compras = compras_filtradas.get("CUSTO TOTAL (RECALC)", compras_filtradas.get("CUSTO TOTAL (RECALC)", pd.Series(dtype=float))).sum() if not compras_filtradas.empty else 0
valor_custo_estoque = estoque["VALOR_CUSTO_TOTAL"].sum() if not estoque.empty else 0
valor_venda_estoque = estoque["VALOR_VENDA_TOTAL"].sum() if not estoque.empty else 0
qtde_total_itens = int(estoque["EM ESTOQUE"].sum()) if not estoque.empty else 0

col_filter, col_kpis = st.columns([1,3])
with col_kpis:
    st.markdown(f"""
    <div class="kpi-box" style="display:flex;gap:12px;flex-wrap:wrap;">
      <div style="min-width:180px"><h4>💵 Total Vendido</h4><h2>{formatar_reais_sem_centavos(valor_total_vendido)}</h2></div>
      <div style="min-width:180px"><h4>💸 Total Compras</h4><h2>{formatar_reais_sem_centavos(total_compras)}</h2></div>
      <div style="min-width:180px"><h4>📦 Valor Custo Estoque</h4><h2>{formatar_reais_sem_centavos(valor_custo_estoque)}</h2></div>
      <div style="min-width:180px"><h4>🏷 Valor Venda Estoque</h4><h2>{formatar_reais_sem_centavos(valor_venda_estoque)}</h2></div>
      <div style="min-width:160px"><h4>🔢 Qtde Total Itens</h4><h2>{qtde_total_itens}</h2></div>
    </div>
    """, unsafe_allow_html=True)

# ---------- Abas (SEM TOP10) ----------
tabs = st.tabs(["🛒 VENDAS", "📦 ESTOQUE", "🔍 PESQUISAR"])

# ---------- ABA VENDAS ----------
with tabs[0]:
    st.subheader("Vendas — período selecionado")

    if vendas_filtradas is None or vendas_filtradas.empty:
        st.info("Sem dados de vendas para o período selecionado.")
    else:
        # ---------- TOP5 últimos 90 dias ----------
        st.markdown("### 🏆 Top 5 produtos mais vendidos (últimos 90 dias)")

        # Precauções: garantir colunas PRODUTO e QTD
        if "PRODUTO" in vendas.columns and "QTD" in vendas.columns:
            cutoff = datetime.now() - timedelta(days=90)
            df_hist = vendas.copy()
            if "DATA" in df_hist.columns:
                df_hist = df_hist[df_hist["DATA"] >= cutoff]
            # group safe
            if not df_hist.empty:
                top5 = df_hist.groupby("PRODUTO", dropna=False)["QTD"].sum().reset_index().sort_values("QTD", ascending=False).head(5)
                if not top5.empty:
                    fig_top5 = px.bar(
                        top5,
                        x="QTD",
                        y="PRODUTO",
                        orientation="h",
                        text="QTD",
                        color_discrete_sequence=["#8b5cf6"],
                        height=380
                    )
                    fig_top5.update_traces(textposition="inside")
                    fig_top5.update_layout(plot_bgcolor="#0b0b0b", paper_bgcolor="#0b0b0b", font_color="#f2f2f2")
                    st.plotly_chart(fig_top5, use_container_width=True, config={"displayModeBar": False})
                else:
                    st.info("Não há vendas nos últimos 90 dias.")
            else:
                st.info("Não há registros com DATA dentro dos últimos 90 dias.")
        else:
            st.warning("Não foi possível detectar colunas 'PRODUTO' e/ou 'QTD' na aba VENDAS. Verifique a planilha.")

        # ---------- FATURAMENTO SEMANAL ----------
        st.markdown("### 📅 Faturamento Semanal (período selecionado)")

        df_sem = vendas_filtradas.copy()
        if "DATA" in df_sem.columns and df_sem["DATA"].notna().any():
            df_sem = df_sem.dropna(subset=["DATA"])
            df_sem["SEMANA"] = df_sem["DATA"].dt.isocalendar().week
            df_sem["ANO"] = df_sem["DATA"].dt.year
            df_week = df_sem.groupby(["ANO", "SEMANA"], dropna=False)["VALOR TOTAL"].sum().reset_index()
            def intervalo_sem(row):
                try:
                    ini = datetime.fromisocalendar(int(row["ANO"]), int(row["SEMANA"]), 1)
                    fim = ini + timedelta(days=6)
                    return f"{ini.strftime('%d/%m')} → {fim.strftime('%d/%m')}"
                except:
                    return "N/A"
            df_week["INTERVALO"] = df_week.apply(intervalo_sem, axis=1)
            df_week["LABEL"] = df_week["VALOR TOTAL"].apply(formatar_reais_sem_centavos)
            fig_sem = px.bar(df_week, x="INTERVALO", y="VALOR TOTAL", text="LABEL", color_discrete_sequence=["#8b5cf6"], height=380)
            fig_sem.update_traces(textposition="inside")
            fig_sem.update_layout(plot_bgcolor="#0b0b0b", paper_bgcolor="#0b0b0b", font_color="#f2f2f2")
            st.plotly_chart(fig_sem, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("Sem data válida para gerar gráfico semanal.")

        # ---------- TABELA DE VENDAS ----------
        st.markdown("### 📄 Tabela de Vendas")
        display_cols = [c for c in ["DATA", "PRODUTO", "QTD", "VALOR VENDA", "VALOR TOTAL", "MEDIA C. UNITARIO", "LUCRO UNITARIO"] if c in vendas_filtradas.columns]
        if not display_cols:
            # fallback: exibir todas as colunas
            st.dataframe(vendas_filtradas.reset_index(drop=True), use_container_width=True)
        else:
            df_disp = vendas_filtradas[display_cols].copy()
            # formatar valores se existirem
            if "VALOR TOTAL" in df_disp.columns:
                df_disp["VALOR TOTAL"] = df_disp["VALOR TOTAL"].map(lambda x: formatar_reais_sem_centavos(limpar_moeda(x)))
            if "VALOR VENDA" in df_disp.columns:
                df_disp["VALOR VENDA"] = df_disp["VALOR VENDA"].map(lambda x: formatar_reais_sem_centavos(limpar_moeda(x)))
            st.dataframe(df_disp.sort_values("DATA", ascending=False).reset_index(drop=True), use_container_width=True)

# ---------- ABA ESTOQUE ----------
with tabs[1]:
    st.subheader("📦 Estoque — visão detalhada")
    if estoque is None or estoque.empty:
        st.info("Sem dados de estoque.")
    else:
        display_cols_e = [c for c in ["PRODUTO", "EM ESTOQUE", "Media C. UNITARIO", "Valor Venda Sugerido", "VALOR_CUSTO_TOTAL", "VALOR_VENDA_TOTAL"] if c in estoque.columns]
        df_est = estoque.copy()
        if "EM ESTOQUE" in df_est.columns:
            fig_e = px.bar(df_est.sort_values("EM ESTOQUE", ascending=False).head(25), x="PRODUTO", y="EM ESTOQUE", text="EM ESTOQUE", color_discrete_sequence=["#8b5cf6"], height=380)
            fig_e.update_traces(textposition="inside")
            fig_e.update_layout(plot_bgcolor="#0b0b0b", paper_bgcolor="#0b0b0b", font_color="#f2f2f2")
            st.plotly_chart(fig_e, use_container_width=True, config={"displayModeBar": False})
        st.dataframe(df_est[display_cols_e].sort_values("EM ESTOQUE", ascending=False).reset_index(drop=True), use_container_width=True)

# ---------- ABA PESQUISAR ----------
with tabs[2]:
    st.subheader("🔍 Pesquisar produto no estoque")
    termo = st.text_input("Digite parte do nome:")
    if termo and (estoque is not None and not estoque.empty and "PRODUTO" in estoque.columns):
        res = estoque[estoque["PRODUTO"].astype(str).str.contains(termo, case=False, na=False)]
        if res.empty:
            st.info("Nenhum produto encontrado.")
        else:
            st.dataframe(res.reset_index(drop=True), use_container_width=True)
    elif termo:
        st.warning("Sem dados de estoque ou coluna PRODUTO ausente para buscar.")

# ---------- RODAPÉ ----------
st.markdown('<div class="small">Nota: este dashboard lê a planilha e detecta automaticamente cabeçalhos na segunda linha (formato que você enviou). Se algo ainda não aparecer, me envie as primeiras 5 linhas da aba especificada que eu ajusto rápido.</div>', unsafe_allow_html=True)
