import requests

API_BASE  = 'http://141.11.160.187:3000'
ADMIN_KEY = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
ADMIN_HDR = {'x-admin-key': ADMIN_KEY, 'Content-Type': 'application/json'}

TITLES_TO_DELETE = [
    "Kakakku Bos Mafia", "Runtuhnya Mahkota", "Berkat Sistem", 
    "Sang Penagih Utang Takdir", "Putri Disakiti", "Pelindungku Cinta Terlarangku",
    "Cinta Takkan Berbalik", "Ratu Hati Sang Pembalap", "Menyala di Salju", "Naga Dalam Darahku Bangkit"
]

page = 1
found = 0

print("Scanning all pages to find dramas to delete...")
while True:
    r = requests.get(f"{API_BASE}/api/dramas?page={page}&limit=100", timeout=15)
    if not r.ok: break
    
    dramas = r.json().get('dramas', [])
    if not dramas: break
        
    for dr in dramas:
        for t in TITLES_TO_DELETE:
            if t.lower() in dr.get('title', '').lower():
                drama_id = dr['id']
                print(f"FOUND: {dr['title']} (ID: {drama_id})")
                
                del_r = requests.delete(f"{API_BASE}/api/admin/dramas/{drama_id}", headers=ADMIN_HDR, timeout=15)
                print(f"  -> DELETE status: {del_r.status_code}")
                found += 1
                
    page += 1

print(f"Scan complete. Found/Deleted {found} dramas.")
