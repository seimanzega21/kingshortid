import sys
with open('d:/kingshortid/scripts/scrape_flareflow_provider.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

in_loop_block = False
new_lines = []

for line in lines:
    if line.strip() == "eps = detail.get('list', [])":
        in_loop_block = True
        new_lines.append("        total_eps = detail.get('totalEpisodes', 0)\n")
        new_lines.append("        if not total_eps:\n")
        new_lines.append("            print('  -> [WARN] No episodes found in detail list.')\n")
        new_lines.append("            if newly_created and db_id:\n")
        new_lines.append("                print(f'  -> [DB] Cleaning up empty drama (ID: {db_id})...')\n")
        new_lines.append("                requests.delete(f'{API_BASE}/admin/dramas/{db_id}', headers=ADMIN_HDR, timeout=10)\n")
        new_lines.append("            return False\n\n")
        new_lines.append("        eps_to_process = list(range(1, total_eps + 1))\n")
        new_lines.append("        if is_test_run:\n")
        new_lines.append("            print('  -> TEST RUN: Processing Episode 1 only.')\n")
        new_lines.append("            eps_to_process = [1]\n\n")
        new_lines.append("        print(f'  -> Total Episodes to process: {total_eps}')\n")
        new_lines.append("        success_count = 0\n")
        new_lines.append("        failed_count = 0\n")
        new_lines.append("        skipped_count = 0\n\n")
        new_lines.append("        for ep_no in eps_to_process:\n")
        new_lines.append("            ep_id = f'{movie_id}_{ep_no}'\n")
        continue
        
    if in_loop_block:
        if line.strip() == "ep_id = ep.get('id')":
            in_loop_block = False
        continue
        
    new_lines.append(line)

with open('d:/kingshortid/scripts/scrape_flareflow_provider.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
