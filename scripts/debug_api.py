import requests
import json
import os

drama_id = 'ygjqw4e2ypmafvn5ap6249ba'
headers = {'User-Agent': 'Mozilla/5.0'}

# The frontend app usually calls an endpoint like /api/episodes/{dramaId} or similar.
# Let's see what /api/dramas/{dramaId} returns or /api/episodes?dramaId=
# Usually it's /api/episodes?dramaId={dramaId} based on typical REST.
# Or /api/episodes/{dramaId}
res = requests.get(f'https://api.shortlovers.id/api/episodes?dramaId={drama_id}', headers=headers)
if res.status_code != 200:
    res = requests.get(f'https://api.shortlovers.id/api/episodes/{drama_id}', headers=headers)
    
if res.status_code == 200:
    data = res.json()
    episodes = data if isinstance(data, list) else data.get('episodes', [])
    if isinstance(data, dict) and not 'episodes' in data:
        episodes = data.get('data', [])
        
    print(f"Found {len(episodes)} episodes.")
    if len(episodes) > 0:
        print("First episode video url:", episodes[0].get('videoUrl'))
        print("Last episode video url:", episodes[-1].get('videoUrl'))
else:
    print(f"Failed to fetch episodes. Status: {res.status_code}, Body: {res.text}")
