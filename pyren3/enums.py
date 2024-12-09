import enum


class Command(str, enum.Enum):
    START = "start"
    SCAN = "scan"
    DEMO = "demo"
    DDT = "ddt"
    CHECK = "check"
    TERM = "term"
    PIDS = "pids"
    MON = "mon"

    @classmethod
    def all(cls):
        return [cmd.value for cmd in cls.__members__.values()]
