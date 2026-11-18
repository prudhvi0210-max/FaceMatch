"""Loopback-only FaceMatch UI. Start: python app/ui.py"""
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import secrets
import sqlite3
import threading
import webbrowser

from database import create_table
import ui_service
from settings import SIMILARITY_THRESHOLD

WEB = Path(__file__).resolve().parent / 'web'
MAX_BODY = 28 * 1024 * 1024


class LocalServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address):
        super().__init__(address, Handler)
        self.token = secrets.token_urlsafe(32)
        self.operation = threading.Lock()
        self.origin = f'http://127.0.0.1:{self.server_port}'


class Handler(BaseHTTPRequestHandler):
    def setup(self):
        super().setup()
        self.connection.settimeout(30)

    def log_message(self, *args):
        pass  # Do not write names, uploads or recognition results to access logs.

    def reply(self, status, data, content_type='application/json'):
        if content_type == 'application/json':
            data = json.dumps(data, allow_nan=False).encode()
        try:
            self.send_response(status)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(data)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('X-Frame-Options', 'DENY')
            self.send_header('Referrer-Policy', 'no-referrer')
            self.send_header('Content-Security-Policy', "default-src 'self'; img-src 'self' blob:; style-src 'self'; script-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
            self.end_headers()
            self.wfile.write(data)
        except (BrokenPipeError, ConnectionResetError, TimeoutError):
            pass  # A closed tab must not turn a completed operation into a failure.

    def valid_host(self):
        return self.headers.get('Host') == f'127.0.0.1:{self.server.server_port}'

    def do_GET(self):
        if not self.valid_host():
            return self.reply(403, {'error': 'Open the app using its 127.0.0.1 address.'})
        assets = {'/': ('index.html', 'text/html; charset=utf-8'), '/app.css': ('app.css', 'text/css; charset=utf-8'), '/app.js': ('app.js', 'text/javascript; charset=utf-8')}
        if self.path in assets:
            filename, kind = assets[self.path]
            return self.reply(200, WEB.joinpath(filename).read_bytes(), kind)
        if self.path == '/api/state':
            try:
                return self.reply(200, dict(people=ui_service.people(), token=self.server.token, threshold=SIMILARITY_THRESHOLD))
            except (sqlite3.Error, OSError):
                return self.reply(500, {'error': 'The local database could not be read.'})
        self.reply(404, {'error': 'Page not found.'})

    def do_POST(self):
        if (not self.valid_host() or self.headers.get('Origin') != self.server.origin
                or not secrets.compare_digest(self.headers.get('X-FaceMatch-Token', ''), self.server.token)):
            return self.reply(403, {'error': 'Refresh the FaceMatch page before trying again.'})
        if self.path not in {'/api/recognize', '/api/register'}:
            return self.reply(404, {'error': 'Operation not found.'})
        if self.headers.get('Content-Type') != 'application/json':
            return self.reply(415, {'error': 'Expected a photograph upload.'})
        try:
            length = int(self.headers.get('Content-Length', '0'))
        except ValueError:
            return self.reply(400, {'error': 'Invalid upload length.'})
        if length <= 0 or length > MAX_BODY:
            return self.reply(413, {'error': 'Choose a photograph smaller than 20 MB.'})
        if not self.server.operation.acquire(blocking=False):
            return self.reply(409, {'error': 'Another photo is being processed. Please wait and try again.'})
        try:
            payload = json.loads(self.rfile.read(length))
            if not isinstance(payload, dict):
                raise ValueError('Invalid upload.')
            action = ui_service.recognize if self.path == '/api/recognize' else ui_service.register
            result = action(payload)
            self.reply(200, result)
        except (ValueError, UnicodeError):
            # Explicit service errors are user-readable, but model errors may contain paths.
            import sys
            error = sys.exc_info()[1]
            message = str(error)
            if len(message) > 240 or '/private/' in message or '/Users/' in message:
                message = 'The photograph could not be processed. Please try a clear photo with one face.'
            self.reply(400, {'error': message})
        except Exception:
            self.reply(500, {'error': 'Processing failed. Check the local model setup, then try again. No registration was completed.'})
        finally:
            self.server.operation.release()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--no-browser', action='store_true')
    args = parser.parse_args()
    try:
        create_table()
        server = LocalServer(('127.0.0.1', args.port))
    except (OSError, sqlite3.Error) as error:
        parser.exit(1, f'FaceMatch could not start: {error}\nTry another port with --port 8766.\n')
    print(f'FaceMatch is running at {server.origin}\nPress Control-C to stop.')
    if not args.no_browser:
        webbrowser.open(server.origin)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nFaceMatch stopped.')
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
