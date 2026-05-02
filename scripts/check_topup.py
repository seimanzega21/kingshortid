import requests

API = 'https://api.shortlovers.id'

# 1. Login dengan test account (jika ada)
login_res = requests.post(f'{API}/api/auth/login', 
    json={'email':'test@test.com','password':'123456'}, timeout=15)
print(f'Login: {login_res.status_code}')

# 2. Kalau login success, coba topup
if login_res.status_code == 200:
    token = login_res.json().get('token')
    headers = {'Authorization': f'Bearer {token}'}
    topup_res = requests.post(f'{API}/api/coins/topup', 
        json={'packageId': 2000}, headers=headers, timeout=10)
    print(f'Topup: {topup_res.status_code}')
    print(f'Topup body: {topup_res.text}')
    if topup_res.status_code == 503:
        print('SUCCESS: Topup is locked!')
    elif topup_res.status_code == 200:
        print('WARNING: Topup is still open!')
else:
    print(f'Login failed: {login_res.text[:200]}')
    print('Cannot test topup without auth')
