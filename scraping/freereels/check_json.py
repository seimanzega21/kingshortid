import json
data = json.loads(open('tab514_all_dramas.json', encoding='utf-8').read())
print(f'Total: {len(data)}')
print()
id_audio = sum(1 for v in data.values() if v.get('has_id_audio'))
dubbed   = sum(1 for v in data.values() if v.get('is_dubbed'))
print(f'  has_id_audio: {id_audio}')
print(f'  is_dubbed:    {dubbed}')
print()
for k, v in list(data.items())[:15]:
    print(f'  {v["title"][:40]} | id={v.get("has_id_audio")} dub={v.get("is_dubbed")}')
