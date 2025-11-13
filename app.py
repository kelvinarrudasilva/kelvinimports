# ======================
# Sidebar: Seletor de tema
# ======================
st.sidebar.header("🎨 Tema do Painel")
tema = st.sidebar.radio(
    "Escolha um tema discreto:",
    options=["Preto & Dourado", "Escuro & Azul", "Claro & Verde"],
    index=0
)

# ======================
# Define cores por tema
# ======================
if tema == "Preto & Dourado":
    root_colors = "--gold:#FFD700; --bg:#000000; --card:#0f0f0f; --muted:#bfbfbf;"
elif tema == "Escuro & Azul":
    root_colors = "--gold:#00BFFF; --bg:#0A0A0A; --card:#111111; --muted:#AAAAAA;"
elif tema == "Claro & Verde":
    root_colors = "--gold:#228B22; --bg:#F5F5F5; --card:#FFFFFF; --muted:#555555;"

# ======================
# Inject CSS dinamicamente
# ======================
st.markdown(
    f"""
    <style>
      :root {{ {root_colors} }}
      .stApp {{ background-color: var(--bg); color: var(--gold); }}
      .title {{ color: var(--gold); font-weight:700; font-size:22px; }}
      .subtitle {{ color: var(--muted); font-size:12px; margin-bottom:12px; }}
      .kpi {{ background: linear-gradient(90deg, #111111, #0b0b0b); padding:12px; border-radius:10px; text-align:center; }}
      .kpi-value {{ color: var(--gold); font-size:20px; font-weight:700; }}
      .kpi-label {{ color:var(--muted); font-size:13px; }}
      .stDataFrame table {{ background-color:#050505; color:#e6e2d3; }}
    </style>
    """,
    unsafe_allow_html=True,
)
