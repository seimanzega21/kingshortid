import requests
import re
import json

API_BASE = "https://api.shortlovers.id/api"
ADMIN_KEY = "00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14"
ADMIN_HDR = {"x-admin-key": ADMIN_KEY, "Content-Type": "application/json"}

target_titles = [
    "Ikatan dengan Raja Mafia",
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
    print("Fetching dramas from DB...")
    r = requests.get(f"{API_BASE}/dramas?limit=1500&includeInactive=true", headers=ADMIN_HDR)
    if not r.ok:
        print(f"Failed to fetch dramas: {r.status_code}")
        return
        
    dramas = r.json()
    if isinstance(dramas, dict):
        dramas = dramas.get("dramas", [])
        
    print(f"Total dramas fetched: {len(dramas)}")
    
    # Map by title (lowercased, stripped)
    db_map = {}
    for d in dramas:
        title_clean = d.get("title", "").strip().lower()
        db_map[title_clean] = d
        
    print("\nMatching target dramas:")
    found_targets = []
    missing_targets = []
    
    for idx, target in enumerate(target_titles, start=3):
        target_clean = target.strip().lower()
        
        # Try exact match first
        match = db_map.get(target_clean)
        
        # Try loose match (like ignoring parentheses or prefix) if exact fails
        if not match:
            for k, v in db_map.items():
                if target_clean in k or k in target_clean:
                    match = v
                    break
                    
        if match:
            # Check episodes
            ep_url = f"{API_BASE}/dramas/{match['id']}/episodes?includeInactive=true"
            ep_r = requests.get(ep_url, headers=ADMIN_HDR)
            ep_count = 0
            if ep_r.ok:
                eps = ep_r.json()
                ep_list = eps if isinstance(eps, list) else eps.get('episodes', eps.get('data', []))
                ep_count = len(ep_list)
                
            found_targets.append({
                "no": idx,
                "title": target,
                "db_title": match['title'],
                "id": match['id'],
                "isActive": match.get('isActive'),
                "registered_eps": ep_count,
                "totalEpisodes": match.get('totalEpisodes'),
                "cover": match.get('cover')
            })
        else:
            missing_targets.append((idx, target))
            
    print("\n--- FOUND DRAMAS ---")
    for f in found_targets:
        print(f"No {f['no']}: {f['title']} -> DB ID: {f['id']} | DB Title: {f['db_title']}")
        print(f"   Status: {'Active' if f['isActive'] else 'Pending'} | Eps Registered: {f['registered_eps']} / Total: {f['totalEpisodes']}")
        print(f"   Cover: {f['cover']}")
        
    if missing_targets:
        print("\n--- MISSING DRAMAS IN DB ---")
        for m in missing_targets:
            print(f"No {m[0]}: {m[1]}")

if __name__ == "__main__":
    main()
