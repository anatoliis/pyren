#!/usr/bin/env python3
import argparse
import os
import pickle

import config
import mod_db_manager
import mod_utils
from mod_acf_func import acf_load_modules
from mod_acf_proc import acf_mtc_generate_defaults
from mod_elm import ELM
from mod_mtc import acf_get_mtc
from mod_optfile import optfile
from mod_scan_ecus import ScanEcus, families as families, findTCOM as findTCOM
from mod_utils import get_vin
from serial.tools import list_ports


def opt_parser():
    """Parsing of command line parameters. User should define at least com port name"""

    parser = argparse.ArgumentParser(description="acf - auto configuration tool")

    parser.add_argument("-p", help="ELM327 com port name", dest="port", default="")

    parser.add_argument(
        "-s",
        help="com port speed configured on ELM {38400[default],57600,115200,230400,500000} DEPRECATED",
        dest="speed",
        default="38400",
    )

    parser.add_argument(
        "-r",
        help="com port rate during diagnostic session {38400[default],57600,115200,230400,500000}",
        dest="rate",
        default="38400",
    )

    parser.add_argument(
        "--si", help="try SlowInit first", dest="si", default=False, action="store_true"
    )

    parser.add_argument(
        "-L",
        help="language option {RU[default],GB,FR,IT,...}",
        dest="lang",
        default="RU",
    )

    parser.add_argument(
        "--cfc",
        help="turn off automatic FC and do it by script",
        dest="cfc",
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
        "--dev",
        help="swith to Development Session for commands from DevList, you should define alternative command for opening the session, like a 1086",
        dest="dev",
        default="",
    )

    parser.add_argument(
        "--can2",
        help="CAN network connected to pin 13 and pin 12",
        dest="can2",
        default=False,
        action="store_true",
    )

    parser.add_argument("--vin", help="vin number", dest="vinnum", default="")

    parser.add_argument("--ref", help="alternative ref", dest="ref", default="")

    parser.add_argument(
        "-vv",
        "--verbose",
        help="show parameter explanations",
        dest="verbose",
        default=False,
        action="store_true",
    )

    parser.add_argument(
        "-vvv",
        help="show parameter explanations",
        dest="verbose2",
        default=False,
        action="store_true",
    )

    options = parser.parse_args()

    if not options.port:
        parser.print_help()
        iterator = sorted(list(list_ports.comports()))
        print("")
        print("Available COM ports:")
        for port, desc, hwid in iterator:
            print("%-30s \n\tdesc: %s \n\thwid: %s" % (port, desc, hwid))
        print("")
        exit(2)
    else:
        config.OPT_PORT = options.port
        config.OPT_SPEED = int(options.speed)
        config.OPT_RATE = int(options.rate)
        config.OPT_LANG = options.lang
        config.OPT_LOG = options.logfile
        config.OPT_DEMO = options.demo
        config.OPT_SCAN = options.scan
        config.OPT_SI = options.si
        config.OPT_CFC0 = options.cfc
        config.OPT_N1C = options.n1c
        config.OPT_CAN2 = options.can2
        config.VIN = options.vinnum
        config.OPT_VERBOSE = options.verbose
        config.opt_verbose2 = options.verbose2
        config.OPT_REF = options.ref


def main():
    """Main function"""

    opt_parser()

    mod_utils.chk_dir_tree()
    mod_db_manager.find_dbs()

    """Check directories"""
    if not os.path.exists("../BVMEXTRACTION"):
        print("Can't find MTC database. (../BVMEXTRACTION)")
        exit()

    print("Loading language ")
    lang = optfile("Location/DiagOnCAN_" + config.OPT_LANG + ".bqm", True)
    config.LANGUAGE_DICT = lang.dict
    print("Done")

    if not config.OPT_DEMO:
        # load connection attributes from savedEcus.p
        print("Opening ELM")
        elm = ELM(config.OPT_PORT, config.OPT_SPEED, config.OPT_LOG)

        # change serial port baud rate
        if config.OPT_SPEED < config.OPT_RATE and not config.OPT_DEMO:
            elm.port.soft_boudrate(config.OPT_RATE)

        print("Loading ECUs list")

        # load savedEcus.p
        scan_ecus = ScanEcus(elm)  # Prepare a list of all ecus
        scan_ecus.scan_all_ecus()  # First scan of all ecus
        detected_ecus = scan_ecus.detectedEcus

        if config.VIN == "":
            print("Reading VINs")
            vin = get_vin(detected_ecus, elm)
            config.VIN = vin

    else:

        # load connection attribute from platform_attr
        platform_id_cache = "./cache/platform_attr.p"
        if os.path.isfile(platform_id_cache):  # if cache exists
            platform_id = pickle.load(open(platform_id_cache, "rb"))  # load it
        else:  # else
            findTCOM("", "", "", True)  # make cache
            platform_id = pickle.load(open(platform_id_cache, "rb"))  # load it
        # but we do not have a platform yet, so load data and then continue

    vin = config.VIN

    if len(vin) != 17:
        print("ERROR!!! Can't find any VIN. Check connection")
        exit()
    else:
        print("\tVIN     :", vin)

    # print 'Finding MTC'
    vin_data, mtc_data, ref_data, platform = acf_get_mtc(vin)

    if vin_data == "" or mtc_data == "" or ref_data == "":
        print("ERROR!!! Can't find MTC data in database")
        exit()

    # print vin_data
    print("\tPlatform:", platform)
    print("\tvin_data:", vin_data)
    print("\tmtc_data:", mtc_data)
    print("\tref_data:", ref_data)

    mtc = (
        mtc_data.replace(" ", "")
        .replace("\n", "")
        .replace("\r", "")
        .replace("\t", "")
        .split(";")
    )

    # now we may continue to prepare connection attributes in demo mode
    if config.OPT_DEMO:
        detected_ecus = []
        for bus_brp in platform_id[platform].keys():
            brp = ""
            if ":" in bus_brp:
                bus, brp = bus_brp.split(":")
            else:
                bus = bus_brp

            for idf in platform_id[platform][bus_brp].keys():
                ent = {}
                ent["idf"] = idf
                ent["ecuname"] = ""
                if bus == "6":
                    ent["pin"] = "can"
                    ent["pin1"] = "6"
                    ent["pin2"] = "14"
                elif bus == "13":
                    ent["pin"] = "can2"
                    ent["pin1"] = "13"
                    ent["pin2"] = "12"
                else:
                    ent["pin"] = "iso"
                    ent["pin1"] = "7"
                    ent["pin2"] = "15"
                ent["brp"] = brp
                ent["vehTypeCode"] = platform
                ent["startDiagReq"] = ""
                for a in platform_id[platform][bus_brp][idf]:
                    if ent["pin"] == "iso":
                        ent["dst"] = a.split("#")[0]
                    else:
                        ent["dst"], ent["idRx"], ent["idTx"], starts = a.split("#")
                    if ent["startDiagReq"] == "":
                        ent["startDiagReq"] = starts
                    else:
                        ent["startDiagReq"] += "#" + starts

                detected_ecus.append(ent)

    print("Loading Modules")
    module_list = acf_load_modules(detected_ecus, ref_data, platform)

    print()

    for module_ in module_list:
        if "sref" not in list(module_.keys()) or module_["sref"] == "":
            continue
        if families[module_["idf"]] in list(config.LANGUAGE_DICT.keys()):
            module_["fam_txt"] = config.LANGUAGE_DICT[families[module_["idf"]]]
        else:
            module_["fam_txt"] = module_["idf"]
        if "sref" in list(module_.keys()):
            print("\n#########   Family : ", module_["idf"], " : ", module_["fam_txt"])
            if "mo" in list(module_.keys()) and module_["mo"] != "":
                print(
                    "%2s : %s : %s"
                    % (module_["idf"], module_["sref"], module_["mo"].NOM)
                )

                acf_mtc_generate_defaults(module_, mtc)
                # acf_MTC_findDiff( module_, mtc, elm )
            else:
                print("%2s : %s :   " % (module_["idf"], module_["sref"]))


if __name__ == "__main__":
    main()
