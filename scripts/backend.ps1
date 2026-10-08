function Invoke-Start {
    $uvicornPath = Resolve-Path (Join-Path $RepoRoot "backend\.venv\Scripts\uvicorn.exe") -ErrorAction SilentlyContinue
    if (-not $uvicornPath) {
        throw "Nie znaleziono uvicorn w srodowisku wirtualnym: backend\.venv\Scripts\uvicorn.exe"
    }
    Write-Host "Uruchomienie FastAPI (uvicorn)..." -ForegroundColor Cyan
    Push-Location (Join-Path $RepoRoot "backend")
    try {
        $proc = Start-Process -FilePath $uvicornPath -ArgumentList "app.main:app", "--reload" -NoNewWindow -PassThru
        Set-Content -Path $BackendPidFile -Value $proc.Id
        $proc.WaitForExit()
    }
    finally {
        Remove-Item $BackendPidFile -ErrorAction SilentlyContinue
        Pop-Location
    }
}

function Invoke-StopBackend {
    Stop-TrackedProcess -PidFile $BackendPidFile -Label "Backend"
    Write-Host "Backend wylaczony." -ForegroundColor Green
}
