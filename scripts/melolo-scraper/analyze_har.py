#!/usr/bin/env python3
"""
MELOLO HAR ANALYZER
===================
Analyzes HAR files captured from the Melolo app via HTTP Toolkit.
Discovers API endpoints, data patterns, and CDN domains.

Usage:
    python analyze_har.py <harfile.har>
"""

import json
import sys
from pathlib import Path
from collections import defaultdict
from urllib.parse import urlparse


def analyze_har(har_file: Path):
    print(f"\n{'='*70}")
    print(f"MELOLO HAR ANALYZER")
    print(f"{'='*70}")
    print(f"File: {har_file.name}")
    print(f"Size: {har_file.stat().st_size / 1024 / 1024:.1f} MB\n")

    with open(har_file, 'r', encoding='utf-8') as f:
        har_data = json.load(f)

    entries = har_data['log']['entries']
    print(f"Total entries: {len(entries)}\n")

    # Categorize by domain
    domains = defaultdict(list)
    api_endpoints = defaultdict(list)
    content_types = defaultdict(int)
    video_urls = []
    image_urls = []
    json_responses = []

    for entry in entries:
        url = entry['request']['url']
        parsed = urlparse(url)
        domain = parsed.netloc
        path = parsed.path
        method = entry['request']['method']
        status = entry['response']['status']
        mime = entry['response']['content'].get('mimeType', '')
        size = entry['response']['content'].get('size', 0)

        domains[domain].append({
            'method': method,
            'path': path,
            'status': status,
            'mime': mime,
            'size': size,
            'url': url
        })

        content_types[mime] += 1

        # Detect video/HLS
        if '.m3u8' in url or '.ts' in url or 'video' in mime:
            video_urls.append(url)

        # Detect images
        if any(ext in url.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp']) or 'image' in mime:
            image_urls.append(url)

        # Detect JSON API responses
        if 'json' in mime and status == 200:
            text = entry['response']['content'].get('text', '')
            if text:
                try:
                    data = json.loads(text)
                    json_responses.append({
                        'url': url,
                        'path': path,
                        'method': method,
                        'data': data,
                        'size': len(text)
                    })
                except json.JSONDecodeError:
                    pass

    # Print domain summary
    print("=" * 50)
    print("DOMAINS DETECTED")
    print("=" * 50)
    for domain, reqs in sorted(domains.items(), key=lambda x: -len(x[1])):
        print(f"\n  {domain}: {len(reqs)} requests")
        # Show unique paths
        paths = set(r['path'] for r in reqs)
        for p in sorted(paths)[:10]:
            matching = [r for r in reqs if r['path'] == p]
            print(f"    {matching[0]['method']:6} {p}  [{matching[0]['status']}] ({len(matching)}x)")
        if len(paths) > 10:
            print(f"    ... and {len(paths) - 10} more paths")

    # Print content type summary
    print(f"\n{'='*50}")
    print("CONTENT TYPES")
    print("=" * 50)
    for ct, count in sorted(content_types.items(), key=lambda x: -x[1]):
        print(f"  {ct}: {count}")

    # Print video URLs
    print(f"\n{'='*50}")
    print(f"VIDEO/HLS URLs: {len(video_urls)}")
    print("=" * 50)
    # Show unique video domains
    video_domains = defaultdict(int)
    for u in video_urls:
        video_domains[urlparse(u).netloc] += 1
    for d, c in sorted(video_domains.items(), key=lambda x: -x[1]):
        print(f"  {d}: {c} segments")
    # Show sample
    for u in video_urls[:5]:
        print(f"  Sample: {u[:120]}...")

    # Print image URLs
    print(f"\n{'='*50}")
    print(f"IMAGE URLs: {len(image_urls)}")
    print("=" * 50)
    image_domains = defaultdict(int)
    for u in image_urls:
        image_domains[urlparse(u).netloc] += 1
    for d, c in sorted(image_domains.items(), key=lambda x: -x[1]):
        print(f"  {d}: {c} images")

    # Print JSON API responses (the gold mine)
    print(f"\n{'='*50}")
    print(f"JSON API RESPONSES: {len(json_responses)}")
    print("=" * 50)
    for resp in json_responses:
        print(f"\n  {resp['method']} {resp['url'][:100]}")
        print(f"  Size: {resp['size']} bytes")
        # Show top-level keys
        if isinstance(resp['data'], dict):
            keys = list(resp['data'].keys())
            print(f"  Keys: {keys[:10]}")
            # Look for drama/book/video related data
            data = resp['data']
            # Check for nested data
            if 'data' in data:
                inner = data['data']
                if isinstance(inner, dict):
                    print(f"  data.keys: {list(inner.keys())[:10]}")
                elif isinstance(inner, list) and len(inner) > 0:
                    print(f"  data[]: {len(inner)} items")
                    if isinstance(inner[0], dict):
                        print(f"  data[0].keys: {list(inner[0].keys())[:10]}")

    # Save full analysis
    output_dir = har_file.parent / "melolo_analysis"
    output_dir.mkdir(exist_ok=True)

    # Save JSON responses for detailed inspection
    analysis = {
        'domains': {d: len(r) for d, r in domains.items()},
        'content_types': dict(content_types),
        'video_count': len(video_urls),
        'image_count': len(image_urls),
        'api_responses': len(json_responses),
        'video_samples': video_urls[:20],
        'image_samples': image_urls[:20],
        'json_api_details': [
            {
                'url': r['url'],
                'method': r['method'],
                'size': r['size'],
                'top_keys': list(r['data'].keys()) if isinstance(r['data'], dict) else str(type(r['data'])),
                'data_preview': str(r['data'])[:500]
            }
            for r in json_responses
        ]
    }

    analysis_file = output_dir / "har_analysis.json"
    with open(analysis_file, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)
    print(f"\nAnalysis saved to: {analysis_file}")

    # Save full JSON responses for deep inspection
    full_responses_file = output_dir / "full_api_responses.json"
    with open(full_responses_file, 'w', encoding='utf-8') as f:
        json.dump([{
            'url': r['url'],
            'method': r['method'],
            'data': r['data']
        } for r in json_responses], f, indent=2, ensure_ascii=False)
    print(f"Full API responses saved to: {full_responses_file}")

    print(f"\n{'='*70}")
    print("NEXT STEP: Review melolo_analysis/full_api_responses.json")
    print("to identify drama metadata, episode list, and video URL patterns.")
    print(f"{'='*70}\n")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python analyze_har.py <harfile.har>")
        print("\nExample:")
        print("  python analyze_har.py HTTPToolkit_melolo.har")
        sys.exit(1)

    har_path = Path(sys.argv[1])
    if not har_path.exists():
        print(f"File not found: {har_path}")
        sys.exit(1)

    analyze_har(har_path)
