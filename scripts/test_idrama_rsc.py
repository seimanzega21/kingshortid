import requests
import re

headers = {
    'User-Agent': 'Mozilla/5.0',
    'RSC': '1',
    'Next-Url': '/provider/idrama'
}

r = requests.get('https://vidrama.asia/provider/idrama', headers=headers)
print('Status:', r.status_code)
text = r.text

titles = re.findall(r'"title"\s*:\s*"([^"]+)"', text)
print('Titles:', titles[:10])

slugs = re.findall(r'"slug"\s*:\s*"([^"]+)"', text)
print('Slugs:', slugs[:10])

# check if we have episodes
episodes = re.findall(r'"episodeNumber"\s*:\s*(\d+)', text)
print('Episodes on provider page?:', len(episodes))
