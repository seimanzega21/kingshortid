import requests, json

DRAMA_ID = "2010948201357684738" # Legenda Naga Kembali
url = f"https://vidrama.asia/api/microdrama?action=detail&id={DRAMA_ID}&lang=id"

print(f"Requesting: {url}")
r = requests.get(url, timeout=20)
if r.ok:
    data = r.json()
    print("Top-level keys in drama detail:")
    for k, v in data.items():
        if k != "episodes":
            print(f"  {k}: {str(v)[:200]}")
        else:
            print(f"  episodes: [List of {len(v)} episodes]")
else:
    print(f"Error: {r.status_code}")
