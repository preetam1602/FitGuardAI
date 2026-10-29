# FitGuard AI - Backend startup (port 3001, matches Vite proxy)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Test-Path ".env")) {
    Write-Host "Creating backend/.env from .env.example with a random SECRET_KEY - update DATABASE_URL and GROQ_API_KEY as needed."
    $secret = python -c "import secrets; print(secrets.token_urlsafe(48))"
    $lines = (Get-Content ".env.example") -replace '^SECRET_KEY=.*$', "SECRET_KEY=$secret"
    # UTF-8 without BOM: a BOM would corrupt the first key when python-dotenv reads the file
    [System.IO.File]::WriteAllLines((Join-Path $PSScriptRoot ".env"), $lines, (New-Object System.Text.UTF8Encoding $false))
}

Write-Host "Starting FitGuard API on http://localhost:3001 ..."
python -m uvicorn server:app --app-dir src --reload --port 3001 --host 127.0.0.1
