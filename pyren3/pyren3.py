import os
import pickle
import sys

from mod import config, db_manager
from mod.optfile import Optfile
from mod.utils import clearScreen, getVIN

if config.OS == "nt":
    import pip

    try:
        import serial
    except ImportError:
        pip.main(["install", "pyserial"])

    try:
        import colorama
    except ImportError:
        pip.main(["install", "colorama"])
        try:
            import colorama
        except ImportError:
            print(
                "\n\n\n\t\t\tGive me access to the Internet for download modules\n\n\n"
            )
            sys.exit()
    colorama.init()
else:
    # let's try android
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
        print("\n\n\n\tPleas install additional modules")
        print("\t\t>sudo easy_install pyserial")
        # print "\t\t>sudo easy_install ply"
        sys.exit()

from mod import utils
from mod.ddt import ddt_utils

from mod.elm import ELM
from mod.scan_ecus import ScanEcus
from mod.ecu import ECU


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
        config.opt_port = options.port
        config.opt_ecuid = options.ecuid
        config.opt_speed = int(options.speed)
        config.opt_rate = int(options.rate)
        config.opt_lang = options.lang
        config.opt_car = options.car
        config.opt_log = options.logfile
        config.opt_demo = options.demo
        config.opt_scan = options.scan
        config.opt_csv = options.csv
        config.opt_csv_only = options.csv_only
        if config.opt_csv:
            config.opt_csv_human = True
        if config.opt_csv_only:
            config.opt_csv = True
        config.opt_csv_human = options.csv_human
        if config.opt_csv_human:
            config.opt_csv = True
        config.opt_usrkey = options.usr_key
        config.opt_verbose = options.verbose
        config.opt_si = options.si
        config.opt_cfc0 = options.cfc
        config.opt_caf = options.caf
        config.opt_n1c = options.n1c
        config.opt_exp = options.exp
        config.opt_dump = options.dump
        config.opt_can2 = options.can2
        config.opt_performance = options.performance
        config.opt_sd = options.sd
        config.opt_minordtc = options.minordtc
        if options.dev == "" or len(options.dev) != 4 or options.dev[0:2] != "10":
            config.opt_dev = False
            config.opt_devses = "1086"
        else:
            print("Development MODE")
            config.opt_dev = True
            config.opt_devses = options.dev
        config.opt_excel = options.excel
        if config.opt_excel:
            config.opt_csv_sep = ";"
            config.opt_csv_dec = ","
        else:
            config.opt_csv_sep = ","
            config.opt_csv_dec = "."


def main():
    """Main function"""
    optParser()

    utils.chkDirTree()
    db_manager.find_DBs()

    print("Opening ELM")
    elm = ELM(config.opt_port, config.opt_speed, config.opt_log)

    # change serial port baud rate
    if config.opt_speed < config.opt_rate and not config.opt_demo:
        elm.port.soft_boudrate(config.opt_rate)

    print("Loading ECUs list")
    se = ScanEcus(elm)  # Prepare list of all ecus

    SEFname = "savedEcus.p"
    if config.opt_can2:
        SEFname = "savedEcus2.p"

    if config.opt_demo and len(config.opt_ecuid) > 0:
        # demo mode with predefined ecu list
        if "tcom" in config.opt_ecuid.lower() or len(config.opt_ecuid) < 4:
            tcomid = "".join([i for i in config.opt_ecuid if i.isdigit()])
            se.load_model_ECUs("Vehicles/TCOM_" + tcomid + ".xml")
            config.opt_ecuid = ",".join(sorted(se.allecus.keys()))
        else:
            se.read_Uces_file(all=True)
        se.detectedEcus = []
        for i in config.opt_ecuid.split(","):
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
        if not os.path.isfile(SEFname) or config.opt_scan:
            # choosing model
            se.chooseModel(config.opt_car)  # choose model of car for doing full scan

        # Do this check every time
        se.scanAllEcus()  # First scan of all ecus

    config.vin = getVIN(se.detectedEcus, elm, getFirst=True)

    print("Loading language ")
    sys.stdout.flush()
    # loading language data
    lang = Optfile("Location/DiagOnCAN_" + config.opt_lang + ".bqm", True)
    config.language_dict = lang.dict
    print("Done")

    ddt_utils.searchddtroot()

    while 1:
        clearScreen()
        choosen_ecu = se.chooseECU(config.opt_ecuid)  # choose ECU among detected
        config.opt_ecuid = ""
        if choosen_ecu == -1:
            continue

        ecucashfile = "./cache/" + choosen_ecu["ModelId"] + "_" + config.opt_lang + ".p"

        if os.path.isfile(ecucashfile):  # if cache exists
            ecu = pickle.load(open(ecucashfile, "rb"))  # load it
        else:
            if len(choosen_ecu["ecuname"]) != 5:
                continue
            ecu = ECU(choosen_ecu, lang.dict)  # loading original data for chosen ECU
            pickle.dump(ecu, open(ecucashfile, "wb"))  # and save cache

        ecu.initELM(elm)  # init ELM for chosen ECU

        if config.opt_demo:
            print("Loading dump")
            ecu.loadDump()
        elif config.opt_dump:
            print("Saving dump")
            ecu.saveDump()

        ecu.show_screens()  # show ECU screens


if __name__ == "__main__":
    main()
