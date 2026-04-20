import sys, requests, os, asyncio
from pathlib import Path

# Add current dir to path to import netshort_pipeline
sys.path.append(str(Path(__file__).parent))
import netshort_pipeline

def main():
    drama_id = "2043863926390652929"
    slug = "demi-ada-di-sisimu"
    title = "Demi Ada di Sisimu"
    
    base_drama = {
        'slug': slug,
        'id': drama_id,
        'title': title,
        'cover_url': ''
    }
    
    print(f"Scraping single: {title}")
    # 1. Get full metadata
    drama = netshort_pipeline.extract_drama_metadata(base_drama)
    if not drama:
        print("Failed to extract metadata")
        return
        
    total_eps = drama["total_episodes"]
    if total_eps < 1: total_eps = 80 # The screenshot shows 80 total episodes
    
    print(f"Info: {total_eps} eps | {drama.get('genres')} | {drama.get('description')[:50]}...")
    
    TEMP_DIR = Path("C:/tmp/netshort_mp4")
    drama_temp = TEMP_DIR / drama["slug"]
    drama_temp.mkdir(parents=True, exist_ok=True)
    
    # Push drama upfront
    cover_url = f"{netshort_pipeline.R2_PUBLIC}/{netshort_pipeline.R2_PREFIX}/{drama['slug']}/cover.webp"
    desc = drama.get("description", "").strip()
    if len(desc) < 10: desc = "No description available for this drama at the moment."
        
    drama_payload = {
        "title": drama["title"],
        "description": desc,
        "status": "Completed", # It says "Completed" on screenshot
        "provider": "Netshort",
        "isActive": False,
        "tags": drama.get("genres", ["Drama", "Romantis"]),
        "cover": cover_url,
        "coverUrl": cover_url,
        "totalEpisodes": total_eps
    }
    
    print("Pushing to Backend API for Drama ID...")
    resp = requests.post(f"{netshort_pipeline.BACKEND_URL}/dramas", json=drama_payload, timeout=20)
    kingshort_drama_id = None
    if resp.status_code in [200, 201]:
        kingshort_drama_id = resp.json().get("id")
        print(f"Created Drama ID in DB: {kingshort_drama_id}")
        requests.patch(f"{netshort_pipeline.BACKEND_URL}/dramas/{kingshort_drama_id}", json={"isActive": False}, timeout=10)
    else:
        print(f"Failed to create drama! {resp.text}")
        return
    
    print("Uploading Cover...")
    netshort_pipeline.upload_cover(drama["cover_url"], drama["slug"])
    
    success_eps = 0
    ep_num = 1
    while ep_num <= total_eps:
        try:
            result = netshort_pipeline.process_episode(drama["id"], drama["slug"], ep_num, drama_temp, total_eps)
            if result:
                success_eps += 1
                real_max = result.get("maxEps", total_eps)
                if real_max > total_eps:
                    total_eps = real_max
                    drama["total_episodes"] = total_eps
                    # We might want to patch the DB totalModels here
                    requests.patch(f"{netshort_pipeline.BACKEND_URL}/dramas/{kingshort_drama_id}", json={"totalEpisodes": total_eps}, timeout=10)
                    
                vtt_url = result["videoUrl"].replace(".mp4", ".vtt") if ".mp4" in result["videoUrl"] else ""
                ep_payload = {
                    "dramaId": kingshort_drama_id,
                    "episodeNumber": result["number"],
                    "videoUrl": result["videoUrl"],
                    "duration": 0
                }
                er = requests.post(f"{netshort_pipeline.BACKEND_URL}/episodes", json=ep_payload, timeout=10)
                if er.status_code in [200, 201]:
                    ep_id = er.json().get("id")
                    if ep_id and vtt_url:
                        sub_payload = {"language": "Indonesian", "label": "Bahasa Indonesia", "url": vtt_url, "isDefault": True}
                        requests.post(f"{netshort_pipeline.BACKEND_URL}/episodes/{ep_id}/subtitles", json=sub_payload, timeout=10)
            else:
                print(f"Failed to process episode {ep_num}")
        except Exception as e:
            print(f"Error ep {ep_num}: {e}")
        ep_num += 1

    print(f"Success. Done scraping {success_eps} episodes!")

if __name__ == "__main__":
    main()
