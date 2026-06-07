# -*- coding: utf-8 -*-
import json

with open("d:/kingshortid/scratch/explore_dramawave_api_results.json", "r", encoding="utf-8") as f:
    data = json.load(f)

episodes = data.get("detail", {}).get("data", {}).get("list", [])
print(f"Checking last 5 episodes:")
for ep in episodes[-5:]:
    ep_no = ep.get("episodeNo")
    subtitles = ep.get("subtitles", [])
    languages = [s.get("language") for s in subtitles]
    print(f"Episode {ep_no:02d}: languages={languages}")
