param (
    [string]$Action = "default",
    [switch]$ForceBuild,
    [switch]$NoCache,
    [switch]$Recreate
)


function Invoke-CleanupTask {
    $ScriptPath = ".\scripts\cleanup.ps1"
    if (Test-Path $ScriptPath) {
        Write-Host "Uruchomienie zadania: Cleanup..." -ForegroundColor Cyan
        & $ScriptPath
    }
    else {
        throw "Nie znaleziono pliku skryptu: $ScriptPath"
    }
}

function Invoke-Dev {
    $venvPath = "backend/.venv/Scripts/Activate.ps1"
    if (Test-Path $venvPath) {
        Write-Host "Aktywacja środowiska wirtualnego Pythona..." -ForegroundColor Cyan
        & $venvPath
    }
    else {
        Write-Host "Nie znaleziono środowiska wirtualnego Pythona. Pomijam aktywację." -ForegroundColor Yellow
    }
}

. (Join-Path $PSScriptRoot "scripts\process-tracking.ps1")

function Invoke-Quality {
    param (
        [string]$QualityTarget = "all"
    )
    $ScriptPath = ".\scripts\quality.ps1"
    if (Test-Path $ScriptPath) {
        Write-Host "Uruchomienie zadania: Quality ($QualityTarget)..." -ForegroundColor Cyan
        & $ScriptPath -Target $QualityTarget
    }
    else {
        throw "Nie znaleziono pliku skryptu: $ScriptPath"
    }
}

function Invoke-BuildTask {
    $ScriptPath = ".\scripts\build.ps1"
    if (Test-Path $ScriptPath) {
        Write-Host "Uruchomienie zadania: Build / Lifecycle..." -ForegroundColor Cyan
        & $ScriptPath -ForceBuild:$ForceBuild -NoCache:$NoCache -Recreate:$Recreate
    }
    else {
        throw "Nie znaleziono pliku skryptu: $ScriptPath"
    }
}

function Invoke-DefaultWorkflow {
    Invoke-BuildTask
}

function Show-Help {
    $availableActions = $TaskRegistry.Keys -join ', '
    Write-Host "Uzycie: .\run.ps1 [-Action] <akcja> [-ForceBuild] [-NoCache] [-Recreate]" -ForegroundColor Cyan
    Write-Host "Dostepne akcje: $availableActions" -ForegroundColor Yellow
}

$TaskRegistry = @{
    "clean"            = { Invoke-CleanupTask }
    "cleanup"          = { Invoke-CleanupTask }
    "build"            = { Invoke-BuildTask }
    "default"          = { Invoke-DefaultWorkflow }
    "dev"              = { Invoke-Dev }
    "backend"          = { Invoke-Start }
    "frontend"         = { Invoke-Frontend }
    "start"            = { Invoke-StartAll }
    "stop"             = { Invoke-StopAll }
    "stop-backend"     = { Invoke-StopBackend }
    "stop-frontend"    = { Invoke-StopFrontend }
    "quality"          = { Invoke-Quality -QualityTarget "all" }
    "quality-backend"  = { Invoke-Quality -QualityTarget "backend" }
    "quality-frontend" = { Invoke-Quality -QualityTarget "frontend" }
    "help"             = { Show-Help }
}


function Invoke-Orchestrator {
    param (
        [string]$TargetAction
    )

    if ([string]::isNullOrWhiteSpace($TargetAction)) {
        $TargetAction = "default"
    }
    if ($TaskRegistry.ContainsKey($TargetAction)) {
        try {
            & $TaskRegistry[$TargetAction]
            Write-Host "Success" -ForegroundColor Green
        }
        catch {
            Write-Host "BŁĄD WYKONANIA: $_" -ForegroundColor Red
            exit 1
        }
    }
    else {
        Write-Host "BŁĄD: Nieznana akcja '$TargetAction'." -ForegroundColor Red
        Show-Help
        exit 1
    }
}

Invoke-Orchestrator -TargetAction $Action
