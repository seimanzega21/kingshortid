import time
import json
import re
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

# Drama Configuration
DRAMA_URL = "https://vidrama.asia/watch/dubbingsopir-taksi-mantan-dewa-balap--846959/?provider=shortmax"
DRAMA_SLUG = "dubbingsopir-taksi-mantan-dewa-balap--846959"
TOTAL_EPISODES = 70
OUTPUT_FILE = f"{DRAMA_SLUG}_episodes.json"

def run():
    print("==================================================")
    print(" VIDRAMA SHORTMAX VIP EXTRACTOR (CDP MODE)")
    print("==================================================")
    print("Pastikan Anda sudah menjalankan 'start_chrome.bat'")
    print("dan sudah login VIP di Vidrama pada browser tersebut.")
    print("--------------------------------------------------")
    
    with sync_playwright() as p:
        print("[+] Mencoba terhubung ke Chrome (port 9222)...")
        try:
            browser = p.chromium.connect_over_cdp("http://localhost:9222")
        except Exception as e:
            print("[!] Gagal terhubung ke Chrome. Pastikan Chrome dijalankan via 'start_chrome.bat'")
            print("Error:", e)
            return

        # Gunakan context pertama (karena kita connect ke browser yang sudah berjalan)
        context = browser.contexts[0]
        page = context.pages[0] if context.pages else context.new_page()

        print("[+] Menuju halaman drama target...")
        page.goto(DRAMA_URL, wait_until="networkidle")
        time.sleep(3)

        episodes_data = {}
        current_episode = None

        # Intercept network requests
        def handle_response(response):
            nonlocal current_episode
            if current_episode and '.m3u8' in response.url:
                if 'master' in response.url or '/index.m3u8' in response.url or 'stream' in response.url or 'playlist' in response.url:
                    if current_episode not in episodes_data:
                        episodes_data[current_episode] = response.url
                        print(f"  -> Mendapatkan URL m3u8 untuk Episode {current_episode}: {response.url[:80]}...")

        page.on("response", handle_response)

        print(f"\n[+] Mulai mengekstrak {TOTAL_EPISODES} episode...")

        # Pastikan list episode terlihat
        try:
            # Kadang ada tombol "Tampilkan Semua" atau semacamnya
            show_all = page.locator("xpath=//button[contains(text(), 'Semua')]").first
            if show_all.is_visible():
                show_all.click()
                time.sleep(1)
        except:
            pass

        for ep in range(1, TOTAL_EPISODES + 1):
            current_episode = ep
            print(f"[*] Memproses Episode {ep}...")
            
            try:
                # Cari div grid episode
                # Di vidrama bentuknya tombol kotak dengan angka
                episode_button = page.locator(f"xpath=//div[contains(@class, 'grid')]//button[normalize-space(text())='{ep}']").first
                if not episode_button.is_visible():
                    episode_button = page.locator(f"xpath=//div[contains(@class, 'grid')]//div[normalize-space(text())='{ep}']").first
                
                if episode_button.is_visible():
                    episode_button.scroll_into_view_if_needed()
                    time.sleep(0.5)
                    episode_button.click()
                    # Tunggu request m3u8 terpancing
                    time.sleep(2.5) 
                else:
                    print(f"  -> [!] Tombol Episode {ep} tidak ditemukan di halaman.")
            except Exception as e:
                print(f"  -> [!] Error mengklik Episode {ep}: {e}")
                
        print("\n[+] Ekstraksi selesai!")
        print(f"[+] Total m3u8 ditemukan: {len(episodes_data)} / {TOTAL_EPISODES}")
        
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump({
                "slug": DRAMA_SLUG,
                "url": DRAMA_URL,
                "total_extracted": len(episodes_data),
                "episodes": episodes_data
            }, f, indent=4)
            
        print(f"[+] Data disimpan ke: {OUTPUT_FILE}")
        
        browser.disconnect()

if __name__ == "__main__":
    run()
