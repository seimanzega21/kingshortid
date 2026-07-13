import re

with open('d:/kingshortid/scripts/scrape_flareflow_provider.py', 'r', encoding='utf-8') as f:
    code = f.read()

# I will replace the episode loop logic
old_loop_logic = """        # Process episodes
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

new_loop_logic = """        # Process episodes
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
"""

code = code.replace(old_loop_logic, new_loop_logic)

with open('d:/kingshortid/scripts/scrape_flareflow_provider.py', 'w', encoding='utf-8') as f:
    f.write(code)
