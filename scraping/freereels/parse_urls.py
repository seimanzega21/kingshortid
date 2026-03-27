"""Parse freereels_urls.json and analyze episode structure"""
import sys, json, re
from collections import defaultdict
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open(r'C:\Users\Seiman\Downloads\freereels_urls.json', 'r') as f:
    urls = json.load(f)

print(f'Total URLs: {len(urls)}')

# Separate m3u8 and srt
m3u8_urls = [u for u in urls if '.m3u8' in u]
srt_urls = [u for u in urls if '.srt' in u]
print(f'm3u8: {len(m3u8_urls)}, srt: {len(srt_urls)}')

# Extract video UUIDs from m3u8 URLs
# Pattern: /vt/{video_uuid}/h264-{audio_uuid}.m3u8
h264 = [u for u in m3u8_urls if 'h264' in u]
h265 = [u for u in m3u8_urls if 'h265' in u]
print(f'h264: {len(h264)}, h265: {len(h265)}')

# Group URLs by episode position (sequential pairs: h264, h265, then srts)
# Each episode has: 2 m3u8 (h264,h265) + N srt files
episodes = []
ep = None
for u in urls:
    if 'h264' in u and '.m3u8' in u:
        if ep:
            episodes.append(ep)
        ep = {'h264': u, 'h265': '', 'srts': []}
    elif 'h265' in u and '.m3u8' in u and ep:
        ep['h265'] = u
    elif '.srt' in u and ep:
        ep['srts'].append(u)
if ep:
    episodes.append(ep)

print(f'\nTotal episodes: {len(episodes)}')
for i, ep in enumerate(episodes[:3]):
    print(f'\nEp {i+1}:')
    print(f'  h264: {ep["h264"][:80]}...')
    print(f'  h265: {ep["h265"][:80]}...')
    print(f'  srts: {len(ep["srts"])}')
    for s in ep['srts'][:2]:
        print(f'    {s[:80]}...')

# Save processed episodes
output = {
    'drama': 'Bos Kuliah Lagi (Sulih Suara)',
    'total_episodes': len(episodes),
    'episodes': []
}
for i, ep in enumerate(episodes):
    output['episodes'].append({
        'number': i + 1,
        'h264': ep['h264'],
        'h265': ep['h265'],
        'subtitles': ep['srts']
    })

with open(r'd:\kingshortid\scraping\freereels\parsed_episodes.json', 'w') as f:
    json.dump(output, f, indent=2)
print(f'\nSaved parsed_episodes.json')
