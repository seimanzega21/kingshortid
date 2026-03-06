"""
Analyze sign_inputs.txt to understand exact format
"""

with open('sign_inputs.txt', 'r', encoding='utf-8') as f:
    content = f.read()

print("FILE CONTENTS:")
print("=" * 80)
print(content)
print("=" * 80)

# Parse first input
sections = content.split('=== Sign Input')
for i, section in enumerate(sections[1:4], 1):  # First 3
    print(f"\n\n=== ANALYSIS OF INPUT {i} ===")
    lines = section.strip().split('\n')
    
    # Find the Input line
    input_line = None
    for j, line in enumerate(lines):
        if line.startswith('Input:'):
            # Next line is the input
            input_line = lines[j+1] if j+1 < len(lines) else None
            break
    
    if input_line:
        print(f"Total length: {len(input_line)}")
        print(f"First 100 chars: {input_line[:100]}")
        print(f"Last 100 chars: {input_line[-100:]}")
        
        # Check if it has timestamp= prefix
        if input_line.startswith('timestamp='):
            print("Has 'timestamp=' prefix: YES")
        else:
            print("Has 'timestamp=' prefix: NO")
            
        # Find package name position
        if 'com.newreading.goodreels' in input_line:
            idx = input_line.index('com.newreading.goodreels')
            before_pkg = input_line[idx-50:idx]
            print(f"50 chars before package name: {before_pkg}")
