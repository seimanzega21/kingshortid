import os
print("Available keys in env:")
for k in os.environ:
    if "key" in k.lower() or "token" in k.lower() or "secret" in k.lower() or "auth" in k.lower():
        print(f"  - {k}: {'***' if os.environ[k] else 'empty'}")
