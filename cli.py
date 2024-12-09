import sys

from pyren3 import config
from pyren3.enums import Command
from pyren3.runner import run
from pyren3.settings import Settings

if __name__ == "__main__":
    config.CLI = True
    if len(sys.argv) < 2:
        cmd = Command.DEMO
    else:
        try:
            cmd = Command(sys.argv[1].lower())
        except ValueError:
            print(f"Invalid command.\nExpected one of:\n\n{', '.join(Command.all())}")
            sys.exit(1)

    print(f"Executing command: {cmd.value}")
    run(settings=Settings(), cmd=Command.DEMO)
