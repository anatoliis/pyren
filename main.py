#!/usr/bin/env python3
import enum
import json
import os
import pprint
import sys

BASE_PATH: str = os.path.dirname(os.path.abspath(__file__))

LANGUAGES = [
    # fmt: off
    "AL", "CNT", "CO", "CR", "CZ", "DK", "EL", "FI", "FR", "GB", "HG", "IT",
    "JP", "NG", "NL", "PL", "PO", "RO", "RU", "SD", "SL", "SP", "TR"
    # fmt: on
]


class CsvOption(str, enum.Enum):
    CSV = "csv"
    CSV_HUMAN = "csv_human"
    CSV_ONLY = "csv_only"


class Command(str, enum.Enum):
    CHECK = "check"
    DEMO = "demo"
    SCAN = "scan"
    PYREN = "pyren"
    TERM = "term"
    PIDS = "pids"


class Settings:
    path: str = "./pyren3"
    port: str = "192.168.0.10:35000"
    lang: str = "RU"
    speed: str = "38400"
    log_name: str = "log.txt"
    csv_option: str = "csv"
    log: bool = True
    cfc: bool = True
    n1c: bool = False
    si: bool = False
    csv: bool = False
    dump: bool = True
    can2: bool = False
    options: str = ""

    def __init__(self):
        self._load_settings()

    def _load_settings(self) -> None:
        path = "./settings.json"
        if not os.path.isfile(path):
            self.save()
        settings_ = self._read_settings(path=path)
        self.__dict__.update(settings_)

    @staticmethod
    def _read_settings(path: str) -> dict:
        settings_ = {}
        with open(path, "r") as file:
            settings_raw: str = file.read()
        try:
            settings_ = json.loads(settings_raw)
        except (TypeError, json.decoder.JSONDecodeError):
            pass
        return settings_

    @staticmethod
    def _write_settings(path: str, data: dict) -> None:
        with open(path, "w") as file:
            file.write(json.dumps(data, indent=2))
        print(data)

    def save(self) -> None:
        self._write_settings(
            path="./settings.json",
            data=self.__dict__,
        )

    def __str__(self):
        return pprint.pformat(self.__dict__)


def get_args_for_command_and_settings(settings: Settings, cmd: Command) -> list:
    args = ["-p" + settings.port]

    if cmd is Command.DEMO:
        args.append("--demo")
    if cmd is Command.SCAN:
        args.append("--scan")
    if settings.log:
        args.append("--log=" + settings.log_name)
    if settings.speed != "38400":
        args.append("-r" + settings.speed)
    if settings.lang != "" and cmd is not Command.TERM:
        args.append("-L" + settings.lang)
    if settings.cfc:
        args.append("--cfc")
    if settings.n1c:
        args.append("--n1c")
    if settings.si:
        args.append("--si")
    if settings.csv:
        args.append("--" + settings.csv_option)
    if settings.dump and cmd is not Command.TERM:
        args.append("--dump")
    if settings.can2 and cmd is not Command.TERM:
        args.append("--can2")
    if settings.options != "":
        args = args + settings.options.split()
    if cmd is Command.TERM:
        args.append("--dialog")

    return args


def run(settings: Settings, cmd: Command) -> None:
    new_path = os.path.join(BASE_PATH, os.path.split(settings.path)[1])
    sys.path.insert(0, new_path)

    if cmd in (Command.PYREN, Command.SCAN, Command.DEMO):
        cmdr = __import__("pyren3")
    elif cmd is Command.CHECK:
        cmdr = __import__("cmdr_chkelm")
    elif cmd is Command.TERM:
        cmdr = __import__("mod_term")
    elif cmd is Command.PIDS:
        cmdr = __import__("mod_ecu")
    else:
        print(f"Unsupported command: {cmd}")
        sys.exit(1)

    args = get_args_for_command_and_settings(cmd=cmd, settings=settings)

    print(f"> python {cmdr.__file__} {' '.join(args)}")
    sys.argv.extend(args)
    os.chdir(new_path)
    cmdr.main()
    sys.exit()


def main():
    for file_name in os.listdir(BASE_PATH):
        path = os.path.join(BASE_PATH, file_name)
        if os.path.isfile(path):
            continue
        serial_path = os.path.join(path, "serial")
        if file_name.startswith("pyren3") and os.path.isdir(serial_path):
            sys.path.append(path)
            sys.path.append(serial_path)

    settings = Settings()
    run(settings, Command.DEMO)


if __name__ == "__main__":
    main()
