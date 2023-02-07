from __future__ import annotations

from argparse import ArgumentParser

from debugpy_uwsgi.commands import Command
from debugpy_uwsgi.commands import Patch
from debugpy_uwsgi.commands import Restore


def main() -> int:
    parser = ArgumentParser(description="Utility to patch uwsgi to use with debugpy")
    sub_parsers = parser.add_subparsers(dest="command")
    commands: tuple[type[Command], ...] = (Patch, Restore)

    for command in commands:
        command.options(
            sub_parsers.add_parser(command.name(), help=command.description())
        )

    options = vars(parser.parse_args())
    command_name = options.pop("command", None)

    for command in commands:
        if command.name() == command_name:
            return command.execute(options)

    parser.print_help()
    return 0
