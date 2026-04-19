import requests
import subprocess
import time

API_URL = "https://api.shortlovers.id/api/dramas?includeInactive=true&limit=9999"
HEADERS = {
    "X-Admin-Key": "00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14"
}

def main():
    print("Fetching active dramas...")
    response = requests.get(API_URL, headers=HEADERS)
    if not response.ok:
        print(f"Failed to fetch dramas. Status: {response.status_code}")
        return

    data = response.json()
    dramas = data.get("dramas", [])
    
    empty_dramas = [d for d in dramas if d.get("totalEpisodes", 0) == 0]
    print(f"Found {len(empty_dramas)} empty dramas.")
    
    for idx, drama in enumerate(empty_dramas):
        title = drama.get("title")
        print(f"\n========================================================")
        print(f"[{idx+1}/{len(empty_dramas)}] Fixing Missing Eps for: {title}")
        print(f"========================================================")
        
        try:
            # Call fix_missing_eps_universal.py
            cmd = ["python", "-u", "fix_missing_eps_universal.py", "--title", title, "--auto"]
            import os
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            process = subprocess.Popen(cmd, env=env, shell=True)
            process.communicate()
        except Exception as e:
            print(f"Error processing {title}: {e}")
            
        time.sleep(2)

if __name__ == "__main__":
    main()
