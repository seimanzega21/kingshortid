#!/usr/bin/env python3
"""
Targeted migration: 12 external episodes from mydramawave.com → R2
- Download HLS (.m3u8) → encode to MP4 720p + 540p → upload to R2 → PATCH via API
"""
import subprocess, requests, boto3, sys
from pathlib import Path
from botocore.config import Config

# ── Config ──────────────────────────────────────────────────
API_BASE   = 'https://api.shortlovers.id'
ADMIN_KEY  = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'

R2_ENDPOINT = 'https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com'
R2_KEY_ID   = '07c99c897986ea52703c1285308d5e2c'
R2_SECRET   = '44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44'
R2_BUCKET   = 'shortlovers'
R2_PUBLIC   = 'https://stream.shortlovers.id'

TEMP_DIR = Path('/tmp/migrate_12')
TEMP_DIR.mkdir(exist_ok=True)

HEADERS = {'x-admin-key': ADMIN_KEY, 'Content-Type': 'application/json'}

# ── 12 External Episodes (confirmed from DB audit) ──────────
EPISODES = [
    # Tak Ada Jalan Kembali
    {
        'id': 'lvoriajj27li7dvokpvcscj3', 'ep': 49,
        'drama': 'Tak Ada Jalan Kembali',
        'prefix': 'tak-ada-jalan-kembali',
        'url': 'https://video-v6.mydramawave.com/vt/e312ad84-8952-4ae3-a1df-0b8963c9bfc7/h264-813e0cd8-f99d-4d45-94e6-33a803a274d8.m3u8'
    },
    {
        'id': 'iefhbvevcqpim8v6aaafst3d', 'ep': 50,
        'drama': 'Tak Ada Jalan Kembali',
        'prefix': 'tak-ada-jalan-kembali',
        'url': 'https://video-v6.mydramawave.com/vt/d4edfa43-dcbd-4efe-b5da-7ba29e9c1cf8/h264-7dc7fc82-a278-4e65-98b9-b1a06945be7e.m3u8'
    },
    # Terbangun sebagai Suami Terburuk
    {
        'id': 'irhvwsularwpr6ive99f5b0b', 'ep': 17,
        'drama': 'Terbangun sebagai Suami Terburuk',
        'prefix': 'terbangun-suami-terburuk',
        'url': 'https://video-v6.mydramawave.com/vt/e090e703-061c-44bf-89e6-8a542b90046e/h264-caeefb20-1835-4163-b179-89bac47ed16c.m3u8'
    },
    {
        'id': 'hdxvpe5f867rcfzct5p3plxw', 'ep': 37,
        'drama': 'Terbangun sebagai Suami Terburuk',
        'prefix': 'terbangun-suami-terburuk',
        'url': 'https://video-v6.mydramawave.com/vt/3a3d007b-a9c6-49e2-b81f-717a6a5180c7/h264-43f510f8-ec5f-4576-b879-c5b35b5899aa.m3u8'
    },
    {
        'id': 'xbkmwot2tnjhd0o0o1ptfv3s', 'ep': 43,
        'drama': 'Terbangun sebagai Suami Terburuk',
        'prefix': 'terbangun-suami-terburuk',
        'url': 'https://video-v6.mydramawave.com/vt/3f7020eb-5565-4c0c-9b8c-8126f1b8ddfc/h264-3d20f00e-b206-4d39-8b1f-d2b3fcedab88.m3u8'
    },
    {
        'id': 'pujw0kb2qu4fnm62e3rrvbv6', 'ep': 44,
        'drama': 'Terbangun sebagai Suami Terburuk',
        'prefix': 'terbangun-suami-terburuk',
        'url': 'https://video-v6.mydramawave.com/vt/853551ba-0053-424d-a997-a17bb7876086/h264-3e9cabc6-467a-4f4c-9a7d-75a7c6d30b37.m3u8'
    },
    {
        'id': 'sr23ozm3mq0n2ih4dicjt5oa', 'ep': 48,
        'drama': 'Terbangun sebagai Suami Terburuk',
        'prefix': 'terbangun-suami-terburuk',
        'url': 'https://video-v6.mydramawave.com/vt/9382bae9-7300-47a3-9364-3f82fb863530/h264-1bf2d942-6414-4288-9e08-4ea9f4a305b4.m3u8'
    },
    {
        'id': 'ycjs3i3jekqjb65x9colak25', 'ep': 49,
        'drama': 'Terbangun sebagai Suami Terburuk',
        'prefix': 'terbangun-suami-terburuk',
        'url': 'https://video-v6.mydramawave.com/vt/769b9ff0-5f64-48f0-a4ad-88964b5488c5/h264-a1bbf8eb-6ed3-4dbe-b168-6f1e4affca25.m3u8'
    },
    {
        'id': 'xf4e3t5d6s9x0ftbq8w43fm8', 'ep': 50,
        'drama': 'Terbangun sebagai Suami Terburuk',
        'prefix': 'terbangun-suami-terburuk',
        'url': 'https://video-v6.mydramawave.com/vt/6228c17b-325c-439b-b286-0ce21f9fde82/h264-36424e2b-3ff7-4598-b6c6-3a8caf47bc52.m3u8'
    },
    {
        'id': 'cp8608n8g7jn6rj39k2l8tol', 'ep': 55,
        'drama': 'Terbangun sebagai Suami Terburuk',
        'prefix': 'terbangun-suami-terburuk',
        'url': 'https://video-v6.mydramawave.com/vt/9eb978d4-b6cc-49cd-858a-85be26558c74/h264-9cd9c44b-14cb-4b77-ba7e-70c2bd0293bc.m3u8'
    },
    {
        'id': 'lmap7r5o9z0ldqta4m8o159u', 'ep': 56,
        'drama': 'Terbangun sebagai Suami Terburuk',
        'prefix': 'terbangun-suami-terburuk',
        'url': 'https://video-v6.mydramawave.com/vt/55bc78be-4bdd-4287-aad4-658e1839c69c/h264-7fa60dbb-478a-4c73-a43f-c50423d0fb84.m3u8'
    },
    {
        'id': 'qdm9rguz2sqvk9irlzrp01zm', 'ep': 59,
        'drama': 'Terbangun sebagai Suami Terburuk',
        'prefix': 'terbangun-suami-terburuk',
        'url': 'https://video-v6.mydramawave.com/vt/8ab4b20d-415f-4cf4-8281-e29398da662d/h264-0c9e7503-5678-41fe-bd6f-883ca2736d14.m3u8'
    },
]

def get_r2():
    return boto3.client(
        's3', endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_KEY_ID,
        aws_secret_access_key=R2_SECRET,
        config=Config(signature_version='s3v4'),
        region_name='auto'
    )

def r2_upload(r2c, path, key):
    print(f"    ↑ Uploading {key}...", end='', flush=True)
    with open(path, 'rb') as f:
        r2c.upload_fileobj(f, R2_BUCKET, key,
            ExtraArgs={'ContentType': 'video/mp4'},
            Config=boto3.s3.transfer.TransferConfig(
                multipart_threshold=30 * 1024 * 1024,
                multipart_chunksize=10 * 1024 * 1024
            )
        )
    print(" ✓")

def encode(m3u8_url, out_720, out_540):
    """Download HLS stream and encode to 720p MP4 + 540p MP4"""
    # 720p: copy video, fix audio codec for mp4 container
    print(f"    📥 Downloading + encoding 720p...", flush=True)
    cmd_720 = [
        'ffmpeg', '-y',
        '-i', m3u8_url,
        '-c', 'copy',
        '-bsf:a', 'aac_adtstoasc',
        '-movflags', '+faststart',
        str(out_720)
    ]
    r = subprocess.run(cmd_720, capture_output=True, text=True, timeout=1200)
    if r.returncode != 0 or not out_720.exists():
        print(f"    ✗ 720p ffmpeg error:\n{r.stderr[-500:]}")
        return False

    # 540p: re-encode from 720p
    print(f"    📥 Encoding 540p...", flush=True)
    cmd_540 = [
        'ffmpeg', '-y',
        '-i', str(out_720),
        '-vf', 'scale=-2:540',
        '-c:v', 'libx264', '-crf', '28', '-preset', 'fast',
        '-c:a', 'aac', '-b:a', '128k',
        '-movflags', '+faststart',
        str(out_540)
    ]
    r2 = subprocess.run(cmd_540, capture_output=True, text=True, timeout=1200)
    if r2.returncode != 0 or not out_540.exists():
        print(f"    ✗ 540p ffmpeg error:\n{r2.stderr[-500:]}")
        return False
    return True

def patch_episode(ep_id, url_720, url_540):
    resp = requests.patch(
        f"{API_BASE}/api/episodes/{ep_id}",
        headers=HEADERS,
        json={"videoUrl": url_720, "videoUrl540p": url_540},
        timeout=30
    )
    return resp.ok, resp.status_code

def main():
    r2c = get_r2()
    success, failed = 0, 0

    print(f"\n{'='*60}")
    print(f"  MIGRATING 12 EXTERNAL EPISODES → R2")
    print(f"{'='*60}\n")

    for i, ep in enumerate(EPISODES, 1):
        ep_id    = ep['id']
        ep_num   = ep['ep']
        prefix   = ep['prefix']
        src_url  = ep['url']
        drama    = ep['drama']

        key_720 = f"{prefix}/ep{ep_num:03d}.mp4"
        key_540 = f"{prefix}/ep{ep_num:03d}_540p.mp4"
        url_720 = f"{R2_PUBLIC}/{key_720}"
        url_540 = f"{R2_PUBLIC}/{key_540}"

        print(f"[{i}/12] {drama} — Ep {ep_num}")

        t_720 = TEMP_DIR / f"tmp_720_ep{ep_num}_{ep_id[:8]}.mp4"
        t_540 = TEMP_DIR / f"tmp_540_ep{ep_num}_{ep_id[:8]}.mp4"

        try:
            if encode(src_url, t_720, t_540):
                r2_upload(r2c, t_720, key_720)
                r2_upload(r2c, t_540, key_540)

                ok, status = patch_episode(ep_id, url_720, url_540)
                if ok:
                    print(f"    ✅ Done! → {url_720}")
                    success += 1
                else:
                    print(f"    ✗ API PATCH failed (HTTP {status})")
                    failed += 1
            else:
                print(f"    ✗ Encode failed, skipping")
                failed += 1
        except Exception as e:
            print(f"    ✗ ERROR: {e}")
            failed += 1
        finally:
            if t_720.exists(): t_720.unlink()
            if t_540.exists(): t_540.unlink()

    print(f"\n{'='*60}")
    print(f"  DONE! ✅ Success: {success}/12 | ✗ Failed: {failed}/12")
    print(f"{'='*60}\n")

if __name__ == '__main__':
    main()
