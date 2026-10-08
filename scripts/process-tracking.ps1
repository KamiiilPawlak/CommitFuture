$RepoRoot = Join-Path $PSScriptRoot ".."
$PidDir = Join-Path $RepoRoot "PID"
$BackendPidFile = Join-Path $PidDir "backend.pid"
$FrontendPidFile = Join-Path $PidDir "frontend.pid"
$BackendLauncherPidFile = Join-Path $PidDir "backend-launcher.pid"
$FrontendLauncherPidFile = Join-Path $PidDir "frontend-launcher.pid"

if (-not (Test-Path $PidDir)) {
    New-Item -ItemType Directory -Path $PidDir -Force | Out-Null
}

function Stop-TrackedProcess {
    param (
        [string]$PidFile,
        [string]$Label
    )

    if (-not (Test-Path $PidFile)) {
        return
    }

    $trackedPid = Get-Content $PidFile -ErrorAction SilentlyContinue
    if ($trackedPid -and (Get-Process -Id $trackedPid -ErrorAction SilentlyContinue)) {
        taskkill /PID $trackedPid /T /F | Out-Null
    }

    Remove-Item $PidFile -ErrorAction SilentlyContinue
}

. (Join-Path $PSScriptRoot "backend.ps1")
. (Join-Path $PSScriptRoot "frontend.ps1")

function Invoke-StartAll {
    Write-Host "Uruchomienie backendu i frontendu w osobnych oknach..." -ForegroundColor Cyan

    $backendLauncher = Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$RepoRoot'; .\run.ps1 backend" -PassThru
    Set-Content -Path $BackendLauncherPidFile -Value $backendLauncher.Id

    $frontendLauncher = Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$RepoRoot'; .\run.ps1 frontend" -PassThru
    Set-Content -Path $FrontendLauncherPidFile -Value $frontendLauncher.Id

    Write-Host "Backend (uvicorn) i frontend (npm run dev) zostaly wystartowane w nowych oknach PowerShell." -ForegroundColor Green
}

function Invoke-StopAll {
    Stop-TrackedProcess -PidFile $BackendPidFile -Label "Backend"
    Stop-TrackedProcess -PidFile $FrontendPidFile -Label "Frontend"
    Stop-TrackedProcess -PidFile $BackendLauncherPidFile -Label "Okno Backend"
    Stop-TrackedProcess -PidFile $FrontendLauncherPidFile -Label "Okno Frontend"
    Write-Host "Aplikacja wylaczona." -ForegroundColor Green
}
