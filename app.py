# app.py — Versão final robusta (não quebra se faltar colunas)
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import unicodedata
import io
import os

st.set_page_config(page_title="Painel de Estoque - Kelvin Arruda", layout="wide")
st.title("📊 KELVIN ARRUDA — Painel de Estoque")

ARQUIVO = "LOJA IMPORTADOS.xlsx"

# ---------- helpers ----------
def normalizar(txt):
    if not isinstance(txt, str):
        return ""
    txt = txt.strip()
    txt = unicodedata.normalize("NFKD", txt).encode("ASCII", "ignore").decode("utf-8")
    return txt.lower()

def fmt_real(x):
    try:
        return f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return ""

# tenta detectar coluna de produto de forma tolerante
def detectar_produto(df):
    # procura por palavras típicas
    keywords = ["produto", "prod", "descr", "item", "nome"]
    for c in df.columns:
        n = normalizar(c)
        for k in keywords:
            if k in n:
                return c
    # fallback: primeira coluna não numérica
    for c in df.columns:
        if not pd.api.types.is_numeric_dtype(df[c]):
            return c
    # ultimate fallback: None
    return None

def detectar_coluna_por_keywords(df, keys):
    for c in df.columns:
        n = normalizar(c)
        for k in keys:
            if k in n:
                return c
    return None

# ---------- leitura ----------
if not os.path.exists(ARQUIVO):
    st.error(f"❌ Arquivo '{ARQUIVO}' não encontrado na pasta do app.")
    st.stop()

try:
    # lê sem assumir header errado; tenta detectar header real se necessário
    df_try = pd.read_excel(ARQUIVO, header=0, engine="openpyxl")
except Exception as e:
    st.error(f"❌ Erro ao ler o Excel: {e}")
    st.stop()

# remove linhas/colunas vazias e padroniza col names
df_try = df_try.dropna(how="all").copy()
df_try.columns = [c if isinstance(c, str) else str(c) for c in df_try.columns]

# detecta colunas
prod_col = detectar_produto(df_try)
estoque_col = detectar_coluna_por_keywords(df_try, ["estoque", "quant", "qtd", "em estoque"])
preco_col = detectar_coluna_por_keywords(df_try, ["preco", "valor", "valor venda", "valor_venda", "valorvenda", "preço"])
vendas_col = detectar_coluna_por_keywords(df_try, ["venda", "vendido", "saída", "saida", "qtd vendida", "quantidade vendida"])

st.write("🔍 **Colunas detectadas (verifique)**")
st.json({
    "produto": prod_col if prod_col is not None else None,
    "estoque": estoque_col if estoque_col is not None else None,
    "preco_venda": preco_col if preco_col is not None else None,
    "vendas": vendas_col if vendas_col is not None else None,
})

# se estoque não foi detectado, tentamos heurística: segunda coluna numérica ou primeira numérica
if estoque_col is None:
    for c in df_try.columns:
        if pd.api.types.is_numeric_dtype(df_try[c]):
            estoque_col = c
            break

# se produto não detectado, cria coluna automática
df = df_try.copy()
if prod_col is None:
    st.warning("⚠️ Coluna de produto não detectada — irei criar nomes automáticos (Produto 1, Produto 2...).")
    df.insert(0, "Produto", [f"Produto {i+1}" for i in range(len(df))])
    prod_col = "Produto"
else:
    # use a coluna detectada como está
    pass

# se ainda não há coluna de estoque, aborta com instrução clara
if estoque_col is None:
    st.error("❌ Não foi possível identificar nenhuma coluna de estoque. Verifique o arquivo.")
    st.dataframe(df.head(10))
    st.stop()

# normaliza números nas colunas detectadas
for col in [estoque_col, preco_col, vendas_col]:
    if col and col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

# renomeia para nomes fixos no dataframe para facilitar uso
rename_map = {}
rename_map[prod_col] = "Produto"
rename_map[estoque_col] = "Estoque"
if preco_col:
    rename_map[preco_col] = "Preco_Venda"
if vendas_col:
    rename_map[vendas_col] = "Vendas"

df = df.rename(columns=rename_map)

# garante colunas existam
if "Produto" not in df.columns:
    df["Produto"] = [f"Produto {i+1}" for i in range(len(df))]
if "Estoque" not in df.columns:
    st.error("❌ Coluna de Estoque obrigatória não encontrada.")
    st.stop()

# limpa linhas sem produto nomeável
df = df[df["Produto"].astype(str).str.strip() != ""].copy()

# ----- KPIs e totais -----
total_skus = df["Produto"].nunique()
total_unidades = int(df["Estoque"].sum())

# calcula valor total em estoque só se preço disponível
valor_estoque = None
if "Preco_Venda" in df.columns:
    valor_estoque = (df["Estoque"] * df["Preco_Venda"]).sum()

# calcula total vendido se coluna existir
valor_vendido = None
if "Vendas" in df.columns and "Preco_Venda" in df.columns:
    valor_vendido = (df["Vendas"] * df["Preco_Venda"]).sum()
elif "Vendas" in df.columns:
    # sem preço, só soma quantidade vendida
    total_vendidos_qtd = int(df["Vendas"].sum())

# mostra KPIs
c1, c2, c3 = st.columns(3)
c1.metric("SKUs únicos", f"{total_skus}")
c2.metric("Unidades em estoque", f"{total_unidades:,}".replace(",", "."))
if valor_estoque is not None:
    c3.metric("Valor total em estoque", fmt_real(valor_estoque))
else:
    c3.metric("Valor total em estoque", "— (coluna de preço ausente)")

# resumo adicional
if "Vendas" in df.columns:
    if valor_vendido is not None:
        st.markdown(f"**Valor total vendido:** {fmt_real(valor_vendido)}")
    else:
        st.markdown(f"**Quantidade total vendida:** {int(df['Vendas'].sum())}")

st.markdown("---")

# ----- Formatação para exibição -----
tabela = df.copy()
if "Preco_Venda" in tabela.columns:
    tabela["Preco_Venda"] = tabela["Preco_Venda"].apply(lambda x: fmt_real(x))
if "Vendas" in tabela.columns:
    tabela["Vendas"] = tabela["Vendas"].astype(int)

# exibir tabela
st.subheader("📋 Tabela (formatada)")
st.dataframe(tabela, use_container_width=True)

# ----- Gráfico: top por estoque -----
st.subheader("📈 Top 15 por Estoque")
top_estoque = df.sort_values("Estoque", ascending=False).head(15)
fig, ax = plt.subplots(figsize=(10, 5))
ax.barh(top_estoque["Produto"][::-1], top_estoque["Estoque"][::-1])
ax.set_xlabel("Quantidade em Estoque")
ax.set_ylabel("Produto")
st.pyplot(fig)

# ----- Alertas de reposição -----
st.subheader("⚠️ Alertas de Reposição")
limite = st.sidebar.number_input("Alerta: estoque menor ou igual a", min_value=0, value=5)
low = df[df["Estoque"] <= limite][["Produto", "Estoque"]]
if low.empty:
    st.success("✅ Nenhum produto abaixo do limite.")
else:
    st.dataframe(low, use_container_width=True)

# ----- Exportar planilha limpa -----
st.subheader("📤 Exportar Estoque Limpo")
buf = io.BytesIO()
df.to_excel(buf, index=False)
st.download_button("💾 Baixar Excel limpo", buf.getvalue(), "estoque_limpo.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

st.caption("Pronto — sem drama. Se quiser, eu já adiciono 'Valor total por produto' no gráfico também.")
