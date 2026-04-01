param(
    [string]$DramaFolder = "D:\kingshortid\Download Drama\mata-ajaib-kekayaanku",
    [int]$EpsPerPart = 5
)

$OutputDir = Join-Path $DramaFolder "parts"
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

$episodes = Get-ChildItem $DramaFolder -Filter "ep*.mp4" | Sort-Object Name
if ($episodes.Count -eq 0) { Write-Host "No episodes found!" -ForegroundColor Red; exit 1 }

Write-Host "Found $($episodes.Count) episodes. Merging every $EpsPerPart into parts..." -ForegroundColor Cyan

$totalParts = [math]::Ceiling($episodes.Count / $EpsPerPart)

for ($part = 1; $part -le $totalParts; $part++) {
    $startIdx = ($part - 1) * $EpsPerPart
    $endIdx   = [math]::Min($startIdx + $EpsPerPart - 1, $episodes.Count - 1)
    $group    = $episodes[$startIdx..$endIdx]

    $firstEp = $group[0].BaseName -replace 'ep', ''
    $lastEp  = $group[-1].BaseName -replace 'ep', ''
    $partNum = $part.ToString('D2')
    $outFile = Join-Path $OutputDir "part${partNum}_ep${firstEp}-ep${lastEp}.mp4"

    # Build concat list WITHOUT BOM (ffmpeg hates BOM)
    $listFile = "$env:TEMP\fflist_part$partNum.txt"
    $lines = $group | ForEach-Object { "file '$($_.FullName -replace '\\', '/')'" }
    [System.IO.File]::WriteAllLines($listFile, $lines)

    Write-Host "Part $part [ep$firstEp-ep$lastEp] ($($group.Count) eps)... " -NoNewline -ForegroundColor White

    # Run ffmpeg directly
    $errFile = "$env:TEMP\ff_err_$partNum.txt"
    $exitCode = (Start-Process ffmpeg -ArgumentList "-y -f concat -safe 0 -i `"$listFile`" -c copy `"$outFile`"" -Wait -PassThru -NoNewWindow -RedirectStandardError $errFile).ExitCode

    if ($exitCode -eq 0 -and (Test-Path $outFile)) {
        $mb = [math]::Round((Get-Item $outFile).Length / 1MB, 1)
        Write-Host "OK ($mb MB)" -ForegroundColor Green
    } else {
        Write-Host "FAILED" -ForegroundColor Red
        Get-Content $errFile | Select-Object -Last 3 | ForEach-Object { Write-Host "  $_" -ForegroundColor DarkRed }
    }

    Remove-Item $listFile -Force -ErrorAction SilentlyContinue
}

Write-Host "`nDone! Parts saved to: $OutputDir" -ForegroundColor Cyan
Get-ChildItem $OutputDir -Filter "part*.mp4" | Sort-Object Name |
    Select-Object Name, @{N='MB';E={"{0:N1}" -f ($_.Length/1MB)}} | Format-Table -AutoSize
