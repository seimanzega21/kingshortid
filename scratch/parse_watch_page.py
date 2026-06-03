import re
import json

with open('scratch/watch_page_snippet.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Try to find Next.js __NEXT_DATA__
match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html, re.DOTALL)
if match:
    print("Found __NEXT_DATA__!")
    data = json.loads(match.group(1))
    # Let's save it to a json file to inspect it
    with open('scratch/next_data.json', 'w', encoding='utf-8') as jf:
        json.dump(data, jf, indent=2)
    print("Saved __NEXT_DATA__ to scratch/next_data.json")
    
    # Try to find info about the drama or episodes
    props = data.get('props', {}).get('pageProps', {})
    print("Keys in pageProps:", list(props.keys()))
    
    movie_info = props.get('movieInfo', {})
    print("Movie Info keys:", list(movie_info.keys()))
    print("Movie Info title:", movie_info.get('title'))
    print("Movie Info ID:", movie_info.get('id'))
    
    episode_list = props.get('episodeList', [])
    print(f"Number of episodes: {len(episode_list)}")
    
    # Let's inspect the first episode structure
    if episode_list:
        print("First episode structure:", json.dumps(episode_list[0], indent=2))
else:
    print("Could not find __NEXT_DATA__ in HTML.")
