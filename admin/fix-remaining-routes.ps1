# Comprehensive fix for all remaining Next.js 16 async params
$filesToFix = @(
    "src\app\api\categories\[id]\route.ts",
    "src\app\api\categories\[id]\dramas\route.ts",
    "src\app\api\dramas\[id]\route.ts",
    "src\app\api\dramas\[id]\episodes\route.ts",
    "src\app\api\episodes\[id]\route.ts",
    "src\app\api\episodes\[id]\stream\route.ts",
    "src\app\api\users\[id]\route.ts"
)

foreach ($file in $filesToFix) {
    if (Test-Path $file) {
        Write-Host "Processing $file..."
        $content = Get-Content $file -Raw
        
        # Pattern 1: Single param 
        # { params }: { params: { id: string } } -> context: { params: Promise<{ id: string }> }
        $content = $content -replace '\{ params \}: \{ params: \{ id: string \} \}', 'context: { params: Promise<{ id: string }> }'
        
        # Pattern 2: Multiple params
        # { params }: { params: { xxx: string; yyy: string } } -> context: { params: Promise<{ xxx: string; yyy: string }> }
        $content = $content -replace '\{ params \}: \{ params: \{([^}]+)\} \}', 'context: { params: Promise<{$1}> }'
        
        # Pattern 3: Fix param extraction
        # const { id } = params; -> const { id } = await context.params;
        $content = $content -replace '(\s+const \{[^}]+\}) = params;', '$1 = await context.params;'
        
        Set-Content $file -Value $content -NoNewline
        Write-Host "Fixed: $file"
    }
    else {
        Write-Host "Not found: $file" -Fore Yellow
    }
}

Write-Host "`n✓ All remaining files fixed!" -Fore Green
