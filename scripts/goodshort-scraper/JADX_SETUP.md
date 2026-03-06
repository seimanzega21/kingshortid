# JADX Setup Guide

## Quick Download & Setup

### Option 1: Direct Download (RECOMMENDED)
1. Go to: https://github.com/skylot/jadx/releases/latest
2. Download: `jadx-1.5.0.zip` (or latest version)
3. Extract to: `d:\kingshortid\scripts\goodshort-scraper\tools\jadx`

### Option 2: via Command Line
```powershell
# Download with PowerShell
$url = "https://github.com/skylot/jadx/releases/download/v1.5.0/jadx-1.5.0.zip"
$output = "jadx.zip"
Invoke-WebRequest -Uri $url -OutFile $output

# Extract
Expand-Archive -Path jadx.zip -DestinationPath tools\jadx

# Clean up
Remove-Item jadx.zip
```

## Usage

### GUI Mode (EASIEST)
```bash
cd d:\kingshortid\scripts\goodshort-scraper
.\tools\jadx\bin\jadx-gui.bat goodreels.apk
```

**In JADX GUI:**
1. Wait for decompilation (2-5 minutes)
2. Use search (Ctrl+Shift+F) to find keywords:
   - `sign`
   - `generateSign`
   - `SignUtil`
   - `encrypt`

### Command Line Mode
```bash
.\tools\jadx\bin\jadx.bat -d output\goodreels goodreels.apk
```

Then search in output folder:
```bash
# Search for "sign" in all Java files
grep -r "sign" output\goodreels\sources\
```

## What to Look For

### Pattern 1: SignUtil Class
```java
public class SignUtil {
    private static final String SECRET = "some_secret_key";
    
    public static String generateSign(String timestamp, String path) {
        String input = timestamp + path + SECRET;
        return MD5.hash(input);
    }
}
```

### Pattern 2: Interceptor
```java
public class SignInterceptor implements Interceptor {
    @Override
    public Response intercept(Chain chain) {
        Request original = chain.request();
        String sign = calculateSign(original);
        
        Request signed = original.newBuilder()
            .addHeader("sign", sign)
            .build();
            
        return chain.proceed(signed);
    }
}
```

### Pattern 3: Network Manager
```java
public class NetworkManager {
    public Request addSignature(Request request) {
        long timestamp = System.currentTimeMillis();
        String path = request.url().encodedPath();
        String sign = SignUtils.generate(timestamp, path);
        
        return request.newBuilder()
            .addHeader("sign", sign)
            .addHeader("timestamp", String.valueOf(timestamp))
            .build();
    }
}
```

## Quick Search Commands in JADX

1. **Open JADX GUI**
2. **Text Search (Ctrl+Shift+F)**
3. **Search for:**
   - `sign` (most common)
   - `signature`
   - `hwyclientreels`
   - `api-akm.goodreels`

4. **Navigate to class**
5. **Read the code**
6. **Copy algorithm!**

## Expected Time

- Download: 1 min
- Extract: 1 min  
- Decompile: 2-5 min
- Search & Find: 10-30 min

**Total: ~15-40 minutes to find sign algorithm**

---

Ready? Download JADX and let's go! 🚀
