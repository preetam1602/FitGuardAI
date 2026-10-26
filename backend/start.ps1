# FitGuard AI — Backend startup (port 3001, matches Vite proxy)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Test-Path ".env")) {
    Write-Host "Creating backend/.env from .env.example — update DATABASE_URL and GROQ_API_KEY as needed."
    Copy-Item ".env.example" ".env"
}

Write-Host "Starting FitGuard API on http://localhost:3001 ..."
python -m uvicorn server:app --app-dir src --reload --port 3001 --host 127.0.0.1
