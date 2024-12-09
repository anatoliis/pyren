from pyren3.enums import Command
from pyren3.mod.term import main
from pyren3.runner_base import BaseRunner


class RunTerm(BaseRunner):
    commands = [Command.TERM]


runner = RunTerm(main)
