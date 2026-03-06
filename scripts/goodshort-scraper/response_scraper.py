"""
RESPONSE INTERCEPTION SCRAPER
================================
Instead of trying to replicate API calls, intercept the app's OWN responses
and extract data directly. This bypasses TLS fingerprinting and sign issues.

WORKFLOW:
1. Attach to running app
2. Hook OkHttp Response to intercept all API responses
3. Extract drama list, chapter list, video URLs from responses
4. Save to JSON/database for scraping pipeline

USAGE:
1. Open GoodShort app and login
2. Run this script
3. Navigate through app (scroll home, tap dramas, play videos)
4. All data will be captured and saved
"""

import frida
import json
import time
import subprocess
from datetime import datetime
from pathlib import Path

# Data storage
captured_data = {
    "capturedAt": None,
    "books": [],
    "chapters": {},  # bookId -> chapter list
    "videoUrls": [],
    "rawResponses": []
}

def on_message(message, data):
    global captured_data
    if message['type'] == 'send':
        payload = message['payload']
        
        if isinstance(payload, dict):
            resp_type = payload.get('type', '')
            
            if resp_type == 'api_response':
                url = payload.get('url', '')
                body = payload.get('body', '')
                
                # Log
                print(f"\n[API] {url[:60]}...")
                
                # Parse and categorize
                try:
                    resp_data = json.loads(body)
                    
                    if resp_data.get('success'):
                        data_obj = resp_data.get('data', {})
                        
                        # Home/Index - book list
                        if '/home/index' in url or '/home/short' in url:
                            books = data_obj.get('bookList', [])
                            print(f"    -> Got {len(books)} books!")
                            captured_data['books'].extend(books)
                        
                        # Chapter list
                        elif '/chapter/list' in url:
                            chapters = data_obj.get('list', data_obj.get('chapterList', []))
                            book_id = None
                            for ch in chapters:
                                if ch.get('bookId'):
                                    book_id = str(ch['bookId'])
                                    break
                            if book_id:
                                captured_data['chapters'][book_id] = chapters
                                print(f"    -> Got {len(chapters)} chapters for book {book_id}")
                        
                        # Reader init - sometimes has video info
                        elif '/reader/init' in url:
                            print(f"    -> Reader init data captured")
                        
                        # Video URL patterns
                        if 'videoUrl' in str(resp_data) or 'playUrl' in str(resp_data):
                            # Extract video URLs
                            extract_video_urls(data_obj, captured_data['videoUrls'])
                        
                        # Store raw for analysis
                        captured_data['rawResponses'].append({
                            'url': url,
                            'data': data_obj
                        })
                        
                except json.JSONDecodeError:
                    pass  # Not JSON
                    
            elif resp_type == 'video_url':
                url = payload.get('url', '')
                if 'goodreels' in url or '.ts' in url:
                    captured_data['videoUrls'].append(url)
                    print(f"[VIDEO] {url[:80]}...")
                    
        else:
            print(str(payload)[:100])

def extract_video_urls(data, url_list):
    """Recursively extract video URLs from response data"""
    if isinstance(data, dict):
        for key, val in data.items():
            if key in ['videoUrl', 'playUrl', 'url', 'hlsUrl', 'm3u8Url']:
                if isinstance(val, str) and val:
                    url_list.append(val)
            else:
                extract_video_urls(val, url_list)
    elif isinstance(data, list):
        for item in data:
            extract_video_urls(item, url_list)

script_code = """
Java.perform(function() {
    send('[*] Response Interception Scraper Starting...');
    
    // Hook OkHttp Response body reading
    var ResponseBody = Java.use('okhttp3.ResponseBody');
    var Buffer = Java.use('okio.Buffer');
    
    // Hook Response.body() to intercept responses
    var Response = Java.use('okhttp3.Response');
    var originalBody = Response.body;
    
    // Hook at BridgeInterceptor level for cleaner capture
    try {
        var BridgeInterceptor = Java.use('okhttp3.internal.http.BridgeInterceptor');
        BridgeInterceptor.intercept.implementation = function(chain) {
            var response = this.intercept(chain);
            
            try {
                var request = chain.request();
                var url = request.url().toString();
                
                // Only capture goodreels API
                if (url.includes('goodreels') && url.includes('/hwycclientreels/')) {
                    var body = response.body();
                    if (body) {
                        var source = body.source();
                        source.request(Long.MAX_VALUE);
                        var buffer = source.buffer().clone();
                        var bodyString = buffer.readUtf8();
                        
                        send({
                            type: 'api_response',
                            url: url,
                            code: response.code(),
                            body: bodyString
                        });
                    }
                }
            } catch(e) {
                // Silent fail - some responses may not be readable
            }
            
            return response;
        };
        send('[OK] BridgeInterceptor hooked');
    } catch(e) {
        send('[!] BridgeInterceptor hook failed: ' + e.message);
    }
    
    // Also hook URL connections for video URLs
    try {
        var URL = Java.use('java.net.URL');
        URL.openConnection.overload().implementation = function() {
            var url = this.toString();
            if (url.includes('goodreels') || url.includes('.ts') || url.includes('.m3u8')) {
                send({type: 'video_url', url: url});
            }
            return this.openConnection();
        };
        send('[OK] URL hook ready');
    } catch(e) {}
    
    send('');
    send('[READY] Now browse the app - scroll, tap dramas, play videos!');
    send('[INFO] All API responses will be captured automatically.');
});
"""

def save_data():
    """Save captured data to files"""
    captured_data['capturedAt'] = datetime.now().isoformat()
    
    output_dir = Path('scraped_data')
    output_dir.mkdir(exist_ok=True)
    
    # Save main data
    with open(output_dir / 'captured_data.json', 'w', encoding='utf-8') as f:
        json.dump(captured_data, f, indent=2, ensure_ascii=False)
    
    # Save books list
    if captured_data['books']:
        unique_books = {b['bookId']: b for b in captured_data['books'] if 'bookId' in b}
        with open(output_dir / 'books.json', 'w', encoding='utf-8') as f:
            json.dump(list(unique_books.values()), f, indent=2, ensure_ascii=False)
        print(f"\n[SAVED] {len(unique_books)} unique books")
    
    # Save chapters
    if captured_data['chapters']:
        with open(output_dir / 'chapters.json', 'w', encoding='utf-8') as f:
            json.dump(captured_data['chapters'], f, indent=2, ensure_ascii=False)
        print(f"[SAVED] Chapters for {len(captured_data['chapters'])} books")
    
    # Save video URLs
    if captured_data['videoUrls']:
        with open(output_dir / 'video_urls.txt', 'w') as f:
            for url in set(captured_data['videoUrls']):
                f.write(url + '\n')
        print(f"[SAVED] {len(set(captured_data['videoUrls']))} video URLs")
    
    print(f"\n[OK] All data saved to {output_dir}/")

def main():
    print("=" * 60)
    print("GOODSHORT RESPONSE INTERCEPTION SCRAPER")
    print("=" * 60)
    print("This captures data directly from app responses!")
    print()
    
    result = subprocess.run(['adb', 'shell', 'pidof', 'com.newreading.goodreels'],
                          capture_output=True, text=True)
    pid = int(result.stdout.strip()) if result.stdout.strip() else None
    
    if not pid:
        print("[!] App not running! Start GoodShort and login first.")
        return
    
    print(f"[OK] Connected to app (PID: {pid})")
    
    device = frida.get_usb_device()
    session = device.attach(pid)
    
    script = session.create_script(script_code)
    script.on('message', on_message)
    script.load()
    
    print("\n" + "=" * 60)
    print(">>> BROWSE THE APP NOW <<<")
    print("- Scroll home page")
    print("- Tap on dramas")  
    print("- Play videos")
    print("=" * 60)
    print("\nCapturing for 3 minutes (Ctrl+C to stop early)...")
    
    try:
        time.sleep(180)  # 3 minutes
    except KeyboardInterrupt:
        print("\n[!] Stopped by user")
    
    session.detach()
    save_data()
    
    print("\n" + "=" * 60)
    print("CAPTURE COMPLETE!")
    print("=" * 60)

if __name__ == '__main__':
    main()
