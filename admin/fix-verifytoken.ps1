# Batch fix all verifyToken(request) to getAuthUser(request)
$files = @(
    "src\app\api\watch-party\[code]\join\route.ts",
    "src\app\api\watch-party\route.ts",
    "src\app\api\subscriptions\route.ts",
    "src\app\api\social\following\route.ts",
    "src\app\api\social\followers\route.ts",
    "src\app\api\social\follow\[userId]\route.ts",
    "src\app\api\seasons\route.ts",
    "src\app\api\reviews\route.ts",
    "src\app\api\reports\route.ts",
    "src\app\api\reviews\[id]\helpful\route.ts",
    "src\app\api\notifications\route.ts",
    "src\app\api\playlists\route.ts",
    "src\app\api\playlists\[id]\dramas\route.ts", "src\app\api\comments\[id]\route.ts",
    "src\app\api\comments\route.ts"
)

foreach ($file in $files) {
    if (Test-Path $file) {
        Write-Host "Fixing $file..."
        $content = Get-Content $file -Raw
        
        # Replace import
        $content = $content -replace "import \{ verifyToken \} from '@/lib/auth';", "import { getAuthUser } from '@/lib/auth';"
        
        # Replace function calls
        $content = $content -replace "verifyToken\(request\)", "getAuthUser(request)"
        
        Set-Content $file -Value $content -NoNewline
        Write-Host "  Fixed: $file" -Fore Green
    }
}

Write-Host "`nAll files fixed!" -Fore Cyan
