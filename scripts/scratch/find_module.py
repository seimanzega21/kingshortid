import requests
import re

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://vidrama.asia/'
}

with open('watch_shortmax.html', 'r', encoding='utf-8') as f:
    html = f.read()

chunks = re.findall(r'src="(/_next/static/chunks/[^"]+)"', html)
for c in set(chunks):
    res = requests.get(f'https://vidrama.asia{c}', headers=headers, verify=False)
    if '4621427' in res.text:
        print(f"Module 4621427 found in {c}")
        # Search for 4621427 definition
        m = re.search(r'4621427:\s*(function|\([^)]*\)\s*=>|\{)', res.text)
        if m:
            start = m.start()
            print("Found definition:", res.text[start:start+500])
        else:
            # find all occurrences of 4621427
            for occ in re.finditer(r'4621427', res.text):
                print("Occ:", res.text[max(0, occ.start()-50):min(len(res.text), occ.end()+100)])
