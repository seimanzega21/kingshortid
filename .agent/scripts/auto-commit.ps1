# auto-commit.ps1
# Auto-commit dan push semua perubahan ke GitHub
# Usage: .\auto-commit.ps1
# Setup via Task Scheduler untuk berjalan otomatis

$repoPath = "D:\kingshortid"
Set-Location $repoPath

# Cek apakah ada uncommitted changes
$status = git status --porcelain 2>&1
if (-not $status) {
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Tidak ada perubahan." -ForegroundColor Gray
    exit 0
}

# Timestamp untuk commit message
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm"
$changedFiles = ($status -split "`n").Count

# Stage semua perubahan
git add -A

# Commit
$msg = "chore: auto-commit $changedFiles file(s) at $timestamp"
git commit -m $msg

# Push ke origin
git push origin master 2>&1 | Out-Null

if ($LASTEXITCODE -eq 0) {
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] ✅ Auto-commit berhasil: $msg" -ForegroundColor Green
} else {
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] ❌ Push gagal. Check koneksi/credentials." -ForegroundColor Red
}
