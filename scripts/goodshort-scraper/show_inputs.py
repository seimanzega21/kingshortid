"""Analyze captured inputs"""
import json

with open('all_captured_inputs.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"Total captured: {len(data)}")
print()

for i, item in enumerate(data):
    inp = item['input']
    print(f"#{i+1}: len={item['length']}")
    print(f"    Preview: {inp[:100]}")
    
    # Extract body part after timestamp=XXXXXX
    if inp.startswith('timestamp='):
        ts_end = 23  # timestamp=1234567890123
        body_start = inp[ts_end:]
        # Body is JSON - find first {
        if '{' in body_start:
            json_start = body_start.index('{')
            json_part = body_start[json_start:]
            # Find matching }
            depth = 0
            for j, c in enumerate(json_part):
                if c == '{': depth += 1
                elif c == '}': depth -= 1
                if depth == 0:
                    json_body = json_part[:j+1]
                    break
            print(f"    Body: {json_body[:80]}...")
    print()
