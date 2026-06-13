import requests
import re
import urllib3

urllib3.disable_warnings()

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://vidrama.asia/',
}

variations = [
    'https://vidrama.asia/watch/aku-lahirkan-anak-serigala-presiden--161004641891/1?provider=idrama2&lang=id',
    'https://vidrama.asia/watch/aku-lahirkan-anak-serigala-presiden--161004641891/1?provider=idrama2&lang=id_ID',
    'https://vidrama.asia/watch/aku-lahirkan-anak-serigala-presiden--161004641891/1?provider=idrama2&lang=in',
    'https://vidrama.asia/watch/aku-lahirkan-anak-serigala-presiden--161004641891/1?provider=idrama2',
]

for url in variations:
    print(f"\nFetching: {url}...")
    try:
        r = requests.get(url, headers=headers, verify=False, timeout=10)
        print(f"Status code: {r.status_code}")
        
        # Check if "This page could not be found" is in the text
        if "could not be found" in r.text or "404" in r.text and "page-module" in r.text:
            print("  --> Result: 404 Not Found (Components)")
        elif "self.__next_f.push" in r.text:
            # Extract push payloads
            payload_parts = []
            for match in re.finditer(r'self\.__next_f\.push\(\[\d+,\s*"(.*?)"\]\)', r.text):
                part = match.group(1).replace('\\"', '"').replace('\\\\', '\\').replace('\\/', '/')
                payload_parts.append(part)
            full_payload = "".join(payload_parts)
            
            if "not be found" in full_payload or '"404"' in full_payload:
                print("  --> Result: 404 in server component payload")
            else:
                print("  --> Result: SUCCESS! Payload doesn't look like 404.")
                # print a snippet
                print(f"  Snippet: {full_payload[:400]}...")
                # Save this successful payload
                with open('scratch/success_watch_payload.txt', 'w', encoding='utf-8') as f:
                    f.write(full_payload)
        else:
            print("  --> Result: Unknown / No next_f.push")
    except Exception as e:
        print("Error fetching:", e)
