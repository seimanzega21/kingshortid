import json
import re
from bs4 import BeautifulSoup

with open('scratch/freereels.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Vidrama is a Next.js App Router site (since we saw __next_f in playwright output).
# App router sites don't use __NEXT_DATA__, they push chunks into self.__next_f.
# The chunks contain JSON structures with the data.
# Let's search for "freereels" in the html and try to extract titles and slugs/ids.

# In my earlier manual inspection of playwright output, the chunk had:
# ["$","title","0",{"children":"Freereels - Drama Gratis ...
# Let's try to extract video items. Often they are inside a list in one of the chunks.

# Instead of parsing the complex __next_f array, let's just regex search for
# {"id":"...","title":"...","slug":"..."} or similar patterns in the HTML.
import re

# Look for patterns that look like a drama object:
# Usually: "id":"TxCz3hQFxJ" or \"id\":\"TxCz3hQFxJ\"
# Let's clean up escape characters first
clean_html = html.replace('\\"', '"')

# Now find all dict-like structures with title and id
matches = re.findall(r'{"id":"([^"]{8,15})","title":"([^"]+)"', clean_html)
if not matches:
    matches = re.findall(r'{"title":"([^"]+)","id":"([^"]{8,15})"', clean_html)

print(f"Found {len(matches)} matches")

results = set()
for m in matches:
    # m is either (id, title) or (title, id)
    if len(m[0]) <= 15:
        vid_id, title = m[0], m[1]
    else:
        title, vid_id = m[0], m[1]
    
    # Filter out anything that doesn't look like an alphanumeric ID
    if re.match(r'^[A-Za-z0-9]+$', vid_id):
        results.add((vid_id, title))

for vid_id, title in results:
    print(f"{vid_id} -> {title}")

# Also output it to a new JSON queue!
queue = []
for vid_id, title in results:
    queue.append({
        'id': vid_id,
        'title': title,
        'status': 'pending',
        'addedAt': '2026-06-10T12:00:00Z',
        'processedAt': None
    })

with open('scripts/freereels_queue.json', 'w', encoding='utf-8') as f:
    json.dump(queue, f, indent=2, ensure_ascii=False)
print("Updated freereels_queue.json with real FreeReels IDs!")
