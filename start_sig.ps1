# SIG-FDSU RDC - Demarrage local (Windows PowerShell)
# Lance l'API FastAPI (8001) et le dashboard (8000) dans deux fenetres separees.

$ErrorActionPreference = "Stop"

$ProjectRoot = $PSScriptRoot
Set-Location -LiteralPath $ProjectRoot

$venvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$dashboardScript = Join-Path $ProjectRoot "dashboard\serve_utf8.py"
$apiMain = Join-Path $ProjectRoot "api\main.py"

function Write-StartupError {
    param([string]$Message)
    Write-Host ""
    Write-Host "ERREUR : $Message" -ForegroundColor Red
    Write-Host ""
    exit 1
}

if (-not (Test-Path -LiteralPath $venvPython)) {
    Write-StartupError @"
Environnement virtuel '.venv' introuvable.
Creez-le depuis la racine du projet :
  python -m venv .venv
  .\.venv\Scripts\Activate.ps1
  pip install -r requirements.txt
"@
}

if (-not (Test-Path -LiteralPath $dashboardScript)) {
    Write-StartupError "Fichier 'dashboard\serve_utf8.py' introuvable."
}

if (-not (Test-Path -LiteralPath $apiMain)) {
    Write-StartupError "Fichier 'api\main.py' introuvable."
}

Write-Host ""
Write-Host "SIG-FDSU RDC - Demarrage local" -ForegroundColor Cyan
Write-Host "Racine du projet : $ProjectRoot"
Write-Host ""

$apiWindowCommand = @"
Set-Location -LiteralPath '$ProjectRoot'
Write-Host '=== SIG-FDSU RDC - API FastAPI (port 8001) ===' -ForegroundColor Green
Write-Host 'Documentation : http://127.0.0.1:8001/docs'
Write-Host ''
& '$venvPython' -m uvicorn api.main:app --reload --host 127.0.0.1 --port 8001
"@

$dashboardWindowCommand = @"
Set-Location -LiteralPath '$ProjectRoot'
Write-Host '=== SIG-FDSU RDC - Dashboard (port 8000) ===' -ForegroundColor Green
Write-Host 'URL : http://127.0.0.1:8000'
Write-Host ''
& '$venvPython' '$dashboardScript'
"@

Start-Process -FilePath "powershell.exe" -ArgumentList "-NoExit", "-Command", $apiWindowCommand
Start-Process -FilePath "powershell.exe" -ArgumentList "-NoExit", "-Command", $dashboardWindowCommand

Write-Host "Services lances dans deux fenetres PowerShell separees." -ForegroundColor Green
Write-Host ""
Write-Host "  Dashboard : http://127.0.0.1:8000"
Write-Host "  API Docs  : http://127.0.0.1:8001/docs"
Write-Host ""
Write-Host "Ouverture du dashboard dans le navigateur dans 3 secondes..." -ForegroundColor Yellow

Start-Sleep -Seconds 3
Start-Process "http://127.0.0.1:8000"

Write-Host "Demarrage termine." -ForegroundColor Green
Write-Host ""
