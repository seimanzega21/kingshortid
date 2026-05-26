import requests, time
hdr={'cookie':'_tt_enable_cookie=1;'}
def check(ep):
    r = requests.get(f'https://vidrama.asia/api/dramabox3/watch?bookId=42000012098&episode={ep}&lang=in', headers=hdr)
    if not r.ok: return False
    return r.json().get('success') == True

low = 1
high = 150
ans = 1
while low <= high:
    mid = (low+high)//2
    if check(mid):
        ans = mid
        low = mid + 1
    else:
        high = mid - 1
print('TOTAL EPS:', ans)
