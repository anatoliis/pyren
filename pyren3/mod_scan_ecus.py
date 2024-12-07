#!/usr/bin/env python3
# allecus contains such dictionaries
#
# 'dst': '7A'
# 'src': 'F1'
# 'OptimizerId': 'SG0110577.XML'
# 'ModelId': 'FG0110577.XML'}
# 'stdType': 'STD_A'
# 'doc': 'DCM1.2_L4DB_58_ X61_A'
# 'idf': '1'
# 'pin': 'can'
# 'pin1': '6'
# 'pin2': '14'
# 'startDiagReq': '10C0'
# 'startDiagRsp': '50C0'
# 'stopDiagReq': '1081'
# 'stopDiagRsp': '5081'
# 'ids': ['2180','6180','0','6','FF','58','2180','6180','0','16','FF','4D']

import os
import pickle
import string
import sys
import xml.dom.minidom

import config
import mod_db_manager
import mod_elm
from mod_utils import Choice, choice_long, debug, pyren_encode

opt_demo = False

FAMILIES = {
    "1": "13712",
    "2": "13002",
    "3": "13010",
    "4": "13713",
    "5": "13016",
    "6": "13715",
    "7": "60761",
    "8": "13004",
    "9": "13012",
    "10": "13718",
    "11": "13719",
    "12": "13003",
    "13": "19763",
    "14": "13722",
    "15": "17782",
    "16": "7301",
    "17": "58508",
    "18": "13005",
    "19": "55948",
    "20": "13727",
    "21": "13920",
    "22": "23586",
    "23": "7305",
    "24": "51605",
    "25": "15664",
    "26": "15666",
    "27": "18638",
    "28": "15665",
    "29": "19606",
    "30": "61183",
    "31": "58925",
    "32": "58926",
    "33": "24282",
    "34": "60773",
    "35": "60777",
    "36": "60778",
    "37": "61750",
    "38": "53126",
    "39": "61751",
    "40": "8711",
    "41": "24353",
    "42": "61293",
    "43": "5773",
    "44": "63135",
    "45": "C3P_73545",
    "46": "61883",
    "47": "58943",
    "48": "61882",
    "49": "62658",
    "50": "13009",
    "51": "30504",
    "52": "13019",
    "53": "31980",
    "54": "31981",
    "55": "13922",
    "56": "13921",
    "57": "62659",
    "58": "62660",
    "59": "62661",
    "60": "11331",
    "61": "11332",
    "62": "9446",
    "63": "55050",
    "64": "62720",
    "65": "29705",
    "66": "29706",
    "67": "62721",
    "68": "62722",
    "69": "62723",
    "70": "57741",
    "72": "8992",
    "73": "61294",
    "74": "62724",
    "76": "11297",
    "77": "56580",
    "78": "61295",
    "79": "60146",
    "80": "51172",
    "81": "51173",
    "86": "57713",
    "87": "60779",
    "88": "63847",
    "89": "63848",
    "90": "4672",
    "91": "51666",
    "92": "53725",
    "93": "55049",
    "94": "56538",
    "95": "56539",
    "96": "56540",
    "97": "56562",
    "98": "57970",
    "99": "58003",
}


class ScanEcus:
    """List all possible ECUs of this car"""

    all_ecus = {}  # all ecus possible in this model
    id_tx_t = {}  # table of transmit addresses
    id_rx_t = {}  # table of receive addresses
    detected_ecus = []  # ecus detected in car during scan
    vehicle_classes = []
    ecus = []
    models = []
    reqres = []  # results of previous requests
    selected_ecu = 0
    veh_type_code = ""

    def __init__(self, elm_ref):
        self.elm = elm_ref

        ####### Get list car models from vehicles directory #######
        self.vehicle_classes = []

        file_list = mod_db_manager.get_file_list_from_clip("Vehicles/TCOM_*.[Xx]ml")
        for file in file_list:
            try:
                model_n = file[-7:-4]
                if model_n in [
                    "005",
                    "010",
                    "026",
                    "035",
                    "054",
                    "064",
                    "066",
                    "069",
                    "088",
                    "107",
                    "110",
                    "114",
                ]:
                    continue
                # model_n = int(file[-7:-4])
                # if model_n<86: continue
            except ValueError:
                pass

            xmlf = mod_db_manager.get_file_from_clip(file)

            dom_tree = xml.dom.minidom.parse(mod_db_manager.get_file_from_clip(file))
            vh = dom_tree.documentElement
            if vh.hasAttribute("defaultText"):
                vehicle_name = vh.getAttribute("defaultText").strip()
                veh_type_code = vh.getAttribute("vehTypeCode").strip()
                veh_tcom = int(vh.getAttribute("TCOM"))
                veh_index_topo = int(vh.getAttribute("indexTopo"))
                self.vehicle_classes.append(
                    [vehicle_name, file, veh_type_code, veh_tcom, veh_index_topo]
                )

    def scan_all_ecus(self):
        """scan all ecus. If savedEcus.p exists then load it and return"""

        saved_ecus_file_name = "savedEcus.p"
        if config.OPT_CAN2:
            saved_ecus_file_name = "savedEcus2.p"

        # check if savedEcus exists
        if os.path.isfile(saved_ecus_file_name) and not config.OPT_SCAN:
            # load it
            self.detected_ecus = pickle.load(open(saved_ecus_file_name, "rb"))

            # debug
            # check vehTypeCode
            if len(self.detected_ecus) > 0 and "vehTypeCode" not in list(
                self.detected_ecus[0].keys()
            ):
                self.veh_type_code = input("Enter vehTypeCode:")
                # renew savedEcus
                self.all_ecus = {}
                for detected_ecu in self.detected_ecus:
                    detected_ecu["vehTypeCode"] = self.veh_type_code
                    self.all_ecus[detected_ecu["ecuname"]] = detected_ecu
                self.detected_ecus = []
                for ecu_ in list(self.all_ecus.keys()):
                    self.detected_ecus.append(self.all_ecus[ecu_])
                # sort list of detected ECUs
                self.detected_ecus = sorted(
                    self.detected_ecus, key=lambda k: int(k["idf"])
                )
                # save a renewed version
                if len(self.detected_ecus):
                    pickle.dump(self.detected_ecus, open(saved_ecus_file_name, "wb"))

            # check if savedEcus has an old version
            if len(self.detected_ecus) > 0 and "idTx" not in list(
                self.detected_ecus[0].keys()
            ):
                # renew savedEcus
                self.all_ecus = {}
                for i in self.detected_ecus:
                    self.all_ecus[i["ecuname"]] = i
                self.read_uces_file()
                self.detected_ecus = []
                for i in list(self.all_ecus.keys()):
                    self.detected_ecus.append(self.all_ecus[i])
                # sort list of detected ECUs
                self.detected_ecus = sorted(
                    self.detected_ecus, key=lambda k: int(k["idf"])
                )
                # save a renewed version
                if len(self.detected_ecus):
                    pickle.dump(self.detected_ecus, open(saved_ecus_file_name, "wb"))
            return
        else:
            config.OPT_SCAN = True

        config.STATE_SCAN = True

        self.reqres = []
        self.errres = []

        i = 0
        print(
            "\r"
            + "\t\t\t\t"
            + "\rScanning:"
            + str(i)
            + "/"
            + str(len(self.all_ecus))
            + " Detected: "
            + str(len(self.detected_ecus)),
            end=" ",
        )
        sys.stdout.flush()

        # scan CAN ecus

        can_high = "6"
        can_low = "14"
        if config.OPT_CAN2:
            can_high = "13"
            can_low = "12"

        self.elm.init_can()
        for ecu, row in sorted(
            iter(self.all_ecus.items()),
            key=lambda x_y1: x_y1[1]["idf"]
            + x_y1[1]["protocol"]
            + str(1 / float(len(x_y1[1]["ids"]))),
        ):
            if (
                self.all_ecus[ecu]["pin"] == "can"
                and self.all_ecus[ecu]["pin1"] == can_high
                and self.all_ecus[ecu]["pin2"] == can_low
            ):
                i = i + 1
                print(
                    "\r"
                    + "\t\t\t\t"
                    + "\rScanning:"
                    + str(i)
                    + "/"
                    + str(len(self.all_ecus))
                    + " Detected: "
                    + str(len(self.detected_ecus)),
                    end=" ",
                )
                sys.stdout.flush()

                self.elm.set_can_addr(self.all_ecus[ecu]["dst"], self.all_ecus[ecu])
                self.scan_can(self.all_ecus[ecu])

        self.elm.close_protocol()

        # scan KWP ecus
        if not config.OPT_CAN2:
            self.elm.init_iso()  # actually it executed every time the address is changed
            for ecu, row in sorted(
                iter(self.all_ecus.items()),
                key=lambda x_y: x_y[1]["idf"] + x_y[1]["protocol"],
            ):
                if (
                    self.all_ecus[ecu]["pin"] == "iso"
                    and self.all_ecus[ecu]["pin1"] == "7"
                    and self.all_ecus[ecu]["pin2"] == "15"
                ):

                    i = i + 1
                    print(
                        "\r"
                        + "\t\t\t\t"
                        + "\rScanning:"
                        + str(i)
                        + "/"
                        + str(len(self.all_ecus))
                        + " Detected: "
                        + str(len(self.detected_ecus)),
                        end=" ",
                    )
                    sys.stdout.flush()

                    self.elm.set_iso_addr(self.all_ecus[ecu]["dst"], self.all_ecus[ecu])
                    self.scan_iso(self.all_ecus[ecu])

        print(
            "\r"
            + "\t\t\t\t"
            + "\rScanning:"
            + str(i)
            + "/"
            + str(len(self.all_ecus))
            + " Detected: "
            + str(len(self.detected_ecus))
        )

        config.STATE_SCAN = False

        # sort list of detected ECUs
        self.detected_ecus = sorted(self.detected_ecus, key=lambda k: int(k["idf"]))
        if len(self.detected_ecus):
            pickle.dump(self.detected_ecus, open(saved_ecus_file_name, "wb"))
        # print self.detectedEcus

    def re_scan_errors(self):
        """scan only detectedEcus for re-check errors"""

        config.OPT_SCAN = True

        self.reqres = []
        self.errres = []

        i = 0
        print(
            "\r"
            + "\t\t\t\t"
            + "\rScanning:"
            + str(i)
            + "/"
            + str(len(self.detected_ecus)),
            end=" ",
        )
        sys.stdout.flush()

        # scan CAN ecus
        can_high = "6"
        can_low = "14"
        if config.OPT_CAN2:
            can_high = "13"
            can_low = "12"

        self.elm.init_can()
        for row in sorted(self.detected_ecus, key=lambda k: int(k["idf"])):
            if (
                row["pin"] == "can"
                and row["pin1"] == can_high
                and row["pin2"] == can_low
            ):

                i = i + 1
                print(
                    "\r"
                    + "\t\t\t\t"
                    + "\rScanning:"
                    + str(i)
                    + "/"
                    + str(len(self.detected_ecus)),
                    end=" ",
                )
                sys.stdout.flush()

                self.elm.set_can_addr(row["dst"], row)
                self.scan_can(row)

        self.elm.close_protocol()

        # scan KWP ecud
        if not config.OPT_CAN2:
            self.elm.init_iso()
            for row in sorted(self.detected_ecus, key=lambda k: int(k["idf"])):
                if row["pin"] == "iso" and row["pin1"] == "7" and row["pin2"] == "15":

                    i = i + 1
                    print(
                        "\r"
                        + "\t\t\t\t"
                        + "\rScanning:"
                        + str(i)
                        + "/"
                        + str(len(self.detected_ecus)),
                        end=" ",
                    )
                    sys.stdout.flush()

                    self.elm.set_iso_addr(row["dst"], row)
                    self.scan_iso(row)

        print(
            "\r"
            + "\t\t\t\t"
            + "\rScanning:"
            + str(i)
            + "/"
            + str(len(self.detected_ecus))
        )

        # sort list of detected ECUs
        self.detected_ecus = sorted(self.detected_ecus, key=lambda k: int(k["idf"]))

    def select_ecu(self, ecu_id):
        if len(self.detected_ecus) == 0:
            self.scan_all_ecus()

        if len(self.detected_ecus) == 0:
            print("NO ECU detected. Nothing to do. (((")
            exit(2)

        if len(ecu_id) > 4:
            i = 0
            for row in self.detected_ecus:
                if ecu_id in row["ecuname"]:
                    self.selected_ecu = i
                    return self.detected_ecus[self.selected_ecu]
                i = i + 1

        list_ecus = []

        if config.OPT_SCAN:
            print(
                pyren_encode(
                    "\n     %-7s %-6s %-5s %-40s %s"
                    % ("Addr", "Family", "Index", "Name", "Warn")
                )
            )
        else:
            print(
                pyren_encode(
                    "\n     %-7s %-6s %-5s %-40s %s"
                    % ("Addr", "Family", "Index", "Name", "Type")
                )
            )

        for row in self.detected_ecus:
            if "idf" not in list(row.keys()):
                row["idf"] = ""
            if row["dst"] not in list(mod_elm.DNAT.keys()):
                mod_elm.DNAT[row["dst"]] = "000"
                mod_elm.SNAT[row["dst"]] = "000"
            if row["idf"] in list(FAMILIES.keys()) and FAMILIES[row["idf"]] in list(
                config.LANGUAGE_DICT.keys()
            ):
                fmlyn = config.LANGUAGE_DICT[FAMILIES[row["idf"]]]
                if config.OPT_SCAN:
                    line = "%-2s(%3s) %-6s %-5s %-40s %s" % (
                        row["dst"],
                        mod_elm.DNAT[row["dst"]],
                        row["idf"],
                        row["ecuname"],
                        fmlyn,
                        row["rerr"],
                    )
                else:
                    line = "%-2s(%3s) %-6s %-5s %-40s %s" % (
                        row["dst"],
                        mod_elm.DNAT[row["dst"]],
                        row["idf"],
                        row["ecuname"],
                        fmlyn,
                        row["stdType"],
                    )
            else:
                if config.OPT_SCAN:
                    line = "%-2s(%3s) %-6s %-5s %-40s %s" % (
                        row["dst"],
                        mod_elm.DNAT[row["dst"]],
                        row["idf"],
                        row["ecuname"],
                        row["doc"].strip(),
                        row["rerr"],
                    )
                else:
                    line = "%-2s(%3s) %-6s %-5s %-40s %s" % (
                        row["dst"],
                        mod_elm.DNAT[row["dst"]],
                        row["idf"],
                        row["ecuname"],
                        row["doc"].strip(),
                        row["stdType"],
                    )
            list_ecus.append(line)

        list_ecus.append("Rescan errors")
        list_ecus.append("<Exit>")
        choice = Choice(list_ecus, "Choose ECU :")

        if choice[0] == "Rescan errors":
            self.re_scan_errors()
            return -1

        if choice[0].lower() == "<exit>":
            exit()

        i = int(choice[1]) - 1
        self.selected_ecu = i
        return self.detected_ecus[self.selected_ecu]

    def get_selected_ecu(self):
        return self.detected_ecus[self.selected_ecu]

    def load_model_ecus(self, file):
        # loading name list of all possible ECUs

        dom_tree = xml.dom.minidom.parse(mod_db_manager.get_file_from_clip(file))
        vh = dom_tree.documentElement

        if vh.hasAttribute("vehTypeCode"):
            self.veh_type_code = vh.getAttribute("vehTypeCode")

        connector = vh.getElementsByTagName("Connector")
        can_network = connector.item(0).getElementsByTagName("CANNetwork")
        iso_network = connector.item(0).getElementsByTagName("ISONetwork")

        for pin in can_network:
            can_high = pin.getAttribute("canH")
            can_low = pin.getAttribute("canL")

            can_ids = pin.getElementsByTagName("CanId")
            if can_ids:
                for can_id in can_ids:
                    target_address = can_id.getAttribute("targetAddress").strip()
                    id_tx = can_id.getAttribute("idTx").strip()
                    if len(id_tx) == 4:
                        id_tx = id_tx[1:]
                    id_rx = can_id.getAttribute("idRx").strip()
                    if len(id_rx) == 4:
                        id_rx = id_rx[1:]
                    self.id_tx_t[target_address] = id_tx
                    self.id_rx_t[target_address] = id_rx

            brp = ""
            can_network_params = pin.getElementsByTagName("CANNetworkParams")
            if can_network_params:
                for can_network_param in can_network_params:
                    brp += can_network_param.getAttribute("brp").strip()

            ecu_list = pin.getElementsByTagName("EcuList")
            if ecu_list:
                ecu_kinds = ecu_list.item(0).getElementsByTagName("EcuKind")
                for ecu_kind in ecu_kinds:
                    id_family = ecu_kind.getAttribute("idFamily")
                    ecu_ref = ecu_kind.getElementsByTagName("EcuRef")
                    for er in ecu_ref:
                        ecu_name = er.getAttribute("name").strip()
                        ecu_doc = er.getAttribute("doc").strip()
                        self.all_ecus[ecu_name] = {}
                        self.all_ecus[ecu_name]["pin"] = "can"
                        self.all_ecus[ecu_name]["pin1"] = can_high
                        self.all_ecus[ecu_name]["pin2"] = can_low
                        self.all_ecus[ecu_name]["idf"] = id_family
                        self.all_ecus[ecu_name]["doc"] = ecu_doc
                        self.all_ecus[ecu_name]["ecuname"] = ecu_name
                        self.all_ecus[ecu_name]["brp"] = brp
                        self.all_ecus[ecu_name]["vehTypeCode"] = self.veh_type_code

        for pin in iso_network:
            pin_k = pin.getAttribute("pinK")
            pin_l = pin.getAttribute("pinL")
            ecu_list = pin.getElementsByTagName("EcuList")
            if ecu_list:
                ecu_kinds = ecu_list.item(0).getElementsByTagName("EcuKind")
                for ecu_kind in ecu_kinds:
                    id_family = ecu_kind.getAttribute("idFamily")
                    ecu_ref = ecu_kind.getElementsByTagName("EcuRef")
                    for er in ecu_ref:
                        ecu_name = er.getAttribute("name").strip()
                        ecu_doc = er.getAttribute("doc").strip()
                        self.all_ecus[ecu_name] = {}
                        self.all_ecus[ecu_name]["pin"] = "iso"
                        self.all_ecus[ecu_name]["pin1"] = pin_k
                        self.all_ecus[ecu_name]["pin2"] = pin_l
                        self.all_ecus[ecu_name]["idf"] = id_family
                        self.all_ecus[ecu_name]["doc"] = ecu_doc
                        self.all_ecus[ecu_name]["ecuname"] = ecu_name
                        self.all_ecus[ecu_name]["vehTypeCode"] = self.veh_type_code

        self.read_uces_file()

    def read_uces_file(self, read_all: bool = False):
        # Finding them in Uces.xml and loading
        dom_tree = xml.dom.minidom.parse(
            mod_db_manager.get_file_from_clip("EcuRenault/Uces.xml")
        )
        ecus = dom_tree.documentElement
        ecu_datas = ecus.getElementsByTagName("EcuData")
        if ecu_datas:
            for ecu_data in ecu_datas:
                name = ecu_data.getAttribute("name")
                if name in list(self.all_ecus.keys()) or read_all:
                    if read_all:
                        self.all_ecus[name] = {}
                        self.all_ecus[name]["doc"] = ""

                    self.all_ecus[name]["stdType"] = ecu_data.getAttribute("stdType")

                    if ecu_data.getElementsByTagName("ModelId").item(0).firstChild:
                        self.all_ecus[name]["ModelId"] = (
                            ecu_data.getElementsByTagName("ModelId")
                            .item(0)
                            .firstChild.nodeValue.strip()
                        )
                    else:
                        self.all_ecus[name]["ModelId"] = name

                    if ecu_data.getElementsByTagName("OptimizerId").item(0).firstChild:
                        self.all_ecus[name]["OptimizerId"] = (
                            ecu_data.getElementsByTagName("OptimizerId")
                            .item(0)
                            .firstChild.nodeValue.strip()
                        )
                    else:
                        self.all_ecus[name]["OptimizerId"] = ""

                    if self.all_ecus[name]["doc"] == "":
                        self.all_ecus[name]["doc"] = self.all_ecus[name]["ModelId"]

                    ecu_info = ecu_data.getElementsByTagName("ECUInformations")
                    if ecu_info:
                        can_dst = ""
                        src = "F1"

                        fast_init = ""
                        fast_init_tag = ecu_info.item(0).getElementsByTagName(
                            "FastInitAddress"
                        )
                        if fast_init_tag:
                            fast_init = fast_init_tag.item(0).getAttribute("value")
                        self.all_ecus[name]["fastInit"] = fast_init

                        slowinit = ""
                        slowinit_tag = ecu_info.item(0).getElementsByTagName(
                            "SlowInitAddress"
                        )
                        if slowinit_tag:
                            slowinit = slowinit_tag.item(0).getAttribute("value")
                        self.all_ecus[name]["slowInit"] = slowinit

                        error_delay = ""
                        error_delay_tag = ecu_info.item(0).getElementsByTagName(
                            "ErrorDelay"
                        )
                        if error_delay_tag:
                            error_delay = error_delay_tag.item(0).getAttribute("value")
                        self.all_ecus[name]["errorDelay"] = error_delay

                        replay_to_request_delay = ""
                        replay_to_request_delay_tag = ecu_info.item(
                            0
                        ).getElementsByTagName("ReplyToRequestDelay")
                        if replay_to_request_delay_tag:
                            replay_to_request_delay = replay_to_request_delay_tag.item(
                                0
                            ).getAttribute("value")
                        self.all_ecus[name][
                            "replyToRequestDelay"
                        ] = replay_to_request_delay

                        commretry = ""
                        commretry_tag = ecu_info.item(0).getElementsByTagName(
                            "CommRetry"
                        )
                        if commretry_tag:
                            commretry = commretry_tag.item(0).getAttribute("value")
                        self.all_ecus[name]["commRetry"] = commretry

                        programmable = ""
                        programmable_tag = ecu_info.item(0).getElementsByTagName(
                            "Programmable"
                        )
                        if programmable_tag:
                            programmable = programmable_tag.item(0).getAttribute(
                                "value"
                            )
                        self.all_ecus[name]["programmable"] = programmable

                        baudrate = ""
                        baudrate_tag = ecu_info.item(0).getElementsByTagName("BaudRate")
                        if baudrate_tag:
                            baudrate = baudrate_tag.item(0).getAttribute("value")
                        self.all_ecus[name]["baudRate"] = baudrate

                        kw1 = ""
                        kw1_tag = ecu_info.item(0).getElementsByTagName("KW1")
                        if kw1_tag:
                            kw1 = kw1_tag.item(0).getAttribute("value")
                        self.all_ecus[name]["KW1"] = kw1

                        kw2 = ""
                        kw2_tag = ecu_info.item(0).getElementsByTagName("KW2")
                        if kw2_tag:
                            kw2 = kw2_tag.item(0).getAttribute("value")
                        self.all_ecus[name]["KW2"] = kw2

                        timings = ""
                        timings_tag = ecu_info.item(0).getElementsByTagName("Timings")
                        if timings_tag:
                            timings = timings_tag.item(0).getAttribute("value")
                        self.all_ecus[name]["timings"] = timings

                        protocol = ""
                        protocol_tag = ecu_info.item(0).getElementsByTagName("Protocol")
                        if protocol_tag:
                            protocol = protocol_tag.item(0).getAttribute("value")
                        self.all_ecus[name]["protocol"] = protocol

                        canconfig = ""
                        canconfig_tag = ecu_info.item(0).getElementsByTagName(
                            "CANConfig"
                        )
                        if canconfig_tag:
                            canconfig = canconfig_tag.item(0).getAttribute("value")
                        self.all_ecus[name]["CANConfig"] = canconfig

                        addr = ecu_info.item(0).getElementsByTagName("Address")
                        if addr:
                            can_dst = addr.item(0).getAttribute("targetAddress")
                            src = addr.item(0).getAttribute("toolAddress")

                        if can_dst in list(self.id_tx_t.keys()):
                            self.all_ecus[name]["idTx"] = self.id_tx_t[can_dst]
                        else:
                            self.all_ecus[name]["idTx"] = ""

                        if can_dst in list(self.id_rx_t.keys()):
                            self.all_ecus[name]["idRx"] = self.id_rx_t[can_dst]
                        else:
                            self.all_ecus[name]["idRx"] = ""

                        self.all_ecus[name]["src"] = src
                        if len(can_dst) > 0:
                            self.all_ecus[name]["dst"] = can_dst
                        else:
                            if len(fast_init) > 0:
                                self.all_ecus[name]["dst"] = fast_init
                            else:
                                self.all_ecus[name]["dst"] = ""

                        frms = ecu_info.item(0).getElementsByTagName("Frames")
                        if frms:
                            StartDiagSession = frms.item(0).getElementsByTagName(
                                "StartDiagSession"
                            )
                            if StartDiagSession:
                                self.all_ecus[name]["startDiagReq"] = (
                                    StartDiagSession.item(0).getAttribute("request")
                                )
                                self.all_ecus[name]["startDiagRsp"] = (
                                    StartDiagSession.item(0).getAttribute("response")
                                )
                            else:
                                self.all_ecus[name]["startDiagReq"] = ""
                                self.all_ecus[name]["startDiagRsp"] = ""
                            StopDiagSession = frms.item(0).getElementsByTagName(
                                "StopDiagSession"
                            )
                            if StopDiagSession:
                                self.all_ecus[name]["stopDiagReq"] = (
                                    StopDiagSession.item(0).getAttribute("request")
                                )
                                self.all_ecus[name]["stopDiagRsp"] = (
                                    StopDiagSession.item(0).getAttribute("response")
                                )
                            else:
                                self.all_ecus[name]["stopDiagReq"] = ""
                                self.all_ecus[name]["stopDiagRsp"] = ""
                            KeepAlive = frms.item(0).getElementsByTagName("KeepAlive")
                            if KeepAlive:
                                self.all_ecus[name]["keepAliveReq"] = KeepAlive.item(
                                    0
                                ).getAttribute("request")
                                self.all_ecus[name]["KeepAlivePeriod"] = KeepAlive.item(
                                    0
                                ).getAttribute("period")
                            else:
                                self.all_ecus[name]["keepAliveReq"] = ""
                                self.all_ecus[name]["KeepAlivePeriod"] = ""
                        else:
                            self.all_ecus[name]["startDiagReq"] = ""
                            self.all_ecus[name]["startDiagRsp"] = ""
                            self.all_ecus[name]["stopDiagReq"] = ""
                            self.all_ecus[name]["stopDiagRsp"] = ""
                            self.all_ecus[name]["keepAliveReq"] = ""
                            self.all_ecus[name]["KeepAlivePeriod"] = ""

                        idtt = []
                        ids = ecu_info.item(0).getElementsByTagName("Ids")
                        if ids:
                            for id in ids:
                                IdFrame = id.getElementsByTagName("IdFrame")
                                if IdFrame:
                                    idreq = IdFrame.item(0).getAttribute("request")
                                    idrsp = IdFrame.item(0).getAttribute("response")
                                    idlen = IdFrame.item(0).getAttribute("length")
                                idbytes = id.getElementsByTagName("IdByte")
                                if idbytes:
                                    for idb in idbytes:
                                        idrank = idb.getAttribute("rank")
                                        idmask = idb.getAttribute("mask")
                                        idval = idb.getAttribute("value")
                                        idtt.append(idreq)
                                        idtt.append(idrsp)
                                        idtt.append(idlen)
                                        idtt.append(idrank)
                                        idtt.append(idmask)
                                        idtt.append(idval)
                        self.all_ecus[name]["ids"] = idtt

    def choose_model(self, num):
        order_by = 0  # 0 = vehiclename
        # 1 = file
        # 2 = vehTypeCode
        # 3 = vehTCOM
        # 4 = vehindexTopo

        for row in sorted(self.vehicle_classes, key=lambda k: k[order_by]):
            self.models.append(row[2] + " " + row[0])

        if num == 0 or num > len(self.models):
            ch = choice_long(self.models, "Choose model :")
        else:
            ch = [self.models[num - 1], num]

        choice = sorted(self.vehicle_classes, key=lambda k: k[order_by])[int(ch[1]) - 1]

        model = choice[0]
        tcom_file_name = choice[1]

        print("Loading data for :", model, tcom_file_name, end=" ")
        sys.stdout.flush()

        self.all_ecus = {}

        if self.elm.lf != 0:
            self.elm.lf.write("#load: " + model + " " + tcom_file_name + "\n")
            self.elm.lf.flush()

        # self.load_model_ECUs( "../Vehicles/"+tcomfilename )
        self.load_model_ecus(tcom_file_name)
        print("  - " + str(len(self.all_ecus)) + " ecus loaded")

    def compare_ecu(self, row, rrsp, req):
        if len(req) // 2 == 3:
            rrsp = rrsp[3:]

        base = 0
        res = 0
        att = 0

        ttrrsp = rrsp.replace(" ", "")
        if not all(c in string.hexdigits for c in ttrrsp):
            return False

        while base + 6 <= len(row):
            if row[base] != req:
                req = row[base]
                rrsp = self.elm.cmd(req)[3:]

                ttrrsp = rrsp.replace(" ", "")
                if not all(c in string.hexdigits for c in ttrrsp):
                    return False

                if len(req) // 2 == 3:
                    rrsp = rrsp[3:]

            if (int(row[base + 3]) * 3 + 2) > len(rrsp):
                return False

            byte = int(rrsp[int(row[base + 3]) * 3 : int(row[base + 3]) * 3 + 2], 16)
            mask = int(row[base + 4], 16)
            val = int(row[base + 5], 16)

            if (byte & mask) == val:
                res += 1
            att += 1
            if att != res:
                break
            base += 6

        if res == att and res > 0:
            return True
        else:
            return False

    def request_can(self, row):
        global opt_demo

        self.elm.start_session(row["startDiagReq"])  # open session
        rrsp = self.elm.cmd(row["ids"][0])  # get identification data

        self.elm.cmd("at st fa")  # set timeout to 1 second
        self.elm.cmd("at at 0")  # disable adaptive timing

        rerr = ""
        if row["stdType"] == "STD_A":
            rerr = self.elm.cmd("17FF00")  # get errors STD_A

        if row["stdType"] == "STD_B":
            rerr = self.elm.cmd("1902AF")  # get errors STD_B

        if row["stdType"] == "UDS":
            rerr = self.elm.cmd("1902AF")  # get errors UDS

        # if len(row['stopDiagReq'])>0:
        #  self.elm.cmd(row['stopDiagReq'])	#close session

        self.elm.cmd("at at 1")  # enable adaptive timing

        return rrsp, rerr

    def request_iso(self, row):

        global opt_demo

        if len(row["dst"]) != 2:
            return "addr error", "addr error"

        rsp = ""
        cKey = row["dst"] + row["startDiagReq"] + row["stdType"] + row["protocol"]
        for r in self.reqres:
            if cKey == r[0]:
                rsp = r[1]
                break

        # if len(rsp)==0:
        #  rsp = self.elm.cmd("81")	 		    #init bus
        #  self.reqres.append([cKey,rsp,''])

        rrsp = ""
        rerr = ""
        rerrPositive = ""
        if "ERROR" not in rsp and "ERROR" not in self.elm.last_init_response.upper():
            self.elm.start_session(row["startDiagReq"])  # open session

            rrsp = self.elm.cmd(row["ids"][0])  # get identification data

            self.elm.cmd("at st fa")  # set timeout to 1 second
            self.elm.cmd("at at 0")  # disable adaptive timing

            rerr = ""
            if row["stdType"] == "STD_A":
                rerr = self.elm.cmd("17FF00")  # get errors STD_A
                rerrPositive = "57"

            if row["stdType"] == "STD_B":
                rerr = self.elm.cmd("1902AF")  # get errors STD_B
                rerrPositive = "59"

            if row["stdType"] == "UDS":
                rerr = self.elm.cmd("1902AF")  # get errors UDS
                rerrPositive = "59"

            self.elm.cmd("at at 1")  # enable adaptive timing

            if len(row["stopDiagReq"]) > 0:
                self.elm.cmd(row["stopDiagReq"])  # close session

        res = ""
        for s in rrsp.split("\n"):
            dss = s.replace(" ", "")
            if len(dss) == 0:
                continue
            if dss.startswith(row["ids"][1]):
                res = s
            elif len(row["ids"][1]) == (len(row["ids"][0]) + 2) and str(
                row["dst"] + dss
            ).startswith(row["ids"][1]):
                # sometimes ids contains addr
                res = s

        rrsp = res

        res = ""
        for s in rerr.split("\n"):
            if s.replace(" ", "").startswith(rerrPositive):
                res = s
        rerr = res

        return rrsp, rerr

    def scan_can(self, row):

        rrsp = ""
        rerr = ""

        if self.elm.lf != 0:
            self.elm.lf.write(
                "#check: " + row["ecuname"] + " Addr:" + row["dst"] + "\n"
            )
            self.elm.lf.flush()

        for r in self.reqres:
            if (
                row["dst"]
                + row["startDiagReq"]
                + row["stdType"]
                + row["ids"][0]
                + row["protocol"]
            ) == r[0]:
                rrsp = r[1]
                rerr = r[2]

        if rrsp == "":
            rrsp, rerr = self.request_can(row)

            if not rrsp:
                rrsp = ""
            if not rerr:
                rerr = ""

            if row["stdType"] == "STD_A":
                rerr = (
                    str(int(rerr[3:5], 16))
                    if len(rerr) > 5 and rerr[:2] == "57"
                    else "0"
                )
            if row["stdType"] == "STD_B":
                rerr = (
                    str((len(rerr) - 8) // 12)
                    if len(rerr) > 8 and rerr[:2] == "59"
                    else "0"
                )
            if row["stdType"] == "UDS":
                rerr = (
                    str((len(rerr) - 8) // 12)
                    if len(rerr) > 8 and rerr[:2] == "59"
                    else "0"
                )
            if row["stdType"] == "FAILFLAG":
                rerr = "N/A"

            row["rerr"] = rerr

            if rrsp != "":
                self.reqres.append(
                    [
                        row["dst"]
                        + row["startDiagReq"]
                        + row["stdType"]
                        + row["ids"][0]
                        + row["protocol"],
                        rrsp,
                        rerr,
                    ]
                )  # populate cache for not to ask again

        compres = False
        if "ERROR" not in rrsp:
            rrsp = rrsp[3:]
            compres = self.compare_ecu(row["ids"], rrsp, row["ids"][0])

        if compres:
            familynotdeteced = True
            for i in self.detected_ecus:
                if i["idf"] == row["idf"]:
                    familynotdeteced = False
            if familynotdeteced:
                # than we found new ecu
                row["rerr"] = rerr
                self.detected_ecus.append(row)

    def scan_iso(self, row):

        rrsp = ""
        rerr = "0"

        if self.elm.lf != 0:
            self.elm.lf.write(
                "#check: "
                + row["ecuname"]
                + " Addr:"
                + row["dst"]
                + " Protocol:"
                + row["protocol"]
                + " ids:"
                + row["ids"][0]
                + "\n"
            )
            self.elm.lf.flush()

        for r in self.reqres:
            if (
                row["dst"]
                + row["startDiagReq"]
                + row["stdType"]
                + row["ids"][0]
                + row["protocol"]
            ) == r[0]:
                rrsp = r[1]
                rerr = r[2]

        if rrsp == "":
            rrsp, rerr = self.request_iso(row)

            # debug
            debug("rrsp", rrsp)

            if not rrsp:
                rrsp = ""
            if not rerr:
                rerr = ""

            if row["stdType"] == "STD_A":
                rerr = (
                    str(int(rerr[3:5], 16))
                    if len(rerr) > 5 and rerr[:2] == "57"
                    else "0"
                )
            if row["stdType"] == "STD_B":
                rerr = (
                    str((len(rerr) - 8) // 12)
                    if len(rerr) > 8 and rerr[:2] == "59"
                    else "0"
                )
            if row["stdType"] == "UDS":
                rerr = (
                    str((len(rerr) - 8) // 12)
                    if len(rerr) > 8 and rerr[:2] == "59"
                    else "0"
                )
            if row["stdType"] == "FAILFLAG":
                rerr = "N/A"

            row["rerr"] = rerr

            if rrsp != "":
                self.reqres.append(
                    [
                        row["dst"]
                        + row["startDiagReq"]
                        + row["stdType"]
                        + row["ids"][0]
                        + row["protocol"],
                        rrsp,
                        rerr,
                    ]
                )  # populate cache for not to ask again

        # debug
        debug("reqres", str(self.reqres))

        compres = False
        if "ERROR" not in rrsp:
            rrsp = rrsp[3:]
            compres = self.compare_ecu(row["ids"], rrsp, row["ids"][0])

        # debug
        debug("compres", str(str(compres) + " " + row["ecuname"]))

        if not rerr:
            rerr = ""

        if compres:
            familynotdeteced = True
            for i in self.detected_ecus:
                if i["idf"] == row["idf"]:
                    familynotdeteced = False
            if familynotdeteced:
                # than we found new ecu
                row["rerr"] = rerr
                self.detected_ecus.append(row)


def read_ecu_ids(elm):
    # clear cache
    elm.clear_cache()

    start_session = ""
    diag_version = ""
    supplier = ""
    version = ""
    soft = ""
    std = ""
    vin = ""

    # check session start command
    if elm.start_session_ == "":
        # check 10C0
        res = elm.request(req="10C0", positive="50", cache=False)

        if res == "" or "ERROR" in res:  # no response from ecu
            return start_session, diag_version, supplier, version, soft, std, vin

        if res.startswith("50"):
            start_session = "10C0"
        else:
            res = elm.request(req="1003", positive="50", cache=False)
            if res.startswith("50"):
                start_session = "1003"
            else:
                res = elm.request(req="10A0", positive="50", cache=False)
                if res.startswith("50"):
                    start_session = "10A0"
                else:
                    res = elm.request(req="10B0", positive="50", cache=False)
                    if res.startswith("50"):
                        start_session = "10B0"

    else:
        start_session = elm.start_session_
        res = elm.request(req=elm.start_session_, positive="50", cache=False)

    if not res.startswith("50"):
        # debug
        # print 'ERROR: Could not open the session
        pass

    # check STD_A
    id_rsp = elm.request(req="2180", positive="61", cache=False)

    """      0         1         2         3         4         5         6         7      """
    """      01234567890123456789012345678901234567890123456789012345678901234567890123456"""
    # Debug
    # IdRsp = '61 80 34 36 33 32 52 45 34 42 45 30 30 33 37 52 00 83 9D 00 1A 90 01 01 00 88 AA'
    """                           -- --------                ----- -----                  """
    """              DiagVersion--+      |                     |     +--Version           """
    """                        Supplier--+                     +--Soft                    """

    if len(id_rsp) > 59:
        diag_version = str(int(id_rsp[21:23], 16))
        supplier = id_rsp[24:32].replace(" ", "").strip()
        supplier = bytes.fromhex(supplier).decode("utf-8")

        soft = id_rsp[48:53].strip().replace(" ", "")
        version = id_rsp[54:59].strip().replace(" ", "")

        std = "STD_A"

        vin_rsp = elm.request(req="2181", positive="61", cache=False)
        # debug
        # vinRsp = '61 81 56 46 31 30 30 30 30 30 30 30 30 30 30 30 30 30 30 00 00 00 00 00 00 00 00'
        if len(vin_rsp) > 55 and "NR" not in vin_rsp:
            vin = vin_rsp[6:56].strip().replace("00", "30").replace(" ", "")
            vin = bytes.fromhex(vin).decode("utf-8", errors="ignore")

    else:
        try:
            # DiagVersion F1A0
            id_rsp_F1A0 = elm.request(req="22F1A0", positive="62", cache=False)
            if (
                len(id_rsp_F1A0) > 8
                and "NR" not in id_rsp_F1A0
                and "BUS" not in id_rsp_F1A0
            ):
                diag_version = str(int(id_rsp_F1A0[9:11], 16))

            # Supplier F18A
            id_rsp_F18A = elm.request(req="22F18A", positive="62", cache=False)
            if (
                len(id_rsp_F18A) > 8
                and "NR" not in id_rsp_F18A
                and "BUS" not in id_rsp_F18A
            ):
                supplier = id_rsp_F18A[9:].strip().replace(" ", "")
                supplier = bytes.fromhex(supplier).decode("utf-8")

            # Soft F194
            id_rsp_F194 = elm.request(req="22F194", positive="62", cache=False)
            if (
                len(id_rsp_F194) > 8
                and "NR" not in id_rsp_F194
                and "BUS" not in id_rsp_F194
            ):
                soft = id_rsp_F194[9:].strip().replace(" ", "")
                soft = bytes.fromhex(soft).decode("utf-8")

            # Version F195
            id_rsp_F195 = elm.request(req="22F195", positive="62", cache=False)
            if (
                len(id_rsp_F195) > 8
                and "NR" not in id_rsp_F195
                and "BUS" not in id_rsp_F195
            ):
                version = id_rsp_F195[9:].strip().replace(" ", "")
                version = bytes.fromhex(version).decode("utf-8")

            std = "STD_B"

            # Vin F190
            vin_rsp = elm.request(req="22F190", positive="62", cache=False)
            if len(vin_rsp) > 58:
                vin = vin_rsp[9:59].strip().replace("00", "30").replace(" ", "")
                vin = bytes.fromhex(vin).decode("utf-8")
        except:
            pass

    return start_session, diag_version, supplier, version, soft, std, vin


def find_tcom(addr, cmd, rsp, pl_id: bool = False):
    ecu_vhc = {}
    pl_id = {}

    scan_ecus = ScanEcus(None)
    print("Loading Uces.xml")
    scan_ecus.read_uces_file(True)

    print("Read models")
    file_list = mod_db_manager.get_file_list_from_clip("Vehicles/TCOM_*.[Xx]ml")
    for file in file_list:
        # skip synthetic lada vesta
        if "087" in file:
            continue

        dom_tree = xml.dom.minidom.parse(mod_db_manager.get_file_from_clip(file))
        vh = dom_tree.documentElement
        if vh.hasAttribute("defaultText"):
            vehicle_name = vh.getAttribute("defaultText")
            veh_type_code = vh.getAttribute("vehTypeCode")
            veh_tcom = vh.getAttribute("TCOM")
            vehicle = vehicle_name + "#" + veh_tcom
            pl_id[veh_type_code] = {}
            # print vehicle

            connector = vh.getElementsByTagName("Connector")
            can_network = connector.item(0).getElementsByTagName("CANNetwork")
            iso_network = connector.item(0).getElementsByTagName("ISONetwork")
            addresses = {}

            for pin in can_network:
                bus = pin.getAttribute("canH")
                can_network_params = pin.getElementsByTagName("CANNetworkParams")
                brp = can_network_params.item(0).getAttribute("brp")
                bus = bus + ":" + brp  # brp is a can bus speed
                can_ids = pin.getElementsByTagName("CanId")
                addresses[bus] = {}
                for CanId in can_ids:
                    target_address = CanId.getAttribute("targetAddress")
                    id_tx = CanId.getAttribute("idTx")
                    id_rx = CanId.getAttribute("idRx")
                    addresses[bus][target_address] = {"idTx": id_tx, "idRx": id_rx}

                pl_id[veh_type_code][bus] = {}
                ecu_list = pin.getElementsByTagName("EcuList")
                if ecu_list:
                    ecu_kinds = ecu_list.item(0).getElementsByTagName("EcuKind")
                    for ecu_kind in ecu_kinds:
                        id_family = ecu_kind.getAttribute("idFamily")
                        pl_id[veh_type_code][bus][id_family] = {}
                        pl_id[veh_type_code][bus][id_family]["refs"] = []
                        ecu_refs = ecu_kind.getElementsByTagName("EcuRef")
                        for ecu_ref in ecu_refs:
                            ecu_name = ecu_ref.getAttribute("name")
                            pl_id[veh_type_code][bus][id_family]["refs"].append(
                                ecu_name
                            )
                            if ecu_name in list(ecu_vhc.keys()):
                                ecu_vhc[ecu_name].append(vehicle)
                            else:
                                ecu_vhc[ecu_name] = [vehicle]
            for pin in iso_network:
                bus = "7"
                pl_id[veh_type_code][bus] = {}
                ecu_list = pin.getElementsByTagName("EcuList")
                if ecu_list:
                    ecu_kinds = ecu_list.item(0).getElementsByTagName("EcuKind")
                    for ecu_kind in ecu_kinds:
                        id_family = ecu_kind.getAttribute("idFamily")
                        if id_family not in pl_id[veh_type_code][bus].keys():
                            pl_id[veh_type_code][bus][id_family] = {}
                            pl_id[veh_type_code][bus][id_family]["refs"] = []
                        ecu_refs = ecu_kind.getElementsByTagName("EcuRef")
                        for ecu_ref in ecu_refs:
                            ecu_name = ecu_ref.getAttribute("name")
                            pl_id[veh_type_code][bus][id_family]["refs"].append(
                                ecu_name
                            )
                            if ecu_name in list(ecu_vhc.keys()):
                                ecu_vhc[ecu_name].append(vehicle)
                            else:
                                ecu_vhc[ecu_name] = [vehicle]

            if pl_id:
                for bus in pl_id[veh_type_code].keys():
                    for id_family in pl_id[veh_type_code][bus].keys():
                        attr = set()
                        for r in pl_id[veh_type_code][bus][id_family]["refs"]:
                            if r in scan_ecus.all_ecus.keys():
                                # attr.add(se.allecus[r]['stdType']+"#"+se.allecus[r]['dst']+"#"+se.allecus[r]['startDiagReq'])
                                faddr = scan_ecus.all_ecus[r]["dst"]
                                if bus[:1] != "7":
                                    if faddr in addresses[bus].keys():
                                        faddr = (
                                            faddr
                                            + "#"
                                            + addresses[bus][faddr]["idTx"]
                                            + "#"
                                            + addresses[bus][faddr]["idRx"]
                                        )
                                    else:
                                        faddr = faddr + "##"
                                attr.add(
                                    faddr + "#" + scan_ecus.all_ecus[r]["startDiagReq"]
                                )
                            # else:
                            #  print(r)
                        del pl_id[veh_type_code][bus][id_family]["refs"]
                        pl_id[veh_type_code][bus][id_family] = attr

    if cmd != "" and rsp != "":
        # print found ecus
        for r in list(scan_ecus.all_ecus.keys()):
            if scan_ecus.all_ecus[r]["dst"] != addr:
                continue
            if scan_ecus.all_ecus[r]["ids"][0] != cmd:
                continue
            if scan_ecus.compare_ecu(scan_ecus.all_ecus[r]["ids"], rsp, cmd):
                try:
                    print(
                        r,
                        scan_ecus.all_ecus[r]["doc"],
                        scan_ecus.all_ecus[r]["ids"],
                        ecu_vhc[r],
                    )
                except:
                    print()

    if pl_id:
        pickle.dump(pl_id, open("./cache/platform_attr.p", "wb"))


def generate_saved_ecus(ecu_list, file_name):
    scan_ecus = ScanEcus(0)
    scan_ecus.read_uces_file(read_all=True)

    scan_ecus.detected_ecus = []
    for i in ecu_list.split(","):
        if i in list(scan_ecus.all_ecus.keys()):
            scan_ecus.all_ecus[i]["ecuname"] = i
            scan_ecus.all_ecus[i]["idf"] = scan_ecus.all_ecus[i]["ModelId"][2:4]
            if scan_ecus.all_ecus[i]["idf"][0] == "0":
                scan_ecus.all_ecus[i]["idf"] = scan_ecus.all_ecus[i]["idf"][1]
            scan_ecus.all_ecus[i]["pin"] = "can"
            scan_ecus.detected_ecus.append(scan_ecus.all_ecus[i])
    print(scan_ecus.detected_ecus)
    if len(scan_ecus.detected_ecus):
        pickle.dump(scan_ecus.detected_ecus, open(file_name, "wb"))


if __name__ == "__main__":
    mod_db_manager.find_dbs()

    # 10016,10074 savedEcus.p_gen
    if len(sys.argv) == 3:
        generate_saved_ecus(sys.argv[1], sys.argv[2])

    # 2C 2180 '80 31 38 35 33 52 04 41 4D 52 30 32 30 34 30 16 30 16 30 00 DD 01 00 00 88 00'
    if len(sys.argv) == 4:
        find_tcom(sys.argv[1], sys.argv[2], sys.argv[3])
