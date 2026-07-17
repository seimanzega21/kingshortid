import re

with open('d:/kingshortid/ingest_dramawavev2_queue_vps.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace EVERYTHING between DRAMAS_QUEUE = [ and ] with our single item
# We need to make sure we don't accidentally match the wrong brackets
# The safest way is to find DRAMAS_QUEUE = [ and the next def get_r2():

start = content.find("DRAMAS_QUEUE = [")
end = content.find("def get_r2():")

if start != -1 and end != -1:
    new_queue = '''DRAMAS_QUEUE = [
    {'id': 'rz3UJ5zFl4', 'slug': 'ratu-tersembunyi-membalas', 'genres': ['Drama', 'Aksi', 'Balas Dendam']},
]

'''
    content = content[:start] + new_queue + content[end:]
    
    with open('d:/kingshortid/ingest_dramawavev2_queue_vps.py', 'w', encoding='utf-8') as f:
        f.write(content)
        print("Fixed!")
