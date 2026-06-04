import requests
import json
import re

API_BASE = "https://api.shortlovers.id/api"
ADMIN_KEY = "00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14"
ADMIN_HDR = {"x-admin-key": ADMIN_KEY, "Content-Type": "application/json"}

target_titles = [
    "Bangkit Menuju Keabadian",
    "Kebenaran di Hari Bahagia",
    "Iklan Bohongan Pembawa Istri",
    "Pedang Sakti",
    "Loli Terkuat Di Dunia Hitam",
    "Penyesalan Yang Abadi",
    "Laporan Pembawa Cinta",
    "(Dubbing)Yang Paling Mencintaiku di Dunia",
    "Tabib Pelindung Negeri",
    "Menguji Semua Alphaku",
    "Aku Ini Tidak Berbakat",
    "Maut Dimeja Judi",
    "Terjebak Cinta Bos Mafia",
    "Kemunculan Iblis",
    "Ditinggal Nikah, Dikejar Harta",
    "Raja yang Ditakuti Musuh",
    "Akhiri Sandiwara, Mulai Cinta",
    "Balas Budi Ular Suci",
    "Pilihanku Tak Akan Berubah",
    "Saatnya Sang Utama Bangkit"
]

def clean_text(text):
    if not text:
        return ""
    # remove punctuation and lowercase
    text = re.sub(r'[^\w\s]', '', text.lower())
    return text

def main():
    print("Fetching target dramas from DB...")
    r = requests.get(f"{API_BASE}/dramas?limit=1500&includeInactive=true", headers=ADMIN_HDR)
    db_dramas = r.json()
    if isinstance(db_dramas, dict):
        db_dramas = db_dramas.get("dramas", [])
        
    db_targets = []
    for d in db_dramas:
        title = d.get("title", "")
        # Find if it matches one of our target titles
        matched_target = None
        for t in target_titles:
            t_clean = t.strip().lower()
            d_clean = title.strip().lower()
            if t_clean == d_clean or t_clean in d_clean or d_clean in t_clean:
                matched_target = t
                break
        if matched_target:
            db_targets.append(d)
            
    print(f"Matched targets in DB: {len(db_targets)} / {len(target_titles)}")
    
    print("Fetching all microdramas from Vidrama...")
    url = "https://vidrama.asia/api/microdrama?action=list&lang=id&limit=1000"
    mr = requests.get(url, timeout=20)
    microdramas = mr.json().get("dramas", [])
    
    # We will search matching based on keyword matching in description
    print("\n--- MATCHING BY KEYWORDS IN TITLE & DESCRIPTION ---")
    matched_count = 0
    
    for dt in db_targets:
        dt_title = dt.get("title")
        dt_desc = dt.get("description") or ""
        dt_id = dt.get("id")
        
        # Extract name entities or unique keywords from description
        # e.g., words with Capital letter in description or just common words
        desc_words = set(clean_text(dt_desc).split())
        title_words = set(clean_text(dt_title).split())
        
        best_match = None
        best_score = 0
        
        for md in microdramas:
            md_title = md.get("title") or ""
            md_desc = md.get("description") or ""
            
            md_desc_words = set(clean_text(md_desc).split())
            md_title_words = set(clean_text(md_title).split())
            
            # Match score: intersection of words in description + Title match
            overlap = desc_words.intersection(md_desc_words)
            # Ignore short words
            overlap = {w for w in overlap if len(w) > 3}
            
            title_overlap = title_words.intersection(md_title_words)
            title_overlap = {w for w in title_overlap if len(w) > 2}
            
            score = len(overlap) + len(title_overlap) * 5
            
            if score > best_score and score >= 3:
                best_score = score
                best_match = md
                
        if best_match:
            matched_count += 1
            print(f"DB Title: {dt_title} (ID: {dt_id})")
            print(f"  -> Best Micro Match: {best_match['title']} (ID: {best_match['id']})")
            print(f"     Match Score: {best_score}")
        else:
            print(f"DB Title: {dt_title} (ID: {dt_id}) -> NO MATCH FOUND")
            
    print(f"\nMatched: {matched_count} / {len(db_targets)}")

if __name__ == "__main__":
    main()
