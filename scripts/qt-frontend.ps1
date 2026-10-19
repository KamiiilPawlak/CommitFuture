Write-Host "Uruchomienie quality tools: frontend (eslint, prettier, knip, tsc+build, jest)..." -ForegroundColor Cyan
Push-Location frontend
try {
    npm run lint
    if ($LASTEXITCODE -ne 0) { throw "eslint nie powiódł się" }

    npm run format:check
    if ($LASTEXITCODE -ne 0) { throw "prettier nie powiódł się" }

    npm run knip
    if ($LASTEXITCODE -ne 0) { throw "knip nie powiódł się" }

    npm run build
    if ($LASTEXITCODE -ne 0) { throw "typecheck + build nie powiódł się" }

    npm run test
    if ($LASTEXITCODE -ne 0) { throw "jest nie powiódł się" }
}
finally {
    Pop-Location
}

Write-Host "Zakończono quality tools: frontend." -ForegroundColor Green
