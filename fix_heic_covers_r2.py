# -*- coding: utf-8 -*-
import requests
import boto3
import urllib.parse
import io
from botocore.config import Config

R2_ENDPOINT  = 'https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com'
R2_KEY_ID    = '07c99c897986ea52703c1285308d5e2c'
R2_SECRET    = '44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44'
R2_BUCKET    = 'shortlovers'

WEB_HDRS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
}

def get_r2():
    return boto3.client(
        's3', endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_KEY_ID, aws_secret_access_key=R2_SECRET,
        config=Config(signature_version='s3v4'), region_name='auto'
    )

def fix_cover(slug, heic_url):
    print(f"\nProcessing cover for: {slug}")
    converted_url = f"https://wsrv.nl/?url={urllib.parse.quote(heic_url)}&output=jpg"
    print(f"Downloading converted JPEG from wsrv.nl...")
    
    r = requests.get(converted_url, headers=WEB_HDRS, timeout=20)
    if not r.ok:
        print(f"Failed to fetch converted image: {r.status_code}")
        return False
        
    print(f"Successfully converted. Size: {len(r.content)} bytes")
    
    r2 = get_r2()
    r2_key = f"dramas/{slug}/cover.jpg"
    print(f"Uploading to R2 key: {r2_key}...")
    try:
        r2.upload_fileobj(
            io.BytesIO(r.content), R2_BUCKET, r2_key,
            ExtraArgs={'ContentType': 'image/jpeg', 'CacheControl': 'public, max-age=31536000'}
        )
        print("Upload completed successfully!")
        return True
    except Exception as e:
        print(f"Upload failed: {e}")
        return False

def main():
    dramas = [
        {
            'slug': 'reinkarnasi-pilot-ulung',
            'heic_url': 'https://p19-novel-sign.fizzopic.org/novel-images-apsoutheast/3eb2d257bc2d89d6cf9973f39e4eca66~tplv-836v1mcgsk-resize:336:478.heic?rk3s=253f70db&x-expires=1784851523&x-signature=k9AGPMmnTP8JJl3W74FRNySl0Fk%3D'
        },
        {
            'slug': 'cinta-dan-tombak-purba',
            'heic_url': 'https://p16-novel-sign.fizzopic.org/novel-images-apsoutheast/cefa1fc23058ad47863b96fbba24959e~tplv-836v1mcgsk-resize:336:478.heic?rk3s=253f70db&x-expires=1785024371&x-signature=qa2siec1Pz%2BQ3rlQrQ5e8twe%2B2A%3D'
        }
    ]
    
    for d in dramas:
        fix_cover(d['slug'], d['heic_url'])

if __name__ == '__main__':
    main()
