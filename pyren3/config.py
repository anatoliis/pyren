#!/usr/bin/env python3
import os

OPT_DEBUG = False
DEBUG_FILE = None

OPT_PORT = ""
OPT_ECU_ID = ""
OPT_ECU_ADDR = ""
OPT_PROTOCOL = ""
OPT_SPEED = 38400
OPT_RATE = 38400
OPT_LANG = ""
OPT_CAR = ""
OPT_LOG = ""
OPT_DEMO = False
OPT_SCAN = False
OPT_CSV = False
OPT_CSV_ONLY = False
OPT_CSV_HUMAN = False
OPT_CSV_SEP = ","
OPT_CSV_DEC = "."
OPT_EXCEL = False
OPT_USRKEY = ""
OPT_VERBOSE = False
OPT_CMD = False
OPT_SI = False  # try slow init every time
OPT_CFC0 = False  # turn off automatic FC and do it by script
OPT_CAF = False  # turn on CAN Automatic Formatting
OPT_N1C = False  # turn off L1 cache
OPT_DUMP = False  # dump responses from all 21xx and 22xxxx requests
OPT_CAN2 = False  # can connected to pins 13 and 12
OPT_OBD_LINK = False  # basically, STN(PIC24) based ELM327
OPT_STN = (
    False  # STN(PIC24) ELM327 which can automatically switch between two CAN lines
)
OPT_SD = False  # separate doc files
OPT_PERFORMANCE = False
OPT_MINOR_DTC = False
OPT_REF = ""  # alternative ref set for acf
DUMP_NAME = ""

STATE_SCAN = False

EXT_CUR_DTC = "000000"

NONE_VAL = "None"

MTC_DIR = "../MTCSAVE/VIN"
CACHE_DIR = "./cache/"
DUMPS_DIR = "./dumps/"
CLIP_ARC = ""
CLIP_ROOT = ".."

OS = os.name

LANGUAGE_DICT = {}

VIN = ""

DOC_SERVER_PROC = None
