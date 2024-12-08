import sys

from pyren3.enums import Command
from pyren3.settings import Settings


def run(settings: Settings, cmd: Command) -> None:
    if cmd in (Command.PYREN, Command.SCAN, Command.DEMO):
        from pyren3.pyren3 import main
    elif cmd is Command.CHECK:
        from pyren3.cmdr_chkelm import main
    elif cmd is Command.TERM:
        from pyren3.mod.term import main
    elif cmd is Command.PIDS:
        from pyren3.mod.ecu.ecu import main
    else:
        print(f"Unsupported command: {cmd}")
        sys.exit(1)

    args = get_args_for_command_and_settings(cmd=cmd, settings=settings)
    sys.argv.extend(args)

    print(f"> python {main.__module__} {' '.join(args)}")

    main()
    sys.exit()


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
