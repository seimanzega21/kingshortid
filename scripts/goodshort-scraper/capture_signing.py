"""
Master script to capture signing and implement automation
"""

import subprocess
import time
import sys
from pathlib import Path

print("""
================================================================================
🔐 GOODSHORT SIGNING CAPTURE & AUTOMATION
================================================================================

This script will:
1. Run Frida hook on GoodShort app
2. Capture signing function calls
3. Analyze captured data
4. Implement signing in Python
5. Test automated scraping

INSTRUCTIONS:
1. Keep the GoodShort app CLOSED initially
2. This script will launch it with Frida attached
3. Browse 2-3 dramas in the app after it launches
4. Press Ctrl+C when done capturing
5. Script will analyze and implement signing

================================================================================
""")

input("Press ENTER to start...")

print("\n📱 Launching GoodShort with Frida hook...\n")

# Run Frida
frida_cmd = [
    'frida',
    '-U',
    '-f', 'com.newreading.goodreels',
    '-l', 'frida_comprehensive_hook.js'
]

print("Command:", ' '.join(frida_cmd))
print("\n" + "="*80)
print("FRIDA OUTPUT:")
print("="*80 + "\n")

try:
    # Run Frida with live output
    process = subprocess.Popen(
        frida_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    # Capture output
    captured_output = []
    
    print("[*] App launching...")
    print("[*] Use the app to browse dramas")
    print("[*] Press Ctrl+C when done\n")
    
    for line in process.stdout:
        print(line, end='')
        captured_output.append(line)
        
        # Save signing data if found
        if 'SIGN HEADER ADDED' in line or 'Generated Signature' in line:
            with open('frida_capture.log', 'a', encoding='utf-8') as f:
                f.write(line)

except KeyboardInterrupt:
    print("\n\n"  + "="*80)
    print("⏹️  CAPTURE STOPPED")
    print("="*80)
    
    # Kill Frida
    process.terminate()
    
    # Save full output
    with open('frida_full_output.log', 'w', encoding='utf-8') as f:
        f.writelines(captured_output)
    
    print(f"\n✅ Captured {len(captured_output)} lines")
    print("✅ Saved to: frida_capture.log")
    print("✅ Full output: frida_full_output.log")
    
    # Analyze
    print("\n" + "="*80)
    print("📊 ANALYZING CAPTURED DATA...")
    print("="*80 + "\n")
    
    # Search for key information
    sign_headers = []
    signing_data = []
    class_names = []
    
    for line in captured_output:
        if 'SIGN HEADER ADDED' in line:
            sign_headers.append(line)
        elif 'Data to sign' in line or 'Generated Signature' in line:
            signing_data.append(line)
        elif 'FOUND:' in line and ('sign' in line.lower() or 'crypto' in line.lower()):
            class_names.append(line)
    
    print(f"📋 Found {len(sign_headers)} sign headers")
    print(f"📋 Found {len(signing_data)} signing operations")
    print(f"📋 Found {len(class_names)} relevant classes")
    
    if sign_headers:
        print("\n✅ SUCCESS! Captured signing data!")
        print("\nNext: Analyze frida_capture.log to implement signing")
    else:
        print("\n⚠️  No signing data captured")
        print("Try again and make sure to:")
        print("  1. Browse dramas in the app")
        print("  2. Watch videos")
        print("  3. Trigger API requests")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
print("NEXT STEPS:")
print("="*80)
print("\n1. Review frida_capture.log for signing details")
print("2. Implement GoodShortSigner.sign_request()")
print("3. Run: python goodshort_automated_scraper.py")
print("\nOR continue with HAR-based approach for immediate results\n")
