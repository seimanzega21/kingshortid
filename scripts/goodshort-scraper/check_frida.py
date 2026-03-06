"""
Check Frida server and auto-start if needed
"""

import subprocess
import time

def check_frida_server():
    """Check if Frida server is running"""
    
    print("🔍 Checking Frida server on device...")
    
    # Check process
    result = subprocess.run(
        ['adb', '-s', '127.0.0.1:5555', 'shell', 'ps | grep frida-server'],
        capture_output=True,
        text=True
    )
    
    if 'frida-server' in result.stdout:
        print("✅ Frida server is running")
        return True
    else:
        print("❌ Frida server not running")
        return False


def start_frida_server():
    """Start Frida server on device"""
    
    print("\n📱 Starting Frida server...")
    
    # Kill any existing
    subprocess.run(['adb', '-s', '127.0.0.1:5555', 'shell', 'su -c "killall frida-server"'], 
                   capture_output=True)
    time.sleep(1)
    
    # Start server
    subprocess.Popen(
        ['adb', '-s', '127.0.0.1:5555', 'shell', 
         'su -c "/data/local/tmp/frida-server &"'],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    
    time.sleep(2)
    
    if check_frida_server():
        print("✅ Frida server started successfully")
        return True
    else:
        print("❌ Failed to start Frida server")
        print("\nManual steps:")
        print("1. adb -s 127.0.0.1:5555 shell")
        print("2. su")
        print("3. /data/local/tmp/frida-server &")
        return False


def list_frida_processes():
    """List app processes via Frida"""
    
    print("\n📋 Listing GoodShort processes...")
    
    result = subprocess.run(
        ['frida-ps', '-U'],
        capture_output=True,
        text=True
    )
    
    print(result.stdout)
    
    if 'goodreels' in result.stdout.lower():
        print("✅ GoodShort app is running")
        return True
    else:
        print("⚠️  GoodShort app not found")
        print("Please open the GoodShort app manually")
        return False


if __name__ == "__main__":
    print("="*60)
    print("FRIDA SETUP CHECK")
    print("="*60 + "\n")
    
    # Check if running
    if not check_frida_server():
        # Try to start
        start_frida_server()
    
    # List processes
    list_frida_processes()
    
    print("\n" + "="*60)
    print("✅ Ready to run Frida hook!")
    print("="*60)
    print("\nRun:")
    print("  frida -U -f com.newreading.goodreels -l frida_comprehensive_hook.js --no-pause")
