import requests
import urllib3
import json

urllib3.disable_warnings()

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://vidrama.asia/',
}

# The movie title is "Aku Lahirkan Anak Serigala Presiden"
# Let's search with "Anak Serigala" or "Serigala Presiden"
query = "Anak Serigala"
url = f"https://vidrama.asia/api/idrama2/search?q={requests.utils.quote(query)}"
print(f"Searching: {url}...")
try:
    r = requests.get(url, headers=headers, verify=False, timeout=10)
    print(f"Status: {r.status_code}")
    if r.ok:
        data = r.json()
        with open('scratch/serigala_search_results.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print("Results saved to scratch/serigala_search_results.json")
        
        # Print list of found dramas
        dramas = data.get('list', [])
        print(f"Found {len(dramas)} matching dramas.")
        for d in dramas:
            print(f"- ID: {d.get('id')} | Title: {d.get('short_play_name')} / {d.get('introduction')[:50]}...")
    else:
        print("Response:", r.text[:200])
except Exception as e:
    print("Error:", e)
