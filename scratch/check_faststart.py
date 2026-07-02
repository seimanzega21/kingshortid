import requests

url = "https://stream.shortlovers.id/melolo/anak-fana-penakluk-langit/ep001.mp4"
headers = {"Range": "bytes=0-100000"}
r = requests.get(url, headers=headers, timeout=10)
if r.ok:
    data = r.content
    moov_idx = data.find(b'moov')
    mdat_idx = data.find(b'mdat')
    print(f"moov index: {moov_idx}")
    print(f"mdat index: {mdat_idx}")
    if moov_idx != -1 and (mdat_idx == -1 or moov_idx < mdat_idx):
        print("The file has faststart enabled (moov is before mdat)!")
    else:
        print("The file DOES NOT have faststart enabled (mdat is before moov or moov missing in first 100KB).")
else:
    print(f"Failed to fetch: {r.status_code}")
