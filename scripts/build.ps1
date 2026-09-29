param (
    [switch]$ForceBuild,
    [switch]$NoCache
)


docker info >$null 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "BŁĄD: Docker nie jest uruchomiony! Włącz Docker Desktop i spróbuj ponownie." -ForegroundColor Red
    exit 1
}


if ($ForceBuild) {
    if ($NoCache) {
        Write-Host "Wymuszone budowanie obrazów (BEZ CACHE)..." -ForegroundColor Cyan
        docker-compose build --no-cache
    }
    else {
        Write-Host "Wymuszone budowanie obrazów Docker..." -ForegroundColor Cyan
        docker-compose build
    }
    exit $LASTEXITCODE
}


Write-Host "Sprawdzanie obecności obrazów Docker..." -ForegroundColor Cyan
$composeImages = docker-compose config --images 2>$null
$missingImage = $false

foreach ($img in $composeImages) {
    if (-not $img) { continue }
    if (-not (docker images -q $img)) {
        $missingImage = $true
        break
    }
}


if ($missingImage) {
    Write-Host "Brak obrazu – automatycznie uruchamiam budowanie..." -ForegroundColor Yellow
    docker-compose build
}
else {
    Write-Host "Wszystkie obrazy są gotowe." -ForegroundColor Green
}

exit $LASTEXITCODE
