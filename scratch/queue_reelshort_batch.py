import subprocess
import time

ids = [
    "6a82659afc4684b5640b83b9", # Sudah Terlambat Dr Hall
    "684a3b44ec8c6e2bea08f1f5", # Aku Hamil Anak Dosenku
    "6a19282c391d72edbe00cb11", # Nggak Sengaja Rayu Musuh
    "69721600faaa42a2fa084075", # Ayah Payah Jadi Kaisar
    "6a72ac7e1f385f32860cdabf", # Tidur Dengan Putra Mantan Suamiku
    "6a69c27092c1bb2d2c04d95b", # Selamat Tinggal Cinta Pertama
    "69fc5565a41c6f1f3307573b", # Rencana Licik Kasim Palsu
    "6a222c952692e53d6e04b559", # Mantan Napi Itu Ternyata Miliarder
    "6a3df2fbbf940cea59003aa7", # Nero Sang Pangeran Mafia
    "69e1d19cdb5e6478cf0a56a3", # Dulu Ditindas Kini Penguasa Dunia Bawah
    "698597d94dc30d21ea0c6885", # Cerai Bangkit Berkuasa
    "6a5f2c0c4e2340ea77044082", # Kurir Itu Panglima Perang
    "69bba1b68ce3290ad9009434", # Cinta Pura Pura Dengan Bosku
    "69d876c1ee6e6be5e000f14f", # Demi Putriku Aku Membunuh Lagi
    "6a857e5003bc5a7c460a35f0", # Tuan Kini Aku Mantan Istrimu
    "6a4604c49c68c1bca5045cec", # Mata X Ray Menembus Hatimu
    "69c49927e92f4783e60e3923", # Jangan Sampai Anakmu Jatuh Cinta Padaku
    "65b462634138f31e570ad7fd", # Luna Yang Sebenarnya
]

for movie_id in ids:
    print(f"\n=======================================================")
    print(f"Starting REELSHORT scrape for movie_id: {movie_id}")
    print(f"=======================================================\n")
    
    cmd = ['python', 'scripts/scrape_reelshort_provider.py', movie_id]
    subprocess.run(cmd)
    
    print(f"\n[QUEUE] Sleeping for 15 seconds before next drama to prevent rate limiting...\n")
    time.sleep(15)

print("\nAll batch processing completed successfully!")
