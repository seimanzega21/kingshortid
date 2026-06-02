import requests, json

DRAMA_ID = "1924655580142809089" # Dia yang Paling Mencintaiku

urls = [
    f"https://vidrama.asia/api/microdrama?action=detail&id={DRAMA_ID}&lang=id",
    f"https://vidrama.asia/api/microdrama?action=detail&id={DRAMA_ID}"
]

for url in urls:
    print(f"Requesting: {url}")
    r = requests.get(url, timeout=20)
    print(f"Status Code: {r.status_code}")
    if r.ok:
        try:
            data = r.json()
            print("Keys:", data.keys())
            if "drama" in data:
                print("Drama Title:", data["drama"].get("title"))
            eps = data.get("episodes", [])
            print(f"Episodes count: {len(eps)}")
            if eps:
                print("First ep sample:", eps[0])
        except Exception as e:
            print("Failed to parse JSON:", e)
            print("Snippet:", r.text[:200])
    else:
        print("Response text:", r.text[:200])
    print()
