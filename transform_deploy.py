import os

with open('d:/kingshortid/deploy_melolov3_queue.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('ingest_melolov3_queue_vps.py', 'ingest_dramawavev2_queue_vps.py')
content = content.replace('ingest_melolov3_queue.log', 'ingest_dramawavev2_queue.log')

with open('d:/kingshortid/deploy_dramawavev2_queue.py', 'w', encoding='utf-8') as f:
    f.write(content)
