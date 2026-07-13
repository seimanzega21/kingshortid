import requests
import re
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

html = requests.get('https://vidrama.asia/movie/99-mutiara-kasih--2804?provider=flareflow&lang=id', verify=False).text
links = set(re.findall(r'/watch/[^\"]+', html) + re.findall(r'/watch/[^\']+', html))
print([L for L in links if '/1?' in L or '/1\"' in L or '/1\'' in L])
