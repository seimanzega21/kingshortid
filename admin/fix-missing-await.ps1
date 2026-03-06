# Fix missing 'await' for getAuthUser calls
Write-Host "Finding and fixing missing 'await' for getAuthUser..." -Fore Cyan

$allFiles = Get-ChildItem -Recurse -Path "src\app\api" -Filter "*.ts"
$fixedCount = 0

foreach ($file in $allFiles) {
    $lines = Get-Content $file.FullName
    $modified = $false
    $newLines = @()
    
    foreach ($line in $lines) {
        # Check if line has getAuthUser without await
        if ($line -match "=\s*getAuthUser\(" -and $line -notmatch "await\s+getAuthUser\(") {
            $newLine = $line -replace "=\s*getAuthUser\(", "= await getAuthUser("
            $newLines += $newLine
            $modified = $true
        }
        else {
            $newLines += $line
        }
    }
    
    if ($modified) {
        $newLines | Set-Content $file.FullName
        Write-Host "[FIXED] $($file.Name) - Added await" -Fore Green
        $fixedCount++
    }
}

Write-Host "`nDONE! Fixed $fixedCount files" -Fore Cyan
