import os
import sys

from pyren3 import config
from pyren3.enums import Command
from pyren3.settings import Settings


def get_path_list():
    paths = []

    for file_name in os.listdir(config.EXECUTABLES_PATH):
        if os.path.isdir(os.path.join(".", file_name)):
            continue
        if not file_name.lower().startswith(config.EXECUTABLE_PREFIX):
            continue
        if not file_name.lower().endswith(".py"):
            continue
        paths.append(os.path.join(".", file_name))
    return paths


def get_executable(path: str):
    module_name, _ = os.path.splitext(os.path.basename(path))
    executable_module = getattr(__import__(config.EXECUTABLES_PATH), module_name, None)
    if not executable_module:
        print(f"Executable not found: {module_name}.py")
        sys.exit(1)
    return executable_module.runner.run


def get_args_for_command_and_settings(settings: Settings, cmd: Command) -> list:
    args = ["-p" + settings.port]

    if cmd is Command.DEMO:
        args.append("--demo")
    if cmd is Command.SCAN and cmd is not Command.TERM:
        args.append("--scan")
    if settings.log:
        args.append("--log=" + settings.log_name)
    if settings.speed != "38400":
        args.append("-r" + settings.speed)
    if settings.lang != "" and cmd not in (Command.TERM, Command.DDT):
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
        args.extend(settings.options.split())
    if cmd is Command.TERM:
        args.append("--dialog")
    if cmd is Command.DDT:
        args.append("--demo")

    return args


def get_lang_list():
    return [
        # fmt: off
        "AL", "CNT", "CO", "CR", "CZ", "DK", "EL", "FI", "FR", "GB", "HG", "IT",
        "JP", "NG", "NL", "PL", "PO", "RO", "RU", "SD", "SL", "SP", "TR",
        # fmt: on
    ]


def get_port_list():
    ports = []
    if config.OS != "android":
        if config.JNIUS_MODE:
            try:
                autoclass = __import__("jnius").autoclass
            except Exception:
                print("Missing dependency: jnius")
                sys.exit(1)

            bluetooth_adapter = autoclass("android.bluetooth.BluetoothAdapter")

            try:
                paired_devices = (
                    bluetooth_adapter.getDefaultAdapter().getBondedDevices().toArray()
                )
                for device in paired_devices:
                    desc = device.getName()
                    de = str(desc.encode("ascii", "ignore"))
                    ports.append("BT;" + de)
            except Exception:
                ports.append("BT;")
            return ports

        from serial.tools import list_ports

        iterator = sorted(list(list_ports.comports()))
        for port, desc, hwid in iterator:
            try:
                de = str(desc.encode("ascii", "ignore"))
                ports.append(port + ";" + de)
            except Exception:
                ports.append(port + ";")
        if "192.168.0.10:35000;WiFi" not in ports:
            ports.append("192.168.0.10:35000;WiFi")
    else:
        ports = ["BT", "192.168.0.10:35000"]
    return ports
