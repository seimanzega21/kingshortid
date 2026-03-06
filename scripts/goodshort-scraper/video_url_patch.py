# IMPROVED batch_har_processor.py - Insert after line 187

# STEP 3: Extract video URLs from /chapter/load ⭐ CRITICAL!
print("\\nStep 3: Extracting video URLs from /chapter/load...")
video_url_count = 0

for entry in har_data['log']['entries']:
    request_url = entry['request']['url']
    
    if '/hwycclientreels/chapter/load' in request_url:
        response = entry.get('response', {})
        content = response.get('content', {})
        text = content.get('text', '')
        
        if not text:
            continue
        
        try:
            data = json.loads(text)
            chapter_data = data.get('data', {})
            
            # Extract video URL
            video_url = chapter_data.get('videoUrl', chapter_data.get('video', {}).get('url', ''))
            if not video_url:
                continue
            
            # Get chapter ID to match with episodes  
            chapter_id = str(chapter_data.get('chapterId', chapter_data.get('id', '')))
            book_id = str(chapter_data.get('bookId', ''))
            
            if not chapter_id or book_id not in drama_map:
                continue
            
            # Update corresponding episode with video URL
            for episode in drama_map[book_id]['episodes']:
                if str(episode.get('chapterId')) == chapter_id:
                    episode['video_url'] = video_url
                    video_url_count += 1
                    break
        
        except json.JSONDecodeError:
            continue

print(f"  ✅ Added {video_url_count} video URLs to episodes")
