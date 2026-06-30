# -*- coding: utf-8 -*-
"""
Test: Download video segments via Playwright browser fetch (bypass TLS fingerprinting)
"""
import asyncio
import sys
import os
import subprocess
import base64

sys.stdout.reconfigure(encoding='utf-8')

TEMP_DIR = 'D:/kingshortid/temp_raja'
os.makedirs(TEMP_DIR, exist_ok=True)

M3U8_URL = 'https://mmcdn-v.stardust-tv.com/%E5%8D%B0%E5%B0%BC%E8%AF%AD/%E6%88%91%E6%9C%89%E4%B8%80%E5%89%91%EF%BC%8C%E5%8F%AF%E6%96%A9%E9%98%8E%E7%BD%97_ID_DUB/h264/Satu%20Pedang,%20Tebas%20Raja%20Neraka_001/59296e557a9949f4a8238ab67e431dad.m3u8'

async def download_via_browser(ep_no, m3u8_url):
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
        )
        page = await ctx.new_page()

        # Open a blank page (we don't need to open vidrama - just need the browser context)
        # First navigate to vidrama so we have the right origin cookies
        WATCH_URL = f'https://vidrama.asia/watch/satu-pedang-tebas-raja-neraka--19820/{ep_no}?provider=stardusttv'
        print(f"  Opening watch page to get session context...")
        try:
            await page.goto(WATCH_URL, wait_until='networkidle', timeout=30000)
            await asyncio.sleep(3)
        except:
            pass

        print(f"  Fetching m3u8 manifest via browser fetch...")

        # Step 1: Fetch m3u8 manifest via browser
        m3u8_content = await page.evaluate(f"""
            async () => {{
                try {{
                    const response = await fetch('{m3u8_url}', {{
                        method: 'GET',
                        headers: {{
                            'Referer': 'https://vidrama.asia/',
                        }}
                    }});
                    if (!response.ok) return 'HTTP_ERROR_' + response.status;
                    return await response.text();
                }} catch(e) {{
                    return 'FETCH_ERROR: ' + e.toString();
                }}
            }}
        """)

        if not m3u8_content or 'ERROR' in str(m3u8_content):
            print(f"  ❌ Failed to fetch m3u8: {m3u8_content}")
            await browser.close()
            return None

        print(f"  ✅ m3u8 fetched! Length: {len(m3u8_content)} chars")
        print(f"  First 300 chars: {m3u8_content[:300]}")

        # Parse segment URLs from m3u8
        base_url = m3u8_url.rsplit('/', 1)[0]
        lines = m3u8_content.strip().split('\n')
        segments = []
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                if line.startswith('http'):
                    segments.append(line)
                else:
                    segments.append(f"{base_url}/{line}")

        print(f"  Found {len(segments)} segments")
        if segments:
            print(f"  First segment: {segments[0][-70:]}")
            print(f"  Last segment: {segments[-1][-70:]}")

        if not segments:
            print("  ❌ No segments found in m3u8!")
            await browser.close()
            return None

        # Step 2: Download first 5 segments as test
        seg_files = []
        print(f"\n  Downloading first 5 segments via browser fetch...")
        for i, seg_url in enumerate(segments[:5]):
            print(f"    Segment {i+1}/{min(5, len(segments))}...", end='', flush=True)
            
            # Download segment as base64 via browser
            seg_b64 = await page.evaluate(f"""
                async () => {{
                    try {{
                        const response = await fetch('{seg_url}', {{
                            headers: {{ 'Referer': 'https://vidrama.asia/' }}
                        }});
                        if (!response.ok) return 'HTTP_ERROR_' + response.status;
                        const buffer = await response.arrayBuffer();
                        const bytes = new Uint8Array(buffer);
                        let binary = '';
                        for (let i = 0; i < bytes.byteLength; i++) {{
                            binary += String.fromCharCode(bytes[i]);
                        }}
                        return btoa(binary);
                    }} catch(e) {{
                        return 'FETCH_ERROR: ' + e.toString();
                    }}
                }}
            """)
            
            if seg_b64 and not str(seg_b64).startswith('ERROR') and not str(seg_b64).startswith('HTTP'):
                seg_data = base64.b64decode(seg_b64)
                seg_path = os.path.join(TEMP_DIR, f'ep{ep_no:03d}_seg{i:04d}.ts')
                with open(seg_path, 'wb') as f:
                    f.write(seg_data)
                seg_files.append(seg_path)
                print(f" ✅ {len(seg_data)/1024:.1f} KB")
            else:
                print(f" ❌ Failed: {str(seg_b64)[:100]}")
                break

        await browser.close()
        return seg_files, len(segments)

# Run test
result = asyncio.run(download_via_browser(1, M3U8_URL))
if result:
    seg_files, total_segs = result
    print(f"\n✅ Test complete! Downloaded {len(seg_files)}/5 test segments")
    print(f"   Total segments in full episode: {total_segs}")
    
    if seg_files:
        # Test ffmpeg concat
        concat_list = os.path.join(TEMP_DIR, 'concat_test.txt')
        with open(concat_list, 'w') as f:
            for s in seg_files:
                f.write(f"file '{s.replace(chr(92), '/')}'\n")
        
        out_mp4 = os.path.join(TEMP_DIR, 'test_ep1_browser.mp4')
        cmd = ['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', concat_list,
               '-c', 'copy', '-movflags', '+faststart', '-loglevel', 'warning', out_mp4]
        res = subprocess.run(cmd, capture_output=True, text=True, errors='ignore')
        if res.returncode == 0 and os.path.exists(out_mp4):
            size = os.path.getsize(out_mp4)
            print(f"   ✅ FFmpeg concat OK! MP4 size: {size/1024:.1f} KB")
        else:
            print(f"   ❌ FFmpeg concat failed: {res.stderr[-200:]}")
else:
    print("❌ Browser download test failed!")
