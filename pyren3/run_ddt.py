from pyren3.enums import Command
from pyren3.mod.ddt.ddt import main
from pyren3.runner_base import BaseRunner


class RunDDT(BaseRunner):
    commands = [Command.DDT]


runner = RunDDT(main)
