from __future__ import annotations

import sys
from argparse import ArgumentParser
from argparse import Namespace
from pathlib import Path

from debugpy_uwsgi.config import Config


def main() -> int:
    executable = Config.get_uwsgi_executable_path()
    backup = Config.get_uwsgi_backup_path()

    parser = ArgumentParser(description="Utility to patch uwsgi to use with debugpy")
    parser.add_argument(
        "--debug-port",
        type=int,
        default=5678,
        help="Port for debugpy to listen to; Default to 6767",
    )
    parser.add_argument(
        "--wait-for-debugger",
        action="store_true",
        help="Wait for debugger to connect before proceeding",
    )
    parser.add_argument(
        "--auto-reload", action="store_true", help="Auto reload on file changes"
    )
    options = parser.parse_args()

    try:
        if not executable.is_symlink():
            executable.rename(backup)
            apply_patch(executable, options)
            return 0

        if not backup.exists():
            raise Exception("Already patched, but the backup does not exists")

        executable.unlink()
        apply_patch(executable, options)
        return 0
    except Exception as e:
        print(f"Error applying patch; {e}", file=sys.stderr)

    return 1


def apply_patch(executable: Path, options: Namespace) -> None:
    Config.update({**vars(options), "python": sys.executable})
    Config.save()
    executable.symlink_to(Config.get_uswgi_patch_path(), False)
    print("Patch applied!")
