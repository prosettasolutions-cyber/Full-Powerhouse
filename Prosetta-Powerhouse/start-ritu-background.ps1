param(
    [switch]$OpenPortal,
    [switch]$Watch
)

$ErrorActionPreference = "Stop"
$portalUrl = "http://127.0.0.1:8080"
$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonPath = Join-Path (Split-Path -Parent $repoRoot) "ocr-env\Scripts\python.exe"
$serverPath = Join-Path $repoRoot "server.py"
$runtimeRoot = Join-Path (Split-Path -Parent $repoRoot) "Powerhouse\.ritu"
$logRoot = Join-Path $runtimeRoot "logs"
$watchdogLockPath = Join-Path $runtimeRoot "ritu-watchdog.lock"

New-Item -ItemType Directory -Path $logRoot -Force | Out-Null

function Test-RituApi {
    try {
        $response = Invoke-WebRequest -Uri "$portalUrl/api/health" -UseBasicParsing -TimeoutSec 3
        return $response.StatusCode -eq 200
    }
    catch {
        return $false
    }
}

function Start-RituApi {
    if (Test-RituApi) {
        return $true
    }
    if (-not (Test-Path -LiteralPath $pythonPath)) {
        throw "Ritu Python environment is missing: $pythonPath"
    }
    Start-Process `
        -FilePath $pythonPath `
        -ArgumentList @($serverPath) `
        -WorkingDirectory $repoRoot `
        -WindowStyle Hidden `
        -RedirectStandardOutput (Join-Path $logRoot "server-output.log") `
        -RedirectStandardError (Join-Path $logRoot "server-error.log")

    for ($attempt = 0; $attempt -lt 40; $attempt++) {
        Start-Sleep -Milliseconds 500
        if (Test-RituApi) {
            return $true
        }
    }
    return $false
}

if ($Watch) {
    try {
        $watchdogLock = [System.IO.File]::Open(
            $watchdogLockPath,
            [System.IO.FileMode]::OpenOrCreate,
            [System.IO.FileAccess]::ReadWrite,
            [System.IO.FileShare]::None
        )
    }
    catch {
        exit 0
    }
}

try {
    $ready = Start-RituApi
    if ($OpenPortal) {
        if ($ready) {
            Start-Process $portalUrl
        }
        else {
            Add-Type -AssemblyName PresentationFramework
            [System.Windows.MessageBox]::Show(
                "Ritu could not start. Check P:\RituAI\Powerhouse\.ritu\logs\server-error.log.",
                "Ritu Portal"
            ) | Out-Null
        }
    }
    if ($Watch) {
        while ($true) {
            Start-Sleep -Seconds 20
            Start-RituApi | Out-Null
        }
    }
}
finally {
    if ($Watch -and $watchdogLock) {
        $watchdogLock.Dispose()
    }
}
