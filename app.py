# =============================
# PESQUISAR (MODERNIZADA + ANIMADA — FINAL)
# =============================
with tabs[2]:

    # CSS — cards com animação, brilho, hover suave e texto claro
    st.markdown("""
    <style>

    /* Grid responsivo */
    .card-grid {
        display:grid;
        grid-template-columns: repeat(2, minmax(320px, 1fr));
        gap:22px;
        margin-top:18px;
    }
    @media (max-width: 800px) {
        .card-grid { grid-template-columns: 1fr; }
    }

    /* Card animado */
    .search-card {
        background:#141316;
        padding:18px;
        border-radius:14px;
        border:1px solid rgba(167,139,250,0.10);
        box-shadow:0 8px 22px rgba(0,0,0,0.45);
        transition: transform .18s ease, box-shadow .18s ease, border-color .18s ease;
        color:#f2f2f2;
    }
    .search-card:hover {
        transform: translateY(-7px) scale(1.015);
        box-shadow:0 12px 32px rgba(147,112,219,0.28);
        border-color: rgba(167,139,250,0.40);
    }

    .search-title {
        color:#c7b4ff;
        font-weight:900;
        font-size:16px;
        margin-bottom:6px;
        text-shadow:0 0 6px rgba(167,139,250,0.45);
    }

    .meta {
        color:#d4d4d4;
        font-size:13.5px;
        margin-top:10px;
        line-height:1.45;
    }

    /* Badges */
    .badge {
        display:inline-block;
        padding:4px 8px;
        border-radius:8px;
        font-size:12px;
        margin-right:6px;
        background:#222;
        border:1px solid #333;
        color:#eee;
    }
    .low  { background:#4b0000; border-color:#ff6b6b; }
    .hot  { background:#2b0030; border-color:#c77dff; }
    .zero { background:#2f2f2f; border-color:#777; }

    </style>
    """, unsafe_allow_html=True)

    st.subheader("🔍 Buscar produtos — visão moderna e animada")

    # INPUT DE PESQUISA
    col_s1, col_s2 = st.columns([3,1])
    with col_s1:
        termo = st.text_input("Procurar produto", placeholder="Digite parte do nome...")
    with col_s2:
        limpar = st.button("Limpar")

    if limpar:
        st.experimental_set_query_params()
        termo = ""

    # FILTROS — incluindo ❄️ sem vendas
    f1, f2, f3, f4 = st.columns(4)
    filtro_baixo       = f1.checkbox("⚠️ Baixo estoque (≤3)")
    filtro_alto        = f2.checkbox("📦 Alto estoque (≥20)")
    filtro_vendidos    = f3.checkbox("🔥 Com vendas")
    filtro_sem_vendas  = f4.checkbox("❄️ Sem vendas")

    # ORDENAR
    ordenar = st.selectbox(
        "Ordenar por:",
        ["Relevância","Nome A–Z","Estoque (maior→menor)","Preço (maior→menor)"]
    )

    # PAGINAÇÃO — agora com opção TODOS
    colp1, colp2 = st.columns([1,1])
    per_page = colp1.selectbox("Itens por página", ["TODOS", 6,8,10,12], index=1)
    page     = colp2.number_input("Página", min_value=1, value=1, step=1)

    # BASE
    df_src = estoque_df.copy() if not estoque_df.empty else pd.DataFrame()

    if df_src.empty:
        st.info("Nenhum dado disponível.")
    else:

        # VENDAS agrupadas
        vendas_df = dfs.get("VENDAS", pd.DataFrame()).copy()
        if not vendas_df.empty and "QTD" in vendas_df.columns:
            vendas_agregado = vendas_df.groupby("PRODUTO")["QTD"].sum().reset_index().rename(columns={"QTD":"TOTAL_QTD"})
        else:
            vendas_agregado = pd.DataFrame(columns=["PRODUTO","TOTAL_QTD"])

        df = df_src.merge(vendas_agregado, how="left", on="PRODUTO").fillna({"TOTAL_QTD":0})

        # BUSCA
        if termo.strip():
            df = df[df["PRODUTO"].str.contains(termo.strip(), case=False, na=False)]

        # FILTROS
        if filtro_baixo:
            df = df[df["EM ESTOQUE"] <= 3]
        if filtro_alto:
            df = df[df["EM ESTOQUE"] >= 20]
        if filtro_vendidos:
            df = df[df["TOTAL_QTD"] > 0]
        if filtro_sem_vendas:
            df = df[df["TOTAL_QTD"] == 0]

        # FORMATOS
        df["CUSTO_FMT"] = df["Media C. UNITARIO"].fillna(0).map(formatar_reais_com_centavos)
        df["VENDA_FMT"] = df["Valor Venda Sugerido"].fillna(0).map(formatar_reais_com_centavos)
        df["TOTAL_QTD"] = df["TOTAL_QTD"].astype(int)

        # ORDENAR
        if ordenar == "Nome A–Z":
            df = df.sort_values("PRODUTO")
        elif ordenar == "Estoque (maior→menor)":
            df = df.sort_values("EM ESTOQUE", ascending=False)
        elif ordenar == "Preço (maior→menor)":
            df = df.sort_values("Valor Venda Sugerido", ascending=False)
        else:
            df = df.sort_values(["TOTAL_QTD","EM ESTOQUE"], ascending=[False,False])

        # PAGINAÇÃO — agora com opção TODOS
        total_items = len(df)

        if per_page == "TODOS":
            df_page = df.copy()
            total_pages = 1
            page = 1
        else:
            per_page = int(per_page)
            total_pages = max(1, (total_items + per_page - 1) // per_page)
            page = min(max(1, int(page)), total_pages)
            start = (page - 1) * per_page
            df_page = df.iloc[start:start+per_page]

        st.markdown(f"**Resultados:** {total_items} itens — página {page}/{total_pages}")

        # RENDER DOS CARDS
        if df_page.empty:
            st.info("Nenhum produto encontrado.")
        else:
            st.markdown("<div class='card-grid'>", unsafe_allow_html=True)

            for _, r in df_page.iterrows():
                nome     = r["PRODUTO"]
                estoque  = int(r["EM ESTOQUE"])
                venda    = r["VENDA_FMT"]
                custo    = r["CUSTO_FMT"]
                vendidos = int(r["TOTAL_QTD"])

                # BADGES
                badges = []
                if estoque <= 3:
                    badges.append("<span class='badge low'>⚠️ Baixo estoque</span>")
                if vendidos >= 15:
                    badges.append("<span class='badge hot'>🔥 Saindo muito</span>")
                if vendidos == 0:
                    badges.append("<span class='badge zero'>❄️ Sem vendas</span>")

                badges_html = " ".join(badges)

                # CARD FINAL SEM INDENTAÇÃO
                html_card = f"""
<div class='search-card'>
<div class='search-title'>{nome}</div>
<div>{badges_html}</div>
<div class='meta'>
Estoque: <b>{estoque}</b><br>
Preço: <b>{venda}</b><br>
Custo: <b>{custo}</b><br>
Vendidos (total): <b>{vendidos}</b>
</div>
</div>
"""
                st.markdown(html_card, unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

        # EXPORTAÇÃO CSV
        csv = df_page[
            ["PRODUTO","EM ESTOQUE","Valor Venda Sugerido","Media C. UNITARIO","TOTAL_QTD"]
        ].rename(columns={
            "Valor Venda Sugerido":"PRECO_VENDA",
            "Media C. UNITARIO":"CUSTO_UNITARIO",
            "TOTAL_QTD":"VENDIDOS_TOTAL"
        }).to_csv(index=False).encode("utf-8")

        st.download_button(
            "📥 Exportar esta página (CSV)",
            data=csv,
            file_name=f"pesquisa_pagina_{page}.csv",
            mime="text/csv"
        )
