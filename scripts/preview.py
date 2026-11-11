"""Loopback preview of the built site and its local CMS media."""
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]

class Preview(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        route = urlsplit(path).path.removeprefix('/byjahr/')
        source = route.startswith('uploads/')
        self.directory = str(ROOT / ('public' if source else 'dist'))
        return super().translate_path('/' + route.lstrip('/'))

if __name__ == '__main__':
    ThreadingHTTPServer(('127.0.0.1',8021),Preview).serve_forever()
