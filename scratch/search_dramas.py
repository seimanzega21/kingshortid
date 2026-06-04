# -*- coding: utf-8 -*-
import sys
import boto3
import requests
import re
from botocore.config import Config

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

R2_ENDPOINT = 'https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com'
R2_KEY_ID   = '07c99c897986ea52703c1285308d5e2c'
R2_SECRET   = '44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44'
BUCKET      = 'shortlovers'
API_BASE    = 'https://api.shortlovers.id'

TARGET_DRAMAS = [
    "Perangkap Cinta yang Salah",
    "Qilin sampah? Kembalikan hadiah!",
    "Suami yang Mengintip",
    "Zona Dewa-Iblis: Penjaga Terakhir",
    "Siapa seret utusan hantu?",
    "Hubungan Berbahaya",
    "Tangisan Kehilanganku",
    "(Sulih suara) Main Lemah, Tapi Kuat",
    "Bangkrutkan Suami Selingkuh",
    "Mencari Sinar di Lautan",
    "Dua Bayi Ajaib",
    "Dikejar Cinta yang Lupa"
]

r2 = boto3.client(
    's3',
    endpoint_url=R2_ENDPOINT,
    aws_access_key_id=R2_KEY_ID,
    aws_secret_access_key=R2_SECRET,
    config=Config(signature_version='s3v4'),
    region_name='auto'
)

def normalize(title):
    return re.sub(r'\s+', ' ', title.strip().lower())

def title_to_slug(title: str) -> str:
    slug = title.lower().strip()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'\s+', '-', slug)
    return slug

def main():
    print("[*] Fetching drama list dari API...")
    try:
        r = requests.get(f"{API_BASE}/api/dramas?limit=1000", timeout=30)
        r.raise_for_status()
        data = r.json()
        dramas = data if isinstance(data, list) else data.get('dramas', data.get('data', []))
        print(f"    -> {len(dramas)} drama ditemukan di API")
    except Exception as e:
        print(f"    ERROR fetch API: {e}")
        return

    # List all R2 prefixes
    print("[*] Fetching semua prefix di R2 dramas/...")
    all_r2_prefixes = []
    paginator = r2.get_paginator('list_objects_v2')
    for page in paginator.paginate(Bucket=BUCKET, Delimiter='/', Prefix='dramas/'):
        for cp in page.get('CommonPrefixes', []):
            all_r2_prefixes.append(cp['Prefix'])
    print(f"    -> {len(all_r2_prefixes)} folder drama di R2")

    for target in TARGET_DRAMAS:
        norm_target = normalize(target)
        found_api = None
        # Try exact match
        for d in dramas:
            if normalize(d.get('title', '')) == norm_target:
                found_api = d
                break
        
        # Try partial match if not found
        if not found_api:
            for d in dramas:
                if norm_target in normalize(d.get('title', '')) or normalize(d.get('title', '')) in norm_target:
                    found_api = d
                    break
        
        # Try word matches
        if not found_api:
            # strip "(Sulih suara)" etc
            clean_target = re.sub(r'\([^)]*\)', '', target).strip()
            norm_clean = normalize(clean_target)
            for d in dramas:
                if norm_clean in normalize(d.get('title', '')) or normalize(d.get('title', '')) in norm_clean:
                    found_api = d
                    break

        if found_api:
            title = found_api.get('title', '')
            slug = title_to_slug(title)
            r2_prefix = f"dramas/{slug}/"
            
            # Cek prefix
            if r2_prefix not in all_r2_prefixes:
                # Find matching prefix
                matched = [p for p in all_r2_prefixes if slug[:10] in p or any(w in p for w in slug.split('-')[:3] if len(w) > 4)]
                if matched:
                    r2_prefix = matched[0]
                    status = f"Found in R2 as: {r2_prefix}"
                else:
                    status = "Not found in R2"
            else:
                status = f"Found: {r2_prefix}"
            
            print(f"[FOUND API] '{target}' -> API Title: '{title}' | ID: {found_api.get('id')} | R2: {status}")
        else:
            print(f"[NOT FOUND API] '{target}'")

if __name__ == "__main__":
    main()
