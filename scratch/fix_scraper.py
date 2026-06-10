import re

with open('scripts/scrape_freereels_queue.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove any existing check_duplicate_in_api definition if any
content = re.sub(r'def check_duplicate_in_api.*?return False\n+', '', content, flags=re.DOTALL)

func_def = '''
def check_duplicate_in_api(title):
    try:
        import urllib.parse
        import re
        import requests
        words = title.replace('[Versi Dub]', '').replace('(Sulih Suara)', '').replace('[Dubbing]', '').replace('[Dijuluki]', '').split()
        if not words: return False
        q = ' '.join(words[:3])
        r = requests.get(f"{API_BASE}/dramas/search?q={urllib.parse.quote(q)}", timeout=10)
        if r.ok:
            dramas = r.json().get('dramas', [])
            def clean_title(t):
                t = t.lower()
                t = re.sub(r'\\[versi dub\\]|\\(sulih suara\\)|\\[dubbing\\]|\\[dijuluki\\]', '', t)
                return re.sub(r'[^a-z0-9]', '', t)
            my_clean = clean_title(title)
            for d in dramas:
                if clean_title(d['title']) == my_clean:
                    # Check if it was created by freereels
                    if d.get('cover') and 'freereels' in d['cover']:
                        return False # created by freereels scraper, do not skip
                    return True # Duplicate found!
    except Exception as e:
        print(f"      [WARN] Error checking duplicate: {e}")
    return False

'''
content = content.replace('def generate_rich_description', func_def + 'def generate_rich_description')

with open('scripts/scrape_freereels_queue.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Fixed!')
