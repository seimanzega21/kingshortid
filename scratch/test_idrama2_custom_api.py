import requests
import urllib3

urllib3.disable_warnings()

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://vidrama.asia/',
}

movie_id = '161004641891'

endpoints = [
    # idrama
    f"https://vidrama.asia/api/idrama/detail/{movie_id}?lang=id_ID",
    f"https://vidrama.asia/api/idrama/movie/{movie_id}?lang=id_ID",
    f"https://vidrama.asia/api/idrama/episode/{movie_id}/1?lang=id_ID",
    f"https://vidrama.asia/api/idrama/watch?bookId={movie_id}&episode=1&lang=id",
    
    # idrama2
    f"https://vidrama.asia/api/idrama2/detail/{movie_id}?lang=id_ID",
    f"https://vidrama.asia/api/idrama2/movie/{movie_id}?lang=id_ID",
    f"https://vidrama.asia/api/idrama2/episode/{movie_id}/1?lang=id_ID",
    f"https://vidrama.asia/api/idrama2/watch?bookId={movie_id}&episode=1&lang=id",
    
    # Search / List under idrama2
    f"https://vidrama.asia/api/idrama2/search?keyword=serigala",
    f"https://vidrama.asia/api/idrama2/feed/1?lang=id_ID",
]

for url in endpoints:
    print(f"\nProbing: {url}...")
    try:
        r = requests.get(url, headers=headers, verify=False, timeout=10)
        print(f"Status: {r.status_code}")
        if r.ok:
            print(f"Response (text first 300): {r.text[:300]}")
        else:
            print(f"Response (text first 150): {r.text[:150]}")
    except Exception as e:
        print("Error:", e)
