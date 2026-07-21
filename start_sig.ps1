# SIG-FDSU RDC - Demarrage local (Windows PowerShell)
# Lance l'API FastAPI (8001) et le dashboard (8000) dans deux fenetres separees.

param(
    [ValidateSet('json', 'db', 'auto')]
    [string]$Mode = 'auto'
)

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

$dataModeValue = if ($Mode -eq 'db') { 'db' } elseif ($Mode -eq 'json') { 'json' } else { if ($env:DATA_MODE) { $env:DATA_MODE } else { 'json' } }
$env:DATA_MODE = $dataModeValue
# Mode DB : stabilité runtime (pas de WatchFiles) — les caches dérivés sous
# data/cache/ ne doivent pas redémarrer le worker pendant SDG/Needs.
# Mode JSON (dev) : hot-reload conservé.
$useReload = ($dataModeValue -ne 'db')
$uvicornReloadArg = if ($useReload) { '--reload' } else { '' }

if ($dataModeValue -eq 'db') {
    Write-Host "Mode donnees : DB (PostgreSQL/PostGIS)" -ForegroundColor Yellow
    Write-Host "Uvicorn : sans --reload (stabilite runtime)" -ForegroundColor Yellow
} else {
    Write-Host "Mode donnees : JSON (fichiers locaux)" -ForegroundColor Yellow
    Write-Host "Uvicorn : avec --reload (developpement)" -ForegroundColor Yellow
}
Write-Host ""

$apiWindowCommand = @"
Set-Location -LiteralPath '$ProjectRoot'
`$env:DATA_MODE = '$dataModeValue'
Write-Host '=== SIG-FDSU RDC - API FastAPI (port 8001) ===' -ForegroundColor Green
Write-Host "Mode donnees : `$env:DATA_MODE" -ForegroundColor Yellow
Write-Host 'Documentation : http://127.0.0.1:8001/docs'
Write-Host ''
& '$venvPython' -m uvicorn api.main:app $uvicornReloadArg --host 127.0.0.1 --port 8001
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
Write-Host "Attente du health-check dashboard..." -ForegroundColor Yellow
$dashboardHealthUrl = "http://127.0.0.1:8000/healthz"
$dashboardReady = $false
$deadline = [DateTime]::UtcNow.AddSeconds(30)
while ([DateTime]::UtcNow -lt $deadline) {
    try {
        $response = Invoke-WebRequest -UseBasicParsing -Uri $dashboardHealthUrl -TimeoutSec 2
        if ($response.StatusCode -eq 200) {
            $dashboardReady = $true
            break
        }
    } catch {
        Start-Sleep -Milliseconds 250
    }
}
if (-not $dashboardReady) {
    Write-StartupError "Le dashboard ne répond pas sur $dashboardHealthUrl après 30 secondes."
}

Write-Host "Dashboard prêt. Ouverture dans le navigateur..." -ForegroundColor Green
Start-Process "http://127.0.0.1:8000"

Write-Host "Demarrage termine." -ForegroundColor Green
Write-Host ""
