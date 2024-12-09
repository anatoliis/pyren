from pyren3.runner_base import BaseRunner
from pyren3.enums import Command
from pyren3.mod.ecu.ecu import main


class RunPid(BaseRunner):
    commands = [Command.PIDS]


runner = RunPid(main)
