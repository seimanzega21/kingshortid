#!/usr/bin/env python3
"""
Deep validation of ALL dramas on R2
Checks: metadata, cover, episodes, HLS accessibility
"""
import boto3, os, json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

s3 = boto3.client('s3',
    endpoint_url=os.getenv('R2_ENDPOINT'),
    aws_access_key_id=os.getenv('R2_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('R2_SECRET_ACCESS_KEY'),
    region_name='auto'
)

BUCKET = 'shortlovers'
LOCAL_DIR = Path('r2_ready/melolo')

print("=" * 80)
print("  DEEP R2 VALIDATION - ALL DRAMAS")
print("=" * 80)

def get_r2_files(prefix):
    """Get all files under a prefix"""
    files = set()
    paginator = s3.get_paginator('list_objects_v2')
    try:
        for page in paginator.paginate(Bucket=BUCKET, Prefix=prefix):
            for obj in page.get('Contents', []):
                # Store relative path from drama folder
                rel = obj['Key'][len(prefix):].lstrip('/')
                files.add(rel)
    except:
        pass
    return files

def check_drama(slug):
    """Deep check for one drama"""
    prefix = f"melolo/{slug}/"
    files = get_r2_files(prefix)
    
    issues = []
    warnings = []
    
    # 1. Check metadata
    if 'metadata.json' not in files:
        issues.append("Missing metadata.json")
        return {'slug': slug, 'status': 'CRITICAL', 'issues': issues, 'warnings': warnings, 'episodes': 0}
    
    # Get local metadata for comparison
    local_meta_path = LOCAL_DIR / slug / 'metadata.json'
    if local_meta_path.exists():
        with open(local_meta_path, 'r', encoding='utf-8') as f:
            meta = json.load(f)
            expected_episodes = meta.get('captured_episodes', 0)
            title = meta.get('title', slug)
    else:
        issues.append("Local metadata not found")
        expected_episodes = 0
        title = slug
    
    # 2. Check cover
    has_cover = any(f.startswith('cover.') for f in files)
    if not has_cover:
        issues.append("Missing cover image")
    
    # 3. Check episodes
    episode_dirs = set()
    for f in files:
        if f.startswith('episodes/') and '/' in f[9:]:
            ep_num = f.split('/')[1]
            if ep_num.isdigit():
                episode_dirs.add(ep_num)
    
    actual_episodes = len(episode_dirs)
    
    if actual_episodes == 0:
        issues.append("No episodes found")
    elif expected_episodes > 0 and actual_episodes < expected_episodes:
        missing = expected_episodes - actual_episodes
        issues.append(f"Missing {missing} episodes (has {actual_episodes}/{expected_episodes})")
    
    # 4. Check HLS files for each episode
    incomplete_episodes = []
    for ep_num in sorted(episode_dirs):
        ep_prefix = f"episodes/{ep_num}/"
        ep_files = [f for f in files if f.startswith(ep_prefix)]
        
        # Check for playlist
        has_playlist = any(f.endswith('playlist.m3u8') for f in ep_files)
        if not has_playlist:
            incomplete_episodes.append(f"Ep {ep_num}: no playlist.m3u8")
            continue
        
        # Check for segments
        segments = [f for f in ep_files if f.endswith('.ts')]
        if len(segments) == 0:
            incomplete_episodes.append(f"Ep {ep_num}: no .ts segments")
    
    if incomplete_episodes:
        issues.extend(incomplete_episodes[:3])  # Show first 3
        if len(incomplete_episodes) > 3:
            issues.append(f"... and {len(incomplete_episodes)-3} more episodes")
    
    # Determine status
    if issues:
        if 'metadata' in str(issues) or 'No episodes' in str(issues):
            status = 'CRITICAL'
        else:
            status = 'WARNING'
    else:
        status = 'OK'
    
    return {
        'slug': slug,
        'title': title,
        'status': status,
        'issues': issues,
        'warnings': warnings,
        'episodes': actual_episodes,
        'expected': expected_episodes
    }

# Get all dramas from R2
print("\n📡 Fetching drama list from R2...")
r2_dramas = set()
paginator = s3.get_paginator('list_objects_v2')
for page in paginator.paginate(Bucket=BUCKET, Prefix='melolo/', Delimiter='/'):
    for prefix in page.get('CommonPrefixes', []):
        slug = prefix['Prefix'].split('/')[1]
        if slug:
            r2_dramas.add(slug)

print(f"   Found {len(r2_dramas)} dramas on R2\n")

# Validate each drama
results = []
for i, slug in enumerate(sorted(r2_dramas), 1):
    print(f"[{i}/{len(r2_dramas)}] Checking {slug}...", end='', flush=True)
    result = check_drama(slug)
    results.append(result)
    
    if result['status'] == 'OK':
        print(f" ✅ {result['episodes']} eps")
    elif result['status'] == 'WARNING':
        print(f" ⚠️  {result['issues'][0]}")
    else:
        print(f" ❌ {result['issues'][0]}")

# Summary report
print("\n" + "=" * 80)
print("  VALIDATION SUMMARY")
print("=" * 80)

ok_count = sum(1 for r in results if r['status'] == 'OK')
warning_count = sum(1 for r in results if r['status'] == 'WARNING')
critical_count = sum(1 for r in results if r['status'] == 'CRITICAL')

print(f"\n✅ OK:       {ok_count:3} dramas")
print(f"⚠️  WARNING: {warning_count:3} dramas")
print(f"❌ CRITICAL: {critical_count:3} dramas")

# Detail report
if warning_count > 0:
    print("\n" + "-" * 80)
    print("  WARNINGS")
    print("-" * 80)
    for r in results:
        if r['status'] == 'WARNING':
            print(f"\n⚠️  {r['title']}")
            print(f"   Slug: {r['slug']}")
            print(f"   Episodes: {r['episodes']}/{r['expected']}")
            for issue in r['issues']:
                print(f"   - {issue}")

if critical_count > 0:
    print("\n" + "-" * 80)
    print("  CRITICAL ISSUES")
    print("-" * 80)
    for r in results:
        if r['status'] == 'CRITICAL':
            print(f"\n❌ {r.get('title', r['slug'])}")
            print(f"   Slug: {r['slug']}")
            for issue in r['issues']:
                print(f"   - {issue}")

# Save report
report_path = Path('r2_validation_report.json')
with open(report_path, 'w', encoding='utf-8') as f:
    json.dump({
        'summary': {
            'total': len(results),
            'ok': ok_count,
            'warnings': warning_count,
            'critical': critical_count
        },
        'dramas': results
    }, f, indent=2, ensure_ascii=False)

print(f"\n📄 Full report saved: {report_path}")
print("\n" + "=" * 80)
