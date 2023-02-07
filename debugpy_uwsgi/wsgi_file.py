from __future__ import annotations

import sys
import traceback
from argparse import ArgumentParser
from http import HTTPStatus
from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec
from importlib.util import spec_from_loader
from pathlib import Path
from typing import Callable

import debugpy

from debugpy_uwsgi.config import Config

ACTIVATE_PATH = "/debugpy/activate"
STATUS_PATH = "/debugpy/status"

app: Callable | None = None
debugpy_initialized = False
wsgi_entry: tuple[str, str] | None = None


def application(env: dict[str, str], start_response: Callable) -> list[bytes]:
    def response(status: HTTPStatus, body: str) -> list[bytes]:
        start_response(
            f"{status.value} {status.phrase}", [("Content-Type", "text/html")]
        )
        return [body.encode()]

    global app
    request_path = env.get("PATH_INFO", "")
    request_method = env.get("REQUEST_METHOD", "").upper()

    if request_path == ACTIVATE_PATH:
        if request_method != "POST":
            return response(HTTPStatus.METHOD_NOT_ALLOWED, "Use POST method")
        elif app:
            return response(HTTPStatus.CONFLICT, "Debugpy already activated")

        try:
            init_debugpy()
            app = load_wsgi_file(*get_wsgi_entry())
        except Exception as e:
            print(f"Error activating debugpy; {e}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            return response(HTTPStatus.INTERNAL_SERVER_ERROR, "Something went wrong")

        return response(HTTPStatus.OK, "Debugpy activated")
    elif request_path == STATUS_PATH:
        if request_method != "GET":
            return response(HTTPStatus.METHOD_NOT_ALLOWED, "Use GET method")

        status = "active" if app else "not active"
        return response(HTTPStatus.OK, f"Debugpy {status}")
    elif not app:
        print(
            f"Cannot process this request. First activate debugpy by visiting {ACTIVATE_PATH}",
            file=sys.stderr,
        )
        return response(HTTPStatus.BAD_REQUEST, "Debugpy not activated")

    return app(env, start_response)


def init_debugpy() -> None:
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


def get_wsgi_entry() -> tuple[str, str]:
    global wsgi_entry

    if wsgi_entry:
        return wsgi_entry

    parser = ArgumentParser()
    parser.add_argument("--wsgi-entry")
    parsed, unparsed = parser.parse_known_args()
    program = sys.argv[0]
    sys.argv.clear()
    sys.argv.extend([program] + unparsed)
    wsgi_file, callable = parsed.wsgi_entry.split(":", 1)
    wsgi_entry = (wsgi_file, callable)
    return wsgi_entry


def load_wsgi_file(filename: str, callable: str) -> Callable:
    file_path = Path(filename).resolve()
    sys.path.insert(0, str(file_path.parent))
    spec = spec_from_loader(
        file_path.stem, SourceFileLoader(file_path.stem, str(file_path))
    )

    if not spec or not spec.loader:
        raise Exception(f"Could not create spec from {file_path}")

    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, callable)
