#!/usr/bin/env python3
"""
GoodShort mitmproxy Auto-Scraper - FINAL SOLUTION
Captures all GoodShort traffic and extracts complete drama data

Usage:
  1. Install: pip install mitmproxy
  2. Run: mitmdump -s goodshort_mitmproxy.py -p 8888
  3. Configure Android to use proxy: your_ip:8888
  4. Browse GoodShort app
  5. Data auto-saves to mitm_capture/
"""

import json
import os
import re
import time
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from mitmproxy import http, ctx

# Output directories
CAPTURE_DIR = Path(__file__).parent / "mitm_capture"
CAPTURE_DIR.mkdir(exist_ok=True)

# Data store
class GoodShortCapture:
    def __init__(self):
        self.dramas = {}
        self.episodes = defaultdict(list)  # bookId -> [episodes]
        self.video_urls = defaultdict(list)  # bookId -> [video urls with chapterId]
        self.covers = {}
        self.raw_responses = []
        self.start_time = datetime.now().isoformat()
        self.save_counter = 0
        
    def save(self):
        """Auto-save captured data"""
        self.save_counter += 1
        
        output = {
            "capture_info": {
                "start_time": self.start_time,
                "save_time": datetime.now().isoformat(),
                "save_count": self.save_counter
            },
            "stats": {
                "dramas": len(self.dramas),
                "episodes": sum(len(eps) for eps in self.episodes.values()),
                "video_urls": sum(len(urls) for urls in self.video_urls.values()),
                "covers": len(self.covers)
            },
            "dramas": self.dramas,
            "episodes": dict(self.episodes),
            "video_urls": dict(self.video_urls),
            "covers": self.covers
        }
        
        # Save main data
        main_file = CAPTURE_DIR / "goodshort_data.json"
        with open(main_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        # Save raw responses for debugging
        raw_file = CAPTURE_DIR / "raw_responses.json"
        with open(raw_file, 'w', encoding='utf-8') as f:
            json.dump(self.raw_responses[-100:], f, indent=2, ensure_ascii=False)  # Last 100
        
        ctx.log.info(f"💾 Saved: {len(self.dramas)} dramas, {output['stats']['episodes']} episodes")
        
        return output

# Global capture instance
capture = GoodShortCapture()

def response(flow: http.HTTPFlow):
    """Intercept all responses from GoodShort"""
    url = flow.request.pretty_url
    
    # Only process GoodShort traffic
    if 'goodreels.com' not in url and 'goodshort.com' not in url:
        return
    
    try:
        # === VIDEO SEGMENTS (.ts files) ===
        if '.ts' in url and '/mts/books/' in url:
            # Pattern: /mts/books/{x}/{bookId}/{chapterId}/{token}/720p/{filename}.ts
            match = re.search(r'/mts/books/\d+/(\d+)/(\d+)/([a-z0-9]+)/(\d+p)/([a-z0-9]+)_', url)
            if match:
                book_id = match.group(1)
                chapter_id = match.group(2)
                token = match.group(3)
                resolution = match.group(4)
                
                video_entry = {
                    "chapter_id": chapter_id,
                    "token": token,
                    "resolution": resolution,
                    "url": url,
                    "timestamp": datetime.now().isoformat()
                }
                
                # Check if this chapter already captured
                existing = [v for v in capture.video_urls[book_id] if v['chapter_id'] == chapter_id]
                if not existing:
                    capture.video_urls[book_id].append(video_entry)
                    ctx.log.info(f"📹 Video: Book {book_id} Chapter {chapter_id}")
            return
        
        # === COVER IMAGES ===
        if '/videobook/' in url and ('cover' in url or '.jpg' in url or '.png' in url):
            match = re.search(r'/videobook/(\d+)', url)
            if match:
                book_id = match.group(1)
                if book_id not in capture.covers or 'cover-' in url:
                    capture.covers[book_id] = url.split('?')[0]
                    ctx.log.info(f"📷 Cover: Book {book_id}")
            return
        
        # === API RESPONSES ===
        if 'api-akm.goodreels.com' in url or 'hwycclientreels' in url:
            content_type = flow.response.headers.get('content-type', '')
            if 'application/json' not in content_type and 'text/json' not in content_type:
                return
            
            try:
                body = flow.response.get_text()
                if not body:
                    return
                    
                data = json.loads(body)
                
                # Store raw response
                capture.raw_responses.append({
                    "url": url,
                    "timestamp": datetime.now().isoformat(),
                    "path": flow.request.path,
                    "data": data
                })
                
                # === BOOK DETAILS ===
                if '/book/' in url and data.get('code') == 1000:
                    book_data = data.get('data', {})
                    
                    # Handle nested book object
                    if 'book' in book_data:
                        book_data = book_data['book']
                    
                    book_id = str(book_data.get('bookId') or book_data.get('id') or '')
                    
                    if book_id and len(book_id) >= 10:
                        drama = {
                            "book_id": book_id,
                            "title": book_data.get('bookName') or book_data.get('name') or book_data.get('title'),
                            "author": book_data.get('pseudonym') or book_data.get('author') or book_data.get('authorName'),
                            "description": book_data.get('introduction') or book_data.get('desc') or book_data.get('synopsis'),
                            "cover_url": book_data.get('cover') or book_data.get('coverImg') or book_data.get('bookDetailCover'),
                            "chapter_count": book_data.get('chapterCount') or book_data.get('totalChapter') or 0,
                            "view_count": book_data.get('viewCount') or 0,
                            "rating": book_data.get('ratings') or book_data.get('score') or 0,
                            "genre": book_data.get('genreName') or book_data.get('category') or '',
                            "language": book_data.get('languageDisplay') or book_data.get('language') or 'Indonesian',
                            "status": book_data.get('writeStatus') or book_data.get('status') or '',
                            "captured_at": datetime.now().isoformat()
                        }
                        
                        # Update or create
                        if book_id not in capture.dramas:
                            capture.dramas[book_id] = drama
                            ctx.log.info(f"📚 NEW Drama: {drama['title']} (ID: {book_id})")
                        else:
                            # Merge - keep non-null values
                            for k, v in drama.items():
                                if v and (k not in capture.dramas[book_id] or not capture.dramas[book_id][k]):
                                    capture.dramas[book_id][k] = v
                        
                        capture.save()
                
                # === CHAPTER LIST ===
                if ('/chapter' in url or '/episode' in url) and data.get('code') == 1000:
                    chapters = data.get('data', [])
                    
                    # Handle nested list
                    if isinstance(chapters, dict):
                        chapters = chapters.get('list') or chapters.get('chapters') or []
                    
                    if isinstance(chapters, list) and len(chapters) > 0:
                        first_ch = chapters[0]
                        book_id = str(first_ch.get('bookId') or first_ch.get('book_id') or '')
                        
                        if not book_id:
                            # Try to extract from URL
                            match = re.search(r'bookId[=:](\d+)', url)
                            if match:
                                book_id = match.group(1)
                        
                        if book_id:
                            episode_list = []
                            for idx, ch in enumerate(chapters):
                                ep = {
                                    "chapter_id": str(ch.get('id') or ch.get('chapterId') or ch.get('chapter_id') or ''),
                                    "title": ch.get('name') or ch.get('title') or ch.get('chapterName') or f"Episode {idx + 1}",
                                    "sequence": ch.get('sequence') or ch.get('order') or ch.get('chapterOrder') or (idx + 1),
                                    "duration": ch.get('duration') or ch.get('time') or 0,
                                    "is_free": ch.get('free') == 1 or ch.get('isFree') == True or ch.get('is_free') == True
                                }
                                episode_list.append(ep)
                            
                            # Sort by sequence
                            episode_list.sort(key=lambda x: x['sequence'])
                            
                            capture.episodes[book_id] = episode_list
                            ctx.log.info(f"📋 Episodes: {len(episode_list)} for Book {book_id}")
                            
                            capture.save()
                
            except json.JSONDecodeError:
                pass
            except Exception as e:
                ctx.log.error(f"Parse error: {e}")
                
    except Exception as e:
        ctx.log.error(f"Error processing: {e}")


def done():
    """Called when mitmproxy shuts down"""
    final = capture.save()
    ctx.log.info("=" * 60)
    ctx.log.info("📊 FINAL CAPTURE SUMMARY")
    ctx.log.info("=" * 60)
    ctx.log.info(f"  Dramas: {final['stats']['dramas']}")
    ctx.log.info(f"  Episodes: {final['stats']['episodes']}")
    ctx.log.info(f"  Video URLs: {final['stats']['video_urls']}")
    ctx.log.info(f"  Covers: {final['stats']['covers']}")
    ctx.log.info(f"  Saved to: {CAPTURE_DIR}")
    ctx.log.info("=" * 60)


# Addon for mitmproxy
addons = [
    # This module itself is the addon
]
