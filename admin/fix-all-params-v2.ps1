# COMPREHENSIVE FIX v2 - Compatible with all PowerShell versions
# Fixes all getAuthUser(request) to match actual parameter names

Write-Host "Starting comprehensive parameter fix..." -Fore Cyan
Write-Host "=========================================`n" -Fore Cyan

# List of files that need fixing based on grep results
$filesToFix = @(
    "src\app\api\watch-party\route.ts",
    "src\app\api\user\watchlist\route.ts",
    "src\app\api\user\history\route.ts",
    "src\app\api\user\notifications\route.ts",
    "src\app\api\user\notifications\settings\route.ts",
    "src\app\api\user\notifications\register\route.ts",
    "src\app\api\user\favorites\route.ts",
    "src\app\api\subscriptions\route.ts",
    "src\app\api\social\following\route.ts",
    "src\app\api\social\followers\route.ts",
    "src\app\api\seasons\route.ts",
    "src\app\api\rewards\daily-spin\route.ts",
    "src\app\api\reviews\route.ts",
    "src\app\api\reports\route.ts",
    "src\app\api\recommendations\route.ts",
    "src\app\api\playlists\route.ts",
    "src\app\api\notifications\route.ts",
    "src\app\api\episodes\[id]\stream\route.ts",
    "src\app\api\coins\balance\route.ts",
    "src\app\api\coins\spend\route.ts",
    "src\app\api\comments\[id]\like\route.ts",
    "src\app\api\comments\route.ts",
    "src\app\api\coins\earn\ad\route.ts",
    "src\app\api\coins\checkin\route.ts",
    "src\app\api\coins\checkin\status\route.ts",
    "src\app\api\coins\checkin\claim\route.ts",
    "src\app\api\auth\me\route.ts",
    "src\app\api\achievements\route.ts"
)

$fixedCount = 0

foreach ($filePath in $filesToFix) {
    if (Test-Path $filePath) {
        Write-Host "Fixing: $($filePath | Split-Path -Leaf)..." -NoNewline
        
        $lines = Get-Content $filePath
        $modified = $false
        
        # Find parameter name from function signature
        $paramName = "request"
        foreach ($line in $lines) {
            if ($line -match "export\s+async\s+function\s+\w+\s*\(\s*(\w+):\s*NextRequest") {
                $paramName = $Matches[1]
                break
            }
        }
        
        # Replace getAuthUser(request) with correct parameter
        $newLines = @()
        foreach ($line in $lines) {
            if ($line -match "getAuthUser\(request\)") {
                $newLine = $line -replace "getAuthUser\(request\)", "getAuthUser($paramName)"
                $newLines += $newLine
                $modified = $true
            }
            else {
                $newLines += $line
            }
        }
        
        if ($modified) {
            $newLines | Set-Content $filePath
            Write-Host " [FIXED] → getAuthUser($paramName)" -Fore Green
            $fixedCount++
        }
        else {
            Write-Host " [SKIP] Already correct" -Fore Yellow
        }
    }
    else {
        Write-Host "NOT FOUND: $filePath" -Fore Red
    }
}

Write-Host "`n=========================================" -Fore Cyan
Write-Host "COMPLETE! Fixed $fixedCount files" -Fore Green
Write-Host "=========================================`n" -Fore Cyan
