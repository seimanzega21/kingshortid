"""Strip META-INF (signature) from APK files so they can be re-signed."""
import zipfile, shutil, os, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

apks = [
    "xapk_extracted/config.arm64_v8a.apk",
    "xapk_extracted/config.xxhdpi.apk"
]

for apk_path in apks:
    out_path = apk_path.replace(".apk", "_unsigned.apk")
    print(f"Processing: {apk_path}")
    with zipfile.ZipFile(apk_path, 'r') as zin:
        with zipfile.ZipFile(out_path, 'w', zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                if not item.filename.startswith("META-INF/"):
                    data = zin.read(item.filename)
                    zout.writestr(item, data)
    size = os.path.getsize(out_path)
    print(f"  Stripped: {out_path} ({size:,} bytes)")
print("Done!")
