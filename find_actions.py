import requests, re, urllib3
urllib3.disable_warnings()

headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

r = requests.get('https://vidrama.asia/watch/ratu-hamil-sang-bos-mafia--9515/1?provider=flickreelsv2&lang=id', headers=headers, verify=False)
chunks = list(set(re.findall(r'/_next/static/chunks/[^\"]+\.js', r.text)))

print(f"Found {len(chunks)} chunks.")
for c in chunks:
    try:
        cr = requests.get('https://vidrama.asia' + c, headers=headers, verify=False)
        actions = re.findall(r'[a-f0-9]{40}', cr.text)
        if actions:
            print(c, set(actions))
    except:
        pass
