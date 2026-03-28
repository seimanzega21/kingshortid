import os, sys, requests, asyncio
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from netshort_pipeline import extract_dramas_from_provider_page, extract_drama_metadata, BACKEND_URL, log, get_episode_video_data_async, init_browser, _browser
import urllib3
urllib3.disable_warnings()

async def fix_drama(drama_slug="gejolak-asmara-di-ambang-kegelapan", drama_id="1566"):
    log(f"Fetching {drama_slug}...")
    base_drama = {"id": drama_id, "slug": drama_slug, "title": "Gejolak Asmara Di Ambang Kegelapan"}
    
    # Extract meta
    drama = extract_drama_metadata(base_drama)
    log(f"Extracted Desc: {drama.get('description')}")
    log(f"Extracted Genre: {drama.get('genres')}")
    
    # 1. Patch Drama
    drama_payload = {
        "description": drama.get("description", ""),
        "tags": drama.get("genres", ["Drama"])
    }
    
    # Get drama ID from DB
    r = requests.get(f"{BACKEND_URL}/dramas?limit=100", verify=False)
    db_id = None
    for d in r.json().get("data", []):
        if drama_slug in d.get("slug", "") or d.get("title") == base_drama["title"]:
            db_id = d.get("id")
            break
            
    if not db_id:
        log("Drama not found in DB!")
        return
        
    log(f"Patching DB Drama ID {db_id}...")
    requests.patch(f"{BACKEND_URL}/dramas/{db_id}", json=drama_payload)
    
    # 2. Extract Subtitle URL for Episode 1 using Playwright Fallback
    log("Fetching Ep 1 subtitle...")
    video_data = await get_episode_video_data_async(drama_id, drama_slug, 1)
    sub_url = video_data.get("subtitle_url")
    log(f"Found Sub: {sub_url}")
    
    if sub_url:
        # Get episode ID
        re_ep = requests.get(f"{BACKEND_URL}/dramas/{db_id}/episodes")
        episodes = re_ep.json().get("episodes", [])
        for ep in episodes:
            ep_id = ep.get("id")
            log(f"Patching Epi {ep.get('episodeNumber')} ({ep_id})...")
            # Replace MP4 with VTT
            vtt_url = ep.get("videoUrl", "").replace(".mp4", ".vtt")
            sub_payload = {
                "language": "Indonesian",
                "label": "Bahasa Indonesia",
                "url": vtt_url,
                "isDefault": True
            }
            res = requests.post(f"{BACKEND_URL}/episodes/{ep_id}/subtitles", json=sub_payload)
            log(f"  Sub Status: {res.status_code}")
            
    if _browser: await _browser.close()

if __name__ == "__main__":
    asyncio.run(fix_drama())
