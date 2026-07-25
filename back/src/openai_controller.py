from flask import Blueprint, request, jsonify
from dtos import SearchSimilarRequest
from search_service import SearchService
from pathlib import Path

_HERE = Path(__file__).resolve().parents[1]
_SAMPLE_JSON = _HERE / 'dados' / 'planilha.json'

bp = Blueprint("openai", __name__)



@bp.route("/openai/search-similar", methods=["POST"])
def search_similar():
    try:
        if "file" not in request.files:
            return jsonify({"erro": "Arquivo JSON não enviado"}), 400

        if "reference_text" not in request.form:
            return jsonify({"erro": "Texto de referência não informado"}), 400

        uploaded_file = request.files["file"]
        if uploaded_file.filename == "":
            return jsonify({"erro": "Arquivo vazio"}), 400

        if not uploaded_file.filename.lower().endswith(".json"):
            return jsonify({"erro": "Apenas arquivos .json são aceitos"}), 400

        payload = uploaded_file.read().decode("utf-8")
        data = __import__("json").loads(payload)

        request_dto = SearchSimilarRequest(
            reference_text=request.form["reference_text"],
            payload=data,
        )
        # instantiate service lazily so server can start even when OPENAI_API_KEY is not set
        search_service = SearchService()
        result = search_service.search_similar(request_dto)
        return jsonify(result.payload), 200
    except ValueError as exc:
        return jsonify({"erro": str(exc)}), 400
    except Exception as exc:
        return jsonify({"erro": f"Erro interno: {exc}"}), 500


@bp.route('/openai/sample-json', methods=['GET'])
def sample_json():
    try:
        if not _SAMPLE_JSON.exists():
            return jsonify({"erro": "Arquivo de exemplo não encontrado"}), 404
        data = _SAMPLE_JSON.read_text(encoding='utf-8')
        return jsonify(__import__('json').loads(data)), 200
    except Exception as e:
        return jsonify({"erro": f"Erro ao ler arquivo de exemplo: {e}"}), 500
