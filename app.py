# ---------- Upload / Leitura ----------
st.sidebar.header("Dados")
use_upload = st.sidebar.checkbox("Fazer upload do CSV em vez de usar arquivo no repositório?", value=False)

uploaded = None
if use_upload:
    uploaded = st.sidebar.file_uploader("Arraste o CSV aqui (ex: LOJA IMPORTADOS(ESTOQUE).csv)", type=['csv', 'txt'])
    if uploaded is None:
        st.sidebar.info("Faça upload para visualizar os dados aqui.")
else:
    DEFAULT_CSV = "LOJA IMPORTADOS(ESTOQUE).csv"
    if not os.path.exists(DEFAULT_CSV) and not use_upload:
        st.warning(f"O arquivo padrão '{DEFAULT_CSV}' não foi encontrado no repositório. Marque a opção de upload na barra lateral ou envie o arquivo para o repo.")
        uploaded = None

# ---------- Função que detecta automaticamente o cabeçalho ----------
def read_csv_auto_header(file_path_or_buffer):
    """Detecta a linha onde começa o cabeçalho (com 'PRODUTO') e lê a partir dali."""
    try:
        # lê tudo em texto bruto primeiro
        lines = []
        if isinstance(file_path_or_buffer, str):
            with open(file_path_or_buffer, encoding='latin1') as f:
                lines = f.readlines()
        else:
            lines = file_path_or_buffer.read().decode('latin1').splitlines()

        # procura a linha onde aparece "PRODUTO"
        header_idx = 0
        for i, line in enumerate(lines):
            if "PRODUTO" in line.upper():
                header_idx = i
                break

        # lê CSV a partir da linha do cabeçalho detectada
        df = pd.read_csv(
            pd.compat.StringIO("\n".join(lines[header_idx:])),
            sep=";",
            encoding="latin1"
        )
        df.columns = [c.strip() for c in df.columns]
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
        return df
    except Exception as e:
        st.error(f"Erro ao detectar cabeçalho: {e}")
        raise e

# ---------- Carregar dataframe ----------
try:
    if uploaded:
        df_raw = read_csv_auto_header(uploaded)
    else:
        df_raw = read_csv_auto_header(DEFAULT_CSV)
except Exception as e:
    st.error("Erro ao ler CSV: " + str(e))
    st.stop()

# ---------- Normalização ----------
df = normalize_columns(df_raw.copy())
df = ensure_product_names(df)

# --- filtro anti-lixo: remove linhas sem dados reais ---
mask_valid = (
    df['PRODUTO'].notna()
    & ~df['PRODUTO'].str.contains("SEM_NOME_PRODUTO", case=False)
    & (
        (df['EM_ESTOQUE'] > 0)
        | (df['VENDAS'] > 0)
        | (df['COMPRAS'] > 0)
    )
)
df = df[mask_valid].copy()

# garantir colunas numéricas mínimas
for col in ['EM_ESTOQUE', 'COMPRAS', 'MEDIA_CUSTO', 'VALOR_VENDA', 'VENDAS']:
    if col in df.columns:
        df[col] = to_number_series(df[col])
    else:
        df[col] = 0
