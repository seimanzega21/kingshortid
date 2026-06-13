import re

with open('scratch/next_payload.txt', 'r', encoding='utf-8') as f:
    text = f.read()

# Let's search for "player" case-insensitive
player_matches = [m.start() for m in re.finditer(r'player', text, re.IGNORECASE)]
print("Player occurrences count:", len(player_matches))
for i, pos in enumerate(player_matches[:5]):
    print(f"\n--- PLAYER Match {i} ---")
    print(text[max(0, pos-100):min(len(text), pos+300)])

# Let's search for any URL that looks like an iframe or embed source
iframe_srcs = re.findall(r'<iframe[^>]+?src="([^"]+?)"', text)
print("Iframe sources:", iframe_srcs)
