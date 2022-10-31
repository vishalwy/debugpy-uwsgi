import json
import sys
from pathlib import Path


class Config:
    wsgi_file = None
    callable = None
    debug_port = 0
    python = None

    @classmethod
    def update(cls, data):
        for key, value in data.items():
            setattr(cls, key, value)

    @classmethod
    def load(cls):
        with open(cls.get_path()) as file:
            cls.update(json.load(file))

    @classmethod
    def save(cls):
        with open(cls.get_path(), "w") as file:
            data = {
                key: value
                for key, value in vars(cls).items()
                if not isinstance(value, classmethod) and not key.startswith("_")
            }
            return json.dump(data, file)

    @classmethod
    def get_path(cls):
        return str(cls.get_package_path() / "config.json")

    @classmethod
    def get_package_path(cls):
        return Path(__file__).parent.resolve()

    @classmethod
    def get_uwsgi_executable_path(cls):
        return Path(sys.executable).parent / "uwsgi"

    @classmethod
    def get_uwsgi_backup_path(cls):
        return Path(f"{cls.get_uwsgi_executable_path()}.original")

    @classmethod
    def get_uswgi_patch_path(cls):
        return Path(f"{cls.get_uwsgi_executable_path()}.patch")

    @classmethod
    def get_uwsgi_file_path(cls):
        return cls.get_package_path() / "wsgi_file.py"
