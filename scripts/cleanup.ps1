
function Invoke-PythonCleanup {

    Get-ChildItem -Path . -Recurse -Directory -Include "__pycache__", "*.egg-info", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".tox", ".cache", "build", "dist" -ErrorAction SilentlyContinue |
    Remove-Item -Force -Recurse -ErrorAction SilentlyContinue

    Get-ChildItem -Path . -Recurse -File -Include "*.pyc", "*.pyo", ".coverage" -ErrorAction SilentlyContinue |
    Remove-Item -Force -ErrorAction SilentlyContinue

}

function Test-DockerRunning {
    docker info > $null 2>&1
    return ($LASTEXITCODE -eq 0)
}


function Invoke-DockerCleanup {
    if (-not (Test-DockerRunning)) {
        Write-Host "Docker nie jest uruchomiony. Pomijam czyszczenie kontenerów Docker." -ForegroundColor Yellow
        return
    }

    $odpowiedz = Read-Host "Czy chcesz usunąć wszystkie kontenery Docker? (y/n)"
    if ($odpowiedz -notin "t", "tak", "y", "Y") {
        Write-Host "Pominięto czyszczenie kontenerów Docker" -ForegroundColor DarkGray
    }

    Write-Host "Zatrzymanie i czyszczenie kontenerów Docker... " -ForegroundColor Cyan
    docker-compose down --remove-orphans

}

Invoke-PythonCleanup
Invoke-DockerCleanup
