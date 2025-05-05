import os
import pandas as pd

# Caminho absoluto do arquivo Excel
file_path = r"C:\Users\Asus\BRAZIL MINERALS\dashboard_manganes_3d\ASSAY.xlsx"

# Verifica se o arquivo existe
if not os.path.exists(file_path):
    raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")

# Leitura da planilha
df = pd.read_excel(file_path)

# Exibe os nomes das colunas reais antes de qualquer alteração
print("Colunas originais do Excel:")
print(df.columns.tolist())

# Padroniza nomes das colunas
df.columns = (
    df.columns.str.strip()
    .str.replace(" ", "_")
    .str.upper()
    .str.normalize("NFKD")
    .str.encode("ascii", errors="ignore")
    .str.decode("utf-8")
)

# Mostra as colunas após tratamento
print("\nColunas após tratamento:")
print(df.columns.tolist())
