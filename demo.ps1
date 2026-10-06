$ErrorActionPreference="Stop"
Copy-Item .env.example .env -ErrorAction SilentlyContinue
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
$env:PYTHONPATH=(Get-Location).Path
Write-Host "Start backend: uvicorn backend.app.main:app --reload"
Write-Host "Start frontend in another PowerShell: cd frontend; npm install; npm run dev"
