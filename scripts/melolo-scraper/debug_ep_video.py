#!/usr/bin/env python3
"""Debug: cek apakah video ep 16 & 17 bisa dibaca, format benar, drain valid."""
import requests, subprocess, os, json, sys, struct
sys.stdout.reconfigure(encoding="utf-8")
os.makedirs("C:/tmp", exist_ok=True)

BASE = "https://stream.shortlovers.id/dramas/microdrama/legenda-naga-kembali"

for ep in [16, 17]:
    url = f"{BASE}/ep{ep:03d}/video.mp4"
    print(f"\n{'='*55}")
    print(f"  Episode {ep}")
    print(f"  URL: {url}")

    # 1. HTTP HEAD check
    try:
        r = requests.head(url, timeout=10)
        print(f"  HTTP HEAD: {r.status_code}")
        print(f"  Content-Length: {r.headers.get('Content-Length', '?')} bytes")
        print(f"  Content-Type: {r.headers.get('Content-Type', '?')}")
        print(f"  Cache-Control: {r.headers.get('Cache-Control', '?')}")
    except Exception as e:
        print(f"  HEAD error: {e}")

    # 2. Download partial (4MB) dan cek magic bytes
    tmp = f"C:/tmp/ep{ep}_debug.mp4"
    try:
        r2 = requests.get(url, timeout=60, stream=True)
        total = 0
        with open(tmp, "wb") as f:
            for chunk in r2.iter_content(chunk_size=1024*1024):
                f.write(chunk)
                total += len(chunk)
                if total >= 4 * 1024 * 1024:
                    break
        r2.close()
        print(f"  Downloaded partial: {total/1024:.0f} KB")

        # Cek magic bytes MP4 (ftyp box)
        with open(tmp, "rb") as f:
            header = f.read(16)
        hex_header = header.hex()
        print(f"  File header (hex): {hex_header}")
        # MP4: byte 4-7 harusnya "ftyp"
        if b"ftyp" in header:
            print(f"  Magic bytes: OK (ftyp found = valid MP4)")
        elif b"moov" in header[:8]:
            print(f"  Magic bytes: OK (moov at start = faststart OK)")
        else:
            print(f"  Magic bytes: SUSPECT - no ftyp/moov in first bytes")
            print(f"  ASCII: {header[:16]}")

    except Exception as e:
        print(f"  Download error: {e}")
        continue

    # 3. ffprobe (full check)
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-print_format", "json",
             "-show_format", "-show_streams", tmp],
            capture_output=True, text=True, timeout=20
        )
        print(f"  ffprobe exit: {result.returncode}")
        if result.returncode == 0 and result.stdout.strip():
            data = json.loads(result.stdout)
            fmt = data.get("format", {})
            dur = float(fmt.get("duration", 0))
            sz = int(fmt.get("size", 0))
            print(f"  Duration: {dur:.1f}s | Size: {sz/1024/1024:.2f}MB")
            print(f"  Format: {fmt.get('format_name', '?')}")
            for s in data.get("streams", []):
                codec = s.get("codec_name", "?")
                ctype = s.get("codec_type", "?")
                w = s.get("width", "")
                h = s.get("height", "")
                print(f"  Stream: {ctype}/{codec} {w}x{h}")
        else:
            print(f"  ffprobe STDERR: {result.stderr[:300]}")
    except Exception as e:
        print(f"  ffprobe error: {e}")
    finally:
        try: os.unlink(tmp)
        except: pass

print("\n" + "=" * 55)
