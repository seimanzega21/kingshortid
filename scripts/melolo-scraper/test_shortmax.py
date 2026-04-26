import re
with open('d:/kingshortid/scripts/melolo-scraper/shortmax_page.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Look for titles
titles = re.findall(r'\"title\":\"([^\"]+)\"', html)
if titles:
    print('Found JSON titles:', titles[:10])
else:
    print('No JSON titles found')

titles2 = re.findall(r'(?i)sopir\s+taksi', html)
print('Found Sopir Taksi:', titles2)
