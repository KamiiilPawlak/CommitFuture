param (
    [ValidateSet("backend", "frontend", "all")]
    [string]$Target = "all"
)

function Invoke-BackendQuality {
    Write-Host "Uruchomienie narzędzi jakości kodu: backend (ruff, mypy, pytest)..." -ForegroundColor Cyan
    Push-Location backend
    try {
        ruff check .
        if ($LASTEXITCODE -ne 0) { throw "ruff check nie powiódł się" }
        mypy .
        if ($LASTEXITCODE -ne 0) { throw "mypy nie powiódł się" }
        pytest
        if ($LASTEXITCODE -ne 0) { throw "pytest nie powiódł się" }
    }
    finally {
        Pop-Location
    }
}

function Invoke-FrontendQuality {
    Write-Host "Uruchomienie narzędzi jakości kodu: frontend (eslint, prettier, knip, jest)..." -ForegroundColor Cyan
    Push-Location frontend
    try {
        npm run lint
        if ($LASTEXITCODE -ne 0) { throw "eslint nie powiódł się" }
        npm run format:check
        if ($LASTEXITCODE -ne 0) { throw "prettier nie powiódł się" }
        npm run knip
        if ($LASTEXITCODE -ne 0) { throw "knip nie powiódł się" }
        npm run test
        if ($LASTEXITCODE -ne 0) { throw "jest nie powiódł się" }
    }
    finally {
        Pop-Location
    }
}

switch ($Target) {
    "backend"  { Invoke-BackendQuality }
    "frontend" { Invoke-FrontendQuality }
    "all"      { Invoke-BackendQuality; Invoke-FrontendQuality }
}

Write-Host "Zakończono sprawdzanie jakości kodu ($Target)." -ForegroundColor Green
