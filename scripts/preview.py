#!/usr/bin/env python3
"""Build and serve the gallery locally; stop with Ctrl+C."""
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from build import ROOT, build

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--port', type=int, default=4173)
args = parser.parse_args()
build()
try:
    server = ThreadingHTTPServer(('127.0.0.1', args.port), partial(SimpleHTTPRequestHandler, directory=str(ROOT / 'docs')))
except OSError as error:
    parser.exit(1, f'Could not start preview: {error}\nYou can also open docs/index.html directly in your browser.\n')
print(f'Japanese: http://localhost:{args.port}/', flush=True)
print(f'English:  http://localhost:{args.port}/en/', flush=True)
print('Press Ctrl+C to stop. Re-run after editing project metadata.', flush=True)
try:
    server.serve_forever()
except KeyboardInterrupt:
    print('\nPreview stopped.')
finally:
    server.server_close()
