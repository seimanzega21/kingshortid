import requests
import re
import urllib3
urllib3.disable_warnings()

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://vidrama.asia/'
}

def main():
    url = 'https://vidrama.asia/search?q=diputus'
    print(f"Fetching search page: {url}")
    r = requests.get(url, headers=headers, verify=False)
    
    # Extract scripts
    scripts = re.findall(r'src="(/_next/static/[^"]+\.js)"', r.text)
    print(f"Found {len(scripts)} scripts.")
    
    api_patterns = set()
    for s in scripts:
        js_url = f"https://vidrama.asia{s}"
        try:
            res = requests.get(js_url, headers=headers, verify=False, timeout=10)
            if res.ok:
                matches = re.findall(r'/api/[a-zA-Z0-9_\-/]+', res.text)
                for m in matches:
                    api_patterns.add(m)
        except Exception as e:
            print(f"Failed to fetch {js_url}: {e}")
            
    print("\nAPI Endpoints found in JS chunks:")
    for ap in sorted(api_patterns):
        print(f" - {ap}")

if __name__ == "__main__":
    main()
