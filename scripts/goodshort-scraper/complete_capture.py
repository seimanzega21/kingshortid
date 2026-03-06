"""
COMPLETE CAPTURE - Gets EVERYTHING
===================================
- Book metadata (title, cover, description, genre, author)
- Chapter list with titles
- Video URLs
- All API responses

This is the DEFINITIVE capture script - no more missing data!
"""
import frida
import json
import time
import re
from pathlib import Path
from datetime import datetime

class CompleteCapture:
    def __init__(self):
        self.data = {
            'capturedAt': None,
            'books': {},      # bookId -> {title, cover, description, genre, ...}
            'chapters': {},   # bookId -> [{chapterId, title, ...}, ...]
            'videoUrls': [],  # [{url, bookId, chapterId, resolution, ...}, ...]
            'rawApiResponses': [],  # All API response bodies
        }
        self.stats = {'responses': 0, 'videos': 0, 'books': 0, 'chapters': 0}
    
    def on_message(self, message, data):
        if message['type'] == 'send':
            payload = message['payload']
            
            if isinstance(payload, dict):
                ptype = payload.get('type', '')
                
                if ptype == 'api_response':
                    self._process_api_response(payload)
                elif ptype == 'video_url':
                    self._process_video_url(payload)
                elif ptype == 'book_detail':
                    self._process_book_detail(payload)
                elif ptype == 'log':
                    print(f"[LOG] {payload.get('msg', '')}")
                else:
                    print(f"[{ptype}] {str(payload)[:80]}...")
            else:
                print(str(payload)[:100])
    
    def _process_api_response(self, payload):
        body = payload.get('body', '')
        url = payload.get('url', '')
        
        self.stats['responses'] += 1
        
        # Store raw response
        self.data['rawApiResponses'].append({
            'url': url,
            'body': body[:10000]  # Limit size
        })
        
        # Try to parse as JSON and extract book data
        try:
            # Remove BaseEntity wrapper if present
            if body.startswith('BaseEntity'):
                return
            
            obj = json.loads(body)
            
            if obj.get('success') or obj.get('status') == 0:
                data_obj = obj.get('data', obj)
                
                # Check for book list (home/index)
                if 'bookList' in str(data_obj) or 'shortList' in str(data_obj):
                    self._extract_books(data_obj)
                
                # Check for chapter list
                if 'chapterList' in str(data_obj) or 'list' in str(data_obj):
                    self._extract_chapters(data_obj)
                    
        except json.JSONDecodeError:
            pass
    
    def _extract_books(self, data):
        """Extract book metadata from API response"""
        book_list = data.get('bookList', data.get('shortList', data.get('list', [])))
        
        if not isinstance(book_list, list):
            return
        
        for book in book_list:
            if not isinstance(book, dict):
                continue
            
            book_id = str(book.get('bookId', book.get('id', '')))
            if not book_id:
                continue
            
            # Extract all available metadata
            book_data = {
                'bookId': book_id,
                'title': book.get('bookName', book.get('name', book.get('title', ''))),
                'cover': book.get('coverUrl', book.get('cover', book.get('picUrl', ''))),
                'description': book.get('description', book.get('synopsis', book.get('intro', ''))),
                'author': book.get('authorName', book.get('author', '')),
                'genre': book.get('categoryName', book.get('genre', book.get('category', ''))),
                'tags': book.get('tags', book.get('labels', [])),
                'totalChapters': book.get('chapterCount', book.get('totalChapters', 0)),
                'viewCount': book.get('viewCount', book.get('playCount', 0)),
                'status': book.get('status', book.get('bookStatus', '')),
            }
            
            # Only add if we have at least title or cover
            if book_data['title'] or book_data['cover']:
                self.data['books'][book_id] = book_data
                self.stats['books'] += 1
                print(f"[BOOK] {book_id}: {book_data['title'][:30] if book_data['title'] else 'No title'}")
    
    def _extract_chapters(self, data):
        """Extract chapter list from API response"""
        chapter_list = data.get('chapterList', data.get('list', []))
        
        if not isinstance(chapter_list, list):
            return
        
        for chapter in chapter_list:
            if not isinstance(chapter, dict):
                continue
            
            book_id = str(chapter.get('bookId', ''))
            chapter_id = str(chapter.get('chapterId', chapter.get('id', '')))
            
            if not chapter_id:
                continue
            
            chapter_data = {
                'chapterId': chapter_id,
                'bookId': book_id,
                'title': chapter.get('chapterName', chapter.get('title', chapter.get('name', ''))),
                'index': chapter.get('chapterIndex', chapter.get('index', 0)),
                'duration': chapter.get('duration', 0),
                'isVip': chapter.get('isVip', chapter.get('vip', False)),
            }
            
            if book_id:
                if book_id not in self.data['chapters']:
                    self.data['chapters'][book_id] = []
                
                # Avoid duplicates
                existing_ids = [c['chapterId'] for c in self.data['chapters'][book_id]]
                if chapter_id not in existing_ids:
                    self.data['chapters'][book_id].append(chapter_data)
                    self.stats['chapters'] += 1
    
    def _process_video_url(self, payload):
        url = payload.get('url', '')
        
        # Parse URL to extract metadata
        # Pattern: /mts/books/{xxx}/{bookId}/{chapterId}/{token}/{resolution}/{filename}
        pattern = r'/mts/books/\d+/(\d+)/(\d+)/([^/]+)/(\d+p)/([^/]+)'
        match = re.search(pattern, url)
        
        video_data = {'url': url}
        
        if match:
            video_data.update({
                'bookId': match.group(1),
                'chapterId': match.group(2),
                'token': match.group(3),
                'resolution': match.group(4),
                'filename': match.group(5)
            })
        
        # Avoid duplicates
        existing_urls = [v['url'] for v in self.data['videoUrls']]
        if url not in existing_urls:
            self.data['videoUrls'].append(video_data)
            self.stats['videos'] += 1
            
            if self.stats['videos'] % 20 == 0:
                print(f"[VIDEO] {self.stats['videos']} URLs captured...")
    
    def _process_book_detail(self, payload):
        """Process detailed book info from Retrofit response"""
        book_id = payload.get('bookId', '')
        if book_id and book_id not in self.data['books']:
            self.data['books'][book_id] = payload
            self.stats['books'] += 1
            print(f"[BOOK DETAIL] {book_id}")
    
    def save(self, output_dir='scraped_data'):
        """Save all captured data"""
        self.data['capturedAt'] = datetime.now().isoformat()
        
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Save complete data
        with open(output_path / 'complete_capture.json', 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
        
        # Save books separately for easy access
        if self.data['books']:
            with open(output_path / 'books_metadata.json', 'w', encoding='utf-8') as f:
                json.dump(self.data['books'], f, indent=2, ensure_ascii=False)
        
        # Save chapters
        if self.data['chapters']:
            with open(output_path / 'chapters.json', 'w', encoding='utf-8') as f:
                json.dump(self.data['chapters'], f, indent=2, ensure_ascii=False)
        
        # Save video URLs
        if self.data['videoUrls']:
            with open(output_path / 'video_urls.json', 'w', encoding='utf-8') as f:
                json.dump(self.data['videoUrls'], f, indent=2, ensure_ascii=False)
        
        print(f"\n[SAVED] Data saved to {output_path}/")
        return self.data

# Frida script that captures EVERYTHING
FRIDA_SCRIPT = """
setTimeout(function() {
    Java.perform(function() {
        send({type: 'log', msg: 'COMPLETE CAPTURE - Getting ALL data!'});
        
        // 1. Hook Retrofit Response - captures ALL API responses
        try {
            var Response = Java.use('retrofit2.Response');
            Response.body.implementation = function() {
                var body = this.body();
                if (body) {
                    try {
                        var s = body.toString();
                        if (s.length > 20 && !s.includes('BaseEntity')) {
                            send({
                                type: 'api_response',
                                code: this.code(),
                                body: s.substring(0, 10000)
                            });
                        }
                    } catch(e) {}
                }
                return body;
            };
            send({type: 'log', msg: '✓ Retrofit hooked'});
        } catch(e) {
            send({type: 'log', msg: '✗ Retrofit: ' + e.message});
        }
        
        // 2. Hook JSONObject - captures raw JSON parsing
        try {
            var JSONObject = Java.use('org.json.JSONObject');
            JSONObject.$init.overload('java.lang.String').implementation = function(str) {
                var s = str ? str.toString() : '';
                // Capture book metadata JSON
                if (s.length > 100 && (
                    s.includes('"bookId"') || 
                    s.includes('"bookName"') ||
                    s.includes('"coverUrl"') ||
                    s.includes('"bookList"') ||
                    s.includes('"chapterList"')
                )) {
                    send({
                        type: 'api_response',
                        body: s.substring(0, 10000)
                    });
                }
                return this.$init(str);
            };
            send({type: 'log', msg: '✓ JSONObject hooked'});
        } catch(e) {
            send({type: 'log', msg: '✗ JSONObject: ' + e.message});
        }
        
        // 3. Hook Gson for complete JSON deserialization
        try {
            var Gson = Java.use('com.google.gson.Gson');
            Gson.fromJson.overload('java.lang.String', 'java.lang.reflect.Type').implementation = function(json, type) {
                var s = json ? json.toString() : '';
                if (s.length > 100 && (
                    s.includes('"bookId"') ||
                    s.includes('"bookList"') ||
                    s.includes('"coverUrl"')
                )) {
                    send({
                        type: 'api_response',
                        body: s.substring(0, 10000)
                    });
                }
                return this.fromJson(json, type);
            };
            send({type: 'log', msg: '✓ Gson hooked'});
        } catch(e) {}
        
        // 4. Hook URL for video URLs
        try {
            var URL = Java.use('java.net.URL');
            URL.$init.overload('java.lang.String').implementation = function(urlStr) {
                var s = urlStr ? urlStr.toString() : '';
                if (s.includes('.ts') || s.includes('.m3u8') || s.includes('goodreels.com/mts')) {
                    send({type: 'video_url', url: s});
                }
                return this.$init(urlStr);
            };
            send({type: 'log', msg: '✓ URL hooked'});
        } catch(e) {}
        
        // 5. Hook SharedPreferences for cached data
        try {
            var prefs = Java.use('android.app.SharedPreferencesImpl');
            prefs.getString.implementation = function(key, defValue) {
                var result = this.getString(key, defValue);
                // Capture book-related cached data
                if (key && result && result.length > 100) {
                    if (key.includes('book') || key.includes('cache') || key.includes('home')) {
                        try {
                            JSON.parse(result);  // Verify it's JSON
                            send({
                                type: 'api_response',
                                url: 'cache://' + key,
                                body: result.substring(0, 10000)
                            });
                        } catch(e) {}
                    }
                }
                return result;
            };
            send({type: 'log', msg: '✓ SharedPreferences hooked'});
        } catch(e) {}
        
        send({type: 'log', msg: ''});
        send({type: 'log', msg: '=== ALL HOOKS READY ==='});
        send({type: 'log', msg: 'Browse app: Home, Drama details, Play videos'});
    });
}, 3000);
"""

def main():
    import subprocess
    
    print("=" * 60)
    print("COMPLETE CAPTURE - ALL METADATA + VIDEOS")
    print("=" * 60)
    print("\nThis captures EVERYTHING:")
    print("  • Book titles, covers, descriptions, genres")
    print("  • Chapter lists with titles")
    print("  • Video segment URLs")
    print()
    
    # Check if app needs cache clear
    result = subprocess.run(['adb', 'shell', 'pidof', 'com.newreading.goodreels'],
                          capture_output=True, text=True)
    pid = result.stdout.strip()
    
    device = frida.get_usb_device()
    
    if pid:
        print(f"[*] Attaching to running app (PID: {pid})...")
        session = device.attach(int(pid))
    else:
        print("[*] Cache cleared - spawning fresh app...")
        subprocess.run(['adb', 'shell', 'pm', 'clear', 'com.newreading.goodreels'],
                      capture_output=True)
        pid = device.spawn(['com.newreading.goodreels'])
        session = device.attach(pid)
        device.resume(pid)
    
    capture = CompleteCapture()
    
    script = session.create_script(FRIDA_SCRIPT)
    script.on('message', capture.on_message)
    script.load()
    
    print("\n" + "=" * 60)
    print(">>> BROWSE THE APP FOR 5 MINUTES <<<")
    print()
    print("DO THIS:")
    print("1. Login if needed")
    print("2. Scroll HOME PAGE slowly (captures book list)")
    print("3. TAP on 10+ different dramas (captures details)")
    print("4. Go to CATEGORY pages if available")
    print("5. PLAY some video episodes (captures video URLs)")
    print("=" * 60)
    print("\nCapturing for 5 minutes...")
    
    try:
        time.sleep(300)  # 5 minutes
    except KeyboardInterrupt:
        print("\n[!] Stopped early by user")
    
    session.detach()
    
    # Summary
    print("\n" + "=" * 60)
    print("CAPTURE COMPLETE!")
    print("=" * 60)
    print(f"\n  Books captured: {capture.stats['books']}")
    print(f"  Chapters captured: {capture.stats['chapters']}")
    print(f"  Video URLs: {capture.stats['videos']}")
    print(f"  API responses: {capture.stats['responses']}")
    
    # Save
    capture.save()
    
    # Verify
    if capture.stats['books'] == 0:
        print("\n[!] WARNING: No book metadata captured!")
        print("    Make sure to scroll HOME page and tap on dramas!")
    
    return capture

if __name__ == '__main__':
    main()
