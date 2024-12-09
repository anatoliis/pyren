import sys

from pyren3.enums import Command
from pyren3.settings import Settings
from pyren3.utils import get_args_for_command_and_settings


def run(settings: Settings, cmd: Command) -> None:
    if cmd in (Command.PYREN, Command.SCAN, Command.DEMO):
        from pyren3.pyren import main
    elif cmd is Command.CHECK:
        from pyren3.cmdr_chkelm import main
    elif cmd is Command.TERM:
        from pyren3.mod.term import main
    elif cmd is Command.PIDS:
        from pyren3.mod.ecu.ecu import main
    else:
        print(f"Unsupported command: {cmd}")
        sys.exit(1)

    args = get_args_for_command_and_settings(cmd=cmd, settings=settings)
    sys.argv.extend(args)

    print(f"> python {main.__module__} {' '.join(args)}")

    main()
    sys.exit()
