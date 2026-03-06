"""
Extract APK Signature MD5
"""

import zipfile
import hashlib
import sys

def get_apk_signature_md5(apk_path):
    """
    Extract signature from APK and compute MD5
    Same logic as Android's d.a(Context) method
    """
    try:
        # Open APK as ZIP
        with zipfile.ZipFile(apk_path, 'r') as apk:
            # Look for signature files
            signature_files = [f for f in apk.namelist() 
                             if f.startswith('META-INF/') and 
                             (f.endswith('.RSA') or f.endswith('.DSA') or f.endswith('.EC'))]
            
            if not signature_files:
                print("ERROR: No signature files found in APK!")
                return None
            
            # Use first signature file (usually CERT.RSA)
            sig_file = signature_files[0]
            print(f"Found signature file: {sig_file}")
            
            # Read signature bytes
            sig_bytes = apk.read(sig_file)
            print(f"Signature size: {len(sig_bytes)} bytes")
            
            # Compute MD5
            md5 = hashlib.md5(sig_bytes).hexdigest()
            
            # Return uppercase (as per Android implementation)
            return md5.upper()
    
    except Exception as e:
        print(f"ERROR: {e}")
        return None

if __name__ == '__main__':
    apk_path = 'tools/base-emulator.apk'
    
    print("Extracting APK Signature MD5...")
    print(f"APK: {apk_path}\n")
    
    md5 = get_apk_signature_md5(apk_path)
    
    if md5:
        print(f"\n✅ SUCCESS!")
        print(f"APK Signature MD5: {md5}")
        print(f"\nThis is the value needed for appSignatureMD5 parameter!")
        
        # Save to file
        with open('apk-signature-md5.txt', 'w') as f:
            f.write(md5)
        print(f"\nSaved to: apk-signature-md5.txt")
    else:
        print("\n❌ FAILED to extract signature MD5")
        sys.exit(1)
