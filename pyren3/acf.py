import os
import pickle

from serial.tools import list_ports

from pyren3 import config
from pyren3.mod import db_manager, utils
from pyren3.mod.acf_func import acf_loadModules
from pyren3.mod.acf_proc import acf_MTC_generateDefaults, acf_MTC_optionsExplorer
from pyren3.mod.elm import ELM
from pyren3.mod.mtc import acf_getMTC
from pyren3.mod.optfile import Optfile
from pyren3.mod.scan_ecus import ScanEcus, families as families, findTCOM as findTCOM
from pyren3.mod.utils import getVIN


def optParser():
    """Parsing of command line parameters. User should define at least com port name"""

    import argparse

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

    parser.add_argument(
        "--exp", help="Explore options", dest="exp", default=False, action="store_true"
    )

    parser.add_argument("--vin", help="vin number", dest="vinnum", default="")

    parser.add_argument("--ref", help="alternative ref", dest="ref", default="")

    parser.add_argument("--mtc", help="alternative mtc", dest="mtc", default="")

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

    if not options.port and config.OS != "android":
        parser.print_help()
        iterator = sorted(list(list_ports.comports()))
        print("")
        print("Available COM ports:")
        for port, desc, hwid in iterator:
            print("%-30s \n\tdesc: %s \n\thwid: %s" % (port, desc, hwid))
        print("")
        exit(2)
    else:
        config.PORT = options.port
        config.SPEED = int(options.speed)
        config.RATE = int(options.rate)
        config.LANG = options.lang
        config.LOG = options.logfile
        config.DEMO = options.demo
        config.SCAN = options.scan
        config.SLOW_INIT = options.si
        config.CFC0 = options.cfc
        config.N1C = options.n1c
        config.CAN2 = options.can2
        config.VIN = options.vinnum
        config.VERBOSE = options.verbose
        config.opt_verbose2 = options.verbose2
        config.ALTERNATIVE_REFS = options.ref
        config.ALTERNATIVE_MTC = options.mtc
        config.EXPERT_MODE = options.exp

        if options.dev == "" or len(options.dev) != 4 or options.dev[0:2] != "10":
            config.DEV = False
            config.DEV_SESSION = "1086"
        else:
            print("Development MODE")
            config.DEV = True
            config.DEV_SESSION = options.dev


def main():
    """Main function"""

    optParser()

    utils.chkDirTree()
    db_manager.find_DBs()

    """Check directories"""
    if not os.path.exists("../BVMEXTRACTION"):
        print("Can't find MTC database. (../BVMEXTRACTION)")
        exit()

    print("Loading language ")
    lang = Optfile("Location/DiagOnCAN_" + config.LANG + ".bqm", True)
    config.LANGUAGE_DICT = lang.dict
    print("Done")

    if not config.DEMO:
        # load connection attributes from savedEcus.p
        print("Opening ELM")
        elm = ELM(config.PORT, config.SPEED, config.LOG)

        # change serial port baud rate
        if config.SPEED < config.RATE and not config.DEMO:
            elm.port.soft_boudrate(config.RATE)

        print("Loading ECUs list")

        # load savedEcus.p
        se = ScanEcus(elm)  # Prepare list of all ecus
        se.scanAllEcus()  # First scan of all ecus
        de = se.detectedEcus

        if config.VIN == "":
            print("Reading VINs")
            VIN = getVIN(de, elm)
            config.VIN = VIN

    else:

        # load connection attribute from platform_attr
        pl_id_cache = "./cache/platform_attr.p"
        if os.path.isfile(pl_id_cache):  # if cache exists
            pl_id = pickle.load(open(pl_id_cache, "rb"))  # load it
        else:  # else
            findTCOM("", "", "", True)  # make cache
            pl_id = pickle.load(open(pl_id_cache, "rb"))  # load it
        # but we do not have platform yet, so load data and then continue

    VIN = config.VIN

    if len(VIN) != 17:
        print("ERROR!!! Can't find any VIN. Check connection")
        exit()
    else:
        print("\tVIN     :", VIN)

    # print 'Finding MTC'
    vindata, mtcdata, refdata, platform = acf_getMTC(VIN)

    if vindata == "" or mtcdata == "" or refdata == "":
        print("ERROR!!! Can't find MTC data in database")
        exit()

    # print vindata
    print("\tPlatform:", platform)
    print("\tvindata:", vindata)
    print("\tmtcdata:", mtcdata)
    print("\trefdata:", refdata)

    mtc = (
        mtcdata.replace(" ", "")
        .replace("\n", "")
        .replace("\r", "")
        .replace("\t", "")
        .split(";")
    )

    # now we may continue to prepare connection attributes in demo mode
    if config.DEMO:
        de = []
        for bus_brp in pl_id[platform].keys():
            brp = ""
            if ":" in bus_brp:
                bus, brp = bus_brp.split(":")
            else:
                bus = bus_brp

            for idf in pl_id[platform][bus_brp].keys():
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
                for a in pl_id[platform][bus_brp][idf]:
                    if ent["pin"] == "iso":
                        ent["dst"] = a.split("#")[0]
                    else:
                        ent["dst"], ent["idRx"], ent["idTx"], starts = a.split("#")
                    if ent["startDiagReq"] == "":
                        ent["startDiagReq"] = starts
                    else:
                        ent["startDiagReq"] += "#" + starts

                de.append(ent)

    print("Loading Modules")
    module_list = acf_loadModules(de, refdata, platform)

    print()

    for m in module_list:
        if "sref" not in list(m.keys()) or m["sref"] == "":
            continue
        if families[m["idf"]] in list(config.LANGUAGE_DICT.keys()):
            m["fam_txt"] = config.LANGUAGE_DICT[families[m["idf"]]]
        else:
            m["fam_txt"] = m["idf"]
        if "sref" in list(m.keys()):
            print("\n#########   Family : ", m["idf"], " : ", m["fam_txt"])
            if "mo" in list(m.keys()) and m["mo"] != "":
                print("%2s : %s : %s" % (m["idf"], m["sref"], m["mo"].NOM))

                acf_MTC_generateDefaults(m, mtc)
                # acf_MTC_findDiff( m, mtc, elm )

            else:
                print("%2s : %s :   " % (m["idf"], m["sref"]))

    if config.EXPERT_MODE:
        with open("../MTCSAVE/" + VIN + "/mtcexp.txt", "w") as f:
            for option in sorted(mtc):
                res = acf_MTC_optionsExplorer(module_list, option, mtc)
                for l in res:
                    f.write(l + "\n")


if __name__ == "__main__":
    main()
