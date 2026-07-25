from pathlib import Path
import os
import sys
import json

# Carrega .env do diretório back
env_path = Path(__file__).resolve().parents[1] / '.env'
if env_path.exists():
    for raw in env_path.read_text(encoding='utf-8').splitlines():
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        if '=' in line:
            k, v = line.split('=', 1)
            os.environ.setdefault(k.strip(), v.strip())

# Ajusta sys.path para importar módulos locais (src)
src_path = Path(__file__).resolve().parents[1] / 'src'
sys.path.insert(0, str(src_path))

from dtos import SearchSimilarRequest
from search_service import SearchService

def main():
    inp = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1] / 'dados' / 'planilha.json'
    outp = Path(sys.argv[2]) if len(sys.argv) > 2 else Path.home() / 'Downloads' / 'resultado_top5.json'

    if not inp.exists():
        print(f"input file not found: {inp}")
        sys.exit(2)

    with inp.open('r', encoding='utf-8') as f:
        data = json.load(f)

    req = SearchSimilarRequest(reference_text='sabão em barra 200 gramas', payload=data)
    svc = SearchService()
    resp = svc.search_similar(req)

    outp.parent.mkdir(parents=True, exist_ok=True)
    outp.write_text(json.dumps(resp.payload, ensure_ascii=False, indent=2), encoding='utf-8')
    print(str(outp))

if __name__ == '__main__':
    main()
