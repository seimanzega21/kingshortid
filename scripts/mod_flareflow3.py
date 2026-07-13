with open('d:/kingshortid/scripts/scrape_flareflow_provider.py', 'r', encoding='utf-8') as f:
    code = f.read()

old_func = """def api_get_or_create_drama(detail, slug, cover_url):
    title = detail.get('title') or detail.get('name') or 'Unknown Title'
    payload = {
        'title': title,
        'description': detail.get('description') or detail.get('introduction') or title,
        'cover': cover_url,
        'genres': detail.get('tags', ['Drama']) or ['Drama'],
        'totalEpisodes': detail.get('chapterCount', 0),
        'isComplete': True if detail.get('bookStatus') == 1 else False,
        'country': 'China', 
        'language': 'Indonesia',
        'status': 'completed' if detail.get('bookStatus') == 1 else 'ongoing',
        'isActive': False, # Pending!
    }"""

new_func = """def api_get_or_create_drama(detail, slug, cover_url):
    title = detail.get('title') or detail.get('name') or 'Unknown Title'
    genres = [g.get('labelName') for g in detail.get('labelResponseList', [])]
    if not genres: genres = ['Drama']
    
    payload = {
        'title': title,
        'description': detail.get('synopsis') or detail.get('description') or title,
        'cover': cover_url,
        'genres': genres,
        'totalEpisodes': detail.get('totalEpisode', 0),
        'isComplete': True if detail.get('updateStatus') == 1 else False,
        'country': 'China', 
        'language': 'Indonesia',
        'status': 'completed' if detail.get('updateStatus') == 1 else 'ongoing',
        'isActive': True,
    }"""
code = code.replace(old_func, new_func)

# Also update episodes isActive
code = code.replace("'isActive': False,", "'isActive': True,")

with open('d:/kingshortid/scripts/scrape_flareflow_provider.py', 'w', encoding='utf-8') as f:
    f.write(code)
