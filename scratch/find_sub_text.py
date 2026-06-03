import re
with open('scratch/watch_page_snippet.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Search for common subtitle indicators
for ext in ['.vtt', '.srt', 'subtitle', 'track', 'src=']:
    matches = [m.start() for m in re.finditer(ext, html, re.IGNORECASE)]
    print(f"Found {len(matches)} matches for '{ext}'")
    for m in matches[:5]:
        print(f"  Snippet at {m}: {html[max(0, m-50):min(len(html), m+100)]}")
