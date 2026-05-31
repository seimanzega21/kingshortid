import requests
import json

def test():
    urls = [
        "https://api.shortlovers.id/",
        "https://api.shortlovers.id/health",
        "https://api.shortlovers.id/api/health",
        "https://api.shortlovers.id/api/coins/history"
    ]
    for url in urls:
        print(f"\n--- Testing {url} ---")
        try:
            r = requests.get(url, timeout=5)
            print("Status Code:", r.status_code)
            print("Headers:")
            for k, v in r.headers.items():
                print(f"  {k}: {v}")
            try:
                print("JSON:", json.dumps(r.json(), indent=2))
            except:
                print("Text:", r.text[:200])
        except Exception as e:
            print("Error:", e)

if __name__ == "__main__":
    test()
