#!/usr/bin/env python3

import os
import pickle
import sys

import pyren3
from mod import config, db_manager, utils
from mod.ecu import ECU
from mod.mod_elm import ELM
from mod.optfile import Optfile
from mod.scan_ecus import ScanEcus
from mod.utils import pyren_encode

try:
    import androidhelper as android

    config.os = "android"
except:
    try:
        import android

        config.os = "android"
    except:
        pass

if config.os != "android":
    try:
        import serial
        from serial.tools import list_ports
    except ImportError:
        sys.exit()


def prepareECUs():
    """This function loads data for ECUs"""

    global elm
    global ecu
    global se
    global lang

    pyren3.optParser()

    utils.chkDirTree()
    db_manager.find_DBs()

    if len(config.opt_log) == 0:
        config.opt_log = "commander_log.txt"

    print("Opening ELM")
    elm = ELM(config.opt_port, config.opt_speed, config.opt_log)

    print("Loading ECUs list")
    se = ScanEcus(elm)  # Prepare list of all ecus

    if not os.path.isfile("savedEcus.p") or config.opt_scan:
        # choosing model
        se.chooseModel(config.opt_car)  # choose model of car for doing full scan

    # Do this check every time
    se.scanAllEcus()  # First scan of all ecus

    print("Loading language ")
    sys.stdout.flush()
    # loading language data
    lang = Optfile("Location/DiagOnCAN_" + config.opt_lang + ".bqm", True)
    config.language_dict = lang.dict
    print("Done")

    return se.detectedEcus


def chooseEcu(ecu_number):
    global elm
    global ecu
    global se
    global lang

    choosen_ecu = se.chooseECU(ecu_number)
    if choosen_ecu == -1:
        print("#\n" * 3, "#   Unknown ECU defined!!!\n", "#\n" * 3)
        exit(1)

    ecucashfile = "./cache/" + choosen_ecu["ModelId"] + "_" + config.opt_lang + ".p"

    if os.path.isfile(ecucashfile):  # if cache exists
        ecu = pickle.load(open(ecucashfile, "rb"))  # load it
    else:  # else
        ecu = ECU(choosen_ecu, lang.dict)  # load original data for chosen ECU
        pickle.dump(
            ecu, open(ecucashfile, "wb")
        )  # and save data to cache for next time

    ecu.initELM(elm)  # init ELM for chosen ECU

    # ecu.show_screens()                                      # show ECU screens


def main():
    list = prepareECUs()

    tot = ""

    for l in list:
        if l["idf"] == "1":  # family 01
            print("### Connecting to Engine ###")
            chooseEcu(l["ecuname"])
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
            # num, string = ecu.get_pr('PR804')
            # print pyren_encode(string)
            # num, string = ecu.get_pr('PR869')
            # print pyren_encode(string)
            # num, string = ecu.get_pr('PR870')
            # print pyren_encode(string)
            print()
        if l["idf"] == "2":  # family 02
            print("### Connecting to ABS ###")
            chooseEcu(l["ecuname"])
            tot += "%-15s : " % "ABS       PR121"
            num, string = ecu.get_pr("PR121")
            print(pyren_encode(string))
            tot += str(num)
            tot += "\n"
            print()
        if l["idf"] == "3":  # family 03
            print("### Connecting to TDB ###")
            chooseEcu(l["ecuname"])
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
    if config.os != "android":
        print(pyren_encode("Listening to CAN. Please wait a bit..."))
        elm.cmd("at z")
        elm.cmd("at e1")
        elm.cmd("at l1")
        elm.cmd("at h1")
        elm.cmd("at d1")
        elm.cmd("at caf0")
        elm.cmd("at sp 6")
        elm.cmd("at al")
        elm.portTimeout = 1

        elm.cmd("at cf 5C5")
        elm.cmd("at cm 7FF")
        elm.cmd("at cra 5C5")
        resp = elm.cmd("atma")
        elm.cmd("at")
        for l in resp.split("\n"):
            if l.upper().startswith("5C5"):
                kmt = l[9:18].replace(" ", "")
                tot += "%-10s : " % "Frame 5C5"
                tot = tot + str(int(kmt, 16))
                tot += "\n"
                break

        elm.cmd("at cf 715")
        elm.cmd("at cm 7FF")
        elm.cmd("at cra 715")
        elm.portTimeout = 5
        resp = elm.cmd("atma")
        elm.portTimeout = 1
        elm.cmd("at")
        for l in resp.split("\n"):
            if l.upper().startswith("715"):
                kmt = l[6:15].replace(" ", "")
                tot += "%-10s : " % "Frame 715"
                tot = tot + str(int(kmt, 16))
                tot += "\n"
                break

        elm.cmd("at cf 5FD")
        elm.cmd("at cm 7FF")
        elm.cmd("at cra 5FD")
        elm.portTimeout = 5
        resp = elm.cmd("atma")
        elm.portTimeout = 1
        elm.cmd("at")
        for l in resp.split("\n"):
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
