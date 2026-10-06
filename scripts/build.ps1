param (
    [switch]$ForceBuild,
    [switch]$NoCache
)


function Test-DockerRunning {
    docker info >$null 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "BŁĄD: Docker nie jest uruchomiony! Włącz Docker Desktop i spróbuj ponownie." -ForegroundColor Red
        exit 1
    }
}


function Test-DockerImagesExist {
    $composeImages = docker-compose config --images 2> $null
    foreach ($img in $composeImages) {
        if (-not $img) { continue }
        if (-not (docker images -q $img)) {
            return $false
        }
    }
    return $true

}

function Invoke-DockerBuildLifecycle {
    param(
        [bool]$UseNoCache,
        [bool]$CleanOld
    )

    if ($CleanOld) {
        Write-Host "Usuwanie starych kontenerów i czyszczenie..." -ForegroundColor Yellow
        docker-compose down --rmi local --volumes --remove-orphans
    }

    if ($UseNoCache) {
        Write-Host "Budowanie obrazów od zera (BEZ CACHE)..." -ForegroundColor Cyan
        docker-compose build --no-cache
    }
    else {
        Write-Host "Budowanie obrazów..." -ForegroundColor Cyan
        docker-compose build
    }
}

function Start-DockerContainers {
    Write-Host "Uruchamianie kontenerów (docker-compose up)..." -ForegroundColor Green
    docker-compose up -d
}

function Start-BuildWorkflow {
    Test-DockerRunning

    if ($ForceBuild -or $Recreate) {
        Invoke-DockerBuildLifecycle -UseNoCache:$NoCache -CleanOld:$ForceBuild
        Start-DockerContainers
        return
    }

    Write-Host "Sprawdzanie obecności obrazów Docker..." -ForegroundColor Cyan
    if (-not (Test-DockerImagesExist)) {
        Write-Host "Brak obrazu – automatycznie uruchamiam budowanie..." -ForegroundColor Yellow
        Invoke-DockerBuildLifecycle -UseNoCache:$false -CleanOld:$false
    }
    else {
        Write-Host "Wszystkie obrazy są gotowe." -ForegroundColor Green
    }

    Start-DockerContainers
}

# --- URUCHOMIENIE MODUŁU ---
try {
    Start-BuildWorkflow
    exit 0
}
catch {
    Write-Host "BŁĄD: $_" -ForegroundColor Red
    exit 1
}
