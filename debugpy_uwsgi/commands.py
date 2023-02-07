from __future__ import annotations

import sys
from abc import ABC
from abc import abstractmethod
from argparse import ArgumentParser
from typing import Any

from debugpy_uwsgi.config import Config


class Command(ABC):
    @classmethod
    @abstractmethod
    def name(cls) -> str:
        pass

    @classmethod
    @abstractmethod
    def description(cls) -> str:
        pass

    @classmethod
    @abstractmethod
    def execute(cls, options: dict[str, Any]) -> int:
        pass

    @classmethod
    def options(cls, parser: ArgumentParser) -> None:
        pass

    def __init__(self) -> None:
        raise Exception("Cannot instantiate command object")


class Patch(Command):
    @classmethod
    def name(cls) -> str:
        return "patch"

    @classmethod
    def description(cls) -> str:
        return "Patch uwsgi binary"

    @classmethod
    def execute(cls, options: dict[str, Any]) -> int:
        executable = Config.get_uwsgi_executable_path()
        backup = Config.get_uwsgi_backup_path()

        def apply_patch() -> None:
            Config.update({**options, "python": sys.executable})
            Config.save()
            executable.symlink_to(Config.get_uswgi_patch_path(), False)
            print("Patch applied!")

        try:
            if not executable.is_symlink():
                executable.rename(backup)
                apply_patch()
                return 0

            if not backup.exists():
                raise Exception("Already patched, but the backup does not exists")

            executable.unlink()
            apply_patch()
            return 0
        except Exception as e:
            print(f"Error applying patch; {e}", file=sys.stderr)

        return 1

    @classmethod
    def options(cls, parser: ArgumentParser) -> None:
        parser.add_argument(
            "--debug-port",
            type=int,
            default=5678,
            help="Port for debugpy to listen to; Default to 5678",
        )
        parser.add_argument(
            "--wait-for-debugger",
            action="store_true",
            help="Wait for debugger to connect before proceeding",
        )
        parser.add_argument(
            "--auto-reload", action="store_true", help="Auto reload on file changes"
        )


class Restore(Command):
    @classmethod
    def name(cls) -> str:
        return "restore"

    @classmethod
    def description(cls) -> str:
        return "Restore uwsgi binary"

    @classmethod
    def execute(cls, options: dict[str, Any]) -> int:
        executable = Config.get_uwsgi_executable_path()
        backup = Config.get_uwsgi_backup_path()

        try:
            if not executable.is_symlink() or not backup.exists():
                raise Exception("Either the symlink or the backup does not exists")

            executable.unlink()
            backup.rename(executable)
        except Exception as e:
            print(f"Error restoring patch; {e}", file=sys.stderr)
            return 1

        return 0
