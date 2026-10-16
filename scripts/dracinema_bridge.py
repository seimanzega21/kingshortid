from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
import json
import queue
import threading

task_queue = queue.Queue()
result_map = {}
result_events = {}

class BridgeHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass # Quiet

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    # Browser polls this to get pending playback requests
    def do_GET(self):
        if self.path == '/poll':
            try:
                task = task_queue.get(timeout=20)
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(task).encode('utf-8'))
            except queue.Empty:
                self.send_response(204) # No Content
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        data = self.rfile.read(length)
        body = json.loads(data.decode('utf-8'))

        # Browser posts result here
        if self.path == '/result':
            req_id = body.get('id')
            if req_id and req_id in result_events:
                result_map[req_id] = body.get('result')
                result_events[req_id].set()
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(b'OK')

        # Python client asks for playback here
        elif self.path == '/request':
            req_id = body.get('id')
            event = threading.Event()
            result_events[req_id] = event
            task_queue.put(body)

            # Wait for browser to respond (up to 30s)
            got_res = event.wait(timeout=30)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            if got_res and req_id in result_map:
                res = result_map.pop(req_id)
                del result_events[req_id]
                self.wfile.write(json.dumps({'ok': True, 'data': res}).encode('utf-8'))
            else:
                if req_id in result_events: del result_events[req_id]
                if req_id in result_map: del result_map[req_id]
                self.wfile.write(json.dumps({'ok': False, 'error': 'timeout'}).encode('utf-8'))

if __name__ == '__main__':
    server = ThreadingHTTPServer(('127.0.0.1', 20199), BridgeHandler)
    print("Multi-threaded bridge server running on http://127.0.0.1:20199")
    server.serve_forever()
