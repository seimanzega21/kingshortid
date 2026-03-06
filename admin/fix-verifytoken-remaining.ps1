# Batch fix REMAINING files with verifyToken import issues  
$files = @(
    "src\app\api\watch-party\[code]\join\route.ts",
    "src\app\api\social\follow\[userId]\route.ts",
    "src\app\api\rewards\daily-spin\route.ts",
    "src\app\api\reviews\[id]\helpful\route.ts",
    "src\app\api\recommendations\route.ts",
    "src\app\api\playlists\[id]\dramas\route.ts",
    "src\app\api\leaderboard\[type]\route.ts",
    "src\app\api\comments\[id]\route.ts",
    "src\app\api\challenges\route.ts",
    "src\app\api\comments\[id]\replies\route.ts",
    "src\app\api\achievements\route.ts",
    "src\app\api\achievements\check\route.ts"
)

foreach ($file in $files) {
    if (Test-Path $file) {
        Write-Host "Fixing $file..."
        $content = Get-Content $file -Raw
        
        # Replace import
        $content = $content -replace "import \{ verifyToken \} from '@/lib/auth';", "import { getAuthUser } from '@/lib/auth';"
        
        # Replace function calls  
        $content = $content -replace "verifyToken\(request\)", "getAuthUser(request)"
        $content = $content -replace "verifyToken\(token\)", "getAuthUser(request)"
        
        Set-Content $file -Value $content -NoNewline
        Write-Host "  FIXED!" -Fore Green
    }
}

Write-Host "`nDONE - All remaining files fixed!" -Fore Cyan
