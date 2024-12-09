from pyren3.enums import Command
from pyren3.pyren import main
from pyren3.runner_base import BaseRunner


class RunPyren(BaseRunner):
    commands = [Command.START, Command.SCAN, Command.DEMO]


runner = RunPyren(main)
