import requests
import json
import re
import os

def test_scrape_goodshort():
    url = "https://vidrama.asia/watch/penyesalan-tiada-akhir--31001370470/1?provider=goodshortv2&lang=in"
    
    headers = {
        "next-action": "40fa27522e54e68e8594b146009c64be3fdf864e9b",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/x-component",
        "Content-Type": "text/plain;charset=UTF-8",
        "Referer": url
    }
    
    # ID Drama: 31001370470
    data = '["31001370470"]'
    
    print("Mengirim request ke Vidrama Server Action...")
    try:
        response = requests.post(url, headers=headers, data=data, timeout=15)
        print(f"Status Code: {response.status_code}")
        
        # Simpan raw response
        with open("raw_goodshort_response.txt", "w", encoding="utf-8") as f:
            f.write(response.text)
        print("Raw response disimpan ke: raw_goodshort_response.txt")
        
        # Coba parse data URL Videonya
        urls = re.findall(r'"(https?://[^"]+\.(?:m3u8|mp4|ts)[^"]*)"', response.text)
        if urls:
            print("\n[BERHASIL] Ditemukan URL Video/M3U8:")
            for u in urls[:5]:
                print(f"- {u[:100]}...")
            
            with open("goodshort_urls.json", "w", encoding="utf-8") as f:
                json.dump(urls, f, indent=2)
            print("\nSemua URL video berhasil diekstrak dan disimpan ke: goodshort_urls.json")
        else:
            print("\n[INFO] Tidak menemukan direct URL (.m3u8/.mp4) dari response.")
            print("Cek file raw_goodshort_response.txt untuk melihat struktur datanya.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_scrape_goodshort()
