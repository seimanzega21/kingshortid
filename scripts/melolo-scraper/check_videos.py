#!/usr/bin/env python3
"""Check if .ts segments actually exist on R2 for working vs non-working dramas"""
import requests

R2 = "https://stream.shortlovers.id"

# Working drama
dramas_to_check = [
    ("800-ribu-beli-dunia-kultivasi", "episodes/002/playlist.m3u8"),  # WORKS
    ("bos-supermarket-yang-hebat", "episodes/002/playlist.m3u8"),     # probably broken
    ("cinta-sejati-abadi", "episodes/002/playlist.m3u8"),             # probably broken
    ("harga-diri-anak-angkat", "episodes/002/playlist.m3u8"),         # probably broken
]

for slug, ep_path in dramas_to_check:
    m3u8_url = f"{R2}/melolo/{slug}/{ep_path}"
    print(f"\n=== {slug} ===")
    
    # Check m3u8
    try:
        r = requests.get(m3u8_url, timeout=10)
        if r.status_code != 200:
            print(f"  m3u8: FAIL ({r.status_code})")
            continue
        print(f"  m3u8: OK ({len(r.text)} bytes)")
        
        # Parse m3u8 and check first segment
        lines = r.text.strip().split('\n')
        segments = [l for l in lines if not l.startswith('#') and l.strip()]
        if segments:
            first_seg = segments[0]
            # If relative, build full URL
            if not first_seg.startswith('http'):
                base = m3u8_url.rsplit('/', 1)[0]
                seg_url = f"{base}/{first_seg}"
            else:
                seg_url = first_seg
            
            sr = requests.head(seg_url, timeout=10)
            size = sr.headers.get('content-length', '?')
            print(f"  segment[0] ({first_seg}): {sr.status_code} (size: {size})")
            print(f"    URL: {seg_url}")
            
            # Check total segments
            print(f"  Total segments in m3u8: {len(segments)}")
        else:
            print(f"  No segments found in m3u8!")
    except Exception as e:
        print(f"  ERROR: {e}")
