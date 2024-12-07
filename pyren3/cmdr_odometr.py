#!/usr/bin/env python3
import os
import pickle
import sys

import config
import mod_utils
import pyren3
from mod_db_manager import find_dbs
from mod_ecu import ECU
from mod_elm import ELM
from mod_optfile import optfile
from mod_scan_ecus import ScanEcus
from mod_utils import pyren_encode


def prepare_ecus(scan_ecus: ScanEcus):
    """This function loads data for ECUs"""
    pyren3.opt_parser()

    mod_utils.chk_dir_tree()
    find_dbs()

    if len(config.OPT_LOG) == 0:
        config.OPT_LOG = "commander_log.txt"

    if not os.path.isfile("savedEcus.p") or config.OPT_SCAN:
        # choosing model
        scan_ecus.choose_model(
            config.OPT_CAR
        )  # choose model of a car for doing full scan

    # Do this check every time
    scan_ecus.scan_all_ecus()  # First scan of all ecus
    return scan_ecus.detected_ecus


def select_ecu(scan_ecus, ecu_number, elm, lang):
    selected_ecu = scan_ecus.select_ecu(ecu_number)
    if selected_ecu == -1:
        print("#\n" * 3, "#   Unknown ECU defined!!!\n", "#\n" * 3)
        exit(1)

    ecu_cash_file = "./cache/" + selected_ecu["ModelId"] + "_" + config.OPT_LANG + ".p"

    if os.path.isfile(ecu_cash_file):  # if cache exists
        ecu = pickle.load(open(ecu_cash_file, "rb"))  # load it
    else:  # else
        ecu = ECU(selected_ecu, lang.dict)  # load original data for chosen ECU
        pickle.dump(
            ecu, open(ecu_cash_file, "wb")
        )  # and save data to cache for next time

    ecu.init_elm(elm)  # init ELM for chosen ECU
    return ecu


def main():
    print("Opening ELM")
    elm = ELM(config.OPT_PORT, config.OPT_SPEED, config.OPT_LOG)
    print("Loading ECUs list")
    scan_ecus = ScanEcus(elm)  # Prepare a list of all ecus
    print("Loading language ")
    sys.stdout.flush()
    # loading language data
    lang = optfile("Location/DiagOnCAN_" + config.OPT_LANG + ".bqm", True)
    config.LANGUAGE_DICT = lang.dict
    print("Done")

    list_ = prepare_ecus(scan_ecus)

    tot = ""

    for l in list_:
        if l["idf"] == "1":  # family 01
            print("### Connecting to Engine ###")
            ecu = select_ecu(scan_ecus, l["ecuname"], elm, lang)
            tot += "%-15s : " % "Engine    PR025"
            num, string = ecu.get_pr("PR025")
            print(pyren_encode(string))
            tot += str(num)
            tot += "\n"
            tot += "%-15s : " % "Engine    PR992"
            num, string = ecu.get_pr("PR992")
            print(pyren_encode(string))
            tot += str(num)
            tot += "\n"
            num, string = ecu.get_pr("PR391")
            print(pyren_encode(string))
            num, string = ecu.get_pr("PR412")
            print(pyren_encode(string))
            print()
        if l["idf"] == "2":  # family 02
            print("### Connecting to ABS ###")
            ecu = select_ecu(scan_ecus, l["ecuname"], elm, lang)
            tot += "%-15s : " % "ABS       PR121"
            num, string = ecu.get_pr("PR121")
            print(pyren_encode(string))
            tot += str(num)
            tot += "\n"
            print()
        if l["idf"] == "3":  # family 03
            print("### Connecting to TDB ###")
            ecu = select_ecu(scan_ecus, l["ecuname"], elm, lang)
            tot += "%-15s : " % "TDB       PR009"
            num, string = ecu.get_pr("PR009")
            print(pyren_encode(string))
            tot += str(num)
            tot += "\n"
            tot += "%-15s : " % "TDB (km)  PR025"
            num, string = ecu.get_pr("PR025")
            print(pyren_encode(string))
            tot += str(num)
            tot += "\n"
            tot += "%-15s : " % "TDB (mil) PR026"
            num, string = ecu.get_pr("PR026")
            print(pyren_encode(string))
            tot += str(num)
            tot += "\n"
            print()

    print(pyren_encode("Listening to CAN. Please wait a bit..."))
    elm.cmd("at z")
    elm.cmd("at e1")
    elm.cmd("at l1")
    elm.cmd("at h1")
    elm.cmd("at d1")
    elm.cmd("at caf0")
    elm.cmd("at sp 6")
    elm.cmd("at al")
    elm.port_timeout = 1

    elm.cmd("at cf 5C5")
    elm.cmd("at cm 7FF")
    elm.cmd("at cra 5C5")
    response = elm.cmd("atma")
    elm.cmd("at")
    for l in response.split("\n"):
        if l.upper().startswith("5C5"):
            kmt = l[9:18].replace(" ", "")
            tot += "%-10s : " % "Frame 5C5"
            tot = tot + str(int(kmt, 16))
            tot += "\n"
            break

    elm.cmd("at cf 715")
    elm.cmd("at cm 7FF")
    elm.cmd("at cra 715")
    elm.port_timeout = 5
    response = elm.cmd("atma")
    elm.port_timeout = 1
    elm.cmd("at")
    for l in response.split("\n"):
        if l.upper().startswith("715"):
            kmt = l[6:15].replace(" ", "")
            tot += "%-10s : " % "Frame 715"
            tot = tot + str(int(kmt, 16))
            tot += "\n"
            break

    elm.cmd("at cf 5FD")
    elm.cmd("at cm 7FF")
    elm.cmd("at cra 5FD")
    elm.port_timeout = 5
    response = elm.cmd("atma")
    elm.port_timeout = 1
    elm.cmd("at")
    for l in response.split("\n"):
        if l.upper().startswith("5FD"):
            kmt = l[6:15].replace(" ", "")
            tot += "%-10s : " % "Frame 5FD"
            tot = tot + str(int(kmt, 16))
            tot += "\n"
            break

    elm.lastMessage = tot


if __name__ == "__main__":
    main()
