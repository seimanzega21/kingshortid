#!/usr/bin/env python3
"""
AUTO PURGE CLOUDFLARE AFTER FASTSTART
======================================
Script ini MENUNGGU r2_mp4_faststart.py selesai, lalu otomatis
purge Cloudflare cache untuk shortlovers.id.

Usage:
    python auto_purge_after_faststart.py --token YOUR_CF_API_TOKEN

Cara dapat token:
    https://dash.cloudflare.com/profile/api-tokens
    → Create Token → Edit Cache (Zone) → shortlovers.id
"""
import os, sys, time, subprocess, requests, argparse
from pathlib import Path
from datetime import datetime

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# ─── Config ──────────────────────────────────────────────────
ZONE_ID        = "a143b29a5d64943cb251157e25eaf3"   # shortlovers.id
CF_API_BASE    = "https://api.cloudflare.com/client/v4"
FASTSTART_LOCK = Path("C:/tmp/faststart_backfill")   # temp dir used by script
POLL_INTERVAL  = 30  # seconds between checks

# ─── Parse args ──────────────────────────────────────────────
parser = argparse.ArgumentParser()
parser.add_argument("--token", required=True, help="Cloudflare API Token")
args = parser.parse_args()

CF_TOKEN = args.token

def log(msg: str):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")

def is_faststart_running() -> bool:
    """Check if r2_mp4_faststart.py is still running."""
    # Check via temp dir existence (script creates/removes it)
    if FASTSTART_LOCK.exists():
        # Also check temp files inside
        files = list(FASTSTART_LOCK.glob("*.mp4*"))
        return len(files) > 0

    # Fallback: check via process list
    try:
        result = subprocess.run(
            ["powershell", "-Command",
             "Get-Process python -ErrorAction SilentlyContinue | "
             "Where-Object {$_.CommandLine -like '*faststart*'} | Measure-Object"],
            capture_output=True, text=True, timeout=10
        )
        return "Count    : 0" not in result.stdout
    except:
        return False

def check_faststart_process() -> bool:
    """Check if faststart process is running via PowerShell."""
    try:
        result = subprocess.run(
            ["powershell", "-Command",
             "Get-WmiObject Win32_Process | Where-Object {$_.CommandLine -like '*r2_mp4_faststart*'} | Select-Object -ExpandProperty ProcessId"],
            capture_output=True, text=True, timeout=10
        )
        return bool(result.stdout.strip())
    except:
        return False

def purge_cloudflare_everything(token: str, zone_id: str) -> bool:
    """Purge ALL cache for the zone."""
    url = f"{CF_API_BASE}/zones/{zone_id}/purge_cache"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    payload = {"purge_everything": True}

    try:
        r = requests.post(url, json=payload, headers=headers, timeout=30)
        data = r.json()
        if data.get("success"):
            log("✅ Cloudflare Purge Everything: SUCCESS!")
            return True
        else:
            log(f"❌ Purge failed: {data.get('errors', data)}")
            return False
    except Exception as e:
        log(f"❌ Purge error: {e}")
        return False

def verify_token(token: str, zone_id: str) -> bool:
    """Verify Cloudflare token works using token verify endpoint."""
    url = f"{CF_API_BASE}/user/tokens/verify"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        data = r.json()
        if data.get("success") and data.get("result", {}).get("status") == "active":
            log(f"Token valid! Status: active")
            return True
        else:
            log(f"Token invalid: {data.get('errors', data)}")
            return False
    except Exception as e:
        log(f"Token verify error: {e}")
        return False

def check_sample_sizes() -> dict:
    """Check a few episode sizes to see compression progress."""
    import requests as req
    results = {}
    for ep in [1, 5, 10]:
        url = f"https://stream.shortlovers.id/dramas/microdrama/legenda-naga-kembali/ep{ep:03d}/video.mp4"
        try:
            r = req.head(url, timeout=8)
            size_mb = int(r.headers.get("Content-Length", 0)) / 1024 / 1024
            cf = r.headers.get("cf-cache-status", "?")
            results[ep] = (size_mb, cf)
        except:
            results[ep] = (0, "err")
    return results

# ─── Main ────────────────────────────────────────────────────
def main():
    log("=" * 55)
    log("  AUTO PURGE AFTER FASTSTART WATCHER")
    log("=" * 55)
    log(f"Zone ID : {ZONE_ID}")
    log(f"Polling : every {POLL_INTERVAL}s")
    log("")

    # Verify token first
    log("Verifying Cloudflare token...")
    if not verify_token(CF_TOKEN, ZONE_ID):
        log("Token tidak valid! Cek token dan coba lagi.")
        log("Cara buat token: https://dash.cloudflare.com/profile/api-tokens")
        sys.exit(1)

    log("")
    log("Checking current episode sizes (before purge):")
    sizes = check_sample_sizes()
    for ep, (size, cf) in sizes.items():
        status = "✅" if size < 15 else "⚠️ masih besar"
        log(f"  Ep {ep:2}: {size:.2f} MB | cf: {cf} {status}")

    log("")
    log("Menunggu r2_mp4_faststart.py selesai...")
    log("(Script ini akan otomatis purge cache setelah selesai)")
    log("")

    iteration = 0
    last_file_count = -1

    while True:
        iteration += 1

        # Check temp dir for files still being processed
        temp_files = []
        if FASTSTART_LOCK.exists():
            temp_files = list(FASTSTART_LOCK.glob("*"))

        # Also check process
        still_running = check_faststart_process()

        file_count = len(temp_files)
        if file_count != last_file_count:
            if file_count > 0:
                log(f"📁 Processing... ({file_count} temp file(s)) | Process: {'running' if still_running else 'checking...'}")
            last_file_count = file_count

        if not still_running and not FASTSTART_LOCK.exists():
            log("")
            log("✅ r2_mp4_faststart.py selesai!")
            log("")
            break

        if iteration % 10 == 0:  # every 5 minutes
            log(f"  ... masih berjalan ({iteration * POLL_INTERVAL // 60} menit menunggu)")

        time.sleep(POLL_INTERVAL)

    # Script selesai - purge cache
    log("🔥 Memulai Cloudflare Purge Everything...")
    success = purge_cloudflare_everything(CF_TOKEN, ZONE_ID)

    if success:
        log("")
        log("Menunggu 10 detik lalu verifikasi...")
        time.sleep(10)

        log("Cek ukuran episode setelah purge:")
        sizes_after = check_sample_sizes()
        for ep, (size, cf) in sizes_after.items():
            status = "✅ OK!" if size < 15 else "⚠️ masih besar (faststart mungkin skip)"
            log(f"  Ep {ep:2}: {size:.2f} MB | cf: {cf} {status}")

        log("")
        log("🎉 SELESAI! Cache sudah dipurge. Video seharusnya cepat sekarang.")
    else:
        log("")
        log("⚠️  Purge gagal. Lakukan manual di:")
        log("    https://dash.cloudflare.com → shortlovers.id → Caching → Purge Everything")

if __name__ == "__main__":
    main()
