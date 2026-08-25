import requests, json

url = 'https://vidrama.asia/en/watch/slug--9515/1?provider=flickreelsv2'
hdrs = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
    'Referer': url,
    'Accept': 'text/x-component',
    'Content-Type': 'text/plain;charset=UTF-8',
}

actions = [
    '7081ea77aada73681c85542d033db73abd6689d036',
    '606146411e3ced67ff8de818206cde8d14174de4',
    '40f6b0fa0d7c9157a1eaf4e2ca9beefa1ceebb95',
    '707f344965206fac4a82b9a9bc48480737e6e744',
    '40de993eab44ea7dad5e633dbf06be01f1bf9477',
    '60197395d957204a93d4f5c392d07b434c15e8da',
    '6001c5850b92d452d5afce7dbbe6fb297776e347',
    '6074e495caacadbc4869085daa4df705f5fc8acb',
    '602a8b7bb69bab9443f84e5ebeeb4a89d33b9735',
    '70fba0aaa600d3bcf60b06fe3a590f5f1e73c382'
]

payloads = [
    ["9515", 1, "id"],
    [9515, 1, "id"],
    ["9515", "1", "id"],
    ["9515", 1],
    [9515, 1]
]

for a in actions:
    hdrs['next-action'] = a
    for p in payloads:
        try:
            r = requests.post(url, headers=hdrs, data=json.dumps(p), verify=False, timeout=3)
            if r.status_code == 200:
                print(f"SUCCESS Action {a} Payload {p}")
                print(r.text[:300])
        except Exception: pass
