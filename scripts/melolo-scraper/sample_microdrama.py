#!/usr/bin/env python3
"""Sample all 255 microdrama dramas and find Indonesian ones."""
import requests, sys, json, re
sys.stdout.reconfigure(encoding="utf-8")

ID_MARKERS = {
    "sang", "si", "di", "ke", "dari", "dan", "atau", "untuk", "yang", "dengan",
    "para", "nya", "pak", "bu", "mas", "mbak", "bang", "mba",
    "tak", "bukan", "jangan", "tidak", "belum", "sudah", "masih", "pun",
    "cinta", "kasih", "hati", "jiwa", "anak", "ibu", "ayah", "suami", "istri",
    "kakak", "adik", "saudari", "saudara", "keluarga", "pernikahan", "sahabat",
    "dokter", "raja", "ratu", "putri", "pangeran", "tabib", "pendekar",
    "kultivator", "penakluk", "penguasa", "pembalas", "penyelamat",
    "naga", "harimau", "langit", "desa", "kota", "dunia", "hutan", "bunga",
    "bangkit", "terjatuh", "kembali", "lahir", "hidup", "jatuh", "cium",
    "menikah", "cerai", "benci", "dendam", "balas", "terjebak", "terbuang",
    "tersembunyi", "terperangkap", "tercinta", "pembalasan",
    "takdir", "nasib", "rahasia", "musuh", "kaya", "miskin",
    "menjadi", "bangsa", "istana", "kerajaan", "mafia", "bos", "perusahaan",
}

EN_STOPWORDS = {
    "the", "a", "an", "my", "your", "his", "her", "our", "their",
    "she", "he", "they", "we", "i", "me", "you", "him", "us",
    "was", "is", "are", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did",
    "will", "would", "could", "should", "may", "might", "must",
    "and", "or", "but", "nor", "so", "yet", "for", "of", "in",
    "on", "at", "to", "by", "as", "if", "not", "no",
    "this", "that", "these", "those", "what", "who", "how", "when",
    "from", "with", "out", "up", "back", "off", "down", "into",
    "after", "before", "over", "under", "about", "than", "more",
    "like", "just", "now", "then", "here", "there", "all", "each",
    "get", "got", "make", "take", "give", "go", "come", "see",
    "can", "cannot", "whose", "which", "where", "why",
    "love", "life", "heart", "time", "night", "day", "year",
    "ceo", "boss", "cold", "hot", "new", "old", "little", "big",
    "girl", "boy", "man", "woman", "wife", "husband", "son", "daughter",
    "mother", "father", "sister", "brother", "family",
    "rich", "poor", "good", "bad", "true", "wrong"
}

def is_indonesian(title):
    words = re.findall(r"[a-zA-Z]+", title.lower())
    if not words:
        return False
    en_hits = sum(1 for w in words if w in EN_STOPWORDS)
    if en_hits > 0:
        return False
    id_hits = sum(1 for w in words if w in ID_MARKERS)
    return id_hits >= 1

# Scan all pages (255 total = 6 pages of 50)
all_dramas = []
for page in range(10):  # scan up to 10 pages
    r = requests.get(f"https://vidrama.asia/api/microdrama?action=list&limit=50&offset={page * 50}", timeout=15)
    data = r.json()
    dramas = data.get("dramas", [])
    if not dramas:
        print(f"Page {page+1}: empty, done")
        break
    all_dramas.extend(dramas)
    print(f"Page {page+1}: {len(dramas)} dramas, total so far: {len(all_dramas)}")

print(f"\nTotal dramas in API: {len(all_dramas)}")

# Find Indonesian
id_dramas = [d for d in all_dramas if is_indonesian(d["title"])]
print(f"Indonesian dramas: {len(id_dramas)}")
print()

# Show all Indonesian titles
for i, d in enumerate(id_dramas, 1):
    print(f"{i:3}. {d['title']} ({d.get('episodes', '?')} eps)")

# Also show some borderline titles
print("\n--- Sample of non-matched titles (first 20) ---")
non_id = [d for d in all_dramas if not is_indonesian(d["title"])]
for d in non_id[:20]:
    print(f"  SKIP: {d['title']}")

# Save Indonesian dramas
with open("microdrama_id_sample.json", "w", encoding="utf-8") as f:
    json.dump(id_dramas, f, indent=2, ensure_ascii=False)
