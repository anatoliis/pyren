import os
import pickle
import sys

from serial.tools import list_ports

from pyren3 import config
from pyren3.mod import db_manager, utils
from pyren3.mod.ddt import ddt_utils
from pyren3.mod.ecu.ecu import ECU
from pyren3.mod.elm import ELM
from pyren3.mod.optfile import Optfile
from pyren3.mod.scan_ecus import ScanEcus
from pyren3.mod.utils import clearScreen, getVIN


def optParser():
    """Parsing of command line parameters. User should define at least com port name"""

    import argparse

    parser = argparse.ArgumentParser(
        # usage = "%prog -p <port> [options]",
        # version="pyRen Version 0.9.q",
        description="pyRen - python program for diagnostic Renault cars"
    )

    parser.add_argument("-p", help="ELM327 com port name", dest="port", default="")

    parser.add_argument(
        "-s",
        help="com port speed configured on ELM {38400[default],115200,230400,500000} DEPRECATED",
        dest="speed",
        default="38400",
    )

    parser.add_argument(
        "-r",
        help="com port rate during diagnostic session {38400[default],115200,230400,500000}",
        dest="rate",
        default="38400",
    )

    parser.add_argument(
        "-L",
        help="language option {RU[default],GB,FR,IT,...}",
        dest="lang",
        default="RU",
    )

    parser.add_argument(
        "--sd", help="separate doc files", dest="sd", default=False, action="store_true"
    )

    parser.add_argument(
        "-m", help="number of car model", dest="car", default=0, type=int
    )

    parser.add_argument(
        "-vv",
        "--verbose",
        help="show parameter explanations",
        dest="verbose",
        default=False,
        action="store_true",
    )

    parser.add_argument(
        "-e",
        help="index of ECU, or comma separeted list for DEMO MODE",
        dest="ecuid",
        default="",
    )

    parser.add_argument(
        "--si", help="try SlowInit first", dest="si", default=False, action="store_true"
    )

    parser.add_argument(
        "--cfc",
        help="turn off automatic FC and do it by script",
        dest="cfc",
        default=False,
        action="store_true",
    )

    parser.add_argument(
        "--caf",
        help="turn on CAN Auto Formatting. Available only for OBDLink",
        dest="caf",
        default=False,
        action="store_true",
    )

    parser.add_argument(
        "--n1c",
        help="turn off L1 cache",
        dest="n1c",
        default=False,
        action="store_true",
    )

    parser.add_argument(
        "--csv",
        help="save data in csv format",
        dest="csv",
        default=False,
        action="store_true",
    )

    parser.add_argument(
        "--csv_only",
        help="data doesnt show on screen for speed up",
        dest="csv_only",
        default=False,
        action="store_true",
    )

    parser.add_argument(
        "--csv_human",
        help="data saves to csv in readable format",
        dest="csv_human",
        default=False,
        action="store_true",
    )

    parser.add_argument(
        "--usr_key", help="add user events to log", dest="usr_key", default=""
    )

    parser.add_argument("--log", help="log file name", dest="logfile", default="")

    parser.add_argument(
        "--scan",
        help="scan ECUs even if savedEcus.p file exists",
        dest="scan",
        default=False,
        action="store_true",
    )

    parser.add_argument(
        "--demo",
        help="for debuging purpose. Work without car and ELM",
        dest="demo",
        default=False,
        action="store_true",
    )

    parser.add_argument(
        "--dump",
        help="dump responses from all 21xx and 22xxxx requests",
        dest="dump",
        default=False,
        action="store_true",
    )

    parser.add_argument(
        "--dev",
        help="swith to Development Session for commands from DevList, you should define alternative command for opening the session, like a 1086",
        dest="dev",
        default="",
    )

    parser.add_argument(
        "--exp",
        help="swith to Expert mode (allow to use buttons in DDT)",
        dest="exp",
        default=False,
        action="store_true",
    )

    parser.add_argument(
        "--can2",
        help="CAN network connected to pin 13 and pin 12",
        dest="can2",
        default=False,
        action="store_true",
    )

    parser.add_argument(
        "--performance",
        help="use UDS performance mode (read multiple DIDs in one request)",
        dest="performance",
        default=False,
        action="store_true",
    )

    parser.add_argument(
        "--minordtc",
        help="use to show all DTCs without checking computation formula",
        dest="minordtc",
        default=False,
        action="store_true",
    )

    parser.add_argument(
        "--excel",
        help="Save csv in excel compatible format",
        dest="excel",
        default=False,
        action="store_true",
    )

    options = parser.parse_args()

    if not options.port and config.OS != "android":
        parser.print_help()
        iterator = sorted(list(list_ports.comports()))
        print("")
        print("Available COM ports:")
        for port, desc, hwid in iterator:
            print(
                "%-30s \n\tdesc: %s \n\thwid: %s" % (port, desc, hwid)
            )  # .decode("windows-1251")
        print("")
        exit()
    else:
        config.PORT = options.port
        config.ECU_ID = options.ecuid
        config.SPEED = int(options.speed)
        config.RATE = int(options.rate)
        config.LANG = options.lang
        config.CAR = options.car
        config.LOG = options.logfile
        config.DEMO = options.demo
        config.SCAN = options.scan
        config.CSV = options.csv
        config.CSV_ONLY = options.csv_only
        if config.CSV:
            config.CSV_HUMAN = True
        if config.CSV_ONLY:
            config.CSV = True
        config.CSV_HUMAN = options.csv_human
        if config.CSV_HUMAN:
            config.CSV = True
        config.USER_KEY = options.usr_key
        config.VERBOSE = options.verbose
        config.SLOW_INIT = options.si
        config.CFC0 = options.cfc
        config.CAF = options.caf
        config.N1C = options.n1c
        config.EXPERT_MODE = options.exp
        config.DUMP = options.dump
        config.CAN2 = options.can2
        config.PERFORMANCE_MODE = options.performance
        config.SEPARATE_DOC_FILES = options.sd
        config.MINOR_DTC = options.minordtc
        if options.dev == "" or len(options.dev) != 4 or options.dev[0:2] != "10":
            config.DEV = False
            config.DEV_SESSION = "1086"
        else:
            print("Development MODE")
            config.DEV = True
            config.DEV_SESSION = options.dev
        config.EXCEL = options.excel
        if config.EXCEL:
            config.CSV_SEP = ";"
            config.CSV_DEC = ","
        else:
            config.CSV_SEP = ","
            config.CSV_DEC = "."


def main():
    """Main function"""
    optParser()

    utils.chkDirTree()
    db_manager.find_DBs()

    print("Opening ELM")
    elm = ELM(config.PORT, config.SPEED, config.LOG)

    # change serial port baud rate
    if config.SPEED < config.RATE and not config.DEMO:
        elm.port.soft_boudrate(config.RATE)

    print("Loading ECUs list")
    se = ScanEcus(elm)  # Prepare list of all ecus

    SEFname = "savedEcus.p"
    if config.CAN2:
        SEFname = "savedEcus2.p"

    if config.DEMO and len(config.ECU_ID) > 0:
        # demo mode with predefined ecu list
        if "tcom" in config.ECU_ID.lower() or len(config.ECU_ID) < 4:
            tcomid = "".join([i for i in config.ECU_ID if i.isdigit()])
            se.load_model_ECUs("Vehicles/TCOM_" + tcomid + ".xml")
            config.ECU_ID = ",".join(sorted(se.allecus.keys()))
        else:
            se.read_Uces_file(all=True)
        se.detectedEcus = []
        for i in config.ECU_ID.split(","):
            if i in list(se.allecus.keys()):
                se.allecus[i]["ecuname"] = i
                se.allecus[i]["idf"] = se.allecus[i]["ModelId"][2:4]
                if se.allecus[i]["idf"] != "":
                    if se.allecus[i]["idf"][0] == "0":
                        se.allecus[i]["idf"] = se.allecus[i]["idf"][1]
                else:
                    continue
                se.allecus[i]["pin"] = "can"
                se.detectedEcus.append(se.allecus[i])
    else:
        if not os.path.isfile(SEFname) or config.SCAN:
            # choosing model
            se.chooseModel(config.CAR)  # choose model of car for doing full scan

        # Do this check every time
        se.scanAllEcus()  # First scan of all ecus

    config.VIN = getVIN(se.detectedEcus, elm, getFirst=True)

    print("Loading language ")
    sys.stdout.flush()
    # loading language data
    lang = Optfile("Location/DiagOnCAN_" + config.LANG + ".bqm", True)
    config.LANGUAGE_DICT = lang.dict
    print("Done")

    ddt_utils.searchddtroot()

    while 1:
        clearScreen()
        choosen_ecu = se.chooseECU(config.ECU_ID)  # choose ECU among detected
        config.ECU_ID = ""
        if choosen_ecu == -1:
            continue

        ecucashfile = "./cache/" + choosen_ecu["ModelId"] + "_" + config.LANG + ".p"

        if os.path.isfile(ecucashfile):  # if cache exists
            ecu = pickle.load(open(ecucashfile, "rb"))  # load it
        else:
            if len(choosen_ecu["ecuname"]) != 5:
                continue
            ecu = ECU(choosen_ecu, lang.dict)  # loading original data for chosen ECU
            pickle.dump(ecu, open(ecucashfile, "wb"))  # and save cache

        ecu.initELM(elm)  # init ELM for chosen ECU

        if config.DEMO:
            print("Loading dump")
            ecu.loadDump()
        elif config.DUMP:
            print("Saving dump")
            ecu.saveDump()

        ecu.show_screens()  # show ECU screens


if __name__ == "__main__":
    main()
