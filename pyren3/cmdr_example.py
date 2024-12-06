#!/usr/bin/env python3

#  ______  ___   ___      ___       ___  ___   ______    __       _______
# |   ___| \  \ /  /     /   \     |   \/   | |   _  \  |  |     |   ____|
# |  |__    \  V  /     /  ^  \    |  \  /  | |  |_)  | |  |     |  |__
# |   __|    >   <     /  /_\  \   |  |\/|  | |   ___/  |  |     |   __|
# |  |___   /  .  \   /  _____  \  |  |  |  | |  |      |  `----.|  |____
# |______| /__/ \__\ /__/     \__\ |__|  |__| | _|      |_______||_______|
#

import os
import pickle
import sys
import time

import config
import pyren3
from mod_ecu import ECU
from mod_elm import ELM
from mod_optfile import optfile
from mod_scan_ecus import ScanEcus
from mod_utils import clear_screen


def prepare_ecu():
    """This function loads data for ECU"""

    global elm
    global ecu

    pyren3.opt_parser()

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

    # clearScreen()

    selected_ecu = se.select_ecu(config.OPT_ECU_ID)  # choose ECU among detected
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
    prepare_ecu()

    #####
    ##### Example start
    #####

    # Example of using raw commands

    print(elm.request(req="2180", positive="61", cache=False))
    print(elm.request(req="2181", positive="61", cache=False))

    # print elm.request( req = '3B815646314C4D314230483131313131313131518C', positive = '7B', cache = False )

    # Example of using states, parameters and ids

    for i in range(1, 10):
        value1, datastr1 = ecu.get_st(
            "E019"
        )  # when you know that it is state name (internal or codeMR)
        value2, datastr2 = ecu.get_pr(
            "PR141"
        )  # when you know that it is parameter name (internal or codeMR)
        value3, datastr3 = ecu.get_val(
            "PR091"
        )  # when you do't know what it is state, param or id
        value4, datastr4 = ecu.get_id(
            "ID008"
        )  # when you know that it is identification name (internal or codeMR)

        # get all values before showing them for avoid screen flickering

        clear_screen()
        print()
        print("E019 ", value1)
        print("RP141", value2)
        print("PR091", value3)
        print("ID008", value4)
        time.sleep(0.3)  # 300 milliseconds

    # ecu.run_cmd('CF125', 'B0')
    ecu.run_cmd("RZ001")

    #####
    ##### Example end
    #####


if __name__ == "__main__":
    main()
