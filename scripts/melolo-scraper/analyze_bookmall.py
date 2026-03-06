#!/usr/bin/env python3
"""Deep dive into bookmall cell/tab structure to find book_ids"""
import json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

with open('melolo4.har', 'r', encoding='utf-8') as f:
    har = json.load(f)

# 1. Analyze bookmall/tab response deeply
print("=" * 70)
print("  bookmall/tab/v1/ — DEEP STRUCTURE")
print("=" * 70)

for entry in har['log']['entries']:
    url = entry['request']['url']
    if 'bookmall/tab/v1/' not in url:
        continue
    text = entry['response']['content'].get('text', '')
    if not text: continue
    try: data = json.loads(text)
    except: continue
    
    tabs = data.get('data', {}).get('book_tab_infos', [])
    if isinstance(tabs, list):
        print(f"\n  book_tab_infos: list[{len(tabs)}]")
        for i, tab in enumerate(tabs):
            if not isinstance(tab, dict): continue
            print(f"\n  --- Tab {i} ---")
            print(f"    tab_name: {tab.get('tab_name','')}")
            print(f"    tab_type: {tab.get('tab_type','')}")
            print(f"    keys: {list(tab.keys())[:15]}")
            
            cells = tab.get('cells', [])
            if isinstance(cells, list) and cells:
                print(f"    cells: list[{len(cells)}]")
                for j, cell in enumerate(cells[:3]):
                    if not isinstance(cell, dict): continue
                    print(f"\n      cell[{j}] keys: {list(cell.keys())[:15]}")
                    print(f"      cell_id: {cell.get('cell_id','')}")
                    print(f"      cell_type: {cell.get('cell_type','')}")
                    print(f"      title: {cell.get('title','')}")
                    
                    # Look for books
                    books = cell.get('books', [])
                    if isinstance(books, list) and books:
                        print(f"      books: list[{len(books)}]")
                        for b in books[:3]:
                            print(f"        book_id={b.get('book_id','')}, name={b.get('book_name','')}")
                    
                    # Look for other nested structures containing dramas
                    for k, v in cell.items():
                        if isinstance(v, list) and v and isinstance(v[0], dict):
                            if k != 'books':
                                has_bid = any('book_id' in item for item in v[:5])
                                print(f"      {k}: list[{len(v)}] (has book_id: {has_bid})")
                                if has_bid:
                                    for item in v[:2]:
                                        print(f"        book_id={item.get('book_id','')}, name={item.get('book_name','')}")
            if i >= 2:
                break
    break

# 2. Analyze cell/change response deeply
print(f"\n\n{'=' * 70}")
print("  bookmall/cell/change/v1/ — DEEP CELL STRUCTURE")
print("=" * 70)

all_book_ids = set()
for idx, entry in enumerate(har['log']['entries']):
    url = entry['request']['url']
    if 'bookmall/cell/change/v1/' not in url:
        continue
    text = entry['response']['content'].get('text', '')
    if not text: continue
    try: data = json.loads(text)
    except: continue
    
    cell_data = data.get('data', {})
    cell = cell_data.get('cell', {})
    
    if idx < 3 or True:  # Show first 3
        print(f"\n  --- Call ---")
        print(f"    has_more: {cell_data.get('has_more')}")
        print(f"    next_offset: {cell_data.get('next_offset')}")
    
    if isinstance(cell, dict):
        if idx == 0:
            print(f"    cell keys: {list(cell.keys())[:15]}")
            print(f"    cell_id: {cell.get('cell_id','')}")
            print(f"    cell_type: {cell.get('cell_type','')}")
        
        books = cell.get('books', [])
        if isinstance(books, list) and books:
            if idx == 0:
                print(f"    books: list[{len(books)}]")
                print(f"    books[0] keys: {list(books[0].keys())[:15]}")
            for b in books:
                bid = str(b.get('book_id', ''))
                bname = b.get('book_name', '')
                if bid and len(bid) > 5:
                    all_book_ids.add(bid)
                    if idx == 0:
                        print(f"      book_id={bid}, name={bname}")
        else:
            # Check nested structures
            for k, v in cell.items():
                if isinstance(v, list) and v and isinstance(v[0], dict):
                    has_bid = any('book_id' in item for item in v[:5])
                    if has_bid and idx == 0:
                        print(f"    {k}: list[{len(v)}]")
                        for item in v[:2]:
                            bid = str(item.get('book_id',''))
                            if bid:
                                all_book_ids.add(bid)
                                print(f"      book_id={bid}, name={item.get('book_name','')}")

print(f"\n  TOTAL unique book_ids from ALL cell/change calls: {len(all_book_ids)}")
for bid in sorted(all_book_ids):
    print(f"    {bid}")

# 3. Also collect ALL book_ids from entire HAR for comparison
print(f"\n\n{'=' * 70}")
print("  ALL BOOK_IDS FROM ENTIRE HAR (any endpoint)")
print("=" * 70)

all_har_bids = set()
def _collect(obj, depth=0):
    if depth > 8: return
    if isinstance(obj, dict):
        bid = str(obj.get('book_id', ''))
        if bid and len(bid) > 10:
            all_har_bids.add((bid, obj.get('book_name','')))
        for v in obj.values():
            if isinstance(v, (dict, list)):
                _collect(v, depth+1)
    elif isinstance(obj, list):
        for item in obj[:100]:
            _collect(item, depth+1)

for entry in har['log']['entries']:
    text = entry['response']['content'].get('text', '')
    if not text: continue
    try: data = json.loads(text)
    except: continue
    _collect(data)

print(f"  Total unique book_ids in entire HAR: {len(all_har_bids)}")
for bid, bname in sorted(all_har_bids, key=lambda x: x[1]):
    print(f"    {bid}: {bname}")
