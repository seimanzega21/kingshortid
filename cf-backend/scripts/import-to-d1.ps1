$ErrorActionPreference = "Continue"
$outputDir = "d:\kingshortid\cf-backend\scripts\output"
$files = @("categories.sql", "dramas.sql") + (Get-ChildItem "$outputDir\episodes_*.sql" | Sort-Object Name | ForEach-Object { $_.Name }) + @("users.sql")

$total = $files.Count
$current = 0

foreach ($file in $files) {
    $current++
    Write-Host "[$current/$total] Importing $file..." -NoNewline
    $result = npx wrangler d1 execute kingshortid --remote --file="scripts/output/$file" --yes 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host " OK" -ForegroundColor Green
    }
    else {
        Write-Host " FAILED" -ForegroundColor Red
        Write-Host $result
    }
}

Write-Host "`nDone! Verify: https://kingshortid-api.toonplay-seiman.workers.dev/api/dramas"
