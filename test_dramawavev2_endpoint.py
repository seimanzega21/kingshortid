import requests
import json

def test_api():
    upstream_id = 'rz3UJ5zFl4'
    detail_url = f'https://vidrama.asia/api/dramawavev2?action=detail&id={upstream_id}'
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }
    
    r = requests.get(detail_url, headers=headers, verify=False)
    if r.ok:
        data = r.json().get('data', {})
        print("chapterCount:", data.get('chapterCount'))
        lst = data.get('list', [])
        print("list len:", len(lst))
        if lst:
            print("list[0]:", lst[0])
            print("list[-1]:", lst[-1])
    else:
        print("Failed:", r.status_code)

if __name__ == '__main__':
    import urllib3
    urllib3.disable_warnings()
    test_api()
