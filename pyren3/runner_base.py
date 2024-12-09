import abc
import os
import sys
from typing import Callable

from pyren3.enums import Command
from pyren3.settings import Settings
from pyren3.utils import get_args_for_command_and_settings

registered_runners = []


def get_runner(path: str):
    for runner in registered_runners:
        if runner.path == path:
            return runner

    print(
        f"No runner found: {path}\nAvailable runners: {', '.join(r.path for r in registered_runners)}"
    )
    sys.exit(1)


class BaseRunner(abc.ABC):
    commands: list[Command]
    executable: Callable
    path: str

    def __init__(self, executable: Callable):
        self.executable = executable
        file_name = f"{self.__class__.__module__.split('.')[-1]}.py"
        self.path = os.path.join(".", file_name)
        registered_runners.append(self)

    def run(self, settings: Settings, cmd: Command | None = None) -> None:
        if cmd not in self.commands:
            expected_commands = ", ".join(cmd.value for cmd in self.commands)
            print(f"Unsupported command: {cmd}. Expected: {expected_commands}")
            sys.exit(1)

        args = get_args_for_command_and_settings(cmd=cmd, settings=settings)

        path = os.path.join(
            os.path.basename(os.path.dirname(__file__)), os.path.basename(settings.path)
        )
        print(f"> python {path} {' '.join(args)}")

        sys.argv.extend(args)
        self.executable()

        sys.exit()
