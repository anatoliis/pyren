import os

BASE_PATH = None

OPT_DEBUG = False
DEBUG_FILE = None

PORT = ""
ECU_ID = ""
ECU_ADDR = ""
PROTOCOL = ""
SPEED = 38400
RATE = 38400
LANG = ""
CAR = ""
LOG = ""
DEMO = False
SCAN = False
CSV = False
CSV_ONLY = False
CSV_HUMAN = False
CSV_SEP = ","
CSV_DEC = "."
EXCEL = False
USER_KEY = ""
VERBOSE = False
CMD = False
DDT = False
SLOW_INIT = False  # try slow init every time
CFC0 = False  # turn off automatic FC and do it by script
CAF = False  # turn on CAN Automatic Formatting
N1C = False  # turn off L1 cache
DEV = False  # switch to development session for commands from DevList
DEV_SESSION = "1086"  # development session for commands from DevList
EXPERT_MODE = False  # allow using buttons in ddt
DUMP = False  # dump responses from all 21xx and 22xxxx requests
CAN2 = False  # CAN is connected to pins 13 and 12
DDT_XML = ""
OBD_LINK = False  # basically, STN(PIC24) based ELM327
STN = False  # STN(PIC24) ELM327 which can automatically switch between two CAN lines
SEPARATE_DOC_FILES = False  # separate doc files
PERFORMANCE_MODE = False
MINOR_DTC = False
ALTERNATIVE_REFS = ""  # alternative ref set for acf
ALTERNATIVE_MTC = ""  # alternative mtc set for acf
DUMP_NAME = ""

STATE_SCAN = False

EXT_CUR_DTC = "000000"

NONE_VAL = "None"

MTC_DIR = "./MTCSAVE/VIN"
CACHE_DIR = "./cache/"
LOG_DIR = "./logs/"
DUMPS_DIR = "./dumps/"
DDT_ARC = ""
DDT_ROOT = (
    ".."  # parent folder for backward compatibility. for 9n and up use ../DDT2000data
)
CLIP_ARC = ""
CLIP_ROOT = ".."

OS = os.name

try:
    import androidhelper as android

    OS = "android"
except ImportError:
    try:
        import android

        OS = "android"
    except ImportError:
        pass

if OS == "nt":
    import colorama

    colorama.init()

try:
    import jnius
except Exception:
    JNIUS_MODE = False
else:
    JNIUS_MODE = True

print(f"Detected OS: {OS}{' (jnius mode)' if JNIUS_MODE else ''}")

LANGUAGE_DICT = {}

VIN = ""

DOC_SERVER_PROC = None

CSV_OPTIONS = ["csv", "csv_human", "csv_only"]
