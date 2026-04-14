import os
from dotenv import load_dotenv
import requests

load_dotenv(r"d:\kingshortid\cf-backend\.env.production")

with open('clean.txt', 'w', encoding='utf-8') as f:
    try:
        r = requests.get("https://api.shortlovers.id/api/dramas?includeInactive=true&limit=20")
        data = r.json()
        dramas = data.get("dramas", [])
        
        f.write("Top 20 Dramas in Backend (include Inactive):\n")
        for i, d in enumerate(dramas):
            status_pub = "Tayang" if d.get("isActive") else "Pending"
            f.write(f"{i+1}. {d.get('title')} | Eps: {d.get('totalEpisodes')} | Publikasi: {status_pub}\n")
            
    except Exception as e:
        f.write(str(e))
