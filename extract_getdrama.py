import requests
import re
c = requests.get('https://vidrama.asia/_next/static/chunks/43f5bb3acc7e88b0.js', headers={'User-Agent': 'Mozilla/5.0'}).text
idx = c.find('getDrama')
if idx != -1:
    print(c[max(0, idx-100):idx+200])
