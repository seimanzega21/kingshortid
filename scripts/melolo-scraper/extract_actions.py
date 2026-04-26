import re

def extract():
    with open('d:/kingshortid/scripts/melolo-scraper/2ecddc6f978f5fb2.js', 'r', encoding='utf-8') as f:
        content = f.read()

    # Generic regex
    matches = re.finditer(r'createServerReference\)\("([a-f0-9]+)"(?:.*?)"([^"]+)"\)', content)
    for m in matches:
        print(f"{m.group(2)} -> {m.group(1)}")

if __name__ == '__main__':
    extract()
