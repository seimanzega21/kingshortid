# Automated APK Analysis Script
# Decompiles APK and searches for signing mechanism

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Automated APK Analysis" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$apkPath = "goodshort.apk"
$jadxPath = "C:\Users\Seiman\Downloads\jadx-gui-1.5.0-with-jre-win\bin\jadx.bat"
$outputDir = "goodshort_decompiled"

# Check APK exists
if (-not (Test-Path $apkPath)) {
    Write-Host "ERROR: goodshort.apk not found!" -ForegroundColor Red
    exit 1
}

Write-Host "[1/4] Checking jadx CLI..." -ForegroundColor Yellow
if (-not (Test-Path $jadxPath)) {
    Write-Host "  jadx not found at expected location" -ForegroundColor Yellow
    Write-Host "  Trying alternative path..." -ForegroundColor Yellow
    $jadxPath = "jadx"  # Try system PATH
}

Write-Host "[2/4] Decompiling APK (this takes 2-3 minutes)..." -ForegroundColor Yellow
Write-Host "  Output: $outputDir" -ForegroundColor Gray

# Decompile APK
if (Test-Path $jadxPath) {
    & $jadxPath -d $outputDir $apkPath --show-bad-code
} else {
    Write-Host "  Using jadx from PATH..." -ForegroundColor Gray
    jadx -d $outputDir $apkPath --show-bad-code
}

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Decompilation failed!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "[3/4] Searching for signing code..." -ForegroundColor Yellow

# Search patterns
$searches = @{
    "RSA_KEY" = "-----BEGIN"
    "SIGN_UTIL" = "class.*Sign.*Util"
    "SHA256_RSA" = "SHA256withRSA"
    "KEY_FACTORY" = "KeyFactory"
    "SIGNATURE_INSTANCE" = "Signature\.getInstance"
}

$results = @{}

foreach ($name in $searches.Keys) {
    $pattern = $searches[$name]
    Write-Host "  Searching: $name" -ForegroundColor Gray
    
    $found = Select-String -Path "$outputDir\sources\**\*.java" -Pattern $pattern -SimpleMatch:$false | 
             Where-Object { $_.Path -match "newreading|goodreels" } |
             Select-Object -First 5
    
    if ($found) {
        $results[$name] = $found
        Write-Host "    ✓ Found $($found.Count) matches" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "[4/4] Analysis Results:" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan

foreach ($name in $results.Keys) {
    Write-Host ""
    Write-Host "$name matches:" -ForegroundColor Green
    foreach ($match in $results[$name]) {
        $relativePath = $match.Path -replace [regex]::Escape($outputDir), ""
        Write-Host "  File: $relativePath" -ForegroundColor Gray
        Write-Host "  Line $($match.LineNumber): $($match.Line.Trim())" -ForegroundColor White
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Decompiled code location: $outputDir\sources" -ForegroundColor Yellow
Write-Host ""
Write-Host "Next: Analyzing specific files..." -ForegroundColor Yellow

