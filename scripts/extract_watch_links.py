import requests
import re
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

html = requests.get('https://vidrama.asia/movie/99-mutiara-kasih--2804?provider=flareflow&lang=id', headers={'User-Agent': 'Mozilla/5.0'}, verify=False).text
matches = re.findall(r'/watch/[^\"]+', html)
matches_single = re.findall(r'/watch/[^\']+', html)
all_matches = set(matches + matches_single)
for m in all_matches:
    if '2804' in m:
        print(m)
