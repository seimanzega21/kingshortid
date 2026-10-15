from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class DumpHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        data = self.rfile.read(length)
        parsed = json.loads(data.decode('utf-8'))
        filename = self.path.strip('/')
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(parsed, f, indent=2)
        print(f"Saved {filename} with {len(parsed)} entries!")
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(b'OK')

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

if __name__ == '__main__':
    server = HTTPServer(('127.0.0.1', 20199), DumpHandler)
    print("Receiver running on port 20199...")
    server.serve_forever()
