import requests, re

url = 'https://vidrama.asia/movie/gejolak-keluarga-konglomerat--2034897075744800770?provider=netshort'
text = requests.get(url).text

print("Desc:", re.findall(r'"description"\s*:\s*"([^"]+)"', text)[:5])
print("Genre:", list(set(re.findall(r'"genre"\s*:\s*"([^"]+)"', text))))
