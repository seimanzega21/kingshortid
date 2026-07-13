import sys
with open('d:/kingshortid/scripts/scrape_flareflow_provider.py', 'r', encoding='utf-8') as f:
    code = f.read()

import re
code = re.sub(r"if not res_json\.get\('success'\):.*?return False", "", code, flags=re.DOTALL)
code = re.sub(r"detail = res_json\.get\('data', \{\}\)", "detail = res_json", code)

with open('d:/kingshortid/scripts/scrape_flareflow_provider.py', 'w', encoding='utf-8') as f:
    f.write(code)
