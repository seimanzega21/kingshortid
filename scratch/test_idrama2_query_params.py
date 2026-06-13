import requests
import urllib3
import json

urllib3.disable_warnings()

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://vidrama.asia/',
}

correct_id = '160001641891'

endpoints = [
    f"https://vidrama.asia/api/idrama2/detail?id={correct_id}&lang=id_ID",
    f"https://vidrama.asia/api/idrama2/detail?bookId={correct_id}&lang=id_ID",
    f"https://vidrama.asia/api/idrama2/movie?id={correct_id}&lang=id_ID",
    
    # Episode level stream patterns with query parameters
    f"https://vidrama.asia/api/idrama2/episode?id={correct_id}&episode=1&lang=id_ID",
    f"https://vidrama.asia/api/idrama2/episode?bookId={correct_id}&episode=1&lang=id_ID",
    f"https://vidrama.asia/api/idrama2/episode?id={correct_id}&episodeNum=1&lang=id_ID",
    f"https://vidrama.asia/api/idrama2/episode?id={correct_id}&ep=1&lang=id_ID",
    f"https://vidrama.asia/api/idrama2/episode?dramaId={correct_id}&episodeNum=1&lang=id_ID",
    
    # Watch pattern with query parameters
    f"https://vidrama.asia/api/idrama2/watch?bookId={correct_id}&episode=1&lang=id_ID",
    f"https://vidrama.asia/api/idrama2/watch?id={correct_id}&episode=1&lang=id_ID",
]

for url in endpoints:
    print(f"\nProbing: {url}...")
    try:
        r = requests.get(url, headers=headers, verify=False, timeout=10)
        print(f"Status: {r.status_code}")
        if r.ok:
            data = r.json()
            if 'error' in data or 'err' in data:
                print(f"Error: {data.get('error') or data.get('msg')}")
            else:
                print(f"Success! Keys: {list(data.keys())}")
                # print snippet of data
                print(str(data)[:250])
        else:
            print("Response:", r.text[:150])
    except Exception as e:
        print("Error:", e)
