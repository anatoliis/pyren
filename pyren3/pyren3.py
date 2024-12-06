#!/usr/bin/env python3
import argparse
import os
import pickle
import sys

import mod_globals
from mod_db_manager import find_dbs
from mod_ddt_utils import searchddtroot
from mod_ecu import ECU
from mod_elm import ELM
from mod_optfile import optfile
from mod_scan_ecus import ScanEcus
from mod_utils import chk_dir_tree, clear_screen, get_vin
from serial.tools import list_ports

mod_globals.os = os.name

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
        "--exp",
        help="switch to Expert mode (allow to use buttons in DDT)",
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

    if not options.port:
        parser.print_help()
        iterator = sorted(list(list_ports.comports()))
        print("\nAvailable COM ports:")
        for port, desc, hwid in iterator:
            print("%-30s \n\tdesc: %s \n\thwid: %s" % (port, desc, hwid))
        print("")
        exit()
    else:
        mod_globals.opt_port = options.port
        mod_globals.opt_ecu_id = options.ecuid
        mod_globals.opt_speed = int(options.speed)
        mod_globals.opt_rate = int(options.rate)
        mod_globals.opt_lang = options.lang
        mod_globals.opt_car = options.car
        mod_globals.opt_log = options.logfile
        mod_globals.opt_demo = options.demo
        mod_globals.opt_scan = options.scan
        mod_globals.opt_csv = options.csv
        mod_globals.opt_csv_only = options.csv_only
        if mod_globals.opt_csv:
            mod_globals.opt_csv_human = True
        if mod_globals.opt_csv_only:
            mod_globals.opt_csv = True
        mod_globals.opt_csv_human = options.csv_human
        if mod_globals.opt_csv_human:
            mod_globals.opt_csv = True
        mod_globals.opt_usrkey = options.usr_key
        mod_globals.opt_verbose = options.verbose
        mod_globals.opt_si = options.si
        mod_globals.opt_cfc0 = options.cfc
        mod_globals.opt_caf = options.caf
        mod_globals.opt_n1c = options.n1c
        mod_globals.opt_exp = options.exp
        mod_globals.opt_dump = options.dump
        mod_globals.opt_can2 = options.can2
        mod_globals.opt_performance = options.performance
        mod_globals.opt_sd = options.sd
        mod_globals.opt_minordtc = options.minordtc
        mod_globals.opt_excel = options.excel
        if mod_globals.opt_excel:
            mod_globals.opt_csv_sep = ";"
            mod_globals.opt_csv_dec = ","
        else:
            mod_globals.opt_csv_sep = ","
            mod_globals.opt_csv_dec = "."


def main():
    opt_parser()

    chk_dir_tree()
    find_dbs()

    print("Opening ELM")
    elm = ELM(mod_globals.opt_port, mod_globals.opt_speed, mod_globals.opt_log)

    # change serial port baud rate
    if mod_globals.opt_speed < mod_globals.opt_rate and not mod_globals.opt_demo:
        elm.port.soft_boudrate(mod_globals.opt_rate)

    print("Loading ECUs list")
    se = ScanEcus(elm)  # Prepare list of all ecus

    SEFname = "savedEcus.p"
    if mod_globals.opt_can2:
        SEFname = "savedEcus2.p"

    if mod_globals.opt_demo and len(mod_globals.opt_ecu_id) > 0:
        # demo mode with predefined ecu list
        if "tcom" in mod_globals.opt_ecu_id.lower() or len(mod_globals.opt_ecu_id) < 4:
            tcomid = "".join([i for i in mod_globals.opt_ecu_id if i.isdigit()])
            se.load_model_ECUs("Vehicles/TCOM_" + tcomid + ".xml")
            mod_globals.opt_ecu_id = ",".join(sorted(se.allecus.keys()))
        else:
            se.read_Uces_file(all=True)
        se.detectedEcus = []
        for i in mod_globals.opt_ecu_id.split(","):
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
        if not os.path.isfile(SEFname) or mod_globals.opt_scan:
            # choosing model
            se.chooseModel(
                mod_globals.opt_car
            )  # choose model of car for doing full scan

        # Do this check every time
        se.scanAllEcus()  # First scan of all ecus

    mod_globals.vin = get_vin(se.detectedEcus, elm, getFirst=True)

    print("Loading language ")
    sys.stdout.flush()
    # loading language data
    lang = optfile("Location/DiagOnCAN_" + mod_globals.opt_lang + ".bqm", True)
    mod_globals.language_dict = lang.dict
    print("Done")

    searchddtroot()

    while True:
        clear_screen()
        selected_ecu = se.select_ecu(
            mod_globals.opt_ecu_id
        )  # choose ECU among detected
        mod_globals.opt_ecu_id = ""
        if selected_ecu == -1:
            continue

        ecu_cache_file = os.path.join(
            "./cache/", selected_ecu["ModelId"] + "_" + mod_globals.opt_lang + ".p"
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

        if mod_globals.opt_demo:
            print("Loading dump")
            ecu.loadDump()
        elif mod_globals.opt_dump:
            print("Saving dump")
            ecu.saveDump()

        ecu.show_screens()  # show ECU screens


if __name__ == "__main__":
    main()
