# -*- coding: utf-8 -*-
"""
Test: Intercept TS segment responses directly from the video player
(Playwright captures what the HLS player downloads naturally)
"""
import asyncio
import sys
import os
import subprocess

sys.stdout.reconfigure(encoding='utf-8')

TEMP_DIR = 'D:/kingshortid/temp_raja/test_intercept'
os.makedirs(TEMP_DIR, exist_ok=True)

WATCH_URL = 'https://vidrama.asia/watch/satu-pedang-tebas-raja-neraka--19820/1?provider=stardusttv'

async def capture_via_intercept():
    from playwright.async_api import async_playwright

    segments = {}  # url -> bytes
    m3u8_content = None
    m3u8_url = None

    async def on_response(response):
        nonlocal m3u8_content, m3u8_url
        url = response.url
        try:
            # Capture m3u8 manifest
            if '.m3u8' in url and ('stardust' in url.lower() or 'mmcdn' in url.lower()):
                if m3u8_content is None:
                    body = await response.body()
                    m3u8_content = body.decode('utf-8', errors='ignore')
                    m3u8_url = url
                    print(f"\n  ✅ M3U8 captured! ({len(m3u8_content)} chars)")
                    # Count segments
                    seg_count = sum(1 for l in m3u8_content.split('\n') if l.strip() and not l.startswith('#'))
                    print(f"     Segments in this episode: {seg_count}")
                    
            # Capture .ts segments
            elif '.ts' in url and ('stardust' in url.lower() or 'mmcdn' in url.lower()):
                if url not in segments:
                    body = await response.body()
                    segments[url] = body
                    idx = len(segments)
                    if idx % 5 == 0 or idx <= 3:
                        print(f"  📦 Segment {idx}: {len(body)/1024:.1f} KB ({url[-50:]})")
        except Exception as e:
            pass

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
        )
        page = await ctx.new_page()
        page.on('response', on_response)

        print(f"Opening watch page...")
        try:
            await page.goto(WATCH_URL, wait_until='networkidle', timeout=30000)
        except:
            pass

        # Wait for initial segments to load
        await asyncio.sleep(5)

        # Try to auto-play and seek video to trigger more segments
        print(f"\nTriggering video playback and seeking...")
        try:
            await page.evaluate("""
                async () => {
                    const video = document.querySelector('video');
                    if (video) {
                        video.volume = 0;
                        video.muted = true;
                        await video.play().catch(()=>{});
                        console.log('Video duration:', video.duration);
                        // Seek forward to trigger more buffer loads
                        if (video.duration > 0) {
                            for (let t = 10; t < video.duration; t += 20) {
                                video.currentTime = t;
                                await new Promise(r => setTimeout(r, 500));
                            }
                        }
                    }
                }
            """)
        except Exception as e:
            print(f"  Seek error: {e}")

        # Wait for more segments to download
        print(f"Waiting for segments to buffer...")
        await asyncio.sleep(15)

        print(f"\n=== RESULTS ===")
        print(f"M3U8 captured: {'Yes' if m3u8_content else 'No'}")
        print(f"Segments captured: {len(segments)}")

        await browser.close()

    if not segments:
        print("❌ No segments captured!")
        return

    # Get expected total from m3u8
    total_segs = 0
    if m3u8_content:
        total_segs = sum(1 for l in m3u8_content.split('\n') if l.strip() and not l.startswith('#'))
        print(f"Expected total segments: {total_segs}")
        print(f"Captured: {len(segments)}/{total_segs}")

    # Save captured segments to disk in order
    seg_dir = TEMP_DIR
    # Order segments based on m3u8 playlist order
    ordered_segs = []
    if m3u8_content and m3u8_url:
        base_url = m3u8_url.rsplit('/', 1)[0]
        for line in m3u8_content.split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                full_url = line if line.startswith('http') else f"{base_url}/{line}"
                if full_url in segments:
                    ordered_segs.append((full_url, segments[full_url]))
    else:
        ordered_segs = list(segments.items())

    print(f"\nSaving {len(ordered_segs)} segments to disk...")
    saved_files = []
    for i, (url, data) in enumerate(ordered_segs):
        path = os.path.join(seg_dir, f'seg_{i:04d}.ts')
        with open(path, 'wb') as f:
            f.write(data)
        saved_files.append(path)

    if not saved_files:
        print("❌ No segments to save!")
        return

    # Concatenate with ffmpeg
    concat_file = os.path.join(seg_dir, 'concat.txt')
    with open(concat_file, 'w') as f:
        for sf in saved_files:
            f.write(f"file '{sf.replace(chr(92), '/')}'\n")

    out_mp4 = os.path.join(TEMP_DIR, 'test_ep1_intercepted.mp4')
    print(f"\nConcatenating with ffmpeg...")
    cmd = [
        'ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', concat_file,
        '-c', 'copy', '-movflags', '+faststart', '-loglevel', 'warning', out_mp4
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, errors='ignore', timeout=120)
    if res.returncode == 0 and os.path.exists(out_mp4):
        size_mb = os.path.getsize(out_mp4) / (1024*1024)
        print(f"✅ SUCCESS! MP4 size: {size_mb:.2f} MB")
        print(f"   Output: {out_mp4}")
    else:
        print(f"❌ FFmpeg failed: {res.stderr[-300:]}")

asyncio.run(capture_via_intercept())
