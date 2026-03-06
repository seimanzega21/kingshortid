#!/usr/bin/env python3
"""Re-register missing R2 episodes for a specific drama into DB."""
import boto3, os, re, sys, time, requests
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

DRAMA_ID = 'cmlnybvzj019gw3jy93ay8l5v'
DRAMA_SLUG = 'sang-penguasa-tertinggi'


def get_r2_episodes(slug):
    prefix = f"melolo/{slug}/"
    episodes = {}
    paginator = s3.get_paginator('list_objects_v2')
    for page in paginator.paginate(Bucket=BUCKET, Prefix=prefix):
        for obj in page.get('Contents', []):
            key = obj['Key']
            rel = key[len(prefix):]
            # Match episodes/N/playlist.m3u8
            m = re.match(r'episodes/(\d+)/playlist\.m3u8$', rel)
            if m:
                ep_num = int(m.group(1))
                if ep_num not in episodes:
                    episodes[ep_num] = f"{R2_PUBLIC}/{key}"
                continue
            # Match epN/playlist.m3u8
            m = re.match(r'ep(\d+)/playlist\.m3u8$', rel)
            if m:
                ep_num = int(m.group(1))
                if ep_num not in episodes:
                    episodes[ep_num] = f"{R2_PUBLIC}/{key}"
                continue
            # Match epN.mp4
            m = re.match(r'ep(\d+)\.mp4$', rel)
            if m:
                ep_num = int(m.group(1))
                if ep_num not in episodes:
                    episodes[ep_num] = f"{R2_PUBLIC}/{key}"
    return sorted(episodes.items())


def get_db_episodes(drama_id):
    r = requests.get(f"{BACKEND}/dramas/{drama_id}", timeout=10)
    data = r.json()
    eps = data.get('episodes', [])
    return set(ep['episodeNumber'] for ep in eps)


def main():
    print("=" * 65)
    print("  RE-REGISTER MISSING EPISODES: Sang Penguasa Tertinggi")
    print("=" * 65)

    # Get existing DB episodes
    print("\n[1] Checking DB episodes...")
    db_eps = get_db_episodes(DRAMA_ID)
    print(f"  Episodes in DB: {len(db_eps)} -> {sorted(db_eps)[:15]}...")

    # Get R2 episodes
    print("\n[2] Scanning R2...")
    r2_eps = get_r2_episodes(DRAMA_SLUG)
    print(f"  Episodes in R2: {len(r2_eps)}")

    # Find missing
    r2_nums = set(ep[0] for ep in r2_eps)
    missing_nums = r2_nums - db_eps
    print(f"\n[3] Missing from DB: {len(missing_nums)} episodes")

    if not missing_nums:
        print("  Nothing to register!")
        return

    # Register missing
    print(f"\n[4] Registering {len(missing_nums)} episodes...")
    ok = 0
    fail = 0
    r2_map = dict(r2_eps)

    for ep_num in sorted(missing_nums):
        video_url = r2_map[ep_num]
        payload = {
            "dramaId": DRAMA_ID,
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
                time.sleep(2)
                resp2 = requests.post(f"{BACKEND}/episodes", json=payload, timeout=10)
                if resp2.status_code in [200, 201]:
                    ok += 1
                else:
                    fail += 1
                    print(f"  FAIL ep{ep_num}: {resp2.status_code}")
            else:
                fail += 1
                print(f"  FAIL ep{ep_num}: {resp.status_code} {resp.text[:100]}")
        except Exception as e:
            fail += 1
            print(f"  ERROR ep{ep_num}: {e}")
        time.sleep(0.15)

        if ok % 20 == 0 and ok > 0:
            print(f"  ...registered {ok}/{len(missing_nums)}", flush=True)

    # Update totalEpisodes
    total = len(db_eps) + ok
    print(f"\n[5] Updating totalEpisodes to {total}...")
    try:
        requests.put(f"{BACKEND}/dramas/{DRAMA_ID}", json={"totalEpisodes": total}, timeout=10)
    except:
        print("  (Could not update totalEpisodes, update manually)")

    print(f"\n{'='*65}")
    print(f"  DONE: Registered={ok}, Failed={fail}, Total={total}")
    print(f"{'='*65}")


if __name__ == "__main__":
    main()
