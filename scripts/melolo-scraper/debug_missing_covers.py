import re

def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return re.sub(r"-+", "-", text).strip("-")

data = open('d:/kingshortid/scripts/melolo-scraper/netshort_scrape.log', encoding='utf-8', errors='ignore').read()
matches = re.findall(r"Scraping drama:\s*(\d+).*?\n.*?Title:\s*([^\n]+)", data, re.IGNORECASE)
unique_matches = list(set(matches))
print(f"Total Unique Mappings in Log: {len(unique_matches)}")

for m in unique_matches:
    if "Konspirasi" in m[1]:
        clean_title = m[1].replace("(Sulih suara)", "").replace("(sulih suara)", "")
        print(f"ID: {m[0]} | Title: {m[1]} | Slug: {slugify(clean_title)}")

