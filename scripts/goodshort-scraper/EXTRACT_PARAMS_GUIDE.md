# Device Parameter Extraction Guide

## Quick Start

### Method 1: Use Frida Hook (Recommended)

```bash
# 1. Run the extraction script
start-extract-params.bat

# 2. Use the GoodShort app normally:
#    - Browse dramas
#    - Login if prompted
#    - Open a drama detail page

# 3. Copy the exported JSON from console
# 4. Save to: extracted-params.json
```

### Method 2: Manual Extraction

If Frida hook doesn't work, try these alternative methods:

#### Extract APK Signature MD5

```bash
# Method A: Using keytool
keytool -printcert -jarfile goodreels.apk

# Method B: Using apksigner
apksigner verify --print-certs goodreels.apk

# Then compute MD5 of the certificate
openssl dgst -md5 certificate.der
```

#### Extract GAID & Android ID

Option 1: Use ADB
```bash
# Get Android ID
adb shell settings get secure android_id

# Get GAID (if available)
adb shell content query --uri content://com.google.android.gsf.gservices --projection _id:value --where "name='advertising_id'"
```

Option 2: Use another Frida script
```javascript
Java.perform(function() {
    // Hook Google Advertising ID
    var AdvertisingIdClient = Java.use('com.google.android.gms.ads.identifier.AdvertisingIdClient');
    var Info = Java.use('com.google.android.gms.ads.identifier.AdvertisingIdClient$Info');
    
    Info.getId.implementation = function() {
        var id = this.getId();
        console.log('[GAID]:', id);
        return id;
    };
});
```

### Method 3: Use Dummy Values (May Work)

If the API doesn't strictly validate:

```typescript
const config = {
    gaid: '00000000-0000-0000-0000-000000000000',
    androidId: 'ffffffffffffffff',
    userToken: '',
    appSignatureMD5: ''
};
```

## Expected Output

After extraction, you should have:

```json
{
  "gaid": "abc12345-...",
  "androidId": "def67890...",
  "appSignatureMD5": "A1B2C3D4E5F6G7H8",
  "userToken": "eyJhbGc....",
  "packageName": "com.newreading.goodreels",
  "timestamp": "2026-01-31T16:45:00.000Z"
}
```

## Next Steps

1. **Save extracted params** to `extracted-params.json`
2. **Update API client:**
   ```typescript
   import params from './extracted-params.json';
   const client = new GoodShortAPIClient(params);
   ```
3. **Test API calls** with real params
4. **Verify authentication** works

## Troubleshooting

### Frida Hook Not Capturing

1. Check if obfuscated class names changed:
   - Search for `getGAID` in JADX
   - Update Frida script with correct class names

2. Try starting app from Frida:
   ```bash
   frida -U -f com.newreading.goodreels -l extract-device-params.js --no-pause
   ```

### API Still Returns 403

This means:
- Sign generation is correct (wouldn't get 403, would get 401)
- But device parameters are validated
- Need REAL device values, not dummy

**Solution:** Must extract actual device params from running app.
