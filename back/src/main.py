from pathlib import Path
import io
import json
import warnings
import json

import pandas as pd
from bs4 import XMLParsedAsHTMLWarning

arquivo = Path(__file__).resolve().parent.parent / "dados" / "planilha.xls"
html = arquivo.read_text(encoding="utf-8")

with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)
    planilha = pd.read_html(io.StringIO(html), header=0)[0]

# Remove espaços extras dos nomes das colunas
planilha.columns = planilha.columns.str.strip()

# Mantém apenas as colunas desejadas
planilha = planilha[
    [
        "Órgão",
        "Instrumento",
        "Nr.",
        "Ano",
        "Assinatura",
        "Item",
        "Valor Un. Inicial",
    ]
]

orcamentos = []

for indice, linha in planilha.iterrows():

    registro = {
        "indice": int(indice),
        "orgao": str(linha["Órgão"]),
        "instrumento": str(linha["Instrumento"]),
        "numero": int(linha["Nr."]),
        "ano": int(linha["Ano"]),
        "assinatura": str(linha["Assinatura"]),
        "descricao": str(linha["Item"]),
        "valor": float(linha["Valor Un. Inicial"]),
    }

    orcamentos.append(registro)

arquivo_json = Path(__file__).resolve().parent.parent / "dados" / "planilha.json"
planilha.to_json(
    arquivo_json,
    orient="records",
    force_ascii=False,
    indent=4,
)

print(f"Arquivo JSON salvo em: {arquivo_json}")
print(f"\nTotal de registros: {len(orcamentos)}")
