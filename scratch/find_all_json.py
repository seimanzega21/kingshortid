import re
import json

with open('scratch/next_payload.txt', 'r', encoding='utf-8') as f:
    text = f.read()

# Let's find any occurrences of {...} or [...] and see if we can parse it
# Wait, let's print all matches of a regex that finds json structures
# Since next_f payloads are mixed, let's just search for keys like "title", "episodes", "videos" and print their values
print("--- SEARCH FOR KEYWORDS ---")
patterns = [
    r'\"title\"\s*:\s*\"([^\"]+?)\"',
    r'\"cover\"\s*:\s*\"([^\"]+?)\"',
    r'\"description\"\s*:\s*\"([^\"]+?)\"',
    r'\"episodes\"\s*:\s*(\[.*?\])',
    r'\"videos\"\s*:\s*(\[.*?\])',
    r'\"subtitles\"\s*:\s*(\[.*?\])'
]

for pat in patterns:
    matches = re.findall(pat, text)
    print(f"Pattern '{pat}': found {len(matches)} matches")
    for m in matches[:3]:
        print("  Match:", str(m)[:200])

# Let's print out text that contains episode information
# e.g., 'episodeNum' or 'episode-1'
matches_ep = re.findall(r'\"episodeNum\"\s*:\s*\d+', text)
print("episodeNum occurrences:", len(matches_ep))
if matches_ep:
    # Print a block of text around one of the episodeNum occurrences
    pos = text.find('episodeNum')
    print("Snippet around episodeNum:\n", text[pos-100:pos+300])
