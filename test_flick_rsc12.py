import requests, urllib3, re, urllib.parse
urllib3.disable_warnings()

headers = {
  'rsc': '1',
  'sec-ch-ua-platform': '"Android"',
  'Referer': 'https://vidrama.asia/movie/ratu-hamil-sang-bos-mafia--9515?provider=flickreelsv2&lang=id',
  'sec-ch-ua': '"Not=A?Brand";v="99", "Google Chrome";v="151", "Chromium";v="151"',
  'sec-ch-ua-mobile': '?1',
  'next-router-state-tree': '%5B%22%22%2C%7B%22children%22%3A%5B%22watch%22%2C%7B%22children%22%3A%5B%5B%22slug%22%2C%22ratu-hamil-sang-bos-mafia--9515%22%2C%22d%22%5D%2C%7B%22children%22%3A%5B%5B%22episode%22%2C%2212%22%2C%22d%22%5D%2C%7B%22children%22%3A%5B%22__PAGE__%22%2C%7B%7D%2Cnull%2Cnull%2Cfalse%5D%7D%2Cnull%2Cnull%2Cfalse%5D%7D%2Cnull%2Cnull%2Cfalse%5D%7D%2Cnull%2C%22refetch%22%2Cfalse%5D%7D%2Cnull%2Cnull%2Ctrue%5D',
  'next-url': '/movie/ratu-hamil-sang-bos-mafia--9515',
  'User-Agent': 'Mozilla/5.0 (Linux; Android 15; Pixel 9) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Mobile Safari/537.36'
}

with open('d:/kingshortid/ingest_flickreelsv2_local.py', 'r', encoding='utf-8') as f:
    text = f.read()
cookie = re.search(r'\'cookie\':\s*\'([^\']+)\'', text).group(1)
headers['cookie'] = cookie

url = 'https://vidrama.asia/watch/ratu-hamil-sang-bos-mafia--9515/12?provider=flickreelsv2&lang=id&_rsc=17ze4'

r = requests.get(url, headers=headers, verify=False)
with open('d:/kingshortid/rsc12.txt', 'w', encoding='utf-8') as f:
    f.write(r.text)
print('Saved to rsc12.txt')
