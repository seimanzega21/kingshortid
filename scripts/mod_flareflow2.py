import sys
with open('d:/kingshortid/scripts/scrape_flareflow_provider.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Replace the detail fetching logic
old_fetch = """          if not res_json.get('success'):
              print(f"[ERROR] API returned success=false: {res_json}")
              return False
          detail = res_json.get('data', {})"""
new_fetch = """          if 'id' not in res_json:
              print(f"[ERROR] API returned invalid response: {res_json}")
              return False
          detail = res_json"""
code = code.replace(old_fetch, new_fetch)

# Fix cover logic
code = code.replace("cover_url = detail.get('coverUrl') or detail.get('cover')", "cover_url = detail.get('horizontalCoverId') or detail.get('picUrl')")

# Fix episodes loop logic
old_eps = """      episodes = detail.get('episodes', [])
      if not episodes:
          print("[WARN] No episodes found.")
          return False
          
      total_eps = len(episodes)
      print(f"Total episodes: {total_eps}")
      
      # 2. Register to DB
      api_get_or_create_drama(detail, slug, cover_url)
      
      print("Starting download and transcode process...")
      
      for i, ep in enumerate(episodes):
          ep_no = ep.get('index') or (i + 1)
          ep_id = ep.get('id')"""

new_eps = """      total_eps = detail.get('totalEpisode', 0)
      if not total_eps:
          print("[WARN] No episodes found.")
          return False
          
      print(f"Total episodes: {total_eps}")
      
      # 2. Register to DB
      api_get_or_create_drama(detail, slug, cover_url)
      
      print("Starting download and transcode process...")
      
      for ep_no in range(1, total_eps + 1):
          ep_id = f"{movie_id}_{ep_no}" """
code = code.replace(old_eps, new_eps)

with open('d:/kingshortid/scripts/scrape_flareflow_provider.py', 'w', encoding='utf-8') as f:
    f.write(code)
