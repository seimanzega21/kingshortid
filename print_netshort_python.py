# -*- coding: utf-8 -*-
import sys

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    encodings = ['utf-16', 'utf-16le', 'utf-8', 'latin1']
    for enc in encodings:
        try:
            with open('d:/kingshortid/scrape_netshort.py', 'r', encoding=enc) as f:
                content = f.read()
            print(f"--- SUCCESS WITH ENCODING {enc} ---")
            print(content[:3000])
            return
        except Exception as e:
            print(f"Failed with {enc}: {e}")

if __name__ == '__main__':
    main()
