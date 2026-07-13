import sys, re
with open('d:/kingshortid/scripts/scrape_dramawavev2_provider.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Replace provider names
code = code.replace('dramawavev2', 'flareflow')
code = code.replace('DramaWaveV2', 'FlareFlow')

# 2. Replace endpoints
code = code.replace("f\"https://vidrama.asia/api/flareflow?action=detail&id={movie_id}\"", "f\"https://vidrama.asia/api/flareflow/detail?id={movie_id}&lang=id\"")
code = code.replace("f\"https://vidrama.asia/api/flareflow?action=stream&id={movie_id}&episode={ep_no}\"", "f\"https://vidrama.asia/api/flareflow/episode?id={movie_id}&ep={ep_no}&lang=id\"")

# 3. Replace detail extraction (no success wrapper)
code = re.sub(r"if not res_json\.get\('success'\):.*?return False", "", code, flags=re.DOTALL)
code = re.sub(r"detail = res_json\.get\('data', \{\}\)", "detail = res_json", code)

# 4. Replace detail DB payload creation
old_func = """def api_get_or_create_drama(detail, slug, cover_url):
    title = detail.get('title') or detail.get('name') or 'Unknown Title'
    payload = {
        'title': title,
        'description': detail.get('description') or detail.get('introduction') or title,
        'cover': cover_url,
        'genres': detail.get('tags', ['Drama']) or ['Drama'],
        'totalEpisodes': detail.get('chapterCount', 0),
        'isComplete': True if detail.get('bookStatus') == 1 else False,
        'country': 'China', 
        'language': 'Indonesia',
        'status': 'completed' if detail.get('bookStatus') == 1 else 'ongoing',
        'isActive': False, # Pending!
    }"""

new_func = """def api_get_or_create_drama(detail, slug, cover_url):
    title = detail.get('shortPlayName') or 'Unknown Title'
    genres = [g.get('labelName') for g in detail.get('labelResponseList', [])]
    if not genres: genres = ['Drama']
    
    payload = {
        'title': title,
        'description': detail.get('summary') or title,
        'cover': cover_url,
        'genres': genres,
        'totalEpisodes': detail.get('totalEpisodes', 0),
        'isComplete': True if detail.get('updateStatus') == 1 else False,
        'country': 'China', 
        'language': 'Indonesia',
        'status': 'completed' if detail.get('updateStatus') == 1 else 'ongoing',
        'isActive': True,
    }"""
code = code.replace(old_func, new_func)
code = code.replace("'isActive': False,", "'isActive': True,")
code = code.replace("title = detail.get('title') or detail.get('name') or 'Unknown Title'", "title = detail.get('shortPlayName') or 'Unknown Title'")
code = code.replace("cover_url = detail.get('coverUrl') or detail.get('cover')", "cover_url = detail.get('horizontalCoverId') or detail.get('picUrl')")

# 5. Replace episode loop
old_loop = """        # Process episodes
        eps = detail.get('list', [])
        if not eps:
            print("  -> [WARN] No episodes found in detail list.")
            if newly_created and db_id:
                print(f"  -> [DB] Cleaning up empty drama (ID: {db_id})...")
                requests.delete(f"{API_BASE}/admin/dramas/{db_id}", headers=ADMIN_HDR, timeout=10)
            return False
            
        if is_test_run:
            print("  -> TEST RUN: Processing Episode 1 only.")
            eps = eps[:1]
            
        total_eps = len(eps)
        print(f"  -> Total Episodes to process: {total_eps}")
        
        success_count = 0
        failed_count = 0
        skipped_count = 0
        
        for ep in eps:
            ep_no = ep.get('episodeNo')
            if ep_no is None:
                continue"""

new_loop = """        # Process episodes
        total_eps = detail.get('totalEpisodes', 0)
        if not total_eps:
            print("  -> [WARN] No episodes found in detail list.")
            if newly_created and db_id:
                print(f"  -> [DB] Cleaning up empty drama (ID: {db_id})...")
                requests.delete(f"{API_BASE}/admin/dramas/{db_id}", headers=ADMIN_HDR, timeout=10)
            return False
            
        eps_to_process = list(range(1, total_eps + 1))
        if is_test_run:
            print("  -> TEST RUN: Processing Episode 1 only.")
            eps_to_process = [1]
            
        print(f"  -> Total Episodes to process: {total_eps}")
        
        success_count = 0
        failed_count = 0
        skipped_count = 0
        
        for ep_no in eps_to_process:
            ep = {} # dummy for iteration context if needed below
            ep_id = f"{movie_id}_{ep_no}" """
code = code.replace(old_loop, new_loop)

# 6. Replace stream URL fetch
old_stream = """            try:
                stream_res = requests.get(stream_url, headers=WEB_HDRS, timeout=15, verify=False)
                if stream_res.ok:
                    stream_data = stream_res.json().get('data', {})
                    vurl = stream_data.get('videoUrl')
                    subtitles = stream_data.get('subtitles', [])
            except Exception as e:"""

new_stream = """            try:
                stream_res = requests.get(stream_url, headers=WEB_HDRS, timeout=15, verify=False)
                if stream_res.ok:
                    stream_data = stream_res.json()
                    qualities = stream_data.get('qualities', {})
                    vurl = qualities.get('1080p') or qualities.get('720p') or qualities.get('480p') or stream_data.get('raw', {}).get('videoUrl') or stream_data.get('raw', {}).get('video_1080')
                    subtitles = stream_data.get('subtitles', [])
            except Exception as e:"""
code = code.replace(old_stream, new_stream)

with open('d:/kingshortid/scripts/scrape_flareflow_provider.py', 'w', encoding='utf-8') as f:
    f.write(code)
