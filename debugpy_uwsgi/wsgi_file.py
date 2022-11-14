import argparse
import sys
from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec
from importlib.util import spec_from_loader
from pathlib import Path

import debugpy

from debugpy_uwsgi.config import Config

ACTIVATE_PATH = "/debugpy/activate"
STATUS_PATH = "/debugpy/status"

app = None
debugpy_initialized = False
wsgi_entry = None


def application(env, start_response):
    def response(status, body):
        start_response(status, [("Content-Type", "text/html")])
        return [body.encode()]

    global app
    request_path = env.get("PATH_INFO", "")
    request_method = env.get("REQUEST_METHOD", "").upper()

    if request_path == ACTIVATE_PATH:
        if request_method != "POST":
            return response("405 Method Not Allowed", "Use POST method")
        elif app:
            return response("409 Conflict", "Debugpy already activated")

        try:
            init_debugpy()
            app = load_wsgi_file(*get_wsgi_entry())
        except Exception as e:
            print(f"Error activating debugpy; {e}", file=sys.stderr)
            return response("500 Internal Server Error", "Something went wrong")

        return response("200 OK", "Debugpy activated")
    elif request_path == STATUS_PATH:
        if request_method != "GET":
            return response("405 Method Not Allowed", "Use GET method")

        status = "active" if app else "not active"
        return response("200 OK", f"Debugpy {status}")
    elif not app:
        print(
            f"Cannot process this request. First activate debugpy by visiting {ACTIVATE_PATH}",
            file=sys.stderr,
        )
        return response("400 Bad Request", "Debugpy not activated")

    return app(env, start_response)


def init_debugpy():
    global debugpy_initialized

    if debugpy_initialized:
        return

    Config.load()
    debugpy.configure(python=Config.python)
    debugpy.listen(Config.debug_port)
    debugpy_initialized = True

    if not Config.wait_for_debugger:
        return

    print("Debugpy is waiting for connection...")
    debugpy.wait_for_client()


def get_wsgi_entry():
    global wsgi_entry

    if wsgi_entry:
        return wsgi_entry

    parser = argparse.ArgumentParser()
    parser.add_argument("--wsgi-entry")
    parsed, unparsed = parser.parse_known_args()
    program = sys.argv[0]
    sys.argv.clear()
    sys.argv.extend([program] + unparsed)
    wsgi_file, callable = parsed.wsgi_entry.split(":", 1)
    wsgi_entry = (wsgi_file, callable)
    return wsgi_entry


def load_wsgi_file(filename, callable):
    file_path = Path(filename).resolve()
    sys.path.insert(0, str(file_path.parent))
    spec = spec_from_loader(
        file_path.stem, SourceFileLoader(file_path.stem, str(file_path))
    )
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, callable)
