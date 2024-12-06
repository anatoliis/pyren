#!/usr/bin/env python3
import argparse
import os
import pickle
import sys

import config
from mod_db_manager import find_dbs
from mod_ecu import ECU
from mod_elm import ELM
from mod_optfile import optfile
from mod_scan_ecus import ScanEcus
from mod_utils import chk_dir_tree, clear_screen, get_vin
from serial.tools import list_ports

os.chdir(os.path.dirname(os.path.realpath(sys.argv[0])))


def opt_parser():
    """Parsing of command line parameters. User should define at least com port name"""

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

    if not options.port:
        parser.print_help()
        iterator = sorted(list(list_ports.comports()))
        print("\nAvailable COM ports:")
        for port, desc, hwid in iterator:
            print("%-30s \n\tdesc: %s \n\thwid: %s" % (port, desc, hwid))
        print("")
        exit()
    else:
        config.OPT_PORT = options.port
        config.OPT_ECU_ID = options.ecuid
        config.OPT_SPEED = int(options.speed)
        config.OPT_RATE = int(options.rate)
        config.OPT_LANG = options.lang
        config.OPT_CAR = options.car
        config.OPT_LOG = options.logfile
        config.OPT_DEMO = options.demo
        config.OPT_SCAN = options.scan
        config.OPT_CSV = options.csv
        config.OPT_CSV_ONLY = options.csv_only
        if config.OPT_CSV:
            config.OPT_CSV_HUMAN = True
        if config.OPT_CSV_ONLY:
            config.OPT_CSV = True
        config.OPT_CSV_HUMAN = options.csv_human
        if config.OPT_CSV_HUMAN:
            config.OPT_CSV = True
        config.OPT_USRKEY = options.usr_key
        config.OPT_VERBOSE = options.verbose
        config.OPT_SI = options.si
        config.OPT_CFC0 = options.cfc
        config.OPT_CAF = options.caf
        config.OPT_N1C = options.n1c
        config.OPT_DUMP = options.dump
        config.OPT_CAN2 = options.can2
        config.OPT_PERFORMANCE = options.performance
        config.OPT_SD = options.sd
        config.OPT_MINOR_DTC = options.minordtc
        config.OPT_EXCEL = options.excel
        if config.OPT_EXCEL:
            config.OPT_CSV_SEP = ";"
            config.OPT_CSV_DEC = ","
        else:
            config.OPT_CSV_SEP = ","
            config.OPT_CSV_DEC = "."


def main():
    opt_parser()

    chk_dir_tree()
    find_dbs()

    print("Opening ELM")
    elm = ELM(config.OPT_PORT, config.OPT_SPEED, config.OPT_LOG)

    # change serial port baud rate
    if config.OPT_SPEED < config.OPT_RATE and not config.OPT_DEMO:
        elm.port.soft_boudrate(config.OPT_RATE)

    print("Loading ECUs list")
    se = ScanEcus(elm)  # Prepare list of all ecus

    SEFname = "savedEcus.p"
    if config.OPT_CAN2:
        SEFname = "savedEcus2.p"

    if config.OPT_DEMO and len(config.OPT_ECU_ID) > 0:
        # demo mode with predefined ecu list
        if "tcom" in config.OPT_ECU_ID.lower() or len(config.OPT_ECU_ID) < 4:
            tcomid = "".join([i for i in config.OPT_ECU_ID if i.isdigit()])
            se.load_model_ECUs("Vehicles/TCOM_" + tcomid + ".xml")
            config.OPT_ECU_ID = ",".join(sorted(se.allecus.keys()))
        else:
            se.read_Uces_file(all=True)
        se.detectedEcus = []
        for i in config.OPT_ECU_ID.split(","):
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
        if not os.path.isfile(SEFname) or config.OPT_SCAN:
            # choosing model
            se.chooseModel(config.OPT_CAR)  # choose model of car for doing full scan

        # Do this check every time
        se.scan_all_ecus()  # First scan of all ecus

    config.VIN = get_vin(se.detectedEcus, elm, getFirst=True)

    print("Loading language ")
    sys.stdout.flush()
    # loading language data
    lang = optfile("Location/DiagOnCAN_" + config.OPT_LANG + ".bqm", True)
    config.LANGUAGE_DICT = lang.dict
    print("Done")

    while True:
        clear_screen()
        selected_ecu = se.select_ecu(config.OPT_ECU_ID)  # choose ECU among detected
        config.OPT_ECU_ID = ""
        if selected_ecu == -1:
            continue

        ecu_cache_file = os.path.join(
            "./cache/", selected_ecu["ModelId"] + "_" + config.OPT_LANG + ".p"
        )

        if os.path.isfile(ecu_cache_file):  # if cache exists
            with open(ecu_cache_file, "rb") as f:
                ecu = pickle.load(f)
        else:
            if len(selected_ecu["ecuname"]) != 5:
                continue
            ecu = ECU(selected_ecu, lang.dict)  # loading original data for chosen ECU
            with open(ecu_cache_file, "wb") as f:
                pickle.dump(ecu, f)

        ecu.init_elm(elm)  # init ELM for chosen ECU

        if config.OPT_DEMO:
            print("Loading dump")
            ecu.loadDump()
        elif config.OPT_DUMP:
            print("Saving dump")
            ecu.saveDump()

        ecu.show_screens()  # show ECU screens


if __name__ == "__main__":
    main()
