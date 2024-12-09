import enum


class Command(str, enum.Enum):
    CHECK = "check"
    DEMO = "demo"
    SCAN = "scan"
    PYREN = "pyren"
    TERM = "term"
    PIDS = "pids"
    MON = "mon"
    DDT = "ddt"

    @classmethod
    def all(cls):
        return [cmd.value for cmd in cls.__members__.values()]
