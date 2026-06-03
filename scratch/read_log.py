with open('tunnel_backend.log', 'r', encoding='utf-16') as f:
    text = f.read()
print("=== tunnel_backend.log (last 1000 chars) ===")
print(text[-1000:])
