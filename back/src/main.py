import os
from pathlib import Path

# Carrega variáveis de ambiente de `back/.env` (se existir) antes de
# importar módulos que dependem de `OPENAI_API_KEY` durante a inicialização.
env_path = Path(__file__).resolve().parents[1] / '.env'
if env_path.exists():
    for raw_line in env_path.read_text(encoding='utf-8').splitlines():
        line = raw_line.strip()
        if not line or line.startswith('#'):
            continue
        if '=' in line:
            k, v = line.split('=', 1)
            k = k.strip(); v = v.strip()
            if k:
                os.environ.setdefault(k, v)

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import io
import json
import warnings
import pandas as pd

# Import do controlador OpenAI feito após carregar .env
import openai_controller as _openai_controller

app = Flask(__name__)
CORS(app)
# Register OpenAI blueprint (imported as top-level module to avoid relative import issues)
app.register_blueprint(_openai_controller.bp)

def processar_planilha(arquivo, nome_arquivo):
    """Processa arquivo Excel e retorna dados estruturados"""
    try:
        # Lê o arquivo inteiro uma única vez
        conteudo_bytes = arquivo.read()
        
        if not conteudo_bytes:
            raise Exception("Arquivo enviado está vazio")
        
        # Determina o engine baseado na extensão do arquivo
        extensao = nome_arquivo.lower().split('.')[-1]
        
        df = None
        erro_excel = None
        
        # Tenta ler como Excel primeiro
        if extensao in ['xlsx', 'xls']:
            for engine in ['openpyxl', 'xlrd']:
                try:
                    df = pd.read_excel(io.BytesIO(conteudo_bytes), header=0, engine=engine)
                    if df is not None and not df.empty:
                        break
                except Exception as e:
                    erro_excel = str(e)
        
        # Se falhou como Excel, tenta ler como HTML
        if df is None or df.empty:
            try:
                conteudo_texto = conteudo_bytes.decode('utf-8', errors='replace')
                tabelas = pd.read_html(io.StringIO(conteudo_texto), header=0)
                if tabelas and len(tabelas) > 0:
                    df = tabelas[0]
            except Exception as e:
                raise Exception(f"Erro ao processar: Excel ({erro_excel}), HTML ({str(e)})")
        
        if df is None or df.empty:
            raise Exception("Nenhum dado foi encontrado no arquivo")
        
        # Remove espaços extras dos nomes das colunas
        df.columns = df.columns.str.strip()
        
        # Remove linhas completamente vazias
        df = df.dropna(how='all')
        
        # Mantém apenas as colunas desejadas (se existirem)
        colunas_desejadas = [
            "Órgão",
            "Instrumento",
            "Nr.",
            "Ano",
            "Assinatura",
            "Item",
            "Valor Un. Inicial",
        ]
        
        # Verifica quais colunas existem no arquivo
        colunas_existentes = [col for col in colunas_desejadas if col in df.columns]
        
        if colunas_existentes:
            df = df[colunas_existentes]
        
        orcamentos = []
        
        for indice, linha in df.iterrows():
            # Pula linhas onde todas as colunas são NaN
            if linha.isna().all():
                continue
                
            registro = {
                "indice": int(indice),
            }
            
            # Adiciona valores apenas das colunas que existem
            if "Órgão" in df.columns:
                registro["orgao"] = str(linha["Órgão"]) if pd.notna(linha["Órgão"]) else ""
            if "Instrumento" in df.columns:
                registro["instrumento"] = str(linha["Instrumento"]) if pd.notna(linha["Instrumento"]) else ""
            if "Nr." in df.columns:
                registro["numero"] = int(linha["Nr."]) if pd.notna(linha["Nr."]) else 0
            if "Ano" in df.columns:
                registro["ano"] = int(linha["Ano"]) if pd.notna(linha["Ano"]) else 0
            if "Assinatura" in df.columns:
                registro["assinatura"] = str(linha["Assinatura"]) if pd.notna(linha["Assinatura"]) else ""
            if "Item" in df.columns:
                registro["descricao"] = str(linha["Item"]) if pd.notna(linha["Item"]) else ""
            if "Valor Un. Inicial" in df.columns:
                try:
                    valor = float(linha["Valor Un. Inicial"]) if pd.notna(linha["Valor Un. Inicial"]) else 0.0
                except (ValueError, TypeError):
                    valor = 0.0
                registro["valor"] = valor
            
            orcamentos.append(registro)
        
        return orcamentos, None
    
    except Exception as e:
        import traceback
        print(f"Erro: {str(e)}")
        print(traceback.format_exc())
        return None, str(e)

@app.route('/upload', methods=['POST'])
def upload():
    """Endpoint para upload e processamento de planilha"""
    try:
        if 'arquivo' not in request.files:
            return jsonify({"erro": "Nenhum arquivo enviado"}), 400
        
        arquivo = request.files['arquivo']
        
        if arquivo.filename == '':
            return jsonify({"erro": "Arquivo vazio"}), 400
        
        # Processa a planilha
        dados, erro = processar_planilha(arquivo.stream, arquivo.filename)
        
        if erro:
            print(f"ERRO ao processar: {erro}")
            return jsonify({"erro": f"Erro ao processar arquivo: {erro}"}), 400
        
        if dados is None:
            return jsonify({"erro": "Nenhum dado foi extraído do arquivo"}), 400
        
        # Cria JSON em memória
        json_data = json.dumps(dados, ensure_ascii=False, indent=2)
        json_bytes = io.BytesIO(json_data.encode('utf-8'))
        json_bytes.seek(0)
        
        return send_file(
            json_bytes,
            mimetype='application/json',
            as_attachment=True,
            download_name='planilha.json'
        )
    
    except Exception as e:
        print(f"ERRO GERAL: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return jsonify({"erro": f"Erro no servidor: {str(e)}"}), 500

@app.route('/debug-upload', methods=['POST'])
def debug_upload():
    """Endpoint de debug para ver as colunas do arquivo"""
    try:
        if 'arquivo' not in request.files:
            return jsonify({"erro": "Nenhum arquivo enviado"}), 400
        
        arquivo = request.files['arquivo']
        conteudo_bytes = arquivo.read()
        
        # Tenta ler como HTML
        try:
            conteudo_texto = conteudo_bytes.decode('utf-8', errors='replace')
            tabelas = pd.read_html(io.StringIO(conteudo_texto), header=0)
            if tabelas and len(tabelas) > 0:
                df = tabelas[0]
                return jsonify({
                    "nome_arquivo": arquivo.filename,
                    "colunas": list(df.columns),
                    "num_linhas": len(df),
                    "primeiras_linhas": df.head(3).to_dict('records')
                })
        except Exception as e:
            return jsonify({"erro": f"Erro ao ler HTML: {str(e)}"}), 400
        
    except Exception as e:
        return jsonify({"erro": f"Erro: {str(e)}"}), 500

@app.route('/health', methods=['GET'])
def health():
    """Endpoint para verificar se o servidor está rodando"""
    return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)
