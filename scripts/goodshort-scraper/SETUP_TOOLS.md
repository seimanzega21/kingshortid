# Quick Setup Guide - Decompilation Tools

## Tools Needed

### 1. JADX (Java Decompiler)
**Download:** https://github.com/skylot/jadx/releases/latest

**Quick Install:**
```powershell
# Download jadx-x.x.x.zip
# Extract to C:\tools\jadx
# Add to PATH: C:\tools\jadx\bin
```

**Or use portable:**
```powershell
# Just extract and run from folder:
cd d:\kingshortid\scripts\goodshort-scraper
.\jadx-gui.exe goodreels.apk
```

###2. APKTool (Optional, for resources)
```powershell
# Download apktool.bat + apktool.jar
# Place in C:\Windows or add to PATH
```

---

## Alternative: Online Tools (FASTER FOR NOW)

### Option 1: Use JADX GUI Directly
1. Download JADX: https://github.com/skylot/jadx/releases/latest
2. Extract zip
3. Run `jadx-gui.exe`
4. Open `goodreels.apk`
5. Search for keywords: "sign", "signature", "encrypt"

### Option 2: Focus on Frida Runtime Analysis (RECOMMENDED NOW)
Instead of static analysis, we can use Frida to:
- Hook sign generation function at runtime
- Log the inputs and outputs
- Reverse engineer from behavior

**This is FASTER and often more effective!**

---

## 🎯 Recommended Approach (Skip decompilation for now)

### Step 1: Capture API Traffic (NOW)
```bash
start-api-logger.bat
# Browse app, capture samples
# exportAll() → save JSON
```

### Step 2: Analyze Sign Pattern
From captured data, look for:
- How `sign` correlates with `timestamp`
- What other data is included
- Pattern recognition

### Step 3: Frida Runtime Hooking (If needed)
Hook the actual sign generation function:
```javascript
// Find and hook sign generator
Java.choose("com.newreading.SignUtil", {
  onMatch: function(instance) {
    instance.generateSign.implementation = function(args) {
      console.log("Sign inputs:", args);
      var result = this.generateSign(args);
      console.log("Sign output:", result);
      return result;
    }
  }
});
```

---

## ⚡ PRIORITY FOR NOW:

**1. Run API Logger (MOST IMPORTANT)**
```bash
start-api-logger.bat
```

**2. Capture samples (15 min user action)**

**3. Analyze patterns (I'll do this)**

**Decompilation can wait - runtime analysis often faster!**
