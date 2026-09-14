import requests, urllib3, re, json
urllib3.disable_warnings()

h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'}
r = requests.get('https://vidrama.asia/movie/koki-hebat-kuasai-sekte-4--7680825016186850357?provider=melolov3&lang=id', headers=h, verify=False)
lines = re.findall(r'self\.__next_f\.push\(\[1,\s*"(.*?)"\]\)', r.text)
full_data = "".join(lines).replace('\\"', '"').replace('\\\\', '\\')
urls = re.findall(r'https?://[^"]*inicdn\.net[^"]*', full_data)
print("Found stream urls:", len(urls))
if urls:
    print("Sample URL:", urls[0])
