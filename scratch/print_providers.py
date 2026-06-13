import requests
import urllib3

urllib3.disable_warnings()

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://vidrama.asia/',
}

url = "https://vidrama.asia/api/providers/settings"
try:
    r = requests.get(url, headers=headers, verify=False, timeout=10)
    if r.ok:
        data = r.json()
        providers = data.get('providers', [])
        print(f"Total providers returned: {len(providers)}")
        for idx, p in enumerate(providers):
            print(f"{idx+1}. Label: {p.get('label')} | Key: {p.get('providerKey')} | Href: {p.get('href')}")
    else:
        print("Failed, Status:", r.status_code)
except Exception as e:
    print("Error:", e)
