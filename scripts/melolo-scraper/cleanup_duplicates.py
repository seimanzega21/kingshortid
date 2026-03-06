#!/usr/bin/env python3
"""Clean duplicate MicroDrama entries from DB, keeping only one per title."""
import requests, json, sys

API = "https://api.shortlovers.id/api"

def main():
    dry_run = "--execute" not in sys.argv
    
    print("=" * 60)
    print(f"  CLEANUP DUPLICATE DRAMAS ({'DRY RUN' if dry_run else 'EXECUTE'})")
    print("=" * 60)
    
    # Fetch all dramas
    all_dramas = []
    offset = 0
    while True:
        r = requests.get(f"{API}/dramas?limit=50&offset={offset}", timeout=15)
        data = r.json()
        dramas = data.get("dramas", data.get("data", []))
        if not dramas:
            break
        all_dramas.extend(dramas)
        offset += len(dramas)
        if offset >= data.get("total", 0):
            break
    
    print(f"\n  Total dramas in DB: {len(all_dramas)}")
    
    # Group by title
    by_title = {}
    for d in all_dramas:
        title = d.get("title", "").strip()
        by_title.setdefault(title, []).append(d)
    
    print(f"  Unique titles: {len(by_title)}")
    
    # Find duplicates
    to_delete = []
    for title, entries in by_title.items():
        if len(entries) > 1:
            # Keep the first one, delete the rest
            keep = entries[0]
            dupes = entries[1:]
            to_delete.extend(dupes)
            print(f"  {title}: {len(entries)} copies (keep id:{keep['id']}, delete {len(dupes)})")
    
    print(f"\n  Total to delete: {len(to_delete)}")
    
    if dry_run:
        print(f"\n  Run with --execute to delete duplicates!")
        return
    
    # Delete duplicates
    deleted = 0
    failed = 0
    for d in to_delete:
        try:
            r = requests.delete(f"{API}/dramas/{d['id']}", timeout=10)
            if r.status_code in [200, 204]:
                deleted += 1
            else:
                failed += 1
                print(f"    FAIL delete {d['id']}: {r.status_code}")
        except Exception as e:
            failed += 1
            print(f"    ERROR: {e}")
        
        if deleted % 50 == 0 and deleted > 0:
            print(f"    Deleted {deleted}/{len(to_delete)}...")

    print(f"\n  Deleted: {deleted}")
    print(f"  Failed: {failed}")
    
    # Verify
    r = requests.get(f"{API}/dramas?limit=1", timeout=10)
    final = r.json().get("total", 0)
    print(f"  Final DB count: {final}")


if __name__ == "__main__":
    main()
