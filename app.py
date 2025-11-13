# Comparação vendas últimos 4 meses - gráfico barras horizontais
st.markdown("## 📊 Vendas Últimos 4 Meses")
if not vendas_f.empty:
    vendas_f["_MES"] = vendas_f[v_data].dt.strftime("%b %Y")  # nome do mês legível
    ult_4_meses = sorted(vendas_f["_MES"].unique())[-4:]
    vendas_4 = vendas_f[vendas_f["_MES"].isin(ult_4_meses)].groupby("_MES")["_VAL_TOTAL"].sum().reset_index()
    
    # gráfico de barras horizontais
    fig_4m = px.bar(
        vendas_4, 
        y="_MES", 
        x="_VAL_TOTAL", 
        orientation='h', 
        text="_VAL_TOTAL", 
        color="_VAL_TOTAL", 
        color_continuous_scale=["#00FF00","#007700"],
        labels={"_VAL_TOTAL":"Valor R$", "_MES":"Mês"}
    )
    fig_4m.update_traces(texttemplate='%{text:,.2f}', textposition='outside', marker_line_color='white', marker_line_width=1.5)
    fig_4m.update_layout(
        plot_bgcolor="#000000", 
        paper_bgcolor="#000000", 
        font_color="#FFFFFF",
        yaxis=dict(title="Mês", tickfont=dict(size=16, color="#00FF00")),
        xaxis=dict(title="Total Vendido (R$)", tickfont=dict(size=14, color="#FFFFFF"))
    )
    st.plotly_chart(fig_4m, use_container_width=True)
