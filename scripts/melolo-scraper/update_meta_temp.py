import boto3,os,json
from dotenv import load_dotenv
load_dotenv()
s3=boto3.client('s3',endpoint_url=os.getenv('R2_ENDPOINT'),aws_access_key_id=os.getenv('R2_ACCESS_KEY_ID'),aws_secret_access_key=os.getenv('R2_SECRET_ACCESS_KEY'),region_name='auto')
BUCKET='shortlovers'

resp=s3.get_object(Bucket=BUCKET,Key='melolo/jenderal-terakhir/metadata.json')
meta=json.loads(resp['Body'].read().decode('utf-8'))
print(f"Old title: {meta.get('title')}")
print(f"Old slug: {meta.get('slug')}")

meta['title']='Jenderal Terakhir'
meta['slug']='jenderal-terakhir'

s3.put_object(Bucket=BUCKET,Key='melolo/jenderal-terakhir/metadata.json',Body=json.dumps(meta,indent=2,ensure_ascii=False),ContentType='application/json')
print(f"New title: {meta['title']}")
print(f"New slug: {meta['slug']}")
print("Done!")
