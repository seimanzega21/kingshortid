import requests
import json
import urllib3

urllib3.disable_warnings()

COOKIE = '_fbp=fb.1.1770653154777.876935444165455244; _tt_enable_cookie=1; _ttp=01KH1JE0K4H648BY6E3FQ6EXRZ_.tt.1; _ga=GA1.1.1826262121.1771037718; HstCfa5004644=1772873251576; c_ref_5004644=https%3A%2F%2Fwww.google.com%2F; __dtsu=4C301774685394D291D3AB624E4AA57E; _pubcid=8a5abbf9-164b-422f-b349-0e1ba702ea69; _cc_id=a4a99f9a552125d19ea447bfafb9c63b; global_ui_lang=id; HstCmu5004644=1779384259258; vidrama_chat_anon=45cc06417e3a261dc8f368a8; HstCnv5004644=48; cf_clearance=N5A.kyHMnJ7RBK3hOyqybB6KddOTpRsZyEiE.fgp5kM-1779713242-1.2.1.1-9YHMfsNOniF6J54T1_JEaJY6mYbVJWOz8Kkm0raJacrpotGOYzyN_gG.Kxb7kfPxOO1wYdSenqFW0HIUwqQ57F5gqyjRbwvS8_r8rLFxIbYHNWMAahrr.iKy0dsa1krg8mVhzXDilHK71X.Iszvd8uo_CwVzbHiVUurJ8eF1DyguF2fK1vFa68H3Z5HFzZhBvVaIle1tEW3443.tH9TYjQX.7HKB9SBI2ZHkNto2vDQ2F77XP3cLmCp7GPXINCG8mrZf6l5xsxuh_xyqNp1bIRyxkUhz9IooxQKp3yV9Crri9TFW9II5q0M50yOlhCROGsKwa0AkIkKtWi.pNc5ATg; HstCla5004644=1779713242621; HstPn5004644=2; HstPt5004644=93; HstCns5004644=54; panoramaId_expiry=1779799644224'

WEB_HDRS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://vidrama.asia/',
    'Cookie': COOKIE
}

def check_drama(ns_id):
    url = f"https://vidrama.asia/api/netshortv2/movie/{ns_id}?lang=id_ID"
    try:
        r = requests.get(url, headers=WEB_HDRS, timeout=15, verify=False)
        if r.ok:
            data = r.json()
            if data.get('code') == 200:
                movie = data.get('data', {})
                return True, movie.get('title'), len(movie.get('episodes', [])), None
            else:
                return False, None, 0, f"API code {data.get('code')}: {data.get('msg')}"
        else:
            return False, None, 0, f"HTTP status {r.status_code}"
    except Exception as e:
        return False, None, 0, f"Error: {e}"

def main():
    try:
        with open('scratch/mapped_netshortv2_dramas.json', 'r') as f:
            mapped = json.load(f)
    except Exception as e:
        print("Failed to load mapping:", e)
        return
        
    verified = []
    print("Verifying mapped dramas...")
    
    for item in mapped:
        title = item['title']
        db_id = item['db_id']
        ns_id = item['netshort_id']
        
        if not ns_id:
            print(f"[-] {title} (DB: {db_id}) -> No netshort ID mapped")
            verified.append({**item, "status": "no_id", "eps_count": 0})
            continue
            
        ok, res_title, eps_count, error = check_drama(ns_id)
        if ok:
            print(f"[+] {title} (DB: {db_id}) -> Match: {res_title} (ID: {ns_id}) | Eps: {eps_count}")
            verified.append({
                **item,
                "status": "ok",
                "res_title": res_title,
                "eps_count": eps_count
            })
        else:
            print(f"[X] {title} (DB: {db_id}) -> Failed for ID {ns_id}: {error}")
            verified.append({
                **item,
                "status": "failed",
                "error": error,
                "eps_count": 0
            })
            
    with open('scratch/verified_netshortv2_dramas.json', 'w') as f:
        json.dump(verified, f, indent=2)
    print("\nVerification completed and saved to scratch/verified_netshortv2_dramas.json")

if __name__ == "__main__":
    main()
