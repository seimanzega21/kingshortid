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
    # Hilangkan tanda baca, spasi berlebih, huruf kecil, dan hilangkan kurung (seperti (Sulih suara))
    title = re.sub(r'\([^)]*\)', '', title)
    title = re.sub(r'[^a-zA-Z0-9\s]', ' ', title)
    return re.sub(r'\s+', ' ', title.strip().lower())

def title_to_slug(title: str) -> str:
    slug = title.lower().strip()
    slug = re.sub(r'\([^)]*\)', '', slug)
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'\s+', '-', slug)
    return slug

def main():
    # 1. Fetch API dramas
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

    # 2. Fetch ALL R2 prefixes across major root-level folders
    roots = ['dramas/', 'netshortv2/', 'microdrama/', 'melolo/', 'goodshort/', 'freereels/']
    all_r2_prefixes = []
    paginator = r2.get_paginator('list_objects_v2')
    
    print("[*] Fetching all prefixes in R2...")
    for root in roots:
        count = 0
        for page in paginator.paginate(Bucket=BUCKET, Delimiter='/', Prefix=root):
            for cp in page.get('CommonPrefixes', []):
                all_r2_prefixes.append(cp['Prefix'])
                count += 1
        print(f"    -> {count} prefixes in {root}")
    print(f"    Total R2 prefixes collected: {len(all_r2_prefixes)}")

    # 3. Match each target drama
    results = {}
    for target in TARGET_DRAMAS:
        norm_target = normalize(target)
        target_slug = title_to_slug(target)
        
        # Cari di API
        found_api = None
        for d in dramas:
            if normalize(d.get('title', '')) == norm_target:
                found_api = d
                break
        if not found_api:
            for d in dramas:
                if norm_target in normalize(d.get('title', '')) or normalize(d.get('title', '')) in norm_target:
                    found_api = d
                    break
        
        api_title = found_api.get('title', target) if found_api else target
        api_id = found_api.get('id', 'N/A') if found_api else 'N/A'
        cover = found_api.get('cover', '') if found_api else ''
        api_slug = title_to_slug(api_title)
        
        # Cari R2 prefix yang cocok
        matched_prefixes = []
        for p in all_r2_prefixes:
            # Check if slug is in prefix
            p_lower = p.lower()
            if api_slug in p_lower or target_slug in p_lower:
                matched_prefixes.append(p)
                
        # Jika tidak ketemu, coba parsial kata per kata
        if not matched_prefixes:
            words = [w for w in target_slug.split('-') if len(w) > 3]
            for p in all_r2_prefixes:
                p_lower = p.lower()
                # Jika ada 2+ kata yang cocok
                match_count = sum(1 for w in words if w in p_lower)
                if len(words) >= 2 and match_count >= 2:
                    matched_prefixes.append(p)
                elif len(words) == 1 and match_count == 1:
                    matched_prefixes.append(p)
                    
        # Filter matching duplicate folder names across roots (prefer netshortv2/ or dramas/)
        best_prefix = None
        if matched_prefixes:
            # Sort by putting netshortv2 and dramas first
            matched_prefixes.sort(key=lambda x: 0 if 'netshortv2/' in x or 'dramas/' in x else 1)
            best_prefix = matched_prefixes[0]

        results[target] = {
            'api_title': api_title,
            'api_id': api_id,
            'cover': cover,
            'r2_prefix': best_prefix,
            'all_matches': matched_prefixes
        }
        
    print("\n=== HASIL PENCARIAN & PEMETAAN ===")
    for target, res in results.items():
        print(f"Input: '{target}'")
        print(f"  -> API Title: '{res['api_title']}' (ID: {res['api_id']})")
        print(f"  -> Cover URL: {res['cover']}")
        print(f"  -> R2 Prefix: {res['r2_prefix']}")
        if len(res['all_matches']) > 1:
            print(f"  -> All Matches: {res['all_matches']}")
        print()

if __name__ == "__main__":
    main()
