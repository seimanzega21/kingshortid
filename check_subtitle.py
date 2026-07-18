import requests
import json

upstream_id = 'rz3UJ5zFl4'
ep_no = 1
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://vidrama.asia/',
}

r_stream = requests.get(f'https://vidrama.asia/api/dramawavev2?action=stream&id={upstream_id}&episode={ep_no}', headers=HEADERS, timeout=20, verify=False)
print(json.dumps(r_stream.json(), indent=2))
