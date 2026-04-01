param(
    [string]$Folder = "mata-ajaib-kekayaanku",
    [string]$OutputDir = "D:\kingshortid\Download Drama"
)

$BaseUrl = "https://stream.shortlovers.id/microdrama/$Folder"
$SaveDir = Join-Path $OutputDir $Folder

New-Item -ItemType Directory -Force -Path $SaveDir | Out-Null
Write-Host "Saving to: $SaveDir" -ForegroundColor Cyan

# Download cover
$coverUrl = "$BaseUrl/cover.webp"
$coverPath = Join-Path $SaveDir "cover.webp"
try {
    Invoke-WebRequest -Uri $coverUrl -OutFile $coverPath -ErrorAction Stop
    Write-Host "cover.webp OK" -ForegroundColor Green
} catch { Write-Host "cover.webp not found" -ForegroundColor Yellow }

# Download episodes until 404
$ep = 1
$fail = 0
while ($fail -lt 3) {
    $epStr = $ep.ToString("D3")
    $url = "$BaseUrl/ep$epStr.mp4"
    $out = Join-Path $SaveDir "ep$epStr.mp4"
    
    if (Test-Path $out) {
        Write-Host "[$epStr] Already exists, skip" -ForegroundColor DarkGray
        $ep++
        $fail = 0
        continue
    }
    
    try {
        $resp = Invoke-WebRequest -Uri $url -Method Head -ErrorAction Stop
        Write-Host "[$epStr] Downloading..." -ForegroundColor White -NoNewline
        Invoke-WebRequest -Uri $url -OutFile $out -ErrorAction Stop
        $size = [math]::Round((Get-Item $out).Length / 1MB, 1)
        Write-Host " OK ($($size)MB)" -ForegroundColor Green
        $ep++
        $fail = 0
    } catch {
        Write-Host "[$epStr] Not found - stopping" -ForegroundColor Red
        $fail++
        $ep++
    }
}

$total = (Get-ChildItem $SaveDir -Filter "*.mp4").Count
Write-Host "`nDone! $total episodes downloaded to: $SaveDir" -ForegroundColor Cyan
