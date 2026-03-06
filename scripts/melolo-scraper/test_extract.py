#!/usr/bin/env python3
"""Quick test: run extract_replay_data and show results without downloading"""
import json
from pathlib import Path

# Import directly
import importlib.util
spec = importlib.util.spec_from_file_location("auto_scraper", "auto_scraper.py")
mod = importlib.util.module_from_spec(spec)

# Patch __name__ to prevent main() execution
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

spec.loader.exec_module(mod)

data = mod.extract_replay_data(Path('melolo1.har'))

# Show sample metadata
print("\n\n=== SAMPLE METADATA ===\n")
for sid, info in list(data['series'].items())[:5]:
    print(f"Series: {sid}")
    print(f"  Title: {info['title']}")
    print(f"  Abstract: {info['abstract'][:100]}..." if info['abstract'] else "  Abstract: N/A")
    print(f"  Genres: {info.get('genres', [])}")
    print(f"  Author: {info.get('author', '')}")
    print(f"  Episodes: {info['total_episodes']}")
    print(f"  Cover: {info['cover_url'][:80]}..." if info['cover_url'] else "  Cover: N/A")
    print()
