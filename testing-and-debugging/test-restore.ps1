# ========================================
# TEST RESTORE - Quick restore script
# ========================================
# Restores all champion pool entries from the
# backup created by test-archive.ps1
# ========================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "TEST RESTORE: Champion Pool Data" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "This will restore all champion pool entries from backup." -ForegroundColor Yellow
Write-Host ""

$confirm = Read-Host "Continue with restore? (y/n)"

if ($confirm -ne "y") {
    Write-Host "Restore cancelled." -ForegroundColor Red
    exit
}

Write-Host ""
Write-Host "Running restore SQL script..." -ForegroundColor Cyan

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
    psql -h $host -U $user -d $db -f "test-restore-champions.sql"

    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "✅ Restore complete!" -ForegroundColor Green
        Write-Host ""
        Write-Host "All champion pool data has been restored." -ForegroundColor White
        Write-Host ""
        Write-Host "Verify at:" -ForegroundColor White
        Write-Host "  https://mnm-dashboard-frontend.onrender.com/" -ForegroundColor Cyan
    } else {
        Write-Host ""
        Write-Host "❌ Restore failed!" -ForegroundColor Red
        Write-Host "Check the error messages above." -ForegroundColor Red
    }
} else {
    Write-Host "ERROR: Could not parse DATABASE_URL" -ForegroundColor Red
    exit 1
}
