#!/usr/bin/env python3
import os
import re
import sys
import time
import xml.dom.minidom
from collections import OrderedDict
from datetime import datetime

import config
import mod_db_manager
import mod_ecu_command
import mod_ecu_default
import mod_ecu_identification
import mod_ecu_parameter
import mod_ecu_state
import mod_optfile
import mod_ply
import mod_utils
from mod_ecu_dataids import ecu_dataids, pyren_encode
from mod_elm import ALLOWED_LIST, DNAT, SNAT, pyren_time

os.chdir(os.path.dirname(os.path.realpath(sys.argv[0])))

F2A = {
    "01": "7A",
    "02": "01",
    "03": "51",
    "04": "26",
    "05": "2C",
    "06": "00",
    "07": "24",
    "08": "29",
    "09": "6E",
    "10": "57",
    "11": "52",
    "12": "79",
    "13": "0D",
    "14": "00",
    "15": "32",
    "16": "37",
    "17": "6B",
    "18": "04",
    "19": "3F",
    "20": "27",
    "21": "08",
    "22": "00",
    "23": "3A",
    "24": "50",
    "25": "1C",
    "26": "00",
    "27": "99",
    "28": "00",
    "29": "07",
    "30": "66",
    "31": "A7",
    "32": "60",
    "33": "4B",
    "34": "2B",
    "35": "1B",
    "36": "61",
    "37": "25",
    "38": "1E",
    "39": "D2",
    "40": "23",
    "41": "0E",
    "42": "40",
    "43": "7C",
    "44": "97",
    "45": "3C",
    "46": "82",
    "47": "4D",
    "48": "11",
    "49": "47",
    "50": "02",
    "51": "0F",
    "52": "70",
    "53": "71",
    "54": "72",
    "55": "0E",
    "56": "1A",
    "57": "5D",
    "59": "E2",
    "60": "A5",
    "61": "A6",
    "62": "00",
    "63": "65",
    "64": "DF",
    "65": "2A",
    "66": "FE",
    "67": "7B",
    "68": "73",
    "69": "16",
    "70": "62",
    "72": "00",
    "73": "63",
    "74": "81",
    "76": "13",
    "77": "77",
    "78": "64",
    "79": "D1",
    "80": "F7",
    "81": "F8",
    "86": "2E",
    "87": "06",
    "90": "59",
    "91": "86",
    "92": "87",
    "93": "00",
    "94": "67",
    "95": "93",
    "96": "95",
    "97": "68",
    "98": "A8",
    "99": "C0",
}

ecu_dump = {}  # {'request':'response'}
favourite_screen = mod_ecu_default.ecu_own_screen("FAV")


class ECU:
    """Contains data for one specific ECU
    implement menu for ecu"""

    calc: mod_ply.Calc = None

    path = "EcuRenault/Sessions/"

    getDTCmnemo = ""
    resetDTCcommand = ""
    screens = []
    Defaults = {}
    Parameters = {}
    States = {}
    Identifications = {}
    Commands = {}
    Services = {}
    Mnemonics = {}
    DataIds = {}

    # variables for extended DE information
    ext_de = []

    ecudata = {}

    min_refresh_rate = 0.100

    def __init__(self, cecu, tran):

        self.elm = 0
        self.ecudata = cecu

        self.getDTCmnemo = ""
        self.resetDTCcommand = ""
        self.screens = []
        self.Defaults = {}
        self.Parameters = {}
        self.States = {}
        self.Identifications = {}
        self.Commands = {}
        self.Services = {}
        self.Mnemonics = {}
        self.DataIds = {}

        print("Deflen:", len(self.Defaults))

        print("ECU type: ", cecu["stdType"])

        mdom = xml.dom.minidom.parse(
            mod_db_manager.get_file_from_clip(
                self.path + self.ecudata["ModelId"].strip()[:-3] + "xml"
            )
        )
        mdoc = mdom.documentElement

        print("Loading screens ")
        self.screens = []
        sc_class = mod_ecu_default.ecu_screens(self.screens, mdoc, tran)

        print("Loading optimyzer")
        self.defaults = []
        opt_file = mod_optfile.optfile(
            self.path + self.ecudata["OptimizerId"].strip()[:-3] + "xml"
        )

        print("Loading defaults")
        df_class = mod_ecu_default.ecu_defaults(
            self.Defaults, mdoc, opt_file.dict, tran
        )
        print("Loading parameters")
        pr_class = mod_ecu_parameter.ecu_parameters(
            self.Parameters, mdoc, opt_file.dict, tran
        )
        print("Loading states")
        st_class = mod_ecu_state.ecu_states(self.States, mdoc, opt_file.dict, tran)
        print("Loading identifications")
        id_class = mod_ecu_identification.ecu_identifications(
            self.Identifications, mdoc, opt_file.dict, tran
        )
        print("Loading commands")
        cm_class = mod_ecu_command.ecu_commands(
            self.Commands, mdoc, opt_file.dict, tran
        )
        print("Loading services")
        sv_class = mod_ecu_default.ecu_services(
            self.Services, mdoc, opt_file.dict, tran
        )
        print("Loading mnemonics")
        mm_class = mod_ecu_default.ecu_mnemonics(
            self.Mnemonics, mdoc, opt_file.dict, tran
        )
        print("Loading DTC commands")
        self.getDTCmnemo, self.resetDTCcommand = df_class.getDTCCommands(
            mdoc, opt_file.dict, cecu["stdType"]
        )
        if "DataIds" in list(opt_file.dict.keys()):
            print("Loading DataIds")
            xmlstr = opt_file.dict["DataIds"]
            ddom = xml.dom.minidom.parseString(xmlstr.encode("utf-8"))
            ddoc = ddom.documentElement
            di_class = ecu_dataids(self.DataIds, ddoc, opt_file.dict, tran)

    def init_elm(self, elm):
        print("Loading PLY ")
        self.calc = mod_ply.Calc()

        print("Init ELM")
        self.elm = elm

        if self.ecudata["pin"].lower() == "can":
            self.elm.init_can()
            self.elm.set_can_addr(self.ecudata["dst"], self.ecudata)
        else:
            self.elm.init_iso()
            self.elm.set_iso_addr(self.ecudata["dst"], self.ecudata)

        self.elm.start_session(self.ecudata["startDiagReq"])

        if config.OS == "android" or config.OPT_CSV:
            if (
                self.ecudata["pin"].lower() == "can"
                and self.DataIds
                and config.OPT_PERFORMANCE
            ):
                self.elm.check_module_performance_level(self.DataIds)

        print("Done")

        global ecu_dump
        ecu_dump = {}

    def saveDump(self):
        """save responces from all 21xx, 22xxxx commands"""

        dump_name = (
            "./dumps/" + str(int(time.time())) + "_" + self.ecudata["ecuname"] + ".txt"
        )
        df = open(dump_name, "wt")

        self.elm.clear_cache()

        im = " from " + str(len(list(self.Services.keys())))
        i = 0
        for service in list(self.Services.values()):
            i = i + 1
            print("\r\t\t\t\r", str(i) + im, end=" ")
            sys.stdout.flush()
            if service.startReq[:2] in ALLOWED_LIST + ["17", "19"]:
                if service.startReq[:2] == "19" and service.startReq[:4] != "1902":
                    continue
                if service.startReq[:2] == "22" and len(service.startReq) < 6:
                    continue
                pos = chr(ord(service.startReq[0]) + 4) + service.startReq[1]
                rsp = self.elm.request(service.startReq, pos, False)
                if ":" in rsp:
                    continue
                df.write("%s:%s\n" % (service.startReq, rsp))

        df.close()

    def load_dump(self, dump_name=""):
        """load saved dump for demo mode"""

        global ecu_dump

        ecu_dump = {}

        if len(dump_name) == 0:
            flist = []
            for root, dirs, files in os.walk("./dumps"):
                for f in files:
                    if (self.ecudata["ecuname"] + ".txt") in f:
                        flist.append(f)

            if len(flist) == 0:
                return
            flist.sort()
            dump_name = os.path.join("./dumps/", flist[-1])

        self.elm.load_dump(dump_name)

    def get_st(self, name):
        if name not in list(self.States.keys()):
            for i in list(self.States.keys()):
                if name == self.States[i].agcdRef:
                    name = i
                    break
        if name not in list(self.States.keys()):
            return "none", "unknown state"
        self.elm.clear_cache()
        datastr, help, csvd = mod_ecu_state.get_state(
            self.States[name], self.Mnemonics, self.Services, self.elm, self.calc
        )
        return csvd, datastr

    def get_ref_st(self, name):
        if name not in list(self.States.keys()):
            for i in list(self.States.keys()):
                if name == self.States[i].agcdRef:
                    name = i
                    break
        if name not in list(self.States.keys()):
            return None
        return self.States[name]

    def get_pr(self, name):
        if name not in list(self.Parameters.keys()):
            for i in list(self.Parameters.keys()):
                if name == self.Parameters[i].agcdRef:
                    name = i
                    break
        if name not in list(self.Parameters.keys()):
            return "none", "unknown parameter"
        self.elm.clear_cache()
        datastr, help, csvd = mod_ecu_parameter.get_parameter(
            self.Parameters[name], self.Mnemonics, self.Services, self.elm, self.calc
        )
        return csvd, datastr

    def get_ref_pr(self, name):
        if name not in list(self.Parameters.keys()):
            for i in list(self.Parameters.keys()):
                if name == self.Parameters[i].agcdRef:
                    name = i
                    break
        if name not in list(self.Parameters.keys()):
            return None
        return self.Parameters[name]

    def get_id(self, name, raw=False):
        if name not in list(self.Identifications.keys()):
            for i in list(self.Identifications.keys()):
                if name == self.Identifications[i].codeMR:
                    name = i
                    break
        if name not in list(self.Identifications.keys()):
            return "none", "unknown identification"
        if raw:
            return mod_ecu_identification.get_identification(
                self.Identifications[name],
                self.Mnemonics,
                self.Services,
                self.elm,
                self.calc,
                raw,
            )
        self.elm.clear_cache()
        datastr, help, csvd = mod_ecu_identification.get_identification(
            self.Identifications[name],
            self.Mnemonics,
            self.Services,
            self.elm,
            self.calc,
        )
        return csvd, datastr

    def get_ref_id(self, name):
        if name not in list(self.Identifications.keys()):
            for i in list(self.Identifications.keys()):
                if name == self.Identifications[i].codeMR:
                    name = i
                    break
        if name not in list(self.Identifications.keys()):
            return None
        return self.Identifications[name]

    def get_val(self, name):
        r1, r2 = self.get_st(name)
        if r1 != "none":
            return r1, r2
        r1, r2 = self.get_pr(name)
        if r1 != "none":
            return r1, r2
        r1, r2 = self.get_id(name)
        if r1 != "none":
            return r1, r2
        return "none", "unknown name"

    def acf_ready(self):
        # check if scen_auto_config among commands and scenaium exists
        res = False
        c = ""
        for c in self.Commands.keys():
            if "scen_auto_config" in self.Commands[c].scenario:
                res = True
                break
        if res:
            # check if scenario exists
            path = "EcuRenault/Scenarios/"
            scenarioName, scenarioData = self.Commands[c].scenario.split("#")
            scenarioData = scenarioData[:-4] + ".xml"
            if not mod_db_manager.file_in_clip(os.path.join(path, scenarioData)):
                return ""
            else:
                return c
        else:
            return ""

    def run_cmd(self, name, param="", partype="HEX"):
        if name not in list(self.Commands.keys()):
            for i in list(self.Commands.keys()):
                if name == self.Commands[i].codeMR:
                    name = i
                    break
        if name not in list(self.Commands.keys()):
            return "none"
        self.elm.clear_cache()
        resp = mod_ecu_command.runCommand(
            self.Commands[name], self, self.elm, param, partype
        )
        return resp

    def get_ref_cmd(self, name):
        if name not in list(self.Commands.keys()):
            for i in list(self.Commands.keys()):
                if name == self.Commands[i].codeMR:
                    name = i
                    break
        if name not in list(self.Commands.keys()):
            return None
        return self.Commands[name]

    def show_commands(self, datarefs, path):
        while True:
            mod_utils.clear_screen()
            header = (
                "ECU : " + self.ecudata["ecuname"] + "  " + self.ecudata["doc"] + "\n"
            )
            header = header + "Screen : " + path
            print(pyren_encode(header))
            menu = []
            cmds = []
            for dr in datarefs:
                datastr = dr.name
                if dr.type == "State":
                    datastr = (
                        self.States[dr.name].name
                        + "States not supported on one screen with commands"
                    )
                if dr.type == "Parameter":
                    datastr = (
                        self.Parameters[dr.name].name
                        + "Parameters not supported on one screen with commands"
                    )
                if dr.type == "Identification":
                    datastr = (
                        self.Identifications[dr.name].name
                        + "Identifications not supported on one screen with commands"
                    )
                if dr.type == "Command":
                    datastr = (
                        self.Commands[dr.name].codeMR
                        + " [Command] "
                        + self.Commands[dr.name].label
                    )
                    cmds.append(dr.name)
                menu.append(datastr)

            menu.append("<Up>")
            choice = mod_utils.choice_long(menu, "Choose :", header)
            if choice[0] == "<Up>":
                return

            header = header + " -> " + cmds[int(choice[1]) - 1] + " [Command] "
            mod_ecu_command.executeCommand(
                self.Commands[cmds[int(choice[1]) - 1]], self, self.elm, header
            )

    def show_datarefs(self, datarefs, path):
        mod_utils.clear_screen()
        if os.name == "nt":
            initScreen = chr(27) + "[;H"
        else:
            initScreen = chr(27) + "[2J" + chr(27) + "[;H"

        csvf = 0
        self.elm.currentScreenDataIds = []

        mask = False
        masks = []
        datarefsToRemove = []

        for st in self.States:
            if st.startswith("MAS"):
                mask = True
                mod_ecu_state.get_state(
                    self.States[st], self.Mnemonics, self.Services, self.elm, self.calc
                )
                if int(self.States[st].value):
                    masks.append(self.States[st].name)

        if mask and not config.OPT_DEMO:
            for dr in datarefs:
                if dr.type == "State":
                    if (
                        self.States[dr.name].mask
                        and self.States[dr.name].mask not in masks
                    ):
                        datarefsToRemove.append(dr)
                if dr.type == "Parameter":
                    if (
                        self.Parameters[dr.name].mask
                        and self.Parameters[dr.name].mask not in masks
                    ):
                        datarefsToRemove.append(dr)
                if dr.type == "Identification":
                    if (
                        self.Identifications[dr.name].mask
                        and self.Identifications[dr.name].mask not in masks
                    ):
                        datarefsToRemove.append(dr)
                if dr.type == "Command":
                    if (
                        self.Commands[dr.name].mask
                        and self.Commands[dr.name].mask not in masks
                    ):
                        datarefsToRemove.append(dr)
            for dr in datarefsToRemove:
                datarefs.remove(dr)

        # Check if datarefs contains any commands
        for dr in datarefs:
            if dr.type == "Command":
                self.show_commands(datarefs, path)
                return

        if config.OPT_CSV and config.EXT_CUR_DTC == "000000":
            # prepare to csv save
            self.min_refresh_rate = 0
            if config.OPT_EXCEL:
                csvline = "sep=" + config.OPT_CSV_SEP + "\n"
            csvline = "Time"
            nparams = 0
            for dr in datarefs:
                if dr.type == "State":
                    csvline += (
                        ";"
                        + self.States[dr.name].codeMR
                        + ":"
                        + self.States[dr.name].label
                    )
                    nparams += 1
                if dr.type == "Parameter":
                    csvline += (
                        ";"
                        + self.Parameters[dr.name].codeMR
                        + ":"
                        + self.Parameters[dr.name].label
                        + " ["
                        + self.Parameters[dr.name].unit
                        + "]"
                    )
                    nparams += 1
            if config.OPT_USRKEY:
                csvline += ";User events"
            csvline = pyren_encode(csvline)
            if nparams:
                csv_start_time = int(round(pyren_time() * 1000))
                csv_filename = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
                # here the problem with russian letters. and very long name
                csv_filename = csv_filename + "_" + self.ecudata["ecuname"] + "_" + path
                csv_filename += ".csv"
                csv_filename = csv_filename.replace("/", "_")
                csv_filename = csv_filename.replace(" : ", "_")
                csv_filename = csv_filename.replace(" -> ", "_")
                csv_filename = csv_filename.replace(" ", "_")
                # if config.os == 'android':
                #  csv_filename = csv_filename.encode("ascii","ignore")
                csvf = open(
                    "./csv/" + pyren_encode(csv_filename), "w", encoding="utf-8"
                )
                csvf.write("\ufeff")

        DTCpos = path.find("DTC")
        if DTCpos > 0:
            IDstr = "#" + path[DTCpos + 3 : DTCpos + 9]
        else:
            IDstr = ""

        # debug
        # show_doc(self.ecudata['dst'], IDstr)

        kb = mod_utils.KeyboardHit()

        tb = pyren_time()  # time of begining

        if len(datarefs) == 0 and "DE" not in path:
            return
        self.elm.clear_cache()

        # csv_only mode workflow in performance mode
        # 1. Read all parameters from the current screen using defalut mode
        # 2. Get all dataIds from the 22 service requests and create a list from them according to a module performance level
        # 3. Collect all 21 service requests and push them into requests list
        # 4. Create a complex requests from the all dataIds list and push them into requests list
        # 5. Send reqests from the requests list and save the responses in a responseHistory list
        # 6. On exit generate csv log file from the responseHistory

        if config.OPT_CSV_ONLY:
            print("Data is sending directly to csv-file")
            print("")
            print("Press any key to exit")

        page = 0

        displayed_data_ids = []  # Current screen dataIds list for csv_only mode
        responseHistory = OrderedDict()
        requests = OrderedDict()  # list of requests to send in csv_only mode

        while True:

            strlst = []
            datarefsRequestTime = int(round(pyren_time() * 1000))

            if config.OPT_CSV_HUMAN and csvf != 0:
                csvline = csvline + "\n"
                csvline = csvline.replace(".", config.OPT_CSV_DEC)
                csvline = csvline.replace(",", config.OPT_CSV_DEC)
                csvline = csvline.replace(";", config.OPT_CSV_SEP)
                csvf.write(csvline)
                csvf.flush()
                time_diff = int(round(pyren_time() * 1000)) - csv_start_time
                time_sec = str(time_diff // 1000)
                time_ms = str((time_diff) % 1000)
                csvline = time_sec.zfill(2) + config.OPT_CSV_DEC + time_ms.zfill(3)

            # Collect all the requests from the current screen
            if (
                config.OPT_PERFORMANCE
                and self.elm.performanceModeLevel > 1
                and config.OPT_CSV_ONLY
            ):
                if self.elm.rsp_cache:
                    if not requests:
                        requests = self.generateRequestsList()

            self.elm.clear_cache()
            if not (config.OPT_CSV_ONLY and requests):
                for dr in datarefs:
                    data_string = dr.name
                    help = dr.type
                    if dr.type == "State":
                        if (
                            self.DataIds
                            and "DTC" in path
                            and dr in self.Defaults[config.EXT_CUR_DTC[:4]].memDatarefs
                        ):
                            data_string, help, csvd = mod_ecu_state.get_state(
                                self.States[dr.name],
                                self.Mnemonics,
                                self.Services,
                                self.elm,
                                self.calc,
                                self.DataIds,
                            )
                        else:
                            data_string, help, csvd = mod_ecu_state.get_state(
                                self.States[dr.name],
                                self.Mnemonics,
                                self.Services,
                                self.elm,
                                self.calc,
                            )
                    if dr.type == "Parameter":
                        if (
                            self.DataIds
                            and "DTC" in path
                            and dr in self.Defaults[config.EXT_CUR_DTC[:4]].memDatarefs
                        ):
                            data_string, help, csvd = mod_ecu_parameter.get_parameter(
                                self.Parameters[dr.name],
                                self.Mnemonics,
                                self.Services,
                                self.elm,
                                self.calc,
                                self.DataIds,
                            )
                        else:
                            data_string, help, csvd = mod_ecu_parameter.get_parameter(
                                self.Parameters[dr.name],
                                self.Mnemonics,
                                self.Services,
                                self.elm,
                                self.calc,
                            )
                    if dr.type == "Identification":
                        data_string, help, csvd = (
                            mod_ecu_identification.get_identification(
                                self.Identifications[dr.name],
                                self.Mnemonics,
                                self.Services,
                                self.elm,
                                self.calc,
                            )
                        )
                    if dr.type == "Command":
                        data_string = (
                            dr.name + " [Command] " + self.Commands[dr.name].label
                        )
                    if dr.type == "Text":
                        data_string = dr.name
                        help = ""
                    if (
                        config.OPT_CSV_HUMAN
                        and csvf != 0
                        and (dr.type == "State" or dr.type == "Parameter")
                    ):
                        csvline += ";" + pyren_encode(csvd)

                    if not (config.OPT_CSV and config.OPT_CSV_ONLY):
                        strlst.append(data_string)
                        if config.OPT_VERBOSE and len(help) > 0:
                            tmp_str = ""
                            for s in help:
                                # s = s.replace('\n','\n\t')
                                s = s.replace("\r", "\n")
                                s = s.replace("&gt;", ">")
                                s = s.replace("&le;", "<")
                                tmp_str = tmp_str + s + "\n\n"
                            W = 50
                            for line in tmp_str.split("\n"):
                                i = 0
                                while i * W < len(line):
                                    strlst.append("\t" + line[i * W : (i + 1) * W])
                                    i = i + 1
                            strlst.append("")
            else:  # Send requests, do not calculate data
                for req in requests:
                    self.elm.request(req)

            if not (config.OPT_CSV and config.OPT_CSV_ONLY):
                newScreen = initScreen
                connectionData = (
                    "   (RT:"
                    + "{0:.4f}".format(self.elm.response_time)
                    + " "
                    + "RR:"
                    + "{:>5.1f}".format(self.elm.get_refresh_rate())
                    + ")   "
                )

                header = (
                    "ECU : "
                    + self.ecudata["ecuname"]
                    + connectionData
                    + self.ecudata["doc"]
                    + "\n"
                )
                header = header + "Screen : " + path
                newScreen = newScreen + pyren_encode(header) + "\n"

                H = 25

                pages = len(strlst) // H
                for l in strlst[page * H : (page + 1) * H]:
                    newScreen = newScreen + pyren_encode(l) + "  \n"
                if not path[:3] == "FAV":
                    if pages > 0:
                        newScreen = (
                            newScreen
                            + "\n"
                            + "[Page "
                            + str(page + 1)
                            + " from "
                            + str(pages + 1)
                            + "] [N-next P-prev.] H for help or any other to exit"
                        )
                    else:
                        newScreen = (
                            newScreen + "\n" + "Press H for help or any key to exit"
                        )
                else:
                    newScreen = (
                        newScreen
                        + "\n"
                        + "Press ENTER to add or delete parameter or any other key to exit"
                    )

                print(newScreen, end=" ")
                sys.stdout.flush()

                # check refresh rate
                if config.OPT_DEMO:
                    self.min_refresh_rate = 1

                tc = pyren_time()
                if (tc - tb) < self.min_refresh_rate:
                    time.sleep(tb + self.min_refresh_rate - tc)
                tb = tc

            if config.OPT_CSV_ONLY:
                responseHistory[datarefsRequestTime] = (
                    self.elm.rsp_cache
                )  # Collect data to generate a file

            if config.OPT_PERFORMANCE and self.elm.performanceModeLevel > 1:
                self.elm.currentScreenDataIds = self.getDataIds(
                    self.elm.rsp_cache, self.DataIds
                )
                if (
                    self.elm.currentScreenDataIds
                ):  # DataIds list is generated only at first data read pass in csv_only mode
                    displayed_data_ids = (
                        self.elm.currentScreenDataIds
                    )  # We save it for file generating function

            if kb.keyboard_hit():
                c = kb.get_character()
                if len(c) != 1:
                    continue
                if path[:3] == "FAV":
                    if ord(c) == 13 or ord(c) == 10:
                        kb.set_normal_term()
                        self.add_favourite()
                        kb.set_get_character_term()
                    else:
                        if config.OPT_CSV and (c in config.OPT_USRKEY):
                            csvline += ";" + pyren_encode(c)
                            continue
                        kb.set_normal_term()
                        self.saveFavList()
                        if config.OPT_CSV and csvf != 0:
                            if config.OPT_CSV_HUMAN:
                                csvf.close()
                                return
                            self.create_file(
                                responseHistory,
                                displayed_data_ids,
                                csvline,
                                csvf,
                                datarefs,
                            )
                        return
                else:
                    n = ord(c) - ord("0")
                    if (not config.OPT_CSV_ONLY) and n > 0 and n <= (pages + 1):
                        page = n - 1
                        mod_utils.clear_screen()
                        continue
                    if c in ["h", "H"]:
                        mod_utils.show_doc(self.ecudata["dst"], IDstr)
                        continue
                    if c in ["p", "P"]:
                        if page > 0:
                            page = page - 1
                        mod_utils.clear_screen()
                        continue
                    if c in ["n", "N"]:
                        if page < pages:
                            page = page + 1
                        mod_utils.clear_screen()
                        continue
                    if config.OPT_CSV and (c in config.OPT_USRKEY):
                        csvline += ";" + pyren_encode(c)
                        continue
                    kb.set_normal_term()
                    if config.OPT_CSV and csvf != 0:
                        if config.OPT_CSV_HUMAN:
                            csvf.close()
                            return
                        self.create_file(
                            responseHistory, displayed_data_ids, csvline, csvf, datarefs
                        )
                    if "DTC" in path:
                        config.EXT_CUR_DTC = "000000"
                    return

    def generateRequestsList(self):
        requests = OrderedDict()

        currentScreenDataIdsLength = len(self.elm.currentScreenDataIds)
        for reqDidsIndex in range(
            currentScreenDataIdsLength
        ):  # Create complex requests from all 22 requests
            firstRequest = "22" + self.elm.currentScreenDataIds[0][0].id
            complexRequest, sentDataIdentifires = mod_ecu_default.prepareComplexRequest(
                firstRequest, self.elm.currentScreenDataIds
            )
            requests[complexRequest] = complexRequest
        for req in list(self.elm.rsp_cache.keys()):  # Get all the 21 requests
            if req.startswith("21"):
                requests[req] = req

        return requests

    def create_file(
        self, response_history, displayed_data_ids, csv_line, csv_file, datarefs
    ):
        mod_utils.clear_screen()
        print("Generating a file. Please wait...")

        if len(response_history):
            startTime = next(iter(response_history))

        for reqTime, reqCache in response_history.items():
            for req, rsp in reqCache.items():
                if req.startswith("22") and len(req) > 6:
                    for reqDids in displayed_data_ids:
                        if reqDids[0].id == req[2:6]:
                            mod_ecu_default.parseComplexResponse(
                                self.elm, "62", rsp.replace(" ", ""), reqDids
                            )
                else:
                    self.elm.rsp_cache[req] = rsp

            csv_line = csv_line + "\n"
            csv_line = csv_line.replace(".", config.OPT_CSV_DEC)
            csv_line = csv_line.replace(",", config.OPT_CSV_DEC)
            csv_line = csv_line.replace(";", config.OPT_CSV_SEP)
            csv_file.write(csv_line)
            csv_file.flush()
            time_diff = reqTime - startTime
            time_sec = str(time_diff // 1000)
            time_ms = str((time_diff) % 1000)
            csv_line = time_sec.zfill(2) + config.OPT_CSV_DEC + time_ms.zfill(3)

            for dr in datarefs:
                datastr = dr.name
                help = dr.type
                if dr.type == "State":
                    datastr, help, csvd = mod_ecu_state.get_state(
                        self.States[dr.name],
                        self.Mnemonics,
                        self.Services,
                        self.elm,
                        self.calc,
                    )
                if dr.type == "Parameter":
                    datastr, help, csvd = mod_ecu_parameter.get_parameter(
                        self.Parameters[dr.name],
                        self.Mnemonics,
                        self.Services,
                        self.elm,
                        self.calc,
                    )
                if csv_file != 0 and (dr.type == "State" or dr.type == "Parameter"):
                    csv_line += ";" + csvd

        csv_file.close()

    def add_favourite(self):
        h = 25
        if len(favourite_screen.datarefs) < h:
            user_data_str = input(
                "\nEnter parameter that you want to monitor: "
            ).upper()
            for user_data in user_data_str.split(","):
                user_data = user_data.strip()
                if user_data == "CLEAR":
                    del favourite_screen.datarefs[:]
                pr = self.add_elem(user_data)
                if pr:
                    for dr in favourite_screen.datarefs:
                        if pr == dr.name:
                            favourite_screen.datarefs.remove(dr)
        else:
            input("\nYou have reached parameters limit. Removing last parameter.")
            favourite_screen.datarefs.pop()
        mod_utils.clear_screen()

    def load_fav_list(self):
        fn = "./cache/favlist_" + self.ecudata["ecuname"] + ".txt"

        if not os.path.isfile(fn):
            fav_list_file = open(fn, "wb")
            fav_list_file.close()

        fl = open(fn, "r").readlines()
        if len(fl):
            for drname in fl:
                drname = drname.strip().replace("\n", "")
                if not (
                    drname.startswith("PR")
                    or drname.startswith("ET")
                    or drname.startswith("ID")
                ):
                    return False
                else:
                    self.add_elem(drname)
            return True
        else:
            return False

    def add_elem(self, elem):
        if elem[:2] == "PR":
            for pr in list(self.Parameters.keys()):
                if self.Parameters[pr].agcdRef == elem:
                    if not any(pr == dr.name for dr in favourite_screen.datarefs):
                        favourite_screen.datarefs.append(
                            mod_ecu_default.ecu_screen_dataref("", pr, "Parameter")
                        )
                        return False
                    else:
                        return pr
        elif elem[:2] == "ET":
            for st in list(self.States.keys()):
                if self.States[st].agcdRef == elem:
                    if not any(st == dr.name for dr in favourite_screen.datarefs):
                        favourite_screen.datarefs.append(
                            mod_ecu_default.ecu_screen_dataref("", st, "State")
                        )
                        return False
                    else:
                        return st
        elif elem[:2] == "ID":
            for idk in list(self.Identifications.keys()):
                if self.Identifications[idk].agcdRef == elem:
                    if not any(idk == dr.name for dr in favourite_screen.datarefs):
                        favourite_screen.datarefs.append(
                            mod_ecu_default.ecu_screen_dataref(
                                "", idk, "Identification"
                            )
                        )
                        return False
                    else:
                        return idk
        else:
            return False

    def saveFavList(self):
        fl = open("./cache/favlist_" + self.ecudata["ecuname"] + ".txt", "w")
        for dr in favourite_screen.datarefs:
            if dr.name.startswith("P"):
                for pr in list(self.Parameters.keys()):
                    if dr.name == pr:
                        fl.write(self.Parameters[pr].agcdRef + "\n")
            if dr.name.startswith("E"):
                for st in list(self.States.keys()):
                    if dr.name == st:
                        fl.write(self.States[st].agcdRef + "\n")
            if dr.name.startswith("I"):
                for idk in list(self.Identifications.keys()):
                    if dr.name == idk:
                        fl.write(self.Identifications[idk].agcdRef + "\n")
        fl.close()

    def show_subfunction(self, subfunction, path):
        while 1:
            mod_utils.clear_screen()
            header = (
                "ECU : " + self.ecudata["ecuname"] + "  " + self.ecudata["doc"] + "\n"
            )
            header = header + "Screen : " + path + " -> " + subfunction.text
            print(pyren_encode(header))

            menu = []
            if len(subfunction.datarefs) != 0 and len(subfunction.datarefs) > 0:
                self.show_datarefs(
                    subfunction.datarefs, path + " -> " + subfunction.text
                )
                return
            else:
                return

    def show_function(self, function, path):
        while 1:
            mod_utils.clear_screen()
            header = (
                "ECU : " + self.ecudata["ecuname"] + "  " + self.ecudata["doc"] + "\n"
            )
            header = header + "Screen : " + path + " -> " + function.text
            print(pyren_encode(header))

            menu = []
            if len(function.datarefs) != 0 and len(function.subfunctions) != 0:
                print("Warning: both datarefs and functions not empty")
            if len(function.subfunctions) != 0:
                for sfu in function.subfunctions:
                    menu.append(sfu.text)
                menu.append("<Up>")
                choice = mod_utils.Choice(menu, "Choose :")
                if choice[0] == "<Up>":
                    return
                self.show_subfunction(
                    function.subfunctions[int(choice[1]) - 1],
                    path + " -> " + function.text,
                )
            if len(function.datarefs) != 0:
                self.show_datarefs(function.datarefs, path + " -> " + function.text)
                return

    def show_screen(self, screen):
        while 1:
            mod_utils.clear_screen()
            header = (
                "ECU : " + self.ecudata["ecuname"] + "  " + self.ecudata["doc"] + "\n"
            )
            header = header + "Screen : " + screen.name
            print(pyren_encode(header))

            menu = []
            if len(screen.datarefs) != 0 and len(screen.functions) != 0:
                print("Warning: both datarefs and functions not empty")
            if len(screen.functions) != 0:
                for fu in screen.functions:
                    menu.append(fu.text)
                menu.append("<Up>")
                choice = mod_utils.Choice(menu, "Choose :")
                if choice[0] == "<Up>":
                    return
                self.show_function(screen.functions[int(choice[1]) - 1], screen.name)
            if len(screen.datarefs) != 0:
                self.show_datarefs(screen.datarefs, screen.name)
                return

    def show_defaults_std_a(self):
        while 1:
            path = "DE (STD_A)"
            mod_utils.clear_screen()
            header = (
                "ECU : " + self.ecudata["ecuname"] + "  " + self.ecudata["doc"] + "\n"
            )
            header = header + "Screen : " + path
            print(pyren_encode(header))

            menu = []

            defstr = {}
            hlpstr = {}

            self.elm.clear_cache()

            dtcs, defstr, hlpstr = mod_ecu_default.get_default_std_a(
                self.Defaults,
                self.Mnemonics,
                self.Services,
                self.elm,
                self.calc,
                self.getDTCmnemo,
            )

            listkeys = list(defstr.keys())
            for d in listkeys:
                menu.append(defstr[d])

            menu.append("<Up>")
            menu.append("<Clear>")
            choice = mod_utils.Choice(menu, "Choose one for detailed view or <Clear>:")

            if choice[0] == "<Up>":
                return
            if choice[0] == "<Clear>":
                print("Executing command ", self.resetDTCcommand)
                mod_ecu_command.executeCommand(
                    self.Commands[self.resetDTCcommand], self, self.elm, header
                )
                return

            index = int(choice[1]) - 1
            dtchex = listkeys[index] if len(listkeys) > index else listkeys[0]
            config.EXT_CUR_DTC = dtchex

            path = path + " -> " + defstr[dtchex] + "\n\n" + hlpstr[dtchex] + "\n"

            cur_dtrf = []
            mem_dtrf = []

            if self.Defaults[dtchex[:4]].datarefs:
                cur_dtrf = [
                    mod_ecu_default.ecu_screen_dataref(
                        0, "\n" + config.LANGUAGE_DICT["300"] + "\n", "Text"
                    )
                ] + self.Defaults[dtchex[:4]].datarefs
            if self.Defaults[dtchex[:4]].memDatarefs:
                mem_dtrf_txt = (
                    config.LANGUAGE_DICT["299"] + " DTC" + config.EXT_CUR_DTC + "\n"
                )
                mem_dtrf = [
                    mod_ecu_default.ecu_screen_dataref(0, mem_dtrf_txt, "Text")
                ] + self.Defaults[dtchex[:4]].memDatarefs

            tmp_dtrf = mem_dtrf + cur_dtrf

            self.show_datarefs(tmp_dtrf, path)

    def show_defaults_std_b(self):
        while 1:
            path = "DE (STD_B)"
            mod_utils.clear_screen()
            header = (
                "ECU : " + self.ecudata["ecuname"] + "  " + self.ecudata["doc"] + "\n"
            )
            header = header + "Screen : " + path
            print(pyren_encode(header))

            menu = []

            defstr = {}
            hlpstr = {}

            self.elm.clear_cache()

            dtcs, defstr, hlpstr = mod_ecu_default.get_default_std_b(
                self.Defaults,
                self.Mnemonics,
                self.Services,
                self.elm,
                self.calc,
                self.getDTCmnemo,
            )

            listkeys = list(defstr.keys())
            for d in listkeys:
                menu.append(defstr[d])

            menu.append("<Up>")
            menu.append("<Clear>")
            choice = mod_utils.Choice(menu, "Choose one for detailed view or <Clear>:")

            if choice[0] == "<Up>":
                return
            if choice[0] == "<Clear>":
                print("Executing command ", self.resetDTCcommand)
                mod_ecu_command.executeCommand(
                    self.Commands[self.resetDTCcommand], self, self.elm, header
                )
                return

            index = int(choice[1]) - 1
            dtchex = listkeys[index] if len(listkeys) > index else listkeys[0]
            config.EXT_CUR_DTC = dtchex

            path = path + " -> " + defstr[dtchex] + "\n\n" + hlpstr[dtchex] + "\n"

            cur_dtrf = []
            mem_dtrf = []
            ext_info_dtrf = []

            if self.Defaults[dtchex[:4]].datarefs:
                cur_dtrf = [
                    mod_ecu_default.ecu_screen_dataref(
                        0, "\n" + config.LANGUAGE_DICT["300"] + "\n", "Text"
                    )
                ] + self.Defaults[dtchex[:4]].datarefs
            if self.Defaults[dtchex[:4]].memDatarefs:
                mem_dtrf_txt = (
                    config.LANGUAGE_DICT["299"] + " DTC" + config.EXT_CUR_DTC + "\n"
                )
                mem_dtrf = [
                    mod_ecu_default.ecu_screen_dataref(0, mem_dtrf_txt, "Text")
                ] + self.Defaults[dtchex[:4]].memDatarefs
            if self.ext_de:
                ext_info_dtrf = [
                    mod_ecu_default.ecu_screen_dataref(
                        0, "\n" + config.LANGUAGE_DICT["1691"] + "\n", "Text"
                    )
                ] + self.ext_de

            tmp_dtrf = mem_dtrf + cur_dtrf + ext_info_dtrf

            # self.show_datarefs(self.Defaults[dtchex[:4]].datarefs, path)
            self.show_datarefs(tmp_dtrf, path)

    def show_defaults_failflag(self):
        while 1:
            path = "DE (FAILFLAG)"
            mod_utils.clear_screen()
            header = (
                "ECU : " + self.ecudata["ecuname"] + "  " + self.ecudata["doc"] + "\n"
            )
            header = header + "Screen : " + path
            print(pyren_encode(header))

            menu = []

            defstr = {}
            hlpstr = {}

            self.elm.clear_cache()

            dtcs, defstr, hlpstr = mod_ecu_default.get_default_failflag(
                self.Defaults, self.Mnemonics, self.Services, self.elm, self.calc
            )

            for d in sorted(defstr.keys()):
                menu.append(defstr[d])

            menu.append("<Up>")
            menu.append("<Clear>")
            choice = mod_utils.Choice(menu, "Choose one for detailed view or <Clear>:")

            if choice[0] == "<Up>":
                return
            if choice[0] == "<Clear>":
                print("Executing command ", self.resetDTCcommand)
                # header = "ECU : "+self.ecudata['ecuname']+'  '+self.ecudata['doc']+'\n'+ \
                #     "Screen : "+path
                mod_ecu_command.executeCommand(
                    self.Commands[self.resetDTCcommand], self, self.elm, header
                )
                return

            dtchex = dtcs[int(choice[1]) - 1]
            config.EXT_CUR_DTC = dtchex

            path = path + " -> " + defstr[dtchex] + "\n\n" + hlpstr[dtchex] + "\n"

            self.show_datarefs(self.Defaults[dtchex].datarefs, path)

    def show_screens(self):
        self.screens.append(favourite_screen)
        while 1:
            mod_utils.clear_screen()
            header = (
                "ECU : " + self.ecudata["ecuname"] + "  " + self.ecudata["doc"] + "\n"
            )
            print(pyren_encode(header))

            menu = []
            for l in self.screens:
                if l.name == "DE":
                    l.name = "DE : Device errors"
                if l.name == "ID":
                    l.name = "ID : Identifications"
                if l.name == "SY":
                    l.name = "SY : System state"
                if l.name == "LC":
                    l.name = "LC : System configuration"
                if l.name == "SP":
                    l.name = "SP : System parameters"
                if l.name == "AC":
                    l.name = "AC : Executing tests"
                if l.name == "CF":
                    l.name = "CF : Changing configuration"
                if l.name == "VP":
                    l.name = "VP : VIN programming"
                if l.name == "RZ":
                    l.name = "RZ : Resets"
                if l.name == "SC":
                    l.name = "SC : Configuration scenarios"
                if l.name == "SCS":
                    l.name = "SCS : Security configuration scenarios"
                if l.name == "EZ":
                    l.name = "EZ : EZSTEP"
                if l.name == "FAV":
                    l.name = "FAV : Favourite Parameters"
                if l.name == "ED":
                    self.ext_de = l.datarefs
                    l.name = "ED : DE extra information"
                    continue
                menu.append(l.name)
            if config.OPT_CMD:
                menu.append("ECM : Extended command set")
            if self.Parameters:
                menu.append("PRA : Parameters list")
            if self.States:
                menu.append("ETA : States list")
            if self.Identifications:
                menu.append("IDA : Identifications list")
            if self.acf_ready() != "":
                menu.append("ACI : Auto Config Info")
            menu.append("<Up>")
            choice = mod_utils.Choice(menu, "Choose :")
            if choice[0] == "<Up>":
                favourite_screen.datarefs = []
                return

            if choice[0][:2] == "DE":
                if self.ecudata["stdType"] == "STD_A":
                    self.show_defaults_std_a()
                if (
                    self.ecudata["stdType"] == "STD_B"
                    or self.ecudata["stdType"] == "UDS"
                ):
                    self.show_defaults_std_b()
                if self.ecudata["stdType"] == "FAILFLAG":
                    self.show_defaults_failflag()
                continue

            if choice[0][:3] == "ECM":
                scrn = mod_ecu_default.ecu_screen("ECM")
                scrn.datarefs = []
                for cm in sorted(self.Commands):
                    scrn.datarefs.append(
                        mod_ecu_default.ecu_screen_dataref("", cm, "Command")
                    )
                self.show_screen(scrn)
                continue

            if choice[0][:3] == "PRA":
                scrn = mod_ecu_default.ecu_screen("PRA")
                scrn.datarefs = []
                tempDict = {}
                for pr in self.Parameters:
                    if not self.Parameters[pr].agcdRef.endswith("FF"):
                        tempDict[pr] = self.Parameters[pr].codeMR
                sortedParams = sorted(
                    list(tempDict.items()), key=lambda x: int(x[1][2:])
                )
                for pr in sortedParams:
                    if self.Parameters[pr[0]].mnemolist:
                        if self.Mnemonics[
                            self.Parameters[pr[0]].mnemolist[0]
                        ].serviceID:
                            scrn.datarefs.append(
                                mod_ecu_default.ecu_screen_dataref(
                                    "", pr[0], "Parameter"
                                )
                            )
                self.show_screen(scrn)
                continue

            if choice[0][:3] == "ETA":
                scrn = mod_ecu_default.ecu_screen("ETA")
                scrn.datarefs = []
                tempDict = {}
                for st in self.States:
                    if not self.States[st].agcdRef.endswith("FF") and self.States[
                        st
                    ].agcdRef.startswith("ET"):
                        tempDict[st] = self.States[st].codeMR
                sortedStates = sorted(
                    list(tempDict.items()),
                    key=lambda x: [
                        int(t) if t.isdigit() else t.lower()
                        for t in re.split("(\d+)", x[1])
                    ],
                )
                for st in sortedStates:
                    if self.States[st[0]].mnemolist:
                        if self.Mnemonics[self.States[st[0]].mnemolist[0]].serviceID:
                            scrn.datarefs.append(
                                mod_ecu_default.ecu_screen_dataref("", st[0], "State")
                            )
                self.show_screen(scrn)
                continue

            if choice[0][:3] == "IDA":
                scrn = mod_ecu_default.ecu_screen("IDA")
                scrn.datarefs = []
                for idk in sorted(self.Identifications):
                    scrn.datarefs.append(
                        mod_ecu_default.ecu_screen_dataref("", idk, "Identification")
                    )
                self.show_screen(scrn)
                continue

            if choice[0][:3] == "ACI":
                acf_cmd = self.acf_ready()
                mod_ecu_command.executeCommand(
                    self.Commands[acf_cmd], self, self.elm, header
                )
                continue

            fav_sc = self.screens[int(choice[1]) - 1]
            if choice[0][:3] == "FAV":
                for sc in self.screens:
                    if sc.name.startswith("FAV"):
                        fav_sc = sc
                if not favourite_screen.datarefs:
                    if self.load_fav_list():
                        self.show_screen(fav_sc)
                    else:
                        self.add_favourite()
                else:
                    self.show_screen(fav_sc)
            else:
                self.show_screen(fav_sc)

    def getLanguageMap(self):

        map = {}

        for i in sorted(self.Parameters.keys()):

            m = self.Mnemonics[self.Parameters[i].mnemolist[0]]

            label = self.Parameters[i].label

            if "ETAT" in label:
                continue

            if len(self.Parameters[i].mnemolist) != 1:
                continue
            if m.bitsLength == "":
                continue
            if m.startBit == "":
                continue
            if m.startByte == "":
                continue

            key = "%s:%s:%s:%s" % (m.request, m.startByte, m.startBit, m.bitsLength)

            map[key] = label

        for i in sorted(self.States.keys()):

            m = self.Mnemonics[self.States[i].mnemolist[0]]

            label = self.States[i].label

            if "ETAT" in label:
                continue

            if len(self.States[i].mnemolist) != 1:
                continue
            if m.bitsLength == "":
                continue
            if m.startBit == "":
                continue
            if m.startByte == "":
                continue

            bitsLength = m.bitsLength
            startBit = m.startBit

            # experiment
            comp = self.States[i].computation
            if (m.name + "#") in comp:
                comp = comp.split(m.name + "#")[1]
                startBit = 7 - int(comp[0])
                bitsLength = 1

            # if m.littleEndian != '1':
            #  startBit = 7 - int(startBit)

            key = "%s:%s:%s:%s" % (m.request, m.startByte, startBit, bitsLength)

            # debug
            # print key, m.littleEndian, label

            map[key] = label

        return map

    def getDataIds(self, cache, dataids):
        dataIdsList = []
        if self.elm.performanceModeLevel == 1:
            return dataIdsList

        for req in cache:
            if req.startswith("22"):
                if req[2:] in list(dataids.keys()):
                    if req not in self.elm.notSupportedCommands:
                        dataIdsList.append(dataids[req[2:]])

        chunk_size = self.elm.performanceModeLevel
        if dataIdsList:
            # split dataIdsList into chunks based on the performace level
            return [
                dataIdsList[offset : offset + chunk_size]
                for offset in range(0, len(dataIdsList), chunk_size)
            ]

        return dataIdsList


def bukva(bt, l, sign=False):
    S1 = chr((bt - l) % 26 + ord("A"))
    ex = int(bt - l) // 26
    if ex:
        S2 = chr((ex - 1) % 26 + ord("A"))
        S1 = S2 + S1
    if sign:
        S1 = "signed(" + S1 + ")"
    return S1


def gen_equ(m):

    l = len(m.request) // 2 + 1
    sb = int(m.startByte)
    bits = int(m.bitsLength)
    sbit = int(m.startBit)
    bytes = (bits + sbit - 1) // 8 + 1
    rshift = ((bytes + 1) * 8 - (bits + sbit)) % 8
    mask = str(2**bits - 1)

    if m.type.startswith("SNUM"):
        sign = True
    else:
        sign = False

    equ = bukva(sb, l, sign)

    if bytes == 2:
        equ = bukva(sb, l, sign) + "*256+" + bukva(sb + 1, l)
    if bytes == 3:
        equ = (
            bukva(sb, l, sign)
            + "*65536+"
            + bukva(sb + 1, l)
            + "*256+"
            + bukva(sb + 2, l)
        )
    if bytes == 4:
        equ = (
            bukva(sb, l, sign)
            + "*16777216+"
            + bukva(sb + 1, l)
            + "*65536+"
            + bukva(sb + 2, l)
            + "*256+"
            + bukva(sb + 3, l)
        )

    if m.littleEndian == "1":
        if bytes == 2:
            equ = bukva(sb + 1, l, sign) + "*256+" + bukva(sb, l)
        if bytes == 3:
            equ = (
                bukva(sb + 2, l, sign)
                + "*65536+"
                + bukva(sb + 1, l)
                + "*256+"
                + bukva(sb, l)
            )
        if bytes == 4:
            equ = (
                bukva(sb + 3, l, sign)
                + "*16777216+"
                + bukva(sb + 2, l)
                + "*65536+"
                + bukva(sb + 1, l)
                + "*256+"
                + bukva(sb, l)
            )

    if len(equ) > 2:
        if equ[0] == "(" and equ[-1] == ")":
            pass
        else:
            equ = "(" + equ + ")"

    if bits % 8:
        smask = "&" + mask
    else:
        smask = ""

    if bits == 1:
        equ = "{" + equ + ":" + str(rshift) + "}"
    elif rshift == 0:
        equ = equ + smask
    else:
        equ = "(" + equ + ">" + str(rshift) + ")" + smask

    if len(equ) > 2:
        if (equ[0] == "(" and equ[-1] == ")") or (equ[0] == "{" and equ[-1] == "}"):
            pass
        else:
            equ = "(" + equ + ")"

    return equ


def find_real_ecuid(eid):

    fastinit = ""
    slowinit = ""
    protocol = ""
    candst = ""
    startDiagReq = "10C0"

    DOMTree = xml.dom.minidom.parse(
        mod_db_manager.get_file_from_clip("EcuRenault/Uces.xml")
    )
    Ecus = DOMTree.documentElement
    EcuDatas = Ecus.getElementsByTagName("EcuData")

    if EcuDatas:
        for EcuData in EcuDatas:

            name = EcuData.getAttribute("name")

            if name == eid:

                if EcuData.getElementsByTagName("ModelId").item(0).firstChild:
                    eid = (
                        EcuData.getElementsByTagName("ModelId")
                        .item(0)
                        .firstChild.nodeValue
                    )
                else:
                    eid = name

                ecui = EcuData.getElementsByTagName("ECUInformations")
                if ecui:

                    fastinit_tag = ecui.item(0).getElementsByTagName("FastInitAddress")
                    if fastinit_tag:
                        fastinit = fastinit_tag.item(0).getAttribute("value")

                    slowinit_tag = ecui.item(0).getElementsByTagName("SlowInitAddress")
                    if slowinit_tag:
                        slowinit = slowinit_tag.item(0).getAttribute("value")

                    protocol_tag = ecui.item(0).getElementsByTagName("Protocol")
                    if protocol_tag:
                        protocol = protocol_tag.item(0).getAttribute("value")

                    addr = ecui.item(0).getElementsByTagName("Address")
                    if addr:
                        candst = addr.item(0).getAttribute("targetAddress")

                    frms = ecui.item(0).getElementsByTagName("Frames")
                    if frms:
                        StartDiagSession = frms.item(0).getElementsByTagName(
                            "StartDiagSession"
                        )
                        if StartDiagSession:
                            startDiagReq = StartDiagSession.item(0).getAttribute(
                                "request"
                            )
                break

    if len(eid) > 5:
        eid = eid.upper().replace("FG", "")
        eid = eid.upper().replace(".XML", "")

    return eid, fastinit, slowinit, protocol, candst, startDiagReq


def main():
    if len(sys.argv) < 3:
        print("Usage: mod_ecu.py <ID> <language> [torq] [nochk]")
        print("Example:")
        print("   mod_ecu.py 10016 RU ")
        sys.exit(0)

    ecuid = sys.argv[1]
    lanid = sys.argv[2]

    mod_db_manager.find_dbs()

    if len(ecuid) == 5:
        ecuid, fastinit, slowinit, protocol, candst, startDiagReq = find_real_ecuid(
            ecuid
        )
        sys.argv[1] = ecuid

    Defaults = {}
    Parameters = {}
    States = {}
    Identifications = {}
    Commands = {}
    Services = {}
    Mnemonics = {}

    print("Loading language ")
    sys.stdout.flush()
    lang = mod_optfile.optfile("Location/DiagOnCAN_" + lanid + ".bqm", True)
    print("Done")
    sys.stdout.flush()

    fgfile = "EcuRenault/Sessions/FG" + ecuid + ".xml"
    sgfile = "EcuRenault/Sessions/SG" + ecuid + ".xml"

    mdom = xml.dom.minidom.parse(mod_db_manager.get_file_from_clip(fgfile))
    mdoc = mdom.documentElement

    print("Loading optimyzer")
    sys.stdout.flush()
    opt_file = mod_optfile.optfile(sgfile)

    print("Loading defaults")
    df_class = mod_ecu_default.ecu_defaults(Defaults, mdoc, opt_file.dict, lang.dict)
    print("Loading parameters")
    pr_class = mod_ecu_parameter.ecu_parameters(
        Parameters, mdoc, opt_file.dict, lang.dict
    )
    print("Loading states")
    st_class = mod_ecu_state.ecu_states(States, mdoc, opt_file.dict, lang.dict)
    print("Loading identifications")
    id_class = mod_ecu_identification.ecu_identifications(
        Identifications, mdoc, opt_file.dict, lang.dict
    )
    print("Loading commands")
    cm_class = mod_ecu_command.ecu_commands(Commands, mdoc, opt_file.dict, lang.dict)
    print("Loading mnemonics")
    mm_class = mod_ecu_default.ecu_mnemonics(Mnemonics, mdoc, opt_file.dict, lang.dict)

    if len(sys.argv) == 3:
        print()
        print("Defaults")
        print()
        for i in sorted(Defaults.keys()):
            print(pyren_encode(Defaults[i].name + "[" + i + "] " + Defaults[i].label))

        print()
        print("Parameters")
        print()
        for i in sorted(Parameters.keys()):
            print(
                pyren_encode(
                    Parameters[i].codeMR + "[" + i + "] " + Parameters[i].label
                )
            )

        print()
        print("States")
        print()
        for i in sorted(States.keys()):
            print(pyren_encode(States[i].codeMR + "[" + i + "] " + States[i].label))

        print()
        print("Identifications")
        print()
        for i in sorted(Identifications.keys()):
            print(
                pyren_encode(
                    Identifications[i].codeMR
                    + "["
                    + i
                    + "] "
                    + Identifications[i].label
                )
            )

        print()
        print("Commands")
        print()
        for i in sorted(Commands.keys()):
            print(pyren_encode(Commands[i].codeMR + "[" + i + "] " + Commands[i].label))

        sys.exit(0)

    if len(sys.argv) > 3 and sys.argv[3].upper() != "TORQ":
        sys.exit(0)

    family = sys.argv[1][:2]
    eindex = sys.argv[1][2:]
    if len(candst) > 1:
        sss = SNAT[F2A[family]]
        ddd = DNAT[F2A[family]]
        filename = "PR_" + ddd + "_" + sss + "_" + eindex + "_" + sys.argv[2] + ".csv"
    else:
        sss = "82" + F2A[family] + "F1"
        ddd = "82" + F2A[family] + "F1"
        filename = "PR_" + F2A[family] + "_" + eindex + "_" + sys.argv[2] + ".csv"

    ext_path = "/storage/emulated/0/.torque/extendedpids/"
    if config.OS == "android":
        if not os.path.exists(ext_path):
            os.makedirs(ext_path, exist_ok=True)
        filename = ext_path + filename

    cf = open(filename, "w")

    line = "%s,%s,%s,%s,%s,%s,%s,%s\n" % (
        "name",
        "ShortName",
        "ModeAndPID",
        "Equation",
        "Min Value",
        "Max Value",
        "Units",
        "Header",
    )
    cf.write(line)

    memIt = []
    for i in sorted(Parameters.keys()):

        if Parameters[i].codeMR in memIt:
            continue
        else:
            memIt.append(Parameters[i].codeMR)

        m = Parameters[i].mnemolist[0]

        if len(Parameters[i].mnemolist) != 1:
            continue
        if "?" in Parameters[i].computation:
            if len(sys.argv) == 5 and sys.argv[4].upper() == "NOCHK":
                pass
            else:
                continue
        if Mnemonics[m].bitsLength == "":
            continue
        if Mnemonics[m].startBit == "":
            continue
        if Mnemonics[m].startByte == "":
            continue

        equ = gen_equ(Mnemonics[m])

        c_name = Parameters[i].label.replace(",", ".")
        c_short = Parameters[i].codeMR
        c_pid = Mnemonics[m].request
        c_equ = Parameters[i].computation.replace(m, equ)
        c_min = Parameters[i].min
        c_max = Parameters[i].max
        c_unit = Parameters[i].unit

        line = '"PR_%s","%s","%s","%s","%s","%s","%s","%s"\n' % (
            c_name,
            c_short,
            c_pid,
            c_equ,
            c_min,
            c_max,
            c_unit,
            ddd,
        )
        cf.write(line)

    memIt = []
    for i in sorted(States.keys()):

        if States[i].codeMR in memIt:
            continue
        else:
            memIt.append(States[i].codeMR)

        m = States[i].mnemolist[0]

        if len(States[i].mnemolist) != 1:
            continue
        if Mnemonics[m].bitsLength == "":
            continue
        if Mnemonics[m].startBit == "":
            continue
        if Mnemonics[m].startByte == "":
            continue

        equ = gen_equ(Mnemonics[m])

        c_name = States[i].label.replace(",", ".")
        c_short = States[i].codeMR
        c_pid = Mnemonics[m].request
        if len(sys.argv) == 5 and sys.argv[4].upper() == "NOCHK":
            c_equ = States[i].computation.replace(m, equ)
        else:
            c_equ = equ
        c_min = "0"
        c_max = "0"
        c_unit = ""

        line = '"ST_%s","%s","%s","%s","%s","%s","%s","%s"\n' % (
            c_name,
            c_short,
            c_pid,
            c_equ,
            c_min,
            c_max,
            c_unit,
            ddd,
        )
        cf.write(line)

    cf.close()

    print()
    print("File:", filename, "created")
    print()

    # fastinit, slowinit, protocol, candst
    can250init = (
        "ATAL\\nATSH"
        + ddd
        + "\\nATCRA"
        + sss
        + "\\nATFCSH"
        + ddd
        + "\\nATFCSD300000\\nATFCSM1\\nATSP8\\n"
        + startDiagReq
    )
    can500init = (
        "ATAL\\nATSH"
        + ddd
        + "\\nATCRA"
        + sss
        + "\\nATFCSH"
        + ddd
        + "\\nATFCSD300000\\nATFCSM1\\nATSP6\\n"
        + startDiagReq
    )
    slow05init = (
        "ATSH81" + F2A[family] + "F1\\nATSW96\\nATIB10\\nATSP4\\nATSI\\n" + startDiagReq
    )
    fast10init = (
        "ATSH81" + F2A[family] + "F1\\nATSW96\\nATIB10\\nATSP5\\nATFI\\n" + startDiagReq
    )

    if len(candst) > 1:
        print("Init string for CAN 500:")
        print(can500init)
        print()
        print("Init string for CAN 250:")
        print(can250init)
        print()
    if len(fastinit) > 1:
        print("Init string for Engine K-line (FAST INIT):")
        print(fast10init)
        print()
    if len(slowinit) > 1:
        print("Init string for Engine K-line (SLOW INIT):")
        print(slow05init)
        print()

    # make profile for torque
    profilename = str(int(time.time())) + ".tdv"
    veh_path = "/storage/emulated/0/.torque/vehicles/"
    if config.OS == "android":
        if not os.path.exists(veh_path):
            os.makedirs(veh_path, exist_ok=True)
        profilename = veh_path + str(int(time.time())) + ".tdv"

    prn = open(profilename, "w")
    prn.write("#This is an ECU profile generated by pyren\n")
    prn.write("fuelType=0\n")
    prn.write("obdAdjustNew=1.0\n")
    prn.write("lastMPG=0.0\n")
    prn.write("tankCapacity=295.5\n")
    prn.write("volumetricEfficiency=85.0\n")
    prn.write("weight=1400.0\n")
    prn.write("odoMeter=0.0\n")
    prn.write("adapterName=OBDII [00\:00\:00\:00\:00\:0]\n")
    prn.write("adapter=00\:00\:00\:00\:00\:00\n")
    prn.write("boostAdjust=0.0\n")
    prn.write("mpgAdjust=1.0\n")
    prn.write("fuelCost=0.18000000715255737\n")
    prn.write("ownProfile=false\n")
    prn.write("displacement=1.6\n")
    prn.write("tankUsed=147.75\n")
    prn.write("lastMPGCount=0\n")
    prn.write("maxRpm=7000\n")
    prn.write("fuelDistance=0.0\n")
    prn.write("fuelUsed=0.0\n")
    prn.write("alternateHeader=true\n")
    prn.write(("name=PR_" + ecuid + "\n"))
    if len(candst) > 1:
        prn.write(("customInit=" + can500init.replace("\\", "\\\\") + "\n"))
        prn.write("preferredProtocol=7\n")
    elif len(fastinit) > 1:
        prn.write(("customInit=" + fast10init.replace("\\", "\\\\") + "\n"))
        prn.write("preferredProtocol=6\n")
    else:
        prn.write(("customInit=" + slow05init.replace("\\", "\\\\") + "\n"))
        prn.write("preferredProtocol=5\n")
    prn.close()

    print()
    print("Torque profile:", profilename, "created")
    print()


if __name__ == "__main__":
    main()
