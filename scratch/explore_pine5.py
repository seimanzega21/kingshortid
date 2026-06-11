import requests
import json

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://vidrama.asia/',
    'Cookie': '_fbp=fb.1.1770653154777.876935444165455244; global_ui_lang=id; cf_clearance=gi8rBDL4U_sV5dFUP.Dckjr.DONUzFar9fJlBMJx5_c-1778228148-1.2.1.1-rcSC4qbKF5H0KxB5Zt6Ic88iCIyXH7DESdcJA5w9WLWZvk58Y70clfcHFfqOyxmSRb1I97eRy.96PRr0zF1vV_PWs7vWkLZg2IsJNYLl5ZJvxdv7AnK4pZgxEBspgbrAod7jxce171vMiENcKPDXk_1eVFpBk_P5H8TA07xIBdq5HsL3uPTZKn8BCJv.HufjCR4mRr3DVOGDRagaNcc1CD_VmnRYY6tkanYH9QuDUyPeqreywRNxjb_5tsJVseZjz24po7Gw9o9ZVi3mSl9Ypm88Po1s4zr5n3DfE5R4BCKekPgqBAog2SDMQmDCWQJjMpzKKsJ_iXUHRaincYv9WQ'
}

BASE = 'https://vidrama.asia/api/pine'
collection_id = '7633639412135924737'

# Get episodes to find videoId
r = requests.get(f'{BASE}?action=episodes&collection_id={collection_id}', headers=headers, verify=False, timeout=10)
eps = r.json().get('episodes', [])
print(f"Total episodes: {len(eps)}")
print("First 3 episodes:")
for ep in eps[:3]:
    print(f"  {ep}")

# Now try play action with episode number and videoId
print("\n=== PLAY ENDPOINT ===")
ep1 = eps[0]
video_id = ep1['videoId']
ep_num = ep1['num']

play_tests = [
    f'action=play&collection_id={collection_id}&episode={ep_num}',
    f'action=play&collection_id={collection_id}&episode={ep_num}&videoId={video_id}',
    f'action=play&collection_id={collection_id}&ep={ep_num}',
    f'action=play&collection_id={collection_id}&videoId={video_id}',
    f'action=play&collection_id={collection_id}&video_id={video_id}',
]

for params in play_tests:
    r = requests.get(f'{BASE}?{params}', headers=headers, verify=False, timeout=10)
    print(f'[{r.status_code}] {params.replace(collection_id, "CID").replace(video_id, "VID")}')
    print(f'  -> {r.text[:400]}')
    print()
