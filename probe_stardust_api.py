import requests
import urllib3
urllib3.disable_warnings()

base_headers = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 15; Pixel 9) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Mobile Safari/537.36',
    'Accept': '*/*',
    'Referer': 'https://vidrama.asia/',
}

dramas = [
    ('20921', 'kakakku-bos-mafia'),
    ('20188', 'enam-pewaris-untuk-presdir-bo'),
    ('21861', 'gladiator-api-darah-dan-dendam'),
    ('21734', 'dari-rival-jadi-kekasih'),
    ('21045', 'runtuhnya-mahkota'),
    ('18698', 'berkat-sistem-putri-jadi-milikku'),
    ('18630', 'sang-penagih-utang-takdir'),
    ('20849', 'mantan-istriku-ternyata-ceo'),
    ('21614', 'putri-disakiti-ayah-ternyata-jenderal'),
    ('20742', 'pelindungku-cinta-terlarangku'),
    ('20100', 'cinta-takkan-berbalik'),
    ('20526', 'ratu-hati-sang-pembalap'),
    ('20119', 'aku-cerai-bos-mafia-gila'),
]

print(f"{'Slug':<45} {'ID':<7} {'Lang':<10} {'Subtitles'}")
print("-" * 80)

for mid, slug in dramas:
    try:
        r = requests.get(f"https://vidrama.asia/api/stardusttv?action=episode&id={mid}&episode=1&lang=id", headers=base_headers, timeout=15, verify=False)
        data = r.json().get('data', {})
        video_url = data.get('videoUrl', '')
        subs = data.get('subtitles', [])

        if '_ID_DUB' in video_url or '_id_dub' in video_url.lower():
            lang_type = "DUBBING-ID"
        elif '_DUB' in video_url:
            lang_type = "DUB (other)"
        else:
            lang_type = "NO-DUB"

        print(f"{slug:<45} {mid:<7} {lang_type:<10} {len(subs)} subtitle(s)")
    except Exception as e:
        print(f"{slug:<45} {mid:<7} ERROR: {e}")
