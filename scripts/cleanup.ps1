Write-Host "Czyszczenie plików tymczasowych Pythona..." -ForegroundColor Cyan

Get-ChildItem -Path . -Recurse -Directory -Include "__pycache__", "*.egg-info" -ErrorAction SilentlyContinue |
Remove-Item -Force -Recurse -ErrorAction SilentlyContinue

Get-ChildItem -Path . -Recurse -Directory -Include ".pytest_cache", ".mypy_cache", ".ruff_cache", ".tox", ".cache", "build", "dist" -ErrorAction SilentlyContinue |
Remove-Item -Force -Recurse -ErrorAction SilentlyContinue

Get-ChildItem -Path . -Recurse -File -Include "*.pyc", "*.pyo", ".coverage" -ErrorAction SilentlyContinue |
Remove-Item -Force -ErrorAction SilentlyContinue


docker info >$null 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "Zatrzymywanie i czyszczenie kontenerów..." -ForegroundColor Cyan
    docker-compose down --remove-orphans
}

Write-Host "Gotowe! Projekt wyczyszczony." -ForegroundColor Green
