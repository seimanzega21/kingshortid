import requests

API_BASE = 'https://api.shortlovers.id/api'

def search():
    print("Mencari drama 'murka' via API...")
    try:
        r = requests.get(f"{API_BASE}/dramas/search?q=murka")
        data = r.json()
        dramas = data.get('dramas', [])
        print(f"Ditemukan {len(dramas)} hasil:")
        for d in dramas:
            print(f"ID: {d.get('id')}")
            print(f"Judul: {d.get('title')}")
            print(f"Episodes: {d.get('totalEpisodes')}")
            print("-" * 20)
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    search()
