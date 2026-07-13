import requests
import json
import re

url = "https://vidrama.asia/movie/99-mutiara-kasih--2804?provider=flareflow&lang=id"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}
try:
    r = requests.get(url, headers=headers, timeout=15, verify=False)
    html = r.text
    
    # Try to extract RSC payload which is usually in <script>self.__next_f.push(
    matches = re.findall(r'self\.__next_f\.push\(\[1,"(.*?)"\]\)', html)
    found_data = False
    for m in matches:
        # Unescape the string
        try:
            # We just want to find where the title "99 Mutiara" is
            if "99 Mutiara" in m or "episodeNo" in m:
                print("Found data in next_f chunks!")
                print(m[:1000])
                found_data = True
        except:
            pass
            
    if not found_data:
        print("Could not find data in next_f. Saving HTML to test.html")
        with open("test.html", "w", encoding="utf-8") as f:
            f.write(html)
            
except Exception as e:
    print(f"Error: {e}")
