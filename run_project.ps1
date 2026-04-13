$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

$localEnvPath = Join-Path $root "local.env.ps1"
if (Test-Path $localEnvPath) {
    . $localEnvPath
    Write-Host "Loaded environment from local.env.ps1"
}

$frontendUrl = "http://127.0.0.1:5500/index.html"
$registerUrl = "http://127.0.0.1:5500/register.html"
$apiStatusUrl = "http://127.0.0.1:5000/api/status"
$dbStatusUrl = "http://127.0.0.1:5000/api/db/status"

function Get-PythonCmd {
    if (Get-Command py -ErrorAction SilentlyContinue) { return "py -3" }
    if (Get-Command python -ErrorAction SilentlyContinue) { return "python" }
    throw "Python 3 not found. Install Python and retry."
}

function Get-SystemPythonExe {
    $preferred = @(
        "$env:LOCALAPPDATA\Python\pythoncore-3.14-64\python.exe",
        "$env:LOCALAPPDATA\Python\pythoncore-3.13-64\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python314\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe"
    )
    foreach ($p in $preferred) {
        if (Test-Path $p) { return $p }
    }
    if (Get-Command py -ErrorAction SilentlyContinue) {
        try {
            $exe = (& py -3 -c "import sys; print(sys.executable)" 2>$null).Trim()
            if ($exe -and (Test-Path $exe)) { return $exe }
        } catch { }
    }
    if (Get-Command python -ErrorAction SilentlyContinue) {
        return (Get-Command python).Source
    }
    return $null
}

function Test-PortOpen([int]$Port) {
    try {
        $client = New-Object System.Net.Sockets.TcpClient
        $iar = $client.BeginConnect("127.0.0.1", $Port, $null, $null)
        $ok = $iar.AsyncWaitHandle.WaitOne(500)
        if (-not $ok) {
            $client.Close()
            return $false
        }
        $client.EndConnect($iar)
        $client.Close()
        return $true
    } catch {
        return $false
    }
}

function Wait-ForPort([int]$Port, [int]$TimeoutSec = 25) {
    $deadline = (Get-Date).AddSeconds($TimeoutSec)
    while ((Get-Date) -lt $deadline) {
        if (Test-PortOpen $Port) { return $true }
        Start-Sleep -Milliseconds 500
    }
    return $false
}

function Ensure-Dependencies($venvPythonExe) {
    $missing = @()
    $checks = @{
        "flask" = "flask"
        "flask_cors" = "flask-cors"
        "pandas" = "pandas"
        "numpy" = "numpy"
        "requests" = "requests"
        "sklearn" = "scikit-learn"
        "xgboost" = "xgboost"
        "twilio" = "twilio"
        "mysql.connector" = "mysql-connector-python"
        "bcrypt" = "bcrypt"
    }

    foreach ($module in $checks.Keys) {
        & $venvPythonExe -c "import $module" 2>$null
        if ($LASTEXITCODE -ne 0) {
            $missing += $checks[$module]
        }
    }

    $missing = $missing | Sort-Object -Unique
    if ($missing.Count -eq 0) {
        Write-Host "Dependencies already installed."
        return
    }

    Write-Host "Installing missing dependencies..."
    try {
        & $venvPythonExe -m pip install --upgrade pip | Out-Null
        & $venvPythonExe -m pip install @missing | Out-Null
    } catch {
        Write-Warning "Dependency installation had issues. If startup fails, connect internet and retry."
    }
}

$py = Get-PythonCmd
$venvDir = Join-Path $root ".venv"
$venvPy = Join-Path $venvDir "Scripts\python.exe"

if (-not (Test-Path $venvPy)) {
    Write-Host "Creating virtual environment..."
    & cmd /c "$py -m venv .venv"
}

Ensure-Dependencies $venvPy
# Always use venv Python for the backend so all dependencies
# (mysql-connector-python, bcrypt, etc.) are available.
$backendPy = $venvPy
$backendArgs = "api.py"

if (-not (Test-PortOpen 5000)) {
    Write-Host ("Starting backend API using: " + $backendPy)
    Start-Process -FilePath $backendPy -ArgumentList $backendArgs -WorkingDirectory $root -WindowStyle Minimized | Out-Null
} else {
    Write-Host "Backend API already running on port 5000."
}

if (-not (Test-PortOpen 5500)) {
    Write-Host "Starting frontend server..."
    $frontendDir = Join-Path $root "frontend"
    Start-Process -FilePath $venvPy -ArgumentList "-m http.server 5500" -WorkingDirectory $frontendDir -WindowStyle Minimized | Out-Null
} else {
    Write-Host "Frontend server already running on port 5500."
}

[void](Wait-ForPort 5500 20)
[void](Wait-ForPort 5000 20)

try {
    $dbCheck = Invoke-RestMethod -Method Get -Uri $dbStatusUrl -TimeoutSec 5
    if ($dbCheck.connected -eq $true) {
        Write-Host ("Database: connected (" + $dbCheck.database + ")")
    } else {
        Write-Warning ("Database not connected: " + ($dbCheck.error | Out-String).Trim())
    }
} catch {
    Write-Warning "Could not verify DB status endpoint yet."
}

try {
    Start-Process $frontendUrl | Out-Null
} catch {
    Write-Warning "Could not auto-open browser. Open this manually: $frontendUrl"
}

Write-Host ""
Write-Host "Started successfully."
Write-Host "Frontend:  $frontendUrl"
Write-Host "Register:  $registerUrl"
Write-Host "API:       $apiStatusUrl"
Write-Host "DB status: $dbStatusUrl"
