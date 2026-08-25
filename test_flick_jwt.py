import requests, urllib3, re
urllib3.disable_warnings()

with open('d:/kingshortid/ingest_flickreelsv2_local.py', 'r', encoding='utf-8') as f:
    text = f.read()

cookie = re.search(r'\'cookie\':\s*\'([^\']+)\'', text).group(1)
headers = {
    'cookie': cookie, 
    'referer': 'https://vidrama.asia/',
    'authorization': 'Bearer eyJhbGciOiJFUzI1NiIsImtpZCI6ImY0NTAxYzU1LTY5ZmMtNDczNy05NzFkLTU1OTVjZmRmZDAwNSIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJodHRwczovL2drY25ibmxmcWRsb3RuamFpenh4LnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiI2ZjNlNWMxNS1hMjFjLTRkMTAtYjg2Yy1lODgxNzBlN2I3MmQiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzg3NjgyMzM5LCJpYXQiOjE3ODc2Nzg3MzksImVtYWlsIjoic2VpbWFuemVnYTIxQGdtYWlsLmNvbSIsInBob25lIjoiIiwiYXBwX21ldGFkYXRhIjp7InByb3ZpZGVyIjoiZ29vZ2xlIiwicHJvdmlkZXJzIjpbImdvb2dsZSIsImVtYWlsIl19LCJ1c2VyX21ldGFkYXRhIjp7ImF2YXRhcl91cmwiOiJodHRwczovL2xoMy5nb29nbGV1c2VyY29udGVudC5jb20vYS9BQ2c4b2NLTHVLNzltN2xuOWdBcXJRVEhNVFFDZTFRR3B3Vy10dHh2RW1lNWUzSTF2OHBubGpvPXM5Ni1jIiwiZW1haWwiOiJzZWltYW56ZWdhMjFAZ21haWwuY29tIiwiZW1haWxfdmVyaWZpZWQiOnRydWUsImZ1bGxfbmFtZSI6InNlaW1hbiB6ZWdhIiwiaXNzIjoiaHR0cHM6Ly9hY2NvdW50cy5nb29nbGUuY29tIiwibmFtZSI6InNlaW1hbiB6ZWdhIiwicGhvbmVfdmVyaWZpZWQiOmZhbHNlLCJwaWN0dXJlIj'
}
url = 'https://vidrama.asia/api/proxy-flickreelsv2?action=chapters&playletId=9515&lang=id'
r = requests.get(url, headers=headers, verify=False)
data = r.json().get('data', {}).get('list', [])

for ep in data:
    if ep['chapter_num'] >= 11 and ep['chapter_num'] <= 13:
        print(f"EP {ep['chapter_num']}: hls_url={ep.get('hls_url')} is_locked={ep.get('is_locked')}")
