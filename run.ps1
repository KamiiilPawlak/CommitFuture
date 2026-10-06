param (
    [string]$Action = "default",
    [switch]$ForceBuild,
    [switch]$NoCache
)


function Invoke-CleanupTask {
    $ScriptPath = ".\scripts\cleanup.ps1"
    if (Test-Path $ScriptPath) {
        Write-Host "Uruchomienie zadania: Cleanup..." -ForegroundColor Cyan
        & $ScriptPath -ForceBuild:$ForceBuild -NoCache:$NoCache
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

function Invoke-BuildTask {
    $ScriptPath = ".\scripts\build.ps1"
    if (Test-Path $ScriptPath) {
        Write-Host "Uruchomienie zadania: Build / Lifecycle..." -ForegroundColor Cyan
        & $ScriptPath -ForceBuild:$ForceBuild -NoCache:$NoCache
    }
    else {
        throw "Nie znaleziono pliku skryptu: $ScriptPath"
    }
}

function Invoke-DefaultWorkflow {
    Invoke-BuildTask -ForceBuild:$ForceBuild -NoCache:$NoCache
    
}

$TaskRegistry = @{
    "clean"   = { Invoke-CleanupTask }
    "cleanup" = { Invoke-CleanupTask }
    "build"   = { Invoke-BuildTask }
    "default" = { Invoke-DefaultWorkflow }
    "dev"     = { Invoke-Dev }
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
        $availableActions = $TaskRegistry.Keys -join ', '
        Write-Host "BŁĄD: Nieznana akcja '$TargetAction'." -ForegroundColor Red
        Write-Host "Dostępne akcje: $availableActions" -ForegroundColor Yellow
        exit 1
    }
}

Invoke-Orchestrator -TargetAction $Action