import pandas as pd
import matplotlib.pyplot as plt
import os

# Nome do arquivo
arquivo = "LOJA IMPORTADOS.xlsx"

# Verifica se o arquivo existe
if not os.path.exists(arquivo):
    raise FileNotFoundError(f"Arquivo {arquivo} não encontrado no diretório atual.")

# Carrega o Excel
df = pd.read_excel(arquivo)

# Arruma colunas sem nome
df.columns = [f"coluna_{i+1}" if str(col).startswith('Unnamed') or pd.isna(col) else col for i, col in enumerate(df.columns)]

# Preenche valores nulos com vazio ou zero
df.fillna({"estoque": 0, "vendas": 0, "preco_venda": 0}, inplace=True)

# Converte colunas numéricas
for col in df.columns:
    try:
        df[col] = pd.to_numeric(df[col])
    except:
        pass

# Salva arquivo limpo
df.to_excel("LOJA_IMPORTADOS_limpo.xlsx", index=False)
print("Arquivo limpo salvo como 'LOJA_IMPORTADOS_limpo.xlsx'.")

# --- Gráficos básicos ---

# Estoque por produto (se houver coluna 'produto' e 'estoque')
if 'produto' in df.columns and 'estoque' in df.columns:
    plt.figure(figsize=(10,6))
    df.plot(kind='bar', x='produto', y='estoque', legend=False)
    plt.title('Estoque por Produto')
    plt.ylabel('Quantidade em Estoque')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("estoque_por_produto.png")
    plt.show()

# Vendas por produto (se houver coluna 'produto' e 'vendas')
if 'produto' in df.columns and 'vendas' in df.columns:
    plt.figure(figsize=(10,6))
    df.plot(kind='bar', x='produto', y='vendas', color='orange', legend=False)
    plt.title('Vendas por Produto')
    plt.ylabel('Quantidade Vendida')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("vendas_por_produto.png")
    plt.show()

print("Gráficos gerados: 'estoque_por_produto.png' e 'vendas_por_produto.png'.")
