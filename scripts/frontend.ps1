function Invoke-Frontend {
    $frontendPath = Resolve-Path (Join-Path $RepoRoot "frontend") -ErrorAction SilentlyContinue
    if (-not $frontendPath) {
        throw "Nie znaleziono katalogu frontend"
    }
    Write-Host "Uruchomienie React (npm run dev)..." -ForegroundColor Cyan
    try {
        $proc = Start-Process -FilePath "npm.cmd" -ArgumentList "run", "dev" -WorkingDirectory $frontendPath -NoNewWindow -PassThru
        Set-Content -Path $FrontendPidFile -Value $proc.Id
        $proc.WaitForExit()
    }
    finally {
        Remove-Item $FrontendPidFile -ErrorAction SilentlyContinue
    }
}

function Invoke-StopFrontend {
    Stop-TrackedProcess -PidFile $FrontendPidFile -Label "Frontend"
    Write-Host "Frontend wylaczony." -ForegroundColor Green
}
