import requests
from bs4 import BeautifulSoup

url = 'https://vidrama.asia/provider/netshortv2'
r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
soup = BeautifulSoup(r.text, 'html.parser')
links = soup.find_all('a')
for a in links:
    text = a.text.strip()
    href = a.get('href')
    if text and len(text) > 3:
        print(f'{text} -> {href}')
