"""
Extract metadata from GoodShort APK using APKTool
Alternative to jadx - extracts resources and strings
"""

import subprocess
import json
import re
from pathlib import Path
import zipfile

def extract_strings_from_apk(apk_path: str):
    """Extract strings.xml and analyze for book data"""
    
    print("📦 Extracting APK contents...")
    
    # Create output directory
    output_dir = Path("apk_extracted")
    output_dir.mkdir(exist_ok=True)
    
    # Extract APK (it's just a ZIP)
    try:
        with zipfile.ZipFile(apk_path, 'r') as zip_ref:
            # Extract specific files we care about
            targets = ['resources.arsc', 'assets/', 'res/']
            
            for file in zip_ref.namelist():
                if any(file.startswith(t) for t in ['assets/', 'res/values/']):
                    try:
                        zip_ref.extract(file, output_dir)
                        print(f"  ✅ {file}")
                    except:
                        pass
        
        print("\n✅ APK extracted")
        
        # Look for JSON files in assets
        assets_dir = output_dir / "assets"
        if assets_dir.exists():
            print(f"\n📁 Searching assets for book data...")
            for json_file in assets_dir.rglob("*.json"):
                print(f"\n  📄 {json_file.name}")
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        # Check if it looks like book data
                        if isinstance(data, list) and len(data) > 0:
                            if 'bookName' in str(data[0]) or 'title' in str(data[0]):
                                print(f"    ✅ Potential book data! {len(data)} entries")
                                return json_file
                except:
                    pass
        
        return None
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def analyze_apk_for_metadata(apk_path: str = "goodshort.apk"):
    """Main analysis function"""
    
    if not Path(apk_path).exists():
        print(f"❌ APK not found: {apk_path}")
        return
    
    # Try extraction
    book_data_file = extract_strings_from_apk(apk_path)
    
    if book_data_file:
        print(f"\n🎉 Found book data: {book_data_file}")
        with open(book_data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            print(f"\nSample entries:")
            for item in data[:3]:
                print(json.dumps(item, indent=2, ensure_ascii=False)[:500])
    else:
        print("\n⚠️  No embedded book data found in assets")
        print("\nBook data likely comes from API only.")
        print("Manual metadata entry recommended.")


if __name__ == "__main__":
    analyze_apk_for_metadata()
