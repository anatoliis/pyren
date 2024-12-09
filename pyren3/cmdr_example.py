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

import pyren3
from mod import config
from mod.ecu.ecu import ECU
from mod.elm import ELM
from mod.optfile import Optfile
from mod.scan_ecus import ScanEcus
from mod.utils import clearScreen

try:
    import androidhelper as android

    config.OS = "android"
except:
    try:
        import android

        config.OS = "android"
    except:
        pass

if config.OS != "android":
    try:
        import serial
        from serial.tools import list_ports
    except ImportError:
        sys.exit()


def prepareECU():
    """This function loads data for ECU"""

    global elm
    global ecu

    pyren3.optParser()

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

    # clearScreen()

    choosen_ecu = se.chooseECU(config.opt_ecuid)  # choose ECU among detected
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
    prepareECU()

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

        clearScreen()
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
