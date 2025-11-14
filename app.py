# ----------------------------
# KPIs: total vendido (R$), total lucro (R$)
# ----------------------------
k1, k2, k3 = st.columns(3)
k1.metric("💵 Total Vendido", f"R$ {total_vendido:,.2f}")
k2.metric("🧾 Total Lucro", f"R$ {total_lucro:,.2f}")
k3.metric("💸 Total Compras", f"R$ {total_compras:,.2f}")

# ----------------------------
# Aba TOP10 (VALOR)
# ----------------------------
with tabs[1]:
    st.subheader("Top 10 — por VALOR (R$)")
    if vendas_filtradas is None or vendas_filtradas.empty:
        st.info("Sem dados de vendas para o período selecionado.")
    else:
        dfv = vendas_filtradas.copy()
        if "VALOR TOTAL" not in dfv.columns and "VALOR VENDA" in dfv.columns and "QTD" in dfv.columns:
            dfv["VALOR TOTAL"] = dfv["VALOR VENDA"].fillna(0.0) * dfv["QTD"].fillna(0)
        if "PRODUTO" in dfv.columns and "VALOR TOTAL" in dfv.columns:
            top_val = (dfv.groupby("PRODUTO")["VALOR TOTAL"].sum()
                       .reset_index().sort_values("VALOR TOTAL", ascending=False).head(10))
            top_val["VALOR_TOTAL_FMT"] = top_val["VALOR TOTAL"].map(lambda x: f"R$ {x:,.2f}")
            fig = px.bar(top_val, x="PRODUTO", y="VALOR TOTAL", text="VALOR_TOTAL_FMT")
            fig.update_traces(textposition="inside")
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(top_val.drop(columns=["VALOR_TOTAL_FMT"]).rename(columns={"VALOR TOTAL":"VALOR_TOTAL"}).style.format({"VALOR_TOTAL":"R$ {:,.2f}"}))

# ----------------------------
# Aba TOP10 (QUANTIDADE)
# ----------------------------
with tabs[2]:
    st.subheader("Top 10 — por QUANTIDADE")
    if vendas_filtradas is None or vendas_filtradas.empty:
        st.info("Sem dados de vendas para o período selecionado.")
    else:
        dfv = vendas_filtradas.copy()
        if "QTD" not in dfv.columns and "QUANTIDADE" in dfv.columns:
            dfv["QTD"] = dfv["QUANTIDADE"]
        if "PRODUTO" in dfv.columns and "QTD" in dfv.columns:
            top_q = (dfv.groupby("PRODUTO")["QTD"].sum()
                     .reset_index()
                     .sort_values("QTD", ascending=False)
                     .head(10))
            # garantir texto como int
            top_q["QTD_TEXT"] = top_q["QTD"].fillna(0).astype(int).astype(str)
            fig2 = px.bar(top_q, x="PRODUTO", y="QTD", text="QTD_TEXT")
            fig2.update_traces(textposition="inside")
            st.plotly_chart(fig2, use_container_width=True)
            st.dataframe(top_q.drop(columns=["QTD_TEXT"]).style.format({"QTD":"{:,.0f}"}))
