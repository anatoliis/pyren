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


def prepare_ecus():
    """This function loads data for ECUs"""

    global elm
    global ecu
    global se
    global lang

    pyren3.opt_parser()

    mod_utils.chk_dir_tree()
    find_dbs()

    if len(config.OPT_LOG) == 0:
        config.OPT_LOG = "commander_log.txt"

    print("Opening ELM")
    elm = ELM(config.OPT_PORT, config.OPT_SPEED, config.OPT_LOG)

    print("Loading ECUs list")
    se = ScanEcus(elm)  # Prepare a list of all ecus

    if not os.path.isfile("savedEcus.p") or config.OPT_SCAN:
        # choosing model
        se.chooseModel(config.OPT_CAR)  # choose model of a car for doing full scan

    # Do this check every time
    se.scan_all_ecus()  # First scan of all ecus

    print("Loading language ")
    sys.stdout.flush()
    # loading language data
    lang = optfile("Location/DiagOnCAN_" + config.OPT_LANG + ".bqm", True)
    config.LANGUAGE_DICT = lang.dict
    print("Done")

    return se.detectedEcus


def select_ecu(ecu_number):
    global elm
    global ecu
    global se
    global lang

    selected_ecu = se.select_ecu(ecu_number)
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

    # ecu.show_screens()                                      # show ECU screens


def main():
    list_ = prepare_ecus()

    tot = ""

    for l in list_:
        if l["idf"] == "1":  # family 01
            print("### Connecting to Engine ###")
            select_ecu(l["ecuname"])
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
            select_ecu(l["ecuname"])
            tot += "%-15s : " % "ABS       PR121"
            num, string = ecu.get_pr("PR121")
            print(pyren_encode(string))
            tot += str(num)
            tot += "\n"
            print()
        if l["idf"] == "3":  # family 03
            print("### Connecting to TDB ###")
            select_ecu(l["ecuname"])
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

    # print tot
    elm.lastMessage = tot


if __name__ == "__main__":
    main()
