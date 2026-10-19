Write-Host "Uruchomienie quality tools: backend (ruff, mypy, pylint, bandit, pytest)..." -ForegroundColor Cyan
Push-Location backend
try {
    ruff check .
    if ($LASTEXITCODE -ne 0) { throw "ruff check nie powiódł się" }

    ruff format --check .
    if ($LASTEXITCODE -ne 0) { throw "ruff format --check nie powiódł się" }

    mypy .
    if ($LASTEXITCODE -ne 0) { throw "mypy nie powiódł się" }

    pylint --rcfile=.pylintrc app
    if ($LASTEXITCODE -ne 0) { throw "pylint nie powiódł się" }

    bandit -r app/ -ll
    if ($LASTEXITCODE -ne 0) { throw "bandit nie powiódł się" }

    pytest
    if ($LASTEXITCODE -ne 0) { throw "pytest nie powiódł się" }
}
finally {
    Pop-Location
}

Write-Host "Zakończono quality tools: backend." -ForegroundColor Green
