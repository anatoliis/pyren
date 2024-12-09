from pyren3.bus_monitor.bus_monitor import main
from pyren3.enums import Command
from pyren3.runner_base import BaseRunner


class RunBusMonitor(BaseRunner):
    commands = [Command.MON]


runner = RunBusMonitor(main)
