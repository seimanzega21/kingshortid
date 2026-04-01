param(
    [string]$Folder = "kembalinya-sang-master-kartu",
    [string]$OutputDir = "D:\kingshortid\Download Drama",
    [int]$EpsPerPart = 5
)

$BaseUrl = "https://stream.shortlovers.id/microdrama/$Folder"
$SaveDir = Join-Path $OutputDir $Folder
New-Item -ItemType Directory -Force -Path $SaveDir | Out-Null
Write-Host "=== STEP 1: Download 720p episodes ===" -ForegroundColor Cyan
Write-Host "Saving to: $SaveDir"

# Cover
try {
    Invoke-WebRequest -Uri "$BaseUrl/cover.webp" -OutFile "$SaveDir\cover.webp" -UseBasicParsing -ErrorAction Stop
    Write-Host "cover.webp OK" -ForegroundColor Green
} catch { Write-Host "cover.webp not found" -ForegroundColor DarkGray }

# Download episodes (720p only = ep001.mp4, skip ep001_540p.mp4)
$ep = 1; $fail = 0
while ($fail -lt 3) {
    $epStr = $ep.ToString("D3")
    $url = "$BaseUrl/ep$epStr.mp4"
    $out = "$SaveDir\ep$epStr.mp4"

    if (Test-Path $out) {
        Write-Host "[ep$epStr] Already exists, skipping" -ForegroundColor DarkGray
        $ep++; $fail = 0; continue
    }

    try {
        Invoke-WebRequest -Uri $url -Method Head -UseBasicParsing -ErrorAction Stop | Out-Null
        Write-Host "[ep$epStr] Downloading 720p... " -NoNewline -ForegroundColor White
        Invoke-WebRequest -Uri $url -OutFile $out -UseBasicParsing -ErrorAction Stop
        $mb = [math]::Round((Get-Item $out).Length / 1MB, 1)
        Write-Host "OK ($($mb)MB)" -ForegroundColor Green
        $ep++; $fail = 0
    } catch {
        Write-Host "[ep$epStr] Not found" -ForegroundColor Red
        $fail++; $ep++
    }
}

$downloaded = (Get-ChildItem $SaveDir -Filter "ep*.mp4").Count
Write-Host "`nDownloaded $downloaded episodes." -ForegroundColor Cyan

# === STEP 2: Merge per 5 episodes ===
Write-Host "`n=== STEP 2: Merge every $EpsPerPart episodes into parts ===" -ForegroundColor Cyan
$PartsDir = Join-Path $SaveDir "parts"
New-Item -ItemType Directory -Force -Path $PartsDir | Out-Null

$episodes = Get-ChildItem $SaveDir -Filter "ep*.mp4" | Sort-Object Name
$totalParts = [math]::Ceiling($episodes.Count / $EpsPerPart)

for ($part = 1; $part -le $totalParts; $part++) {
    $startIdx = ($part - 1) * $EpsPerPart
    $endIdx   = [math]::Min($startIdx + $EpsPerPart - 1, $episodes.Count - 1)
    $group    = $episodes[$startIdx..$endIdx]

    $firstEp = $group[0].BaseName -replace "ep", ""
    $lastEp  = $group[-1].BaseName -replace "ep", ""
    $outFile = Join-Path $PartsDir "part$($part.ToString('D2'))_ep${firstEp}-ep${lastEp}.mp4"

    $listFile = "$env:TEMP\fflist_$part.txt"
    $lines = $group | ForEach-Object { "file '$($_.FullName -replace '\\', '/')'" }
    [System.IO.File]::WriteAllLines($listFile, $lines)

    Write-Host "Part $part [ep$firstEp-ep$lastEp] ($($group.Count) eps)... " -NoNewline -ForegroundColor White

    $errFile = "$env:TEMP\ffmerr_$part.txt"
    $p = Start-Process ffmpeg -ArgumentList "-y -f concat -safe 0 -i `"$listFile`" -c copy `"$outFile`"" -Wait -PassThru -NoNewWindow -RedirectStandardError $errFile
    if ($p.ExitCode -eq 0 -and (Test-Path $outFile)) {
        $mb = [math]::Round((Get-Item $outFile).Length / 1MB, 1)
        Write-Host "OK ($($mb)MB)" -ForegroundColor Green
    } else {
        Write-Host "FAILED" -ForegroundColor Red
        Get-Content $errFile | Select-Object -Last 3 | ForEach-Object { Write-Host "  $_" -ForegroundColor DarkRed }
    }
    Remove-Item $listFile -Force -ErrorAction SilentlyContinue
}

Write-Host "`n=== DONE! ===" -ForegroundColor Cyan
Write-Host "Parts saved to: $PartsDir" -ForegroundColor Green
Get-ChildItem $PartsDir -Filter "part*.mp4" | Sort-Object Name |
    Select-Object Name, @{N='MB';E={"{0:N1}" -f ($_.Length/1MB)}} | Format-Table -AutoSize
