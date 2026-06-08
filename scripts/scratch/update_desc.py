import requests

url = 'https://api.shortlovers.id/api/admin/dramas/br6gkk6eikpkqskl8vblyz40'
hdr = {
    'x-admin-key': '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14',
    'Content-Type': 'application/json'
}

payload = {
    'description': 'Drama pernikahan kontrak dan romansa menarik "Suami Jahat Kaya, Tolong Bangun" bertema Pernikahan Kilat. Mengisahkan perjuangan cinta seorang wanita yang terpaksa menikah dengan miliarder koma demi keluarganya, serta intrik rahasia yang terungkap setelah sang suami terbangun.'
}

# Use PATCH!
r = requests.patch(url, headers=hdr, json=payload)
print("Status Code:", r.status_code)
print("Response:", r.text)
