# ======================
# Sidebar filtros de data (mais simples)
# ======================
st.sidebar.header("Filtros Gerais")

# Data de vendas: duas caixas de calendário separadas
if vendas is not None and v_data in vendas.columns:
    min_date = vendas[v_data].min().date()
    max_date = vendas[v_data].max().date()
    d_from = st.sidebar.date_input("Data inicial", value=min_date, min_value=min_date, max_value=max_date)
    d_to = st.sidebar.date_input("Data final", value=max_date, min_value=min_date, max_value=max_date)

    # garantir que d_from <= d_to
    if d_from > d_to:
        st.sidebar.warning("Data inicial maior que a data final. Ajustando automaticamente.")
        d_from, d_to = d_to, d_from

    date_range = (d_from, d_to)
else:
    date_range = None

# Aplicar filtros
vendas_f = vendas.copy() if vendas is not None else pd.DataFrame()
if date_range and v_data in vendas.columns:
    d_from, d_to = date_range
    vendas_f = vendas_f[(vendas_f[v_data].dt.date >= d_from) & (vendas_f[v_data].dt.date <= d_to)]
