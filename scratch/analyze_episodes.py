# -*- coding: utf-8 -*-
import json

with open("d:/kingshortid/scratch/explore_dramawave_api_results.json", "r", encoding="utf-8") as f:
    data = json.load(f)

detail_data = data.get("detail", {}).get("data", {})
episodes = detail_data.get("list", [])
print(f"Total episodes in list: {len(episodes)}")

for ep in episodes[:5] + episodes[-5:]:
    ep_no = ep.get("episodeNo")
    video_path = ep.get("videoPath")
    is_charge = ep.get("isCharge")
    subtitles = ep.get("subtitles", [])
    has_id = any(s.get("language") == "id-ID" for s in subtitles)
    print(f"Episode {ep_no:02d}: isCharge={is_charge}, hasVideo={bool(video_path)}, subtitleCount={len(subtitles)}, hasIndoSub={has_id}")
    if video_path:
        print(f"  Video: {video_path[:80]}...")
