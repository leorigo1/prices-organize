# Iniciar o backend
cd back
.\.venv\Scripts\Activate.ps1
python .\src\main.py

# Iniciar o frontend
cd ..\front
npm run electron

# Build usando Ng
ng build --base-href ./

# Rebuildar o executável do projeto
npm run dist