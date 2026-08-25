import sys
import re

with open('scripts/scrape_melolov3_provider.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace header
content = content.replace('melolov2 Provider', 'melolov3 Provider (Unencrypted)')

# Replace detail fetching logic
old_fetch = '''    # 1. Fetch details from API
    url = f"https://vidrama.asia/api/melolov2?action=detail&id={movie_id}"
    print(f"Fetching details from API: {url}")
    try:
        r = requests.get(url, headers=WEB_HDRS, timeout=15, verify=False)
        if not r.ok:
            print(f"[ERROR] Failed to fetch drama details. Status: {r.status_code}")
            return False
        res_json = r.json()
        if not res_json.get('success'):
            print(f"[ERROR] API returned success=false: {res_json}")
            return False
        detail = res_json.get('data', {})
    except Exception as e:
        print(f"[ERROR] Exception fetching drama details: {e}")
        return False
        
    title = detail.get('title') or detail.get('name') or 'Unknown Title'
    slug = slugify(title)
    prefix = f"melolov2/{slug}"'''

new_fetch = '''    # 1. Fetch details from API
    url = f"https://vidrama.asia/api/melolov3/multi-video?id={movie_id}&lang=id"
    print(f"Fetching details from API: {url}")
    try:
        r = requests.get(url, headers=WEB_HDRS, timeout=15, verify=False)
        if not r.ok:
            print(f"[ERROR] Failed to fetch drama details. Status: {r.status_code}")
            return False
        res_json = r.json()
        detail = res_json.get('series', {})
        eps = res_json.get('episodes', [])
    except Exception as e:
        print(f"[ERROR] Exception fetching drama details: {e}")
        return False
        
    title = detail.get('title') or 'Unknown Title'
    
    # We must remap detail to match api_get_or_create_drama format expected from melolov2
    detail_remapped = {
        'title': title,
        'description': detail.get('intro'),
        'cover': detail.get('cover'),
        'chapterCount': detail.get('episode_count'),
        'bookStatus': 1 # Assume completed if episodes are available
    }
    
    slug = slugify(title)
    prefix = f"melolov3/{slug}"'''
content = content.replace(old_fetch, new_fetch)

# Update api_get_or_create_drama call
content = content.replace('api_get_or_create_drama(detail, slug, r2_cover_url)', 'api_get_or_create_drama(detail_remapped, slug, r2_cover_url)')
content = content.replace("detail.get('cover') or detail.get('image')", "detail.get('cover')")

# Update episodes extraction
content = content.replace("eps = detail.get('episodes', [])", "# eps already extracted above")

# Update stream fetching inside the loop
old_stream = '''            # Fetch stream URL for this episode from stream API
            stream_url = f"https://vidrama.asia/api/melolov2?action=stream&id={movie_id}&episode={ep_no}"
            vurl = None
            subtitles = []
            
            try:
                stream_res = requests.get(stream_url, headers=WEB_HDRS, timeout=15, verify=False)
                if stream_res.ok:
                    stream_data = stream_res.json()
                    vurl = stream_data.get('videoUrl')
                    subtitles = stream_data.get('subtitles', [])
            except Exception as e:
                print(f"(Stream fetch error: {e}) ", end="")'''

new_stream = '''            # Stream URL is directly available in the episode object from multi-video API
            vurl = ep.get('stream_url')
            subtitles = ep.get('subtitles', [])'''
content = content.replace(old_stream, new_stream)

with open('scripts/scrape_melolov3_provider.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Replacements applied successfully!')
