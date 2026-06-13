import requests
import re
import urllib3

urllib3.disable_warnings()

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://vidrama.asia/',
}

urls = [
    'https://vidrama.asia/watch/idrama2/160001641891/1?lang=id_ID',
    'https://vidrama.asia/watch/idrama2/161004641891/1?lang=id_ID',
    'https://vidrama.asia/watch/idrama2/aku-lahirkan-anak-serigala-presiden/1?lang=id_ID',
    'https://vidrama.asia/watch/idrama2/aku-lahirkan-anak-serigala-presiden--161004641891/1?lang=id_ID',
]

for url in urls:
    print(f"\nFetching: {url}...")
    try:
        r = requests.get(url, headers=headers, verify=False, timeout=10)
        print(f"Status code: {r.status_code}")
        
        # Check if Next.js push payload returned
        if "self.__next_f.push" in r.text:
            payload_parts = []
            for match in re.finditer(r'self\.__next_f\.push\(\[\d+,\s*"(.*?)"\]\)', r.text):
                part = match.group(1).replace('\\"', '"').replace('\\\\', '\\').replace('\\/', '/')
                payload_parts.append(part)
            full_payload = "".join(payload_parts)
            
            if "not be found" in full_payload or '"404"' in full_payload:
                print("  --> Result: 404 in server component payload")
            else:
                print("  --> Result: SUCCESS!")
                print(f"  Snippet: {full_payload[:400]}...")
                with open('scratch/direct_watch_success.txt', 'w', encoding='utf-8') as f:
                    f.write(full_payload)
        else:
            print("  --> Result: Not NextJS push page")
    except Exception as e:
        print("Error fetching:", e)
