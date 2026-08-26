import cloudscraper

scraper = cloudscraper.create_scraper()
url = "https://vidrama.asia/provider/stardusttv"
r = scraper.get(url, timeout=15)
with open('stardust.html', 'w', encoding='utf-8') as f:
    f.write(r.text)
print("Saved stardust.html")
