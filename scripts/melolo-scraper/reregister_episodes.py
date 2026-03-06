#!/usr/bin/env python3
"""Re-register R2 episodes into DB. ASCII-safe output."""
import boto3, os, re, sys, time, requests, json
from dotenv import load_dotenv

load_dotenv()

s3 = boto3.client('s3',
    endpoint_url=os.getenv('R2_ENDPOINT'),
    aws_access_key_id=os.getenv('R2_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('R2_SECRET_ACCESS_KEY'),
    region_name='auto'
)
BUCKET = 'shortlovers'
R2_PUBLIC = 'https://stream.shortlovers.id'
BACKEND = 'http://localhost:3001/api'
DRY_RUN = '--execute' not in sys.argv


def slugify(text):
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    return re.sub(r'-+', '-', text).strip('-')


def get_r2_episodes(slug):
    prefix = f"melolo/{slug}/"
    episodes = {}
    paginator = s3.get_paginator('list_objects_v2')
    for page in paginator.paginate(Bucket=BUCKET, Prefix=prefix):
        for obj in page.get('Contents', []):
            key = obj['Key']
            rel = key[len(prefix):]
            m = re.match(r'episodes/(\d+)/playlist\.m3u8$', rel)
            if m:
                ep_num = int(m.group(1))
                if ep_num not in episodes:
                    episodes[ep_num] = f"{R2_PUBLIC}/{key}"
                continue
            m = re.match(r'ep(\d+)/playlist\.m3u8$', rel)
            if m:
                ep_num = int(m.group(1))
                if ep_num not in episodes:
                    episodes[ep_num] = f"{R2_PUBLIC}/{key}"
                continue
            m = re.match(r'ep(\d+)\.mp4$', rel)
            if m:
                ep_num = int(m.group(1))
                if ep_num not in episodes:
                    episodes[ep_num] = f"{R2_PUBLIC}/{key}"
    return sorted(episodes.items())


def main():
    print("=" * 65)
    print("  RE-REGISTER R2 EPISODES -> DB")
    mode = "DRY RUN" if DRY_RUN else "EXECUTING"
    print(f"  Mode: {mode}")
    print("=" * 65)

    # Find dramas without episodes
    print("\n[INFO] Fetching DB dramas...")
    r = requests.get(f"{BACKEND}/dramas?limit=500", timeout=10)
    data = r.json()
    items = data if isinstance(data, list) else data.get("dramas", [])
    print(f"  Total in DB: {len(items)}")

    missing = []
    for d in items:
        did = d["id"]
        er = requests.get(f"{BACKEND}/dramas/{did}/episodes", timeout=5)
        eps = er.json() if er.status_code == 200 else []
        if isinstance(eps, dict):
            eps = eps.get("episodes", [])
        if len(eps) == 0:
            missing.append(d)

    print(f"  Missing episodes: {len(missing)}")

    if not missing:
        print("  Nothing to do!")
        return

    total_ok = 0
    total_fail = 0
    results = []

    for i, drama in enumerate(missing, 1):
        title = drama["title"]
        did = drama["id"]
        slug = slugify(title)
        print(f"\n[{i}/{len(missing)}] {title}")
        print(f"  Slug: {slug}")

        r2_eps = get_r2_episodes(slug)
        if not r2_eps:
            print(f"  [MISS] No episodes found on R2")
            results.append({"t": title, "s": "NO_R2", "c": 0, "f": 0})
            continue

        print(f"  Found {len(r2_eps)} episodes on R2")

        if DRY_RUN:
            print(f"  [DRY] Would register {len(r2_eps)} episodes")
            results.append({"t": title, "s": "DRY", "c": len(r2_eps), "f": 0})
            total_ok += len(r2_eps)
        else:
            ok = 0
            fail = 0
            for ep_num, video_url in r2_eps:
                payload = {
                    "dramaId": did,
                    "episodeNumber": ep_num,
                    "title": f"Episode {ep_num}",
                    "videoUrl": video_url,
                    "duration": 0,
                    "isVip": False,
                    "coinPrice": 0,
                }
                try:
                    resp = requests.post(f"{BACKEND}/episodes", json=payload, timeout=10)
                    if resp.status_code in [200, 201]:
                        ok += 1
                    elif resp.status_code == 429:
                        # Rate limited - wait and retry
                        time.sleep(2)
                        resp2 = requests.post(f"{BACKEND}/episodes", json=payload, timeout=10)
                        if resp2.status_code in [200, 201]:
                            ok += 1
                        else:
                            fail += 1
                    else:
                        fail += 1
                        if fail <= 2:
                            print(f"    FAIL ep{ep_num}: {resp.status_code} {resp.text[:80]}")
                except Exception as e:
                    fail += 1
                    if fail <= 2:
                        print(f"    ERROR ep{ep_num}: {e}")
                time.sleep(0.15)  # 150ms between episodes to avoid rate limit

                if ok % 20 == 0 and ok > 0:
                    print(f"    ...{ok}/{len(r2_eps)}", flush=True)

            print(f"  OK: {ok}, FAIL: {fail}")
            results.append({"t": title, "s": "OK" if fail == 0 else "PARTIAL", "c": ok, "f": fail})
            total_ok += ok
            total_fail += fail

        time.sleep(0.2)

    # Summary
    print(f"\n{'='*65}")
    print(f"  SUMMARY: Registered={total_ok}, Failed={total_fail}")
    print(f"{'='*65}")
    for r in results:
        tag = {"DRY": "[DRY]", "OK": "[ OK]", "PARTIAL": "[WRN]", "NO_R2": "[---]"}.get(r["s"], "[???]")
        print(f"  {tag} {r['t']}: {r['c']} eps" + (f" ({r['f']} failed)" if r["f"] > 0 else ""))


if __name__ == "__main__":
    main()
