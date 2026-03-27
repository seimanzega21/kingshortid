"""Remove orphaned code from freereels_full_eps.py"""
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('freereels_full_eps.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f'Total lines: {len(lines)}')

# Find the two 'return result' lines - first is in new function, second is old dup
return_result_lines = [i for i, l in enumerate(lines) if l.strip() == 'return result']
print(f'return result lines: {return_result_lines}')

# Find '# Helpers' line
helper_lines = [i for i, l in enumerate(lines) if '# ── Helpers' in l]
print(f'# Helpers lines: {helper_lines}')

if len(return_result_lines) >= 2 and len(helper_lines) >= 1:
    # Delete from first return result + 2 lines after to before first # Helpers
    start_del = return_result_lines[0] + 2  # line after 'return result' blank line
    end_del = helper_lines[0]  # up to (not including) # Helpers
    print(f'Deleting lines {start_del+1} to {end_del} (1-indexed)')
    new_lines = lines[:start_del] + lines[end_del:]
    with open('freereels_full_eps.py', 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    print(f'Done! New total: {len(new_lines)} lines')
else:
    print('ERROR: Could not find the right lines to delete')
    for i, l in enumerate(lines[238:260], 239):
        print(f'{i}: {l.rstrip()[:80]}')
