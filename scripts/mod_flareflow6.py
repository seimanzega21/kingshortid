with open('d:/kingshortid/scripts/scrape_flareflow_provider.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Fix detail fetching
old1 = "title = detail.get('title') or detail.get('name') or 'Unknown Title'"
new1 = "title = detail.get('shortPlayName') or 'Unknown Title'"
code = code.replace(old1, new1)

# Fix total episodes
old2 = "total_eps = detail.get('totalEpisode', 0)"
new2 = "total_eps = detail.get('totalEpisodes', 0)"
code = code.replace(old2, new2)

with open('d:/kingshortid/scripts/scrape_flareflow_provider.py', 'w', encoding='utf-8') as f:
    f.write(code)
