import re
import json

with open("d:\\kingshortid\\scratch\\cubetv_page.html", "r", encoding="utf-8") as f:
    html = f.read()

# Find all script tags containing self.__next_f.push
pattern = r'self\.__next_f\.push\(\[\d+,\s*"(.*?)"\]\)'
matches = re.findall(pattern, html, re.DOTALL)

full_data = ""
for m in matches:
    # Decode string escapes
    decoded = m.replace('\\"', '"').replace('\\\\', '\\')
    full_data += decoded

# Let's write the concatenated next_f data to a file for manual inspection or search
with open("d:\\kingshortid\\scratch\\next_f_decoded.txt", "w", encoding="utf-8") as f:
    f.write(full_data)

print(f"Decoded data length: {len(full_data)}")

# Let's search for movie-related keys
# In Next.js App Router, the props returned to the client might contain fields like "title", "id", "slug", "cover", etc.
# We can search for patterns of Movie IDs (typically 19-digit numbers like 2030890517679570946, or similar)
# Let's search for: "id":"123456789..." or "movieId" or movie titles.
id_matches = re.findall(r'"id"\s*:\s*"(\d+)"', full_data)
print(f"Potential IDs found: {list(set(id_matches))}")

title_matches = re.findall(r'"title"\s*:\s*"(.*?)"', full_data)
print(f"Potential titles found (first 10): {list(set(title_matches))[:10]}")

# Let's look for matching pairs
# E.g. {"id":"2030890517679570946","title":"Pengemis Itu Sangat Berkuasa","cover":"..."} or similar structures
# Let's print occurrences of dictionaries or substrings containing "title" and "id" or "cover" or "slug"
print("\n--- Searching for drama objects ---")
# Let's find patterns like: "title":"...", "id":"..." or "id":"...", "title":"..."
# Sometimes Next.js state has keys like "title", "cover", "id", "slug" or similar.
# Let's scan all text blocks that look like JSON objects or contain title / slug / id
matches_with_context = []
for m in re.finditer(r'"id"\s*:\s*"(\d+)"', full_data):
    start = max(0, m.start() - 200)
    end = min(len(full_data), m.end() + 200)
    context = full_data[start:end]
    matches_with_context.append(context)

for i, ctx in enumerate(matches_with_context[:5]):
    print(f"\nMatch {i+1}:")
    print(ctx)
