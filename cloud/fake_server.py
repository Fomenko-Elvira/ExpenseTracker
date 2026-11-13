"""
Мини-сервер, имитирующий Firebase Realtime Database.
Нужен для тестов и для демонстрации синхронизации без интернета и аккаунта Google.

Запуск:   python -m cloud.fake_server
Потом в cloud/config.py:   DATABASE_URL = 'http://127.0.0.1:8000'
"""
import json
from http.server import BaseHTTPRequestHandler, HTTPServer


class _Handler(BaseHTTPRequestHandler):
    def _send_json(self, payload):
        body = json.dumps(payload).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        self._send_json(self.server.data)          # пустая «база» отдаёт null, как Firebase

    def do_PUT(self):
        length = int(self.headers.get('Content-Length', 0))
        self.server.data = json.loads(self.rfile.read(length).decode('utf-8'))
        self._send_json(self.server.data)

    def log_message(self, *args):                   # не засоряем консоль
        pass


def make_server(port=8000):
    server = HTTPServer(('127.0.0.1', port), _Handler)
    server.data = None
    return server


if __name__ == '__main__':
    print('Тестовое облако запущено: http://127.0.0.1:8000  (остановить: Ctrl+C)')
    make_server().serve_forever()
