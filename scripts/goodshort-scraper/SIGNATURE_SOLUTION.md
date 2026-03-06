# GoodShort API Signature - Complete Technical Analysis

## Problem Statement

GoodShort API requires an RSA-SHA256 `sign` header for authentication. Without this signature, API calls fail with authentication errors.

---

## Analysis Results

### From HAR File Analysis

**Total Signed Requests**: 178  
**Unique Signatures**: 178 (each request has unique signature)  
**Signature Format**: BASE64 encoded  
**Signature Length**: ~344 characters

### Sample Signature Pattern

```
URL: /hwycclientreels/chapter/list
Timestamp: 1770110921865
Sign: dyh9nShkWxFr3luE5Rz9f/wxhxSTW60njyYH2AhJPnbZO8N6m...
Method: POST
POST Data: {"bookId":"31001268925"}
```

### Key Findings

1. **Request-Specific Signing**: Each request has a UNIQUE signature
   - Same endpoint + timestamp = different signatures
   - Indicates signing includes dynamic data (timestamp, body, etc.)

2. **Signature Components** (likely):
   - Timestamp
   - Request URL/path
   - POST body (JSON)
   - Possibly device ID or app version
   - Private RSA key (client-side)

3. **Challenge**: Client holds **private RSA key** embedded in APK
   - Cannot generate signatures without extracting the key
   - OR must use Frida to call signing function directly

---

## Solution Options

### Option A: Frida RPC Bridge ⭐ **BEST FOR AUTOMATION**

**How it works**:
1. Run Frida script on Android device with GoodShort app
2. Hook the signing function in the app
3. Create RPC endpoint that Python can call
4. Python script sends (url, timestamp, body) → Frida → returns signature

**Pros**:
- ✅ Fully automated once set up
- ✅ No need to reverse-engineer algorithm
- ✅ Always uses latest app signing logic
- ✅ Python can make unlimited signed requests

**Cons**:
- ⚠️ Requires Android device/emulator running 24/7
- ⚠️ Frida server must be running
- ⚠️ Setup complexity (one-time)

**Implementation Time**: 2-3 hours

---

### Option B: Extract RSA Private Key from APK

**How it works**:
1. Decompile GoodShort APK
2. Find embedded RSA private key
3. Reverse-engineer signing algorithm
4. Implement in Python

**Pros**:
- ✅ No device needed after extraction
- ✅ Fully standalone Python solution
- ✅ Fastest execution (no RPC overhead)

**Cons**:
- ⚠️ High complexity - requires APK reverse engineering
- ⚠️ Key might be obfuscated or encrypted
- ⚠️ Breaks if app updates signing logic
- ⚠️ Might violate app TOS

**Implementation Time**: 4-8 hours (depends on obfuscation)

---

### Option C: Use Captured HAR + Manual Re-Capture ⭐ **SIMPLEST**

**How it works**:
1. User captures HAR file with video playback (~30 mins)
2. Extract video URLs from HAR (already have signatures)
3. Process 10-20 dramas per session
4. Repeat as needed

**Pros**:
- ✅ No reverse engineering needed
- ✅ Works with existing HAR files
- ✅ Guaranteed to work
- ✅ Simple and reliable

**Cons**:
- ⚠️ Manual work required per batch
- ⚠️ Not fully automated
- ⚠️ Limited to dramas captured in HAR

**Implementation Time**: Already implemented! Just need video playback in HAR.

---

### Option D: On-Demand Backend Proxy

**How it works**:
1. Mobile app requests video URL from our backend
2. Backend has persistent Frida connection to Android device
3. Backend uses Frida to sign request, fetch video URL
4. Return URL to mobile app

**Pros**:
- ✅ Seamless UX - users never see loading
- ✅ No pre-fetching needed
- ✅ Always fresh video URLs

**Cons**:
- ⚠️ Requires backend modification
- ⚠️ Need dedicated Android device/VM
- ⚠️ Potential latency on first play

**Implementation Time**: 3-4 hours

---

## Recommended Approach: **Option A (Frida RPC)**

**Why**:
- Best balance of automation + reliability
- One-time setup, unlimited use
- Easy to maintain and update
- Can process 100s of dramas automatically

**Next Steps**:
1. Set up Android emulator with Frida
2. Install GoodShort app
3. Run signing hook script
4. Create Python RPC client
5. Test with 1 drama
6. Scale to batch processing

---

## Files Created

1. **hook_signing.js** - Frida script to intercept signatures
2. **run_signature_hook.bat** - Quick launcher
3. **analyze_signatures.py** - HAR analysis tool
4. **signature_analysis.json** - 178 captured signatures + metadata

---

## Decision Time

**Which option do you want to implement?**

A) Frida RPC Bridge (2-3 hours, full automation)  
B) Extract RSA Key (4-8 hours, standalone Python)  
C) Manual HAR Re-Capture (30 mins, simple)  
D) Backend Proxy (3-4 hours, best UX)

Once decided, I can proceed with implementation immediately.
