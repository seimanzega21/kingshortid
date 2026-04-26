from playwright.sync_api import sync_playwright
import time

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        reqs = []
        def handle_request(route, request):
            if request.resource_type in ["xhr", "fetch"]:
                if 'google-analytics' not in request.url and 'crwdcntrl' not in request.url:
                    reqs.append(request.url)
            route.continue_()
            
        page.route('**/*', handle_request)
        page.goto('https://vidrama.asia/provider/shortmax', wait_until='networkidle')
        time.sleep(3)
        page.goto('https://vidrama.asia/watch/dubbingsopir-taksi-mantan-dewa-balap--846959/?provider=shortmax', wait_until='networkidle')
        time.sleep(3)
        browser.close()
        
        with open('d:/kingshortid/scripts/melolo-scraper/vidrama_reqs_full.txt', 'w') as f:
            f.write('\n'.join(reqs))

if __name__ == '__main__':
    run()
