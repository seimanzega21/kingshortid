# -*- coding: utf-8 -*-
import re

with open('watch_page_melolov3.html', 'r', encoding='utf-8') as f:
    html = f.read()

scripts = re.findall(r'<script[^>]*src=["\'](.*?)["\']', html)
print("Scripts found:")
for s in scripts:
    print("  ", s)
