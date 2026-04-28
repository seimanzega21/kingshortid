import requests
import json

def fetch_netshort():
    url = "https://vidrama.asia/api/microdrama?action=list&lang=id"
    # Actually, is the netshort API mapped to microdrama or another endpoint?
    # Vidrama's microdrama endpoint has all of them.
    r = requests.get(url)
    dramas = r.json().get('dramas', [])
    for d in dramas:
        if 'Pedang' in d.get('title', ''):
            print(f"FOUND: {d['title']} -> ID: {d['id']}")

fetch_netshort()
