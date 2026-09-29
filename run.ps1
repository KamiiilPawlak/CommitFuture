param (
    [string]$Action,
    [switch]$NoCache
)


if (Test-Path "backend/.venv/Scripts/Activate.ps1") {
    . backend/.venv/Scripts/Activate.ps1
}


switch ($Action) {
    "clean" {
        & .\scripts\clean.ps1
    }

    "build" {
        & .\scripts\build.ps1 -ForceBuild -NoCache:$NoCache
    }

    default {

        & .\scripts\build.ps1


        if ($LASTEXITCODE -eq 0) {
            Write-Host "Uruchamiam kontenery..." -ForegroundColor Green
            docker-compose up
        }
        else {
            Write-Host "Anulowano uruchamianie aplikacji." -ForegroundColor Red
        }
    }
}
