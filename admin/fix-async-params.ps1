# Fix Next.js 16 async params in all dynamic routes
$files = @(
    "src\app\api\comments\[id]\replies\route.ts",
    "src\app\api\comments\[id]\route.ts",
    "src\app\api\reviews\[id]\helpful\route.ts",
    "src\app\api\social\follow\[userId]\route.ts",
    "src\app\api\watch-party\[code]\join\route.ts",
    "src\app\api\playlists\[id]\dramas\route.ts",
    "src\app\api\categories\[id]\route.ts",
    "src\app\api\categories\[id]\dramas\route.ts",
    "src\app\api\dramas\[id]\route.ts",
    "src\app\api\dramas\[id]\episodes\route.ts",
    "src\app\api\episodes\[id]\route.ts",
    "src\app\api\episodes\[id]\stream\route.ts",
    "src\app\api\share\[dramaId]\route.ts",
    "src\app\api\users\[id]\route.ts"
)

foreach ($file in $files) {
    if (Test-Path $file) {
        Write-Host "Fixing $file..."
        $content = Get-Content $file -Raw
        
        # Fix pattern: { params }: { params: { xxx } } -> context: { params: Promise<{ xxx }> }
        # Extract param name and fix
        $content = $content -replace '\{ params \}: \{ params: \{ (\w+): string(; (\w+): string)? \} \}', 'context: { params: Promise<{ $1: string$2 }> }'
        
        # Fix: const { xxx } = params; -> const { xxx } = await context.params;
        $content = $content -replace 'const \{ (\w+)(, (\w+))? \} = params;', 'const { $1$2 } = await context.params;'
        
        Set-Content $file -Value $content -NoNewline
        Write-Host "Fixed $file"
    }
}

Write-Host "`nAll files fixed!"
