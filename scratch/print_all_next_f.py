import re

with open("d:\\kingshortid\\scratch\\cubetv_page.html", "r", encoding="utf-8") as f:
    html = f.read()

pattern = r'self\.__next_f\.push\(\[(.*?)\].*?\)'
matches = re.findall(pattern, html, re.DOTALL)

for i, m in enumerate(matches):
    print(f"\n--- Match {i+1} ---")
    print(m[:1000])
    if len(m) > 1000:
        print("... TRUNCATED ...")
