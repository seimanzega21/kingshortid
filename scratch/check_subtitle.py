import requests, warnings
warnings.filterwarnings('ignore')

API = 'https://api.shortlovers.id/api'
DRAMA_ID = 'jayoo8vm9088eggxp69bcd5r'  # Dikuasai Ayah Mantanku - has subtitles

r = requests.get(f'{API}/dramas/{DRAMA_ID}', verify=False, timeout=15)
d = r.json()
eps = d.get('episodes', [])
ep1 = sorted(eps, key=lambda x: x.get('episodeNumber', 0))[0]
ep1_id = ep1['id']
print('Drama:', d.get('title'))
print('Ep1 video URL:', ep1.get('videoUrl', '')[:100])

# Get subtitle
r2 = requests.get(f'{API}/episodes/{ep1_id}/subtitles', verify=False, timeout=10)
subs = r2.json().get('subtitles', [])
print(f'Subtitles: {len(subs)}')
for s in subs:
    lang = s.get('language')
    url = s.get('url', '')[:100]
    print(f'  lang={lang} | url={url}')

# Now check if the VTT URL actually works
if subs:
    vtt_url = subs[0].get('url')
    r3 = requests.get(vtt_url, verify=False, timeout=10)
    print(f'\nVTT URL status: {r3.status_code}')
    if r3.ok:
        print('VTT content (first 200 chars):', r3.text[:200])
    else:
        print('VTT not accessible!')
