from pyren3.cmdr_chkelm import main
from pyren3.enums import Command
from pyren3.runner_base import BaseRunner


class RunCheckElm(BaseRunner):
    commands = [Command.CHECK]


runner = RunCheckElm(main)
