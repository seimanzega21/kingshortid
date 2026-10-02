<#
.SYNOPSIS
    Script auto-check & auto-update 9router untuk Windows (Task Scheduler).
.DESCRIPTION
    Berjalan secara silent setiap 1 jam.
    Hanya mengupdate jika ada versi terbaru di npm.
    Sebelum update, proses 9router yang ada dimatikan (kill).
    Setelah update selesai, 9router dijalankan kembali di background.
#>

$ErrorActionPreference = 'SilentlyContinue'

# Lokasi log (opsional untuk catatan jika ada update)
$logFile = Join-Path -Path $PSScriptRoot -ChildPath "update_9router.log"

function Write-Log {
    param([string]$message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Add-Content -Path $logFile -Value "[$timestamp] $message" -Encoding utf8 -ErrorAction SilentlyContinue
}

try {
    # 1. Cek versi terinstall saat ini
    $npmList = & cmd.exe /c "npm.cmd list -g 9router --depth=0 2>nul"
    $currentMatch = $npmList | Select-String -Pattern '9router@([\d\.]+)'
    $currentVersion = if ($currentMatch) { $currentMatch.Matches.Groups[1].Value.Trim() } else { "" }

    # 2. Cek versi terbaru yang tersedia di npm registry
    $latestVersion = (& cmd.exe /c "npm.cmd view 9router version 2>nul").Trim()

    # Jika offline atau gagal cek versi registry, keluar diam-diam (silent)
    if ([string]::IsNullOrWhiteSpace($latestVersion)) {
        exit 0
    }

    # 3. Update hanya jika versi berbeda / versi baru tersedia
    if ($currentVersion -ne $latestVersion) {

        # a. Kill proses 9router yang sedang berjalan
        Get-Process -Name "*9router*" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue

        # Kill proses node/cmd yang menjalankan script 9router
        Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {
            $_.CommandLine -like "*9router*" -and $_.ProcessId -ne $PID
        } | ForEach-Object {
            Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
        }

        # Lepas port 20128 jika masih ada proses yang menduduki
        $connections = Get-NetTCPConnection -LocalPort 20128 -ErrorAction SilentlyContinue
        if ($connections) {
            $connections.OwningProcess | Select-Object -Unique | ForEach-Object {
                Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue
            }
        }

        # Tunggu port & file resource benar-benar dilepas
        Start-Sleep -Seconds 2

        # b. Update 9router ke versi terbaru secara silent
        & cmd.exe /c "npm.cmd install -g 9router@latest --silent 2>nul" | Out-Null

        # Verifikasi hasil instalasi
        $verifyList = & cmd.exe /c "npm.cmd list -g 9router --depth=0 2>nul"
        $verifyMatch = $verifyList | Select-String -Pattern '9router@([\d\.]+)'
        $newVersion = if ($verifyMatch) { $verifyMatch.Matches.Groups[1].Value.Trim() } else { "" }

        if ($newVersion -eq $latestVersion) {
            Write-Log "9router berhasil diupdate dari versi '$currentVersion' ke '$newVersion'."

            # c. Restart / jalankan kembali 9router di background (tanpa popup jendela)
            Start-Process -FilePath "cmd.exe" -ArgumentList "/c 9router" -WindowStyle Hidden

            Write-Log "9router telah berhasil direstart di background."
        } else {
            Write-Log "Gagal update 9router ke versi $latestVersion. Versi saat ini: $newVersion"
        }
    }
}
catch {
    # Mode silent: abaikan error atau catat ke log jika diperlukan
}
