# COMPREHENSIVE FIX - All getAuthUser parameter mismatches
# This script reads each file and fixes getAuthUser calls to match actual parameter name

$allFiles = Get-ChildItem -Recurse -Path "src\app\api" -Filter "*.ts" | Where-Object { 
    $content = Get-Content $_.FullName -Raw
    $content -match "getAuthUser\(request\)" 
}

$fixedCount = 0

foreach ($file in $allFiles) {
    Write-Host "Processing: $($file.Name)..."
    
    $content = Get-Content $file.FullName -Raw
    
    # Determine the actual parameter name from function signature
    if ($content -match "export\s+async\s+function\s+\w+\s*\(\s*(\w+):\s*NextRequest") {
        $actualParamName = $Matches[1]
        
        if ($actualParamName -ne "request") {
            # Replace getAuthUser(request) with getAuthUser(actualParam)
            $before = $content
            $content = $content -replace "getAuthUser\(request\)", "getAuthUser($actualParamName)"
            
            if ($before -ne $content) {
                Set-Content $file.FullName -Value $content -NoNewline
                Write-Host "  [FIXED] $($file.Name) - Changed getAuthUser(request) to getAuthUser($actualParamName)" -Fore Green
                $fixedCount++
            }
        }
    }
}

Write-Host "`n========================================" -Fore Cyan
Write-Host "DONE! Fixed $fixedCount files" -Fore Green
Write-Host "========================================`n" -Fore Cyan
