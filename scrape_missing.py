import os, sys, time, requests

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from scrape_dramabox3 import process_episode

def retry_missing():
    print("Retrying missing episodes for 'Mahkota Tersembunyi'")
    for ep in range(35, 62):
        print(f"Retrying EP {ep}...")
        success = process_episode('42000006950', 's4im654wydfff5j5sptedali', ep, 'mahkota-tersembunyi')
        if not success:
            print(f"FAILED again for EP {ep}")
        time.sleep(1) # wait to avoid ban
        
    print("\nRetrying missing episodes for 'Di Balik Ruang Rahasia CEO'")
    for ep in range(49, 66):
        print(f"Retrying EP {ep}...")
        success = process_episode('42000008521', 'w4haci51vhdjxiascjb14i54', ep, 'di-balik-ruang-rahasia-ceo')
        if not success:
            print(f"FAILED again for EP {ep}")
        time.sleep(1)

if __name__ == '__main__':
    retry_missing()
