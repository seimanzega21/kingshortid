"""Extract base.apk from XAPK bundle"""
import zipfile, shutil, sys, os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

xapk_path = r"C:\Users\Seiman\Downloads\FreeReels - Dramas & Reels_2.2.10_APKPure.xapk"
out_dir = r"D:\kingshortid\scraping\freereels\xapk_extracted"
os.makedirs(out_dir, exist_ok=True)

print(f"Opening: {xapk_path}")
try:
    with zipfile.ZipFile(xapk_path, 'r') as z:
        names = z.namelist()
        print(f"Files in XAPK ({len(names)}):")
        for n in names:
            info = z.getinfo(n)
            print(f"  {n}: {info.file_size:,} bytes")
        
        # Extract APK files
        for n in names:
            if n.endswith('.apk'):
                print(f"\nExtracting: {n}")
                z.extract(n, out_dir)
        
        # Also extract manifest
        for n in names:
            if 'manifest' in n.lower() or n.endswith('.json'):
                z.extract(n, out_dir)
                
except Exception as e:
    print(f"Error: {e}")
    import traceback; traceback.print_exc()
