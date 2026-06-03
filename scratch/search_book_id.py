import re

with open('scratch/watch_page_snippet.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Look for occurrences of the book ID
book_id = '42000011676'
for match in re.finditer(book_id, html):
    start = max(0, match.start() - 100)
    end = min(len(html), match.end() + 100)
    print(f"Match found at position {match.start()}:\n{html[start:end]}\n" + "-"*50)
