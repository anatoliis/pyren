import argparse
import sys

from pyren3 import config
from pyren3.mod.elm import ELM

parser = argparse.ArgumentParser(
    version="bus_playback Version 0.1",
    description="bus_playback - playing back logs written by bus_monitor.py",
)

parser.add_argument(
    "-p",
    help="ELM327 com port name (or BT mac addr e.g 24:42:16:08:00:00)",
    dest="port",
    default="",
)

parser.add_argument(
    "-r",
    help="com port rate during diagnostic session {38400[default],57600,115200,230400,500000}",
    dest="rate",
    default="38400",
)

parser.add_argument("--log", help="log file name", dest="logfile", default="")

parser.add_argument("log", help="the log file name to be played back")

options = parser.parse_args()

if not options.port and config.OS != "android":
    parser.print_help()

    from serial.tools import list_ports

    print("\nAvailable COM ports:")
    for port, desc, hwid in sorted(list(list_ports.comports())):
        print("%-30s \n\tdesc: %s \n\thwid: %s" % (port, desc, hwid))
    print("")

    exit(2)

config.PORT = options.port
config.RATE = int(options.rate)
config.LOG = options.logfile

try:
    playbackfile = open(options.log)
except IOError as e:
    print("ERROR:", e, file=sys.stderr)
    exit(2)

print("Opening ELM")
elm = ELM(config.PORT, config.SPEED, config.LOG)

if config.SPEED < config.RATE:
    elm.port.soft_boudrate(config.RATE)

print("Init    ELM")
print(elm.cmd("at z"))
# print elm.cmd("at ws")

print(elm.cmd("at d1"))
print(elm.cmd("at h1"))
print(elm.cmd("at al"))
print(elm.cmd("at at 0"))
print(elm.cmd("at st 10"))
print(elm.cmd("at r 0"))

print(elm.cmd("at cea"))
print(elm.cmd("at sp 6"))
print(elm.cmd("at al"))
print(elm.cmd("at caf 0"))
print(elm.cmd("at v1"))
print(elm.cmd("at bi"))

print("Playing data back...")
for n, line in enumerate(open(options.log)):
    t, _, addr, len, data = line.split(None, 4)
    data = data.split(None, 8)
    print(elm.cmd("at sh %s" % addr))
    print(elm.cmd("".join(data[:8])))

playbackfile.close()
