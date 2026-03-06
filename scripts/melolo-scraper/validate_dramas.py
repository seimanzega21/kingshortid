#!/usr/bin/env python3
"""Validate all scraped dramas for completeness before R2 upload."""
import json, sys, io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stdout.reconfigure(line_buffering=True)

d = Path(__file__).parent / 'r2_ready' / 'melolo'
incomplete = []
complete_count = 0

for drama_dir in sorted(d.iterdir()):
    if not drama_dir.is_dir():
        continue
    slug = drama_dir.name
    issues = []

    meta_path = drama_dir / 'metadata.json'
    if not meta_path.exists():
        issues.append('NO metadata.json')
        incomplete.append((slug, issues, 0, 0))
        continue

    with open(meta_path, 'r', encoding='utf-8') as f:
        meta = json.load(f)

    for field in ['title', 'slug', 'description', 'total_episodes', 'episodes']:
        if not meta.get(field):
            issues.append('MISSING: ' + field)

    cover_name = meta.get('cover', 'cover.jpg')
    cover_path = drama_dir / cover_name
    if not cover_path.exists():
        issues.append('NO cover image')
    elif cover_path.stat().st_size < 1000:
        issues.append('Cover image too small (' + str(cover_path.stat().st_size) + 'B)')

    total_eps = meta.get('total_episodes', 0)
    ep_list = meta.get('episodes', [])

    ep_dir = drama_dir / 'episodes'
    actual = 0
    no_ts = 0
    if ep_dir.exists():
        for ef in sorted(ep_dir.iterdir()):
            if ef.is_dir():
                has_m3u8 = list(ef.glob('*.m3u8'))
                has_ts = list(ef.glob('*.ts'))
                if has_m3u8:
                    actual += 1
                    if not has_ts:
                        no_ts += 1

    if actual == 0:
        issues.append('NO episodes on disk (expected ' + str(total_eps) + ')')
    elif actual < total_eps * 0.5:
        issues.append('LOW episodes: ' + str(actual) + ' on disk vs ' + str(total_eps) + ' expected')

    if no_ts > 0:
        issues.append(str(no_ts) + ' episodes missing .ts segments')

    # Check episode number gaps in metadata
    ep_numbers = sorted([e.get('number', 0) for e in ep_list])
    if ep_numbers and ep_numbers[0] > 0:
        # Check if ep 1 is missing
        if 1 not in ep_numbers and ep_numbers[0] > 1:
            issues.append('Episode 1 missing from metadata (starts at ' + str(ep_numbers[0]) + ')')

    if issues:
        incomplete.append((slug, issues, total_eps, actual))
    else:
        complete_count += 1

print('COMPLETE: ' + str(complete_count))
print('ISSUES: ' + str(len(incomplete)))
print('')
for slug, iss, tot, act in incomplete:
    line = '  ' + slug + ' (expected:' + str(tot) + ' actual:' + str(act) + ')'
    print(line)
    for i in iss:
        print('    > ' + i)
