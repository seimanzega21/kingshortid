import os
from dotenv import load_dotenv
import requests

load_dotenv(r"d:\kingshortid\cf-backend\.env.production")

try:
    r = requests.get("https://admin.shortlovers.id/api/dramas?includeInactive=true&limit=50")
    data = r.json()
    dramas = data.get("dramas", [])
    
    print("Top 10 Dramas in Backend (include Inactive):")
    for d in dramas[:10]:
        status_pub = "Tayang" if d.get("isActive") else "Pending"
        print(f"- {d.get('title')} | Eps: {d.get('totalEpisodes')} | Publikasi: {status_pub}")
        
    pending = [d for d in dramas if not d.get("isActive")]
    print(f"\nTotal Pending Dramas shown: {len(pending)}")
except Exception as e:
    print(e)
