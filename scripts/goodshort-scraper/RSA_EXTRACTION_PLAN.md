# RSA Key Extraction & Signing Implementation Plan

## Objective
Extract RSA private key from GoodShort APK and implement signing algorithm in Python for fully autonomous API access.

---

## Phase 1: APK Acquisition & Decompilation

### Step 1: Get APK from Device
```bash
# List installed packages
adb shell pm list packages | grep -i good

# Get APK path
adb shell pm path com.newreading.goodreels

# Pull APK
adb pull /data/app/~~XXX/com.newreading.goodreels-YYY/base.apk goodshort.apk
```

### Step 2: Decompile APK
```bash
# Using apktool (resources + smali)
apktool d goodshort.apk -o goodshort_decompiled

# Using jadx (Java source)
jadx -d goodshort_jadx goodshort.apk
```

---

## Phase 2: Locate RSA Key & Signing Logic

### Common Locations to Check:

**1. Assets Folder**
- `assets/` - PEM files, key files
- `assets/keys/` - dedicated key storage
- Look for: `.pem`, `.key`, `.der`, `private_key`, `rsa_key`

**2. Resources (res/)**
- `res/raw/` - raw resource files
- Encoded as base64 strings in XML

**3. Native Libraries (.so files)**
- `lib/arm64-v8a/libXXX.so`
- Key might be in native code (harder to extract)

**4. Java/Kotlin Code**
- Search for:
  - `"RSA"`, `"SHA256"`, `"PKCS8"`
  - `Signature.getInstance`
  - `KeyFactory`, `PrivateKey`
  - `Base64.encode`
  - Class names with "Sign", "Crypto", "Security"

### Search Commands:
```bash
# Search for RSA references
grep -r "RSA" goodshort_decompiled/
grep -r "-----BEGIN" goodshort_decompiled/

# Search for signing classes
find goodshort_jadx -name "*Sign*"
find goodshort_jadx -name "*Crypto*"

# Search in smali
grep -r "Signature;->getInstance" goodshort_decompiled/smali/
```

---

## Phase 3: Extract Key & Algorithm

### If Key is in Assets:
```python
# Usually base64 encoded
import base64
key_b64 = "MIIEvQIBAD..."  # From assets
key_bytes = base64.b64decode(key_b64)

# Save as PEM
with open('private_key.pem', 'wb') as f:
    f.write(key_bytes)
```

### If Key is Hardcoded:
```java
// Example from decompiled code
String privateKey = "MIIEvQIBADANBgkqhkiG9w0BAQE...";
```

### Identify Signing Algorithm:
Look for code like:
```java
Signature signature = Signature.getInstance("SHA256withRSA");
signature.initSign(privateKey);
signature.update(dataToSign.getBytes());
byte[] signBytes = signature.sign();
String signBase64 = Base64.encodeToString(signBytes);
```

### Identify Data Being Signed:
```java
// Common patterns:
String dataToSign = timestamp + url + body + appVersion;
// OR
String dataToSign = MD5(timestamp + url + body);
// OR sorted params
```

---

## Phase 4: Implement in Python

### Template:
```python
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA256
import base64

class GoodShortSigner:
    def __init__(self, private_key_pem):
        self.key = RSA.import_key(private_key_pem)
        self.signer = PKCS1_v1_5.new(self.key)
    
    def sign_request(self, url, timestamp, body=None):
        # Reconstruct signing data (from reverse engineering)
        data_to_sign = f"{timestamp}{url}"
        if body:
            data_to_sign += body
        
        # Sign
        h = SHA256.new(data_to_sign.encode('utf-8'))
        signature = self.signer.sign(h)
        
        # Encode to base64
        return base64.b64encode(signature).decode('utf-8')
```

---

## Phase 5: Testing & Validation

### Test Script:
```python
# Compare with captured signature from HAR
signer = GoodShortSigner(private_key)

# Use data from signature_analysis.json
test_url = "/hwycclientreels/chapter/list"
test_timestamp = "1770110921865"
test_body = '{"bookId":"31001268925"}'

generated_sign = signer.sign_request(test_url, test_timestamp, test_body)
captured_sign = "dyh9nShkWxFr3luE5Rz9f/wxhxSTW60..."  # From HAR

print(f"Generated: {generated_sign[:50]}...")
print(f"Captured:  {captured_sign[:50]}...")
print(f"Match: {generated_sign == captured_sign}")
```

### If No Match:
- Try different data combinations
- Check order of parameters
- Check encoding (UTF-8, UTF-16, etc.)
- Check if additional headers are included
- May need to include device ID, app version, etc.

---

## Phase 6: Integration

Once working:
```python
# Update auto_fetch_videos.py
from goodshort_signer import GoodShortSigner

signer = GoodShortSigner(PRIVATE_KEY)

def fetch_video_url(book_id, chapter_id):
    timestamp = str(int(time.time() * 1000))
    url = "/hwycclientreels/chapter/load"
    body = json.dumps({"bookId": book_id, "chapterId": chapter_id})
    
    sign = signer.sign_request(url, timestamp, body)
    
    headers = {
        'sign': sign,
        'timestamp': timestamp,
        'User-Agent': 'okhttp/4.9.1'
    }
    
    response = requests.post(
        f"https://api-akm.goodreels.com{url}",
        json={"bookId": book_id, "chapterId": chapter_id},
        headers=headers
    )
    
    return response.json()
```

---

## Tools Needed

```bash
# Install decompilation tools
pip install apkleaks

# For Windows:
# Download from GitHub:
# - apktool: https://github.com/iBotPeaches/Apktool
# - jadx: https://github.com/skylot/jadx
```

---

## Timeline

- Phase 1 (APK extraction): 15 mins
- Phase 2 (Locate key): 30-60 mins
- Phase 3 (Extract & understand): 30-60 mins  
- Phase 4 (Implement): 30 mins
- Phase 5 (Test & debug): 60-120 mins
- Phase 6 (Integration): 30 mins

**Total**: 3-5 hours

---

## Next Action

**Ready to start?** I'll guide you through each phase:

1. First, extract APK from your device
2. We'll decompile and search for the key
3. Implement signing in Python
4. Test with real API calls
5. Integrate into batch processor

Let me know when you're ready to pull the APK from your device!
