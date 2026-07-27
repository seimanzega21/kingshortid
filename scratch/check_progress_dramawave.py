import requests
import urllib.parse

API_BASE = 'https://api.kingshort.id'
# or if it's protected, we might need the admin key, but /dramas/search is usually public.

DRAMAS = [
    {'slug': 'gebetan-rahasia-suamiku', 'title': 'Gebetan Rahasia Suamiku'},
    {'slug': 'raja-keberuntungan-berkekuatan-super', 'title': 'Raja Keberuntungan Berkekuatan Super'},
    {'slug': 'kembalinya-legenda-istana', 'title': 'Kembalinya Legenda Istana'},
    {'slug': 'bos-mafia-hasrat-terlarangku', 'title': 'Bos Mafia Hasrat Terlarangku'}
]

def check_progress():
    print("=== LAPORAN PROGRESS SCRAPING DRAMAWAVEV2 ===")
    for d in DRAMAS:
        # Search drama by title to get ID
        url = f"{API_BASE}/dramas/search?q={urllib.parse.quote(d['title'])}"
        try:
            r = requests.get(url, timeout=10)
            if r.ok:
                data = r.json()
                if not data:
                    print(f"- {d['title']}: Belum terdaftar (Menunggu giliran)")
                    continue
                
                # Check the first match
                drama_id = data[0]['id']
                
                # Get episodes count
                ep_url = f"{API_BASE}/dramas/{drama_id}/episodes?includeInactive=true"
                ep_r = requests.get(ep_url, timeout=10)
                if ep_r.ok:
                    eps = ep_r.json()
                    print(f"- {d['title']}: Sudah masuk {len(eps)} episode")
                else:
                    print(f"- {d['title']}: Terdaftar tapi gagal fetch episode count")
            else:
                # maybe API endpoint is wrong, let's try direct slug if search fails
                print(f"- {d['title']}: API error {r.status_code}")
        except Exception as e:
            print(f"- {d['title']}: Request failed - {e}")

if __name__ == '__main__':
    check_progress()
