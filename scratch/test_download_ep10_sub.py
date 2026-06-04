import requests
import urllib3
urllib3.disable_warnings()

url = 'https://vidrama.asia/api/netshortv2/episode/2056946805631225858/10?lang=id_ID'
r = requests.get(url, verify=False)
ep_data = r.json()
sub_url = ep_data.get('data', {}).get('subtitles', [])[0].get('url')

print("Subtitle URL:", sub_url)

# Test 1: Simple requests (No headers)
r1 = requests.get(sub_url, verify=False)
print("Test 1 Status:", r1.status_code)
print("Test 1 Content:", r1.text[:300])

# Test 2: Standard Browser User-Agent only
hdrs2 = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'}
r2 = requests.get(sub_url, headers=hdrs2, verify=False)
print("Test 2 Status:", r2.status_code)
print("Test 2 Content:", r2.text[:300])

# Test 3: Standard Browser User-Agent and Referer empty or specific
hdrs3 = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://vidrama.asia/'
}
r3 = requests.get(sub_url, headers=hdrs3, verify=False)
print("Test 3 Status:", r3.status_code)
print("Test 3 Content:", r3.text[:300])
