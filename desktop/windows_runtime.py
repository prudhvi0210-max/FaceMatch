"""Portable support for the Windows shell. Import before any FaceMatch modules."""
import os
from pathlib import Path
import threading


def configure_storage(environ=None, home=None):
    """Keep mutable records and model cache outside Program Files/frozen resources."""
    env = os.environ if environ is None else environ
    home = Path.home() if home is None else Path(home)
    local = Path(env.get('LOCALAPPDATA') or home/'AppData'/'Local')
    root = Path(env.get('FACEMATCH_DATA_DIR') or local/'FaceMatch').expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    env['FACEMATCH_DATA_DIR'] = str(root)
    if not env.get('DEEPFACE_HOME'):env['DEEPFACE_HOME'] = str(root)
    return root


def start_service():
    """Use the shared, loopback-only HTTP API with an automatically assigned port."""
    from database import create_table
    from ui import LocalServer
    create_table()
    server = LocalServer(('127.0.0.1', 0))
    thread = threading.Thread(target=server.serve_forever, name='FaceMatch-local-service', daemon=True)
    thread.start()
    return server, thread


def stop_service(server, thread):
    server.shutdown()
    server.server_close()
    thread.join(timeout=5)
