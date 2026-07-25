import json
from pathlib import Path

import pandas as pd

# Arquivo JSON
BASE_DIR = Path(__file__).resolve().parent.parent
arquivo_json = BASE_DIR / "dados" / "resultado_top5.json"

# Ler JSON
with open(arquivo_json, "r", encoding="utf-8") as f:
    dados = json.load(f)

# Criar DataFrame
df = pd.DataFrame(dados)

# Reordenar colunas (opcional)
colunas = [
    "Órgão",
    "Instrumento",
    "Nr.",
    "Ano",
    "Assinatura",
    "Item",
    "Valor Un. Inicial"
]

df = df[colunas]

# Exportar Excel
saida = "resultado_top5.xlsx"
df.to_excel(saida, index=False)

print(f"Arquivo salvo em: {saida}")