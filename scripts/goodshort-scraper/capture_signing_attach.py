"""
Attach to already-running GoodShort app (more reliable than spawning)
"""

import subprocess
import time

print("""
================================================================================
🔐 FRIDA SIGNING CAPTURE (Attach Mode)
================================================================================

INSTRUCTIONS:
1. Open GoodShort app manually on LDPlayer
2. Browse to home screen (don't play videos yet)
3. Press ENTER here to attach Frida
4. Then browse dramas and watch videos in the app
5. Press Ctrl+C when done capturing

================================================================================
""")

input("Open GoodShort app, then press ENTER...")

print("\n🔍 Finding GoodShort process...")

# Get process ID
result = subprocess.run(
    ['frida-ps', '-U'],
    capture_output=True,
    text=True
)

print(result.stdout)

# Find GoodReels
pid = None
for line in result.stdout.splitlines():
    if 'goodreels' in line.lower():
        parts = line.split()
        if parts:
            pid = parts[0]
            print(f"\n✅ Found process: {line.strip()}")
            break

if not pid:
    print("\n❌ GoodShort app not running!")
    print("Please open the app and try again")
    exit(1)

print(f"\n📱 Attaching to PID: {pid}...")

# Attach Frida
frida_cmd = [
    'frida',
    '-U',
    pid,
    '-l', 'frida_comprehensive_hook.js'
]

print("Command:", ' '.join(frida_cmd))
print("\n" + "="*80)
print("FRIDA OUTPUT (Browse dramas in app now):")
print("="*80 + "\n")

try:
    process = subprocess.Popen(
        frida_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    captured_output = []
    
    print("[*] Hook injected!")
    print("[*] Browse dramas and watch videos")
    print("[*] Press Ctrl+C when done\n")
    
    for line in process.stdout:
        print(line, end='')
        captured_output.append(line)
        
        # Save important lines
        if any(keyword in line for keyword in ['SIGN', 'sign', 'Signature', 'CRYPTO']):
            with open('frida_capture.log', 'a', encoding='utf-8') as f:
                f.write(line)

except KeyboardInterrupt:
    print("\n\n" + "="*80)
    print("⏹️  CAPTURE STOPPED")
    print("="*80)
    
    process.terminate()
    
    # Save full output
    with open('frida_full_output.log', 'w', encoding='utf-8') as f:
        f.writelines(captured_output)
    
    print(f"\n✅ Captured {len(captured_output)} lines")
    print("✅ Saved to: frida_capture.log")
    
    # Analyze
    sign_count = sum(1 for line in captured_output if 'SIGN' in line or 'Signature' in line)
    crypto_count = sum(1 for line in captured_output if 'CRYPTO' in line)
    
    print(f"\n📊 Analysis:")
    print(f"  - Sign operations: {sign_count}")
    print(f"  - Crypto operations: {crypto_count}")
    
    if sign_count > 0 or crypto_count > 0:
        print("\n✅ SUCCESS! Captured signing data!")
        print("Review frida_capture.log for details")
    else:
        print("\n⚠️  No signing captured. Try:")
        print("  - Watch a video in the app")
        print("  - Go to detail pages")
        print("  - Trigger more API requests")

except Exception as e:
    print(f"\n❌ Error: {e}")

print("\n" + "="*80)
print("DONE")
print("="*80)
