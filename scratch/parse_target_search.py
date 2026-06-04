import json

target_titles = [
    ("Bangkit Menuju Keabadian", "hlex9e7bn15my5rxojh0xvbf"),
    ("Kebenaran di Hari Bahagia", "vzm4q1veinyj3p0jusirrzxd"),
    ("Iklan Bohongan Pembawa Istri", "l095llnyuhjmbvhqwa79tz2q"),
    ("Pedang Sakti", "o70pkjq5qd5ymo105p3wmvfj"),
    ("Loli Terkuat Di Dunia Hitam", "ws67by8ys2rfvni3y4e8imvi"),
    ("Penyesalan Yang Abadi", "wxmlbyl0bxbte8canrr5801w"),
    ("Laporan Pembawa Cinta", "q7u3p2ukk8coytujs4kuakpx"),
    ("(Dubbing)Yang Paling Mencintaiku di Dunia", "vu6bf6u44x5py5xgp0at4h2p"),
    ("Tabib Pelindung Negeri", "dm4pug3ppvsaqrbppinxvu9w"),
    ("Menguji Semua Alphaku", "rzdmgsmjai8frkg5x5cap67y"),
    ("Aku Ini Tidak Berbakat", "nx8sp7f17moj9bwfz4uh96th"),
    ("Maut Dimeja Judi", "ttwjtdedkdf77fizlxfbz67h"),
    ("Terjebak Cinta Bos Mafia", "nvfwaa1kf96seqnyaaiztdco"),
    ("Kemunculan Iblis", "x4esd4bivq6l0kyizs5l18do"),
    ("Ditinggal Nikah, Dikejar Harta", "s9p0zz3w3nk6yga94imsivun"),
    ("Raja yang Ditakuti Musuh", "o9zd2m18sbcixskge3tpuycu"),
    ("Akhiri Sandiwara, Mulai Cinta", "j66un5vhuxyvmfz1qgg0illa"),
    ("Balas Budi Ular Suci", "vu4lu1d2xwjg9znt5g15j6wg"),
    ("Pilihanku Tak Akan Berubah", "gd3ydkwfv83kf53bfem56m8l"),
    ("Saatnya Sang Utama Bangkit", "hpq82h999e6qcb4z0e7hqyhk")
]

def main():
    try:
        with open('scratch/target_search_netshortv2.json', 'r') as f:
            search_data = json.load(f)
    except Exception as e:
        search_data = {}
        print("Failed to load target_search_netshortv2.json:", e)

    # Let's map target title to netshortv2 matched items
    # Also add the two loose-matched ones manually
    extra_matches = {
        "Ditinggal Nikah, Dikejar Harta": "2059541389742252034",
        "Akhiri Sandiwara, Mulai Cinta": "2039536984908627969"
    }

    mapped = []
    
    for title, db_id in target_titles:
        # Check if we have exact match in search data
        res_list = search_data.get(title, [])
        netshort_id = None
        netshort_title = None
        
        if title in extra_matches:
            netshort_id = extra_matches[title]
            netshort_title = title
        else:
            # Look for exact or closest title match in res_list
            for item in res_list:
                item_title = item.get('title', '').strip().lower()
                clean_title = title.replace("(Dubbing)", "").strip().lower()
                if clean_title == item_title or clean_title in item_title or item_title in clean_title:
                    netshort_id = item.get('id')
                    netshort_title = item.get('title')
                    break
            
            # Fallback to first item if no exact/close match
            if not netshort_id and res_list:
                netshort_id = res_list[0].get('id')
                netshort_title = res_list[0].get('title')
                
        mapped.append({
            "title": title,
            "db_id": db_id,
            "netshort_id": netshort_id,
            "netshort_title": netshort_title
        })

    print(json.dumps(mapped, indent=2))
    
    # Save the mapped JSON
    with open('scratch/mapped_netshortv2_dramas.json', 'w') as f:
        json.dump(mapped, f, indent=2)

if __name__ == "__main__":
    main()
