from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


class Config:
    debug_port = 0
    python = None
    auto_reload = False
    wait_for_debugger = False

    @classmethod
    def update(cls, data: dict[str, Any]) -> None:
        for key, value in data.items():
            setattr(cls, key, value)

    @classmethod
    def load(cls) -> None:
        with open(cls.get_path()) as file:
            cls.update(json.load(file))

    @classmethod
    def save(cls) -> None:
        with open(cls.get_path(), "w") as file:
            data = {
                key: value
                for key, value in vars(cls).items()
                if not isinstance(value, classmethod) and not key.startswith("_")
            }
            json.dump(data, file)

    @classmethod
    def get_path(cls) -> str:
        return str(cls.get_package_path() / "config.json")

    @classmethod
    def get_package_path(cls) -> Path:
        return Path(__file__).parent.resolve()

    @classmethod
    def get_uwsgi_executable_path(cls) -> Path:
        return Path(sys.executable).parent / "uwsgi"

    @classmethod
    def get_uwsgi_backup_path(cls) -> Path:
        return Path(f"{cls.get_uwsgi_executable_path()}.original")

    @classmethod
    def get_uswgi_patch_path(cls) -> Path:
        return Path(f"{cls.get_uwsgi_executable_path()}.patch")

    @classmethod
    def get_uwsgi_file_path(cls) -> Path:
        return cls.get_package_path() / "wsgi_file.py"

    @classmethod
    def get_uwsgi_callable(cls) -> str:
        return "application"
