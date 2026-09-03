"""
Filter new_melolov3_dramas.json to only the 18 still-pending dramas
and run the melolov3 ingestion for them.
"""
import json, subprocess, sys

PENDING_SLUGS = [
    "menaklukkan-liga-eropa-1",
    "ruang-mata-air-spiritual",
    "dewa-pedang-legendaris",
    "putra-dewa-kegelapan",
    "ular-pemangsa-dunia",
    "kembalinya-permaisuri",
    "keajaiban-kolam-andi",
    "kisah-dokter-sakti-andika",
    "dipecat-jadi-bos-bengkel",
    "sentuhan-ajaib-sang-mekanik",
    "raja-daging-rebus",
    "dari-turis-jadi-bos-pasar-gelap",
    "antar-makanan-dapat-bidadari",
    "tahun-1983-dimulai-dari-bengkel",
    "sampah-jadi-emas",
    "mata-naga-penguasa-harta",
    "berkah-sepasang-mata-emas",
    "mata-ajaib-sari",
]

with open("new_melolov3_dramas.json", "r", encoding="utf-8") as f:
    all_dramas = json.load(f)

pending = [d for d in all_dramas if d["slug"] in PENDING_SLUGS]
print(f"Filtered to {len(pending)} pending dramas.")

# Write to a temp queue file
with open("melolov3_pending_queue.json", "w", encoding="utf-8") as f:
    json.dump(pending, f, indent=2, ensure_ascii=False)

print("Written to melolov3_pending_queue.json")
