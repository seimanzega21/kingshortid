"""
Comprehensive HAR Analysis - Find All Data
Fixed encoding issues
"""

import json
import sys
import io
from pathlib import Path
from collections import defaultdict
from urllib.parse import urlparse, parse_qs

# Fix encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

HAR_FILE = Path("fresh_capture.har")
OUTPUT_FILE = Path("har_analysis_report.txt")

print("=" * 70)
print("GOODSHORT HAR ANALYZER - COMPREHENSIVE ANALYSIS")
print("=" * 70)

# Load HAR
with open(HAR_FILE, 'r', encoding='utf-8') as f:
    har_data = json.load(f)

entries = har_data['log']['entries']
print(f"\nTotal Requests: {len(entries)}")

# Data containers
dramas_found = []
episodes_found = []
all_api_calls = []

# Analyze entries
for idx, entry in enumerate(entries):
    url = entry['request']['url']
    
    # Look for API calls
    if 'api-akm.goodreels.com' in url or 'api.goodreels.com' in url:
        try:
            response_text = entry['response']['content'].get('text', '')
            if response_text and len(response_text) > 20:
                # Try to parse JSON
                data = json.loads(response_text)
                
                # Store this API call
                api_info = {
                    'url': url,
                    'method': entry['request']['method'],
                    'status': entry['response']['status'],
                    'data': data
                }
                all_api_calls.append(api_info)
                
                # Look for book/drama data
                if 'data' in data:
                    datum = data['data']
                    
                    # Single drama/book object
                    if isinstance(datum, dict) and 'name' in datum:
                        dramas_found.append({
                            'id': datum.get('id'),
                            'name': datum.get('name'),
                            'full_data': datum
                        })
                    
                    # List of chapters/episodes
                    if isinstance(datum, list) and len(datum) > 0:
                        if 'name' in datum[0] or 'title' in datum[0]:
                            for item in datum:
                                episodes_found.append(item)
        
        except Exception as e:
            pass

print(f"\nAPI Calls Found: {len(all_api_calls)}")
print(f"Dramas Found: {len(dramas_found)}")
print(f"Episodes Found: {len(episodes_found)}")

# Save detailed report
report_lines = []
report_lines.append("=" * 70)
report_lines.append("GOODSHORT HAR ANALYSIS REPORT")
report_lines.append("=" * 70)
report_lines.append(f"\nTotal Requests in HAR: {len(entries)}")
report_lines.append(f"API Calls Captured: {len(all_api_calls)}")
report_lines.append(f"Dramas Found: {len(dramas_found)}")
report_lines.append(f"Episodes Found: {len(episodes_found)}")

# Detail dramas
if dramas_found:
    report_lines.append("\n" + "=" * 70)
    report_lines.append("DRAMAS CAPTURED")
    report_lines.append("=" * 70)
    for drama in dramas_found:
        report_lines.append(f"\nDrama: {drama['name']}")
        report_lines.append(f"  ID: {drama['id']}")
        
        # Show more details
        fd = drama['full_data']
        if 'genreName' in fd:
            report_lines.append(f"  Genre: {fd['genreName']}")
        if 'chapterCount' in fd:
            report_lines.append(f"  Episodes: {fd['chapterCount']}")
        if 'introduction' in fd:
            intro = fd['introduction'][:100]
            report_lines.append(f"  Description: {intro}...")

# Detail episodes sample
if episodes_found:
    report_lines.append("\n" + "=" * 70)
    report_lines.append(f"EPISODES CAPTURED (showing first 20 of {len(episodes_found)})")
    report_lines.append("=" * 70)
    for ep in episodes_found[:20]:
        name = ep.get('name', ep.get('title', 'Unknown'))
        ep_id = ep.get('id', 'N/A')
        seq = ep.get('sequence', ep.get('order', 'N/A'))
        report_lines.append(f"  Episode {seq}: {name} (ID: {ep_id})")

# Save full data
report_lines.append("\n" + "=" * 70)
report_lines.append("SAVING EXTRACTED DATA...")
report_lines.append("=" * 70)

# Save dramas
if dramas_found:
    dramas_file = Path("fresh_capture_analysis/dramas_extracted.json")
    dramas_file.parent.mkdir(exist_ok=True)
    with open(dramas_file, 'w', encoding='utf-8') as f:
        json.dump(dramas_found, f, indent=2, ensure_ascii=False)
    report_lines.append(f"Saved: {dramas_file}")

# Save episodes
if episodes_found:
    episodes_file = Path("fresh_capture_analysis/episodes_extracted.json")
    with open(episodes_file, 'w', encoding='utf-8') as f:
        json.dump(episodes_found, f, indent=2, ensure_ascii=False)
    report_lines.append(f"Saved: {episodes_file}")

# Save all API calls
api_file = Path("fresh_capture_analysis/all_api_calls.json")
with open(api_file, 'w', encoding='utf-8') as f:
    json.dump(all_api_calls, f, indent=2, ensure_ascii=False)
report_lines.append(f"Saved: {api_file}")

# Write report
with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    f.write('\n'.join(report_lines))

print("\n" + "=" * 70)
print("ANALYSIS COMPLETE!")
print("=" * 70)
print(f"\nFull report saved to: {OUTPUT_FILE}")
print("\nKey Findings:")
print(f"  - Dramas: {len(dramas_found)}")
print(f"  - Episodes: {len(episodes_found)}")
print(f"  - API Calls: {len(all_api_calls)}")
