import requests, json, sys
sys.stdout.reconfigure(encoding="utf-8")

url = "https://vidrama.asia/movie/99-mutiara-kasih--2804?provider=flareflow&lang=id"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "RSC": "1"
}

resp = requests.get(url, headers=headers, timeout=15, verify=False)
if resp.ok:
    lines = resp.text.split("\n")
    for line in lines:
        if "episodes" in line and "99 Mutiara" in line:
            print("Found it!")
            # Extract the json part after the chunk id
            try:
                idx = line.find(":")
                chunk = json.loads(line[idx+1:])
                # The chunk is often an array like ["$","$L15",null,{"episodes":[...
                print(json.dumps(chunk, indent=2)[:2000])
            except Exception as e:
                print("Error parsing chunk", e)
else:
    print(resp.status_code)
