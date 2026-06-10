import json
from botocore.config import Config
import boto3

# Delete from R2
R2_ENDPOINT = 'https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com'
R2_KEY_ID   = '07c99c897986ea52703c1285308d5e2c'
R2_SECRET   = '44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44'

r2 = boto3.client('s3', endpoint_url=R2_ENDPOINT,
                  aws_access_key_id=R2_KEY_ID, aws_secret_access_key=R2_SECRET,
                  config=Config(signature_version='s3v4'), region_name='auto')

try:
    r2.delete_object(Bucket='shortlovers', Key='netshortv2/dari-sopir-taksi-menjadi-pelindungnya-versi-dub/ep001.mp4')
    r2.delete_object(Bucket='shortlovers', Key='netshortv2/dari-sopir-taksi-menjadi-pelindungnya-versi-dub/ep001_540p.mp4')
    r2.delete_object(Bucket='shortlovers', Key='netshortv2/dari-sopir-taksi-menjadi-pelindungnya-versi-dub/ep001.vtt')
    print('Deleted ep001 of Dari Sopir Taksi from R2.')
except Exception as e:
    print('Error deleting from R2:', e)

# Update queue
try:
    with open('scripts/freereels_queue.json', 'r', encoding='utf-8') as f:
        queue = json.load(f)
    
    for item in queue:
        if item['id'] == '2hT6AP4RdS':
            item['status'] = 'pending'
            item['processedAt'] = None
            print("Set 'Dari Sopir Taksi' back to pending.")
            break
            
    with open('scripts/freereels_queue.json', 'w', encoding='utf-8') as f:
        json.dump(queue, f, indent=2, ensure_ascii=False)
except Exception as e:
    print('Error updating queue:', e)
