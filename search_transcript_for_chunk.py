# -*- coding: utf-8 -*-
import sys

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    log_path = 'C:/Users/Seiman/.gemini/antigravity/brain/fa36601f-36fa-493d-b7be-e97335b47ed3/.system_generated/logs/transcript.jsonl'
    
    with open(log_path, 'r', encoding='utf-8') as f:
        for idx, line in enumerate(f):
            if '123c8307fc6c5765.js' in line:
                print(f"Line {idx}: {line[:400]}...")
                print("-" * 50)

if __name__ == '__main__':
    main()
