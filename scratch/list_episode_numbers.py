# -*- coding: utf-8 -*-
import json

with open("d:/kingshortid/scratch/explore_dramawave_api_results.json", "r", encoding="utf-8") as f:
    data = json.load(f)

episodes = data.get("detail", {}).get("data", {}).get("list", [])
for idx, ep in enumerate(episodes):
    print(f"Index {idx}: episodeNo={ep.get('episodeNo')}, chapterIndex={ep.get('chapterIndex')}, isCharge={ep.get('isCharge')}, id={ep.get('chapterId')}")
