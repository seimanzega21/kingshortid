"""
GoodShort Token Auto-Refresh System
Automatically extracts fresh tokens from running app via Frida
"""

import json
import subprocess
import time
import re
from pathlib import Path
from typing import Optional, Dict

class GoodShortTokenManager:
    def __init__(self):
        self.token_file = Path("auth_tokens.json")
        self.current_token = None
        self.device_id = None
        self.last_refresh = 0
        self.token_ttl = 3600  # 1 hour default
        
    def load_tokens(self) -> bool:
        """Load saved tokens from file"""
        if self.token_file.exists():
            with open(self.token_file, 'r') as f:
                data = json.load(f)
                self.current_token = data.get('token')
                self.device_id = data.get('device_id')
                self.last_refresh = data.get('last_refresh', 0)
                return True
        return False
    
    def save_tokens(self):
        """Save tokens to file"""
        data = {
            'token': self.current_token,
            'device_id': self.device_id,
            'last_refresh': time.time()
        }
        with open(self.token_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def is_token_expired(self) -> bool:
        """Check if token needs refresh"""
        if not self.current_token:
            return True
        
        elapsed = time.time() - self.last_refresh
        return elapsed > self.token_ttl
    
    def capture_token_from_frida(self) -> Optional[Dict]:
        """
        Use Frida to intercept app requests and extract fresh token
        """
        print("🔍 Capturing fresh token via Frida...")
        
        frida_script = """
        Java.perform(function() {
            var OkHttpClient = Java.use('okhttp3.OkHttpClient');
            var Request = Java.use('okhttp3.Request');
            
            // Hook request builder
            var Interceptor = Java.registerClass({
                name: 'com.custom.TokenInterceptor',
                implements: [Java.use('okhttp3.Interceptor')],
                methods: {
                    intercept: function(chain) {
                        var request = chain.request();
                        var url = request.url().toString();
                        
                        // Only capture GoodShort API requests
                        if (url.indexOf('goodreels') !== -1 || url.indexOf('xintaicz') !== -1) {
                            var headers = request.headers();
                            
                            // Extract token
                            var auth = headers.get('authorization');
                            var sign = headers.get('sign');
                            
                            if (auth) {
                                send({
                                    type: 'token',
                                    token: auth,
                                    sign: sign,
                                    url: url
                                });
                            }
                        }
                        
                        return chain.proceed(request);
                    }
                }
            });
            
            console.log('[*] Token interceptor attached');
        });
        """
        
        # Save script temporarily
        script_path = Path("frida_token_capture.js")
        with open(script_path, 'w') as f:
            f.write(frida_script)
        
        try:
            # Run Frida to capture tokens
            cmd = f"frida -U -n GoodShort -l {script_path} --no-pause"
            
            # This would run Frida and capture output
            # For now, return None (needs actual Frida execution)
            print("⚠️ Frida token capture needs to be implemented with subprocess")
            return None
            
        except Exception as e:
            print(f"❌ Frida capture failed: {e}")
            return None
        finally:
            if script_path.exists():
                script_path.unlink()
    
    def extract_from_har(self, har_path: str) -> bool:
        """Extract token from HAR file (fallback method)"""
        print(f"📄 Extracting token from {har_path}...")
        
        try:
            with open(har_path, 'r', encoding='utf-8') as f:
                har = json.load(f)
            
            entries = har['log']['entries']
            
            # Find first GoodShort API request with auth
            for entry in entries:
                if 'api-akm.goodreels' in entry['request']['url']:
                    headers = entry['request']['headers']
                    
                    for h in headers:
                        if h['name'].lower() == 'authorization':
                            token = h['value'].replace('Bearer ', '')
                            self.current_token = token
                            self.last_refresh = time.time()
                            self.save_tokens()
                            print(f"✅ Token extracted: {token[:50]}...")
                            return True
            
            print("❌ No token found in HAR")
            return False
            
        except Exception as e:
            print(f"❌ Error reading HAR: {e}")
            return False
    
    def refresh_if_needed(self, har_path: Optional[str] = None) -> bool:
        """
        Smart refresh: check if token expired, refresh if needed
        """
        if not self.is_token_expired():
            print("✅ Token still valid")
            return True
        
        print("⚠️ Token expired, refreshing...")
        
        # Try Frida first
        captured = self.capture_token_from_frida()
        if captured:
            self.current_token = captured['token']
            self.save_tokens()
            return True
        
        # Fallback to HAR
        if har_path and Path(har_path).exists():
            return self.extract_from_har(har_path)
        
        print("❌ Token refresh failed")
        return False
    
    def get_auth_header(self) -> Optional[str]:
        """Get current authorization header value"""
        if self.current_token:
            return f"Bearer {self.current_token}"
        return None


# Usage example
if __name__ == "__main__":
    manager = GoodShortTokenManager()
    
    # Try load from file
    if not manager.load_tokens():
        print("No saved tokens, extracting from HAR...")
        if not manager.extract_from_har("fresh_capture.har"):
            print("Failed to get token!")
            exit(1)
    
    # Auto refresh if needed
    manager.refresh_if_needed(har_path="fresh_capture.har")
    
    # Use token
    auth_header = manager.get_auth_header()
    print(f"\n✅ Current token: {auth_header[:70]}...")
    
    # Save for next time
    manager.save_tokens()
