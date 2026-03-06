"""
Extract and decompile APK to find signing logic and RSA keys
"""

import zipfile
from pathlib import Path
import json

def extract_apk():
    """Extract APK contents"""
    
    apk_path = Path("goodshort.apk")
    extract_dir = Path("apk_extracted")
    
    if not apk_path.exists():
        print("❌ goodshort.apk not found!")
        return None
    
    print(f"📦 Extracting APK: {apk_path.name}\n")
    
    # Extract
    with zipfile.ZipFile(apk_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)
    
    print(f"✅ Extracted to: {extract_dir}\n")
    
    return extract_dir


def search_for_keys_and_signing(extract_dir):
    """Search for RSA keys and signing logic in APK"""
    
    if not extract_dir:
        return
    
    print("🔍 Searching for keys and signing logic...\n")
    
    # Common locations for keys
    key_patterns = [
        '**/key*.pem',
        '**/key*.der',
        '**/*rsa*',
        '**/*public*',
        '**/*private*',
        '**/cert*',
        '**/*.key'
    ]
    
    print("📁 Searching for key files:\n")
    
    found_files = []
    for pattern in key_patterns:
        for file in extract_dir.rglob(pattern):
            if file.is_file():
                size = file.stat().st_size
                print(f"  ✅ {file.relative_to(extract_dir)} ({size} bytes)")
                found_files.append(file)
    
    if not found_files:
        print("  ⚠️  No obvious key files found\n")
    
    # Search in assets
    print("\n📂 Checking assets folder:\n")
    assets_dir = extract_dir / 'assets'
    if assets_dir.exists():
        for file in assets_dir.rglob('*'):
            if file.is_file() and file.suffix in ['.json', '.txt', '.xml', '.pem', '.der', '.key']:
                size = file.stat().st_size
                print(f"  • {file.relative_to(assets_dir)} ({size} bytes)")
    
    # Search for strings containing "sign" or "rsa" in DEX files
    print("\n🔍 Searching DEX files for signing references...\n")
    
    dex_files = list(extract_dir.glob('*.dex'))
    print(f"Found {len(dex_files)} DEX files\n")
    
    # Note: Proper decompilation requires jadx or similar tools
    print("💡 For full decompilation, use JADX:")
    print("   Download: https://github.com/skylot/jadx")
    print("   Command: jadx -d apk_decompiled goodshort.apk\n")
    
    return found_files


def search_resources_xml():
    """Search resources for hardcoded values"""
    
    extract_dir = Path("apk_extracted")
    
    print("\n📋 Searching resources.arsc and XML files...\n")
    
    # Check res folder
    res_dir = extract_dir / 'res'
    if res_dir.exists():
        xml_files = list(res_dir.rglob('*.xml'))
        print(f"Found {len(xml_files)} XML files in res/\n")
        
        # Look for strings.xml
        for xml_file in xml_files:
            if 'strings' in xml_file.name.lower():
                print(f"  📄 {xml_file.relative_to(extract_dir)}")


def quick_analysis():
    """Quick analysis without full decompilation"""
    
    print("\n" + "="*80)
    print("📊 QUICK ANALYSIS")
    print("="*80 + "\n")
    
    extract_dir = Path("apk_extracted")
    
    # List important files
    important_patterns = [
        'lib/**/*.so',  # Native libraries (might contain signing)
        'assets/**/*',
        'META-INF/**/*'
    ]
    
    print("🔧 Native libraries (.so files):\n")
    so_files = list(extract_dir.glob('lib/**/*.so'))
    for so_file in so_files:
        size_kb = so_file.stat().st_size / 1024
        print(f"  {so_file.relative_to(extract_dir)} ({size_kb:.1f} KB)")
    
    if so_files:
        print("\n💡 Signing logic might be in native code (.so files)")
        print("   Use IDA Pro or Ghidra to reverse engineer\n")


if __name__ == "__main__":
    print("="*80)
    print("🔓 APK REVERSE ENGINEERING - SIGNING ANALYSIS")
    print("="*80 + "\n")
    
    extract_dir = extract_apk()
    
    if extract_dir:
        search_for_keys_and_signing(extract_dir)
        search_resources_xml()
        quick_analysis()
        
        print("\n" + "="*80)
        print("📝 RECOMMENDATIONS:")
        print("="*80 + "\n")
        print("1. Install JADX for Java decompilation:")
        print("   choco install jadx  (or download from GitHub)")
        print()
        print("2. Decompile APK:")
        print("   jadx -d apk_decompiled goodshort.apk")
        print()
        print("3. Search decompiled code for:")
        print("   - 'sign' method/class")
        print("   - 'RSA' references")
        print("   - 'signature' generation")
        print()
        print("4. Alternative: Use Frida to hook signing function at runtime")
