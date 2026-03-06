"""
Deep analysis - extract components from sign input
"""
import re

with open('sign_inputs.txt', 'r', encoding='utf-8') as f:
    content = f.read()

# Find strings between === markers
inputs = re.findall(r'Input:\n(.+?)(?:\n\n|$)', content, re.DOTALL)

for i, inp in enumerate(inputs[:2]):
    print(f"\n{'='*60}")
    print(f"INPUT {i+1}")
    print(f"{'='*60}")
    print(f"Total length: {len(inp)}")
    
    # Try to find MD5 pattern (32 hex chars before package name)
    pkg = 'com.newreading.goodreels'
    if pkg in inp:
        idx = inp.index(pkg)
        before = inp[max(0,idx-40):idx]
        print(f"\n40 chars before package: [{before}]")
        
        # Extract what looks like MD5 (32 hex chars)
        md5_match = re.search(r'([A-F0-9]{32})' + pkg, inp)
        if md5_match:
            print(f"MD5 found: {md5_match.group(1)}")
        
    # Find timestamp
    ts_match = re.search(r'timestamp=(\d+)', inp)
    if ts_match:
        print(f"Timestamp: {ts_match.group(1)}")
    
    # Find GAID pattern
    gaid_match = re.search(r'([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})', inp)
    if gaid_match:
        print(f"GAID: {gaid_match.group(1)}")
    
    # Find Bearer token
    if 'Bearer' in inp:
        bearer_start = inp.index('Bearer')
        # Token ends before MD5 (32 chars before package)
        token_end = idx - 32 if pkg in inp else len(inp)
        token = inp[bearer_start:token_end]
        print(f"Token (len={len(token)}): {token[:50]}...")
    
    # Print first 150 chars
    print(f"\nFirst 150: {inp[:150]}")
