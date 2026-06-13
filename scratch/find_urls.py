import requests
import re
import urllib3

urllib3.disable_warnings()

url = 'https://vidrama.asia/movie/aku-lahirkan-anak-serigala-presiden--161004641891?provider=idrama2&lang=id'
r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, verify=False)

print("HTML length:", len(r.text))

# Search for any stream format URLs
m3u8_urls = re.findall(r'https?://[^\s"\']+\.m3u8[^\s"\']*', r.text)
print("Found m3u8 URLs in HTML:", len(m3u8_urls), m3u8_urls[:5])

mp4_urls = re.findall(r'https?://[^\s"\']+\.mp4[^\s"\']*', r.text)
print("Found mp4 URLs in HTML:", len(mp4_urls), mp4_urls[:5])

# Let's search for any network requests in next data or script tags
# Search for API URLs
apis = re.findall(r'/api/[^\s"\']+', r.text)
print("Found API paths in HTML:", len(apis), list(set(apis))[:10])
