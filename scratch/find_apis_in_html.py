import re

with open("scratch/movie_page_QZpz60.html", "r", encoding="utf-8") as f:
    html = f.read()

# Find any URLs matching /api/...
apis = re.findall(r'\"/api/[^\"]+\"', html)
print("Found API strings in HTML:")
for api in set(apis):
    print(api)

# Look for any JSON-like data or lists in self.__next_f scripts
# Search for firstEpisodeid "a7w8na" or latestEpisodeid "ZKeVx0" in all scripts
print("\nSearching for episode IDs in HTML:")
for term in ["a7w8na", "ZKeVx0"]:
    count = html.count(term)
    print(f"Term '{term}' found: {count} times")
    if count > 0:
        # Find lines containing it
        lines = html.splitlines()
        for i, line in enumerate(lines):
            if term in line:
                print(f"Line {i} (len={len(line)}): {line[:300]}...")
