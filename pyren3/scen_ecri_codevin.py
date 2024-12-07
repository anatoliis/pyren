#!/usr/bin/env python3
"""
Scenarium usage example

Name of this script should be exactly the same as in scenaruim URL but with '.py' extension

URL  -  scm:scen_ecri_codevin#scen_ecri_codevin_xxxxx.xml

'run' procedure will be executed by pyren script
 
"""
import xml.dom.minidom

import config
import mod_db_manager
from mod_utils import clear_screen, hex_vin_plus_crc, pyren_encode


def run(elm, ecu, command, data):
    """
    MAIN function of scenarium

    Parameters:
        elm     - refernce to adapter class
        ecu     - reference to ecu class
        command - refernce to the command this scenarium belongs to
        data    - name of xml file with parameters from scenarium URL
    """

    clear_screen()
    header = "[" + command.codeMR + "] " + command.label

    ScmSet = {}
    ScmParam = {}

    def get_message(msg):
        if msg in list(ScmParam.keys()):
            value = ScmParam[msg]
        else:
            value = msg
        if value.isdigit() and value in list(config.LANGUAGE_DICT.keys()):
            value = pyren_encode(config.LANGUAGE_DICT[value])
        return value

    def get_message_by_id(id):
        if id.isdigit() and id in list(config.LANGUAGE_DICT.keys()):
            value = pyren_encode(config.LANGUAGE_DICT[id])
        return value

    #
    #      Data file parsing
    #
    DOMTree = xml.dom.minidom.parse(mod_db_manager.get_file_from_clip(data))
    ScmRoom = DOMTree.documentElement

    ScmParams = ScmRoom.getElementsByTagName("ScmParam")

    for Param in ScmParams:
        name = pyren_encode(Param.getAttribute("name"))
        value = pyren_encode(Param.getAttribute("value"))

        ScmParam[name] = value

    ScmSets = ScmRoom.getElementsByTagName("ScmSet")

    for Set in ScmSets:
        setname = pyren_encode(config.LANGUAGE_DICT[Set.getAttribute("name")])
        ScmParams = Set.getElementsByTagName("ScmParam")

        for Param in ScmParams:
            name = pyren_encode(Param.getAttribute("name"))
            value = pyren_encode(Param.getAttribute("value"))

            ScmSet[setname] = value
            ScmParam[name] = value

    #
    #     Important information
    #
    clear_screen()
    value1, datastr1 = ecu.get_id(ScmParam["identVIN"])
    print(pyren_encode(header))
    print()
    print(get_message("TextTitre"))
    print()
    print(get_message("MessageBox3"))
    print()
    print("*" * 80)
    print()
    print(pyren_encode(datastr1))
    print()
    print("*" * 80)
    ch = input("Are you ready to change the VIN? <yes/no>:")
    if ch.lower() != "yes":
        return

    #
    #     Enter new VIN
    #
    clear_screen()
    print(pyren_encode(header))
    print()
    print(get_message("TextTitre"))
    print()
    print("*" * 80)
    print()
    ch = input(get_message("STextTitre1") + ": ").upper()

    while not (len(ch) == 17 and ("I" not in ch) and ("O" not in ch)):
        ch = input(get_message("STextTitre2") + ": ").upper()

    cmd = ecu.get_ref_cmd(get_message("ConfigurationName"))

    vin_crc = hex_vin_plus_crc(ch)

    print()
    ch = input("Are you ready to change the VIN? <yes/no>:")
    if ch.lower() != "yes":
        return

    #
    #     Change VIN
    #
    responce = ecu.run_cmd(ScmParam["ConfigurationName"], vin_crc)
    value1, datastr1 = ecu.get_id(ScmParam["identVIN"])
    print()
    print("*" * 80)
    print()
    print(pyren_encode(datastr1))
    print()
    print("*" * 80)

    ch = input("Press ENTER to continue")
