import requests
import json

headers = {
    'accept': 'application/json, text/plain, */*',
    'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Mobile Safari/537.36',
    'cookie': 'sb-gkcnbnlfqdlotnjaizxx-auth-token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImdrY25ibmxmcWRsb3RuamFpenh4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njg0NjQ5ODEsImV4cCI6MjA4NDA0MDk4MX0.EFP6qcUAT_Dk0bV3ycjxpduZ1MBuhCWOTE0ArIsS9Xo;'
}

url = "https://vidrama.asia/api/shortmax?action=stream&id=dubbingsopir-taksi-mantan-dewa-balap--846959&episode=0"

r = requests.get(url, headers=headers)
print(f"Status: {r.status_code}")
try:
    print(json.dumps(r.json(), indent=2))
except:
    print(r.text)
