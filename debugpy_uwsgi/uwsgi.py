import argparse
import os
import sys

from debugpy_uwsgi.config import Config


def main():
    executable = str(Config.get_uwsgi_backup_path())
    argv = arguments("--processes 1 --threads 1")
    argv.extend(arguments(f"--binary-path {executable}", 1))

    parser = argparse.ArgumentParser(
        description="Patch for uwsgi to modify arguments and enable debugging"
    )
    parser.add_argument("--wsgi-file", required=True)
    parser.add_argument("--callable", default="application")
    parser.add_argument("--processes")
    parser.add_argument("--threads")
    parser.add_argument("--binary-path")
    parser.add_argument("--py-auto-reload", type=int)
    parser.add_argument("--enable-threads", action="store_true")
    parser.add_argument("--pyargv")
    parsed, unparsed = parser.parse_known_args()

    try:
        Config.load()
        pyargv = f"--wsgi-entry {parsed.wsgi_file}:{parsed.callable}"
        argv.extend(arguments(f"--pyargv {parsed.pyargv or ''} {pyargv}", 1))
        argv.extend(arguments(f"--wsgi-file {Config.get_uwsgi_file_path()}", 1))
        argv.extend(arguments(f"--callable {Config.get_uwsgi_callable()}", 1))

        if Config.auto_reload:
            argv.extend(arguments("--py-auto-reload 1"))

        if not parsed.enable_threads:
            argv.extend(arguments("--enable-threads"))

        argv.extend(unparsed)
        os.execve(executable, [executable] + argv, os.environ)
    except Exception as e:
        print(f"Error spawning {executable}: {e}", file=sys.stderr)

    return 1


def arguments(cmdline_args, max_split=-1):
    return cmdline_args.split(maxsplit=max_split)
