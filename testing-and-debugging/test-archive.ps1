# ========================================
# TEST ARCHIVE - Quick test script
# ========================================
# Archives all champion pool entries so you can test
# the accountability check with no champion data.
# ========================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "TEST ARCHIVE: Champion Pool Data" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "This will:" -ForegroundColor Yellow
Write-Host "  1. Back up all champion pool entries" -ForegroundColor Yellow
Write-Host "  2. Delete them from the champion_pools table" -ForegroundColor Yellow
Write-Host "  3. Allow you to test accountability check with no data" -ForegroundColor Yellow
Write-Host ""
Write-Host "Current champion pool data:" -ForegroundColor White
Write-Host "  - Sinus: 5 champions" -ForegroundColor Gray
Write-Host "  - Elias: 5 champions" -ForegroundColor Gray
Write-Host ""
Write-Host "To restore, run: .\test-restore.ps1" -ForegroundColor Green
Write-Host ""

$confirm = Read-Host "Continue with archive? (y/n)"

if ($confirm -ne "y") {
    Write-Host "Archive cancelled." -ForegroundColor Red
    exit
}

Write-Host ""
Write-Host "Running archive SQL script..." -ForegroundColor Cyan

# Load environment variables
if (Test-Path "backend\.env") {
    Get-Content "backend\.env" | ForEach-Object {
        if ($_ -match "^\s*([^#][^=]*?)\s*=\s*(.*?)\s*$") {
            $key = $matches[1]
            $value = $matches[2]
            [Environment]::SetEnvironmentVariable($key, $value, "Process")
        }
    }
}

$databaseUrl = $env:DATABASE_URL

if (-not $databaseUrl) {
    Write-Host "ERROR: DATABASE_URL not found in backend\.env" -ForegroundColor Red
    exit 1
}

# Extract connection details from DATABASE_URL
# Format: postgresql+asyncpg://user:pass@host/db?ssl=require
if ($databaseUrl -match "postgresql\+asyncpg://([^:]+):([^@]+)@([^/]+)/([^?]+)") {
    $user = $matches[1]
    $pass = $matches[2]
    $host = $matches[3]
    $db = $matches[4]

    # Use psql to run the SQL script
    $env:PGPASSWORD = $pass
    psql -h $host -U $user -d $db -f "test-archive-champions.sql"

    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "✅ Archive complete!" -ForegroundColor Green
        Write-Host ""
        Write-Host "Now test the accountability check at:" -ForegroundColor White
        Write-Host "  https://mnm-dashboard-frontend.onrender.com/" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "To restore the data, run:" -ForegroundColor White
        Write-Host "  .\test-restore.ps1" -ForegroundColor Cyan
    } else {
        Write-Host ""
        Write-Host "❌ Archive failed!" -ForegroundColor Red
        Write-Host "Check the error messages above." -ForegroundColor Red
    }
} else {
    Write-Host "ERROR: Could not parse DATABASE_URL" -ForegroundColor Red
    exit 1
}
