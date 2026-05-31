import requests
import json

def test():
    url = "https://api.shortlovers.id/api/coins/watch-ad"
    print(f"Testing POST to {url} with no auth:")
    try:
        r = requests.post(url, json={"type": "cek_lainnya"}, timeout=10)
        print("Status Code:", r.status_code)
        print("Headers:")
        for k, v in r.headers.items():
            print(f"  {k}: {v}")
        print("Text:", r.text[:500])
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    test()
