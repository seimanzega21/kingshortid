import requests
import urllib3
urllib3.disable_warnings()

base_headers = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 15; Pixel 9) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Mobile Safari/537.36',
    'Accept': '*/*',
    'Referer': 'https://vidrama.asia/',
}

dramas = [
    ('15405', 'dia-istri-sang-taipan'),
    ('14556', 'menyala-di-salju'),
    ('12053', 'dendam-judi-jari-terakhir'),
    ('13328', 'raja-judi-kembali-semua-kalah'),
    ('11560', 'naga-dalam-darahku-bangkit'),
]

print(f"{'Slug':<35} {'ID':<7} {'Lang':<12} {'Total Eps'}")
print("-" * 70)

for mid, slug in dramas:
    try:
        # Check language from episode 1
        r = requests.get(f"https://vidrama.asia/api/stardusttv?action=episode&id={mid}&episode=1&lang=id", headers=base_headers, timeout=15, verify=False)
        data = r.json().get('data', {})
        video_url = data.get('videoUrl', '')
        total_eps = data.get('totalEpisodes', '?')

        if '_ID_DUB' in video_url or '_id_dub' in video_url.lower():
            lang_type = "DUBBING-ID"
        elif '_DUB' in video_url:
            lang_type = "DUB (other)"
        else:
            lang_type = "NO-DUB"

        print(f"{slug:<35} {mid:<7} {lang_type:<12} {total_eps}")
    except Exception as e:
        print(f"{slug:<35} {mid:<7} ERROR: {e}")
