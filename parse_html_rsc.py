# -*- coding: utf-8 -*-
import re, json, sys

sys.stdout.reconfigure(encoding='utf-8')

with open('watch_page_melolov3.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Extract self.__next_f.push calls
pushes = re.findall(r'self\.__next_f\.push\(\s*\[\s*\d+\s*,\s*"(.*?)"\s*\]\s*\)', html)
print(f"Total pushes found: {len(pushes)}")

# Combine all strings (unescape backslashes and double quotes)
full_text = ""
for p in pushes:
    # Unescape JSON-like string
    # We can do this by wrapping it in quotes and using json.loads
    try:
        val = json.loads(f'"{p}"')
        full_text += val
    except Exception as e:
        print(f"Failed to unescape a push line: {e}")

print(f"Combined text length: {len(full_text)}")

# Save combined text to file for manual inspection if needed
with open('rsc_combined.txt', 'w', encoding='utf-8') as f:
    f.write(full_text)

# Let's search for some strings in full_text
print("\nSearching for 'Reinkarnasi'...")
for match in re.finditer(r'Reinkarnasi[^\n]{0,100}', full_text, re.IGNORECASE):
    print("Match:", match.group(0))

# Search for m3u8 URLs
m3u8_links = re.findall(r'https?://[^\s"\'>\\{}]+\.m3u8', full_text)
print(f"\nFound {len(m3u8_links)} m3u8 URLs:")
for l in list(set(m3u8_links))[:10]:
    print("  ", l)

# Let's also look for key-value structures like "title", "_h264", etc.
print("\nSearching for _h264:")
for match in re.finditer(r'"_h264"[^,]{0,150}', full_text):
    print("Match:", match.group(0))
