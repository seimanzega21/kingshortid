with open("d:\\kingshortid\\scratch\\cubetv_page.html", "r", encoding="utf-8") as f:
    html = f.read()

keywords = ["cinta", "suami", "istri", "bos", "kaya", "menantu", "balas", "dewa", "dokter", "cubetv", "watch"]
for kw in keywords:
    count = html.lower().count(kw)
    print(f"Keyword '{kw}': {count} occurrences")
