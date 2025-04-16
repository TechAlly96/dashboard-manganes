import os
import pandas as pd

# Caminho relativo para o arquivo Excel
file_path = os.path.join("data", "ASSAY.xlsx")
df = pd.read_excel(file_path)