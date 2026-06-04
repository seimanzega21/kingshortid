import requests
import json

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

def main():
    print("Fetching target dramas from DB...")
    r = requests.get(f"{API_BASE}/dramas?limit=1500&includeInactive=true", headers=ADMIN_HDR)
    db_dramas = r.json()
    if isinstance(db_dramas, dict):
        db_dramas = db_dramas.get("dramas", [])
        
    db_map = {}
    for d in db_dramas:
        title_clean = d.get("title", "").strip().lower()
        db_map[title_clean] = d
        
    print("Fetching all microdramas from Vidrama...")
    url = "https://vidrama.asia/api/microdrama?action=list&lang=id&limit=1000"
    mr = requests.get(url, timeout=20)
    if not mr.ok:
        print("Failed to fetch microdramas")
        return
    microdramas = mr.json().get("dramas", [])
    print(f"Total microdramas: {len(microdramas)}")
    
    micro_map = {}
    for m in microdramas:
        title_clean = m.get("title", "").strip().lower()
        micro_map[title_clean] = m
        
    matched = []
    unmatched = []
    
    for target in target_titles:
        target_clean = target.strip().lower()
        
        # Try direct match
        db_drama = db_map.get(target_clean)
        if not db_drama:
            # loose match in DB
            for k, v in db_map.items():
                if target_clean in k or k in target_clean:
                    db_drama = v
                    break
                    
        if not db_drama:
            unmatched.append((target, "Not found in DB"))
            continue
            
        db_title = db_drama['title']
        db_id = db_drama['id']
        
        # Match with microdrama title
        micro_drama = micro_map.get(target_clean)
        if not micro_drama:
            # Clean parentheses/dubbing from target_clean
            cleaner_target = target_clean.replace("(dubbing)", "").strip()
            micro_drama = micro_map.get(cleaner_target)
            
        if not micro_drama:
            # Loose match in micro
            for k, v in micro_map.items():
                target_word_clean = target_clean.replace("(dubbing)", "").strip()
                if target_word_clean in k or k in target_word_clean:
                    micro_drama = v
                    break
                    
        if micro_drama:
            matched.append({
                "target": target,
                "db_title": db_title,
                "db_id": db_id,
                "micro_title": micro_drama['title'],
                "micro_id": micro_drama['id']
            })
        else:
            unmatched.append((target, f"Not found in microdrama list (DB ID: {db_id})"))
            
    print(f"\n--- MATCHED ({len(matched)} / {len(target_titles)}) ---")
    for m in matched:
        print(f"Target: {m['target']}")
        print(f"  DB Title: {m['db_title']} (ID: {m['db_id']})")
        print(f"  Micro Title: {m['micro_title']} (ID: {m['micro_id']})")
        
    if unmatched:
        print(f"\n--- UNMATCHED ({len(unmatched)}) ---")
        for u in unmatched:
            print(f"Target: {u[0]} | Reason: {u[1]}")

if __name__ == "__main__":
    main()
