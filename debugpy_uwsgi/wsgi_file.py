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


def application(env, start_response):
    def response(status, body):
        start_response(status, [("Content-Type", "text/html")])
        return [body.encode()]

    global app
    request_path = env.get("PATH_INFO", "")
    request_method = env.get("REQUEST_METHOD", "").upper()

    if request_path == ACTIVATE_PATH:
        if request_method != "POST":
            return response("405 Method Not Allowed", "use POST method")
        elif app:
            return response("409 Conflict", "debugpy already activated")

        try:
            Config.load()
            app = load_wsgi_file(Config.wsgi_file, Config.callable)
            debugpy.configure(python=Config.python)
            debugpy.listen(Config.debug_port)
        except Exception as e:
            print(f"Error activating debugpy; {e}", file=sys.stderr)
            return response("500 Internal Server Error", "")

        return response("200 OK", "debugpy activated")
    elif request_path == STATUS_PATH:
        if request_method != "GET":
            return response("405 Method Not Allowed", "use GET method")

        status = "active" if app else "not active"
        return response("200 OK", f"debugpy {status}")
    elif not app:
        print(
            f"Cannot process this request. First activate debugpy by visiting {ACTIVATE_PATH}",
            file=sys.stderr,
        )
        return response("400 Bad Request", "debugpy not activated")

    return app(env, start_response)


def load_wsgi_file(filename, callable):
    file_path = Path(filename).resolve()
    sys.path.insert(0, str(file_path.parent))
    spec = spec_from_loader(
        file_path.stem, SourceFileLoader(file_path.stem, str(file_path))
    )
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, callable)
