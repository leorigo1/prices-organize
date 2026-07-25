import pandas as pd
import io
from pathlib import Path

# Tenta ler o arquivo planilha.xls como HTML
arquivo = Path(__file__).resolve().parent / "dados" / "planilha.xls"

with open(arquivo, 'rb') as f:
    conteudo = f.read()

try:
    conteudo_texto = conteudo.decode('utf-8', errors='replace')
    print("Primeiros 500 caracteres do arquivo:")
    print(conteudo_texto[:500])
    print("\n" + "="*80 + "\n")
    
    tabelas = pd.read_html(io.StringIO(conteudo_texto), header=0)
    if tabelas:
        df = tabelas[0]
        print("Colunas encontradas:")
        print(list(df.columns))
        print("\nPrimeiras 3 linhas:")
        print(df.head(3))
        print(f"\nTotal de linhas: {len(df)}")
    else:
        print("Nenhuma tabela HTML encontrada")
except Exception as e:
    print(f"Erro: {e}")
    import traceback
    traceback.print_exc()
