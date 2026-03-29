import os, sys, requests, asyncio
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from netshort_pipeline import extract_drama_metadata_async, BACKEND_URL, log, get_episode_video_data_async, init_browser, _page, _browser
import urllib3
urllib3.disable_warnings()

async def fix_drama(drama_slug="gejolak-keluarga-konglomerat", drama_id="2034897075744800770"):
    log(f"Fetching {drama_slug}...")
    base_drama = {"id": drama_id, "slug": drama_slug, "title": "Gejolak Keluarga Konglomerat"}
    
    drama = await extract_drama_metadata_async(base_drama)
    desc = drama.get("description", "")
    genres = drama.get("genres", ["Drama", "Romantis"])
        
    log(f"Extracted Desc: {desc[:100]}...")
    log(f"Extracted Genres: {genres}")
        
    # Get drama ID from DB
    r_db = requests.get(f"{BACKEND_URL}/dramas?limit=1000&includeInactive=true", verify=False)
    db_id = None
    for d in r_db.json().get("data", []):
        if drama_slug in d.get("slug", "") or d.get("title") == base_drama["title"]:
            db_id = d.get("id")
            break
            
    if db_id and desc:
        log(f"Patching DB Drama ID {db_id}...")
        requests.patch(f"{BACKEND_URL}/dramas/{db_id}", json={"description": desc, "tags": genres})
    else:
        log("No DB ID or Desc!")
        
    # Get total eps from db to patch all available episodes
    if db_id:
        log("Fetching backend episodes to patch subtitles...")
        re_ep = requests.get(f"{BACKEND_URL}/dramas/{db_id}/episodes")
        episodes = re_ep.json().get("episodes", [])
        patched = 0
        for ep in episodes:
            ep_id = ep.get("id")
            ep_num = ep.get("episodeNumber")
            vtt_url = ep.get("videoUrl", "").replace(".mp4", ".vtt")
            if ".mp4" in ep.get("videoUrl", ""):
                sub_payload = {
                    "language": "Indonesian",
                    "label": "Bahasa Indonesia",
                    "url": vtt_url,
                    "isDefault": True
                }
                res = requests.post(f"{BACKEND_URL}/episodes/{ep_id}/subtitles", json=sub_payload)
                if res.status_code in [200, 201]:
                    patched += 1
        log(f"Patched subtitles for {patched}/{len(episodes)} episodes.")
            
    if _browser: await _browser.close()

if __name__ == "__main__":
    asyncio.run(fix_drama())
