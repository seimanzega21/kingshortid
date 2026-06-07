# -*- coding: utf-8 -*-
import requests
import urllib3
import sys
import json
from bs4 import BeautifulSoup

urllib3.disable_warnings()
sys.stdout.reconfigure(encoding='utf-8')

url = "https://vidrama.asia/provider/dramawave"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://vidrama.asia/',
}

print(f"Fetching: {url}")
r = requests.get(url, headers=headers, verify=False, timeout=15)
print("Status Code:", r.status_code)
print("Content Length:", len(r.text))

soup = BeautifulSoup(r.text, "html.parser")
next_data_script = soup.find("script", id="__NEXT_DATA__")

if next_data_script:
    print("Found __NEXT_DATA__ script!")
    try:
        data = json.loads(next_data_script.string)
        # Let's save the JSON to help inspect it
        with open("d:\\kingshortid\\scratch\\dramawave_next_data.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print("Saved __NEXT_DATA__ to scratch/dramawave_next_data.json")
        
        # Let's inspect the page props to see if it lists dramas
        props = data.get("props", {}).get("pageProps", {})
        print("pageProps keys:", props.keys())
        
        # Look for any series, movies, or providers list
        for k, v in props.items():
            if isinstance(v, list):
                print(f"  List key '{k}': length={len(v)}")
                if v:
                    print(f"    First item sample: {str(v[0])[:150]}")
            elif isinstance(v, dict):
                print(f"  Dict key '{k}': keys={list(v.keys())}")
                if 'movies' in v or 'series' in v or 'dramas' in v:
                    print(f"    Found movies/series key inside '{k}'")
    except Exception as e:
        print(f"Error parsing __NEXT_DATA__: {e}")
else:
    print("No __NEXT_DATA__ script found.")
    # Print first 1000 characters of HTML to inspect
    print(r.text[:1000])
