#!/usr/bin/env python3

import xml.dom.minidom

import mod_db_manager
import mod_globals
from mod_utils import KBHit, clear_screen, pyren_encode


def run(elm, ecu, command, data):
    clear_screen()
    header = "[" + command.codeMR + "] " + command.label

    ScmSet = {}
    ScmParam = {}

    def get_message(msg):
        if msg in list(ScmParam.keys()):
            value = ScmParam[msg]
        else:
            value = msg
        if value.isdigit() and value in list(mod_globals.language_dict.keys()):
            value = pyren_encode(mod_globals.language_dict[value])
        return value

    def get_message_by_id(id):
        if id.isdigit() and id in list(mod_globals.language_dict.keys()):
            value = pyren_encode(mod_globals.language_dict[id])
        return value

    DOMTree = xml.dom.minidom.parse(mod_db_manager.get_file_from_clip(data))
    ScmRoom = DOMTree.documentElement

    ScmParams = ScmRoom.getElementsByTagName("ScmParam")

    for Param in ScmParams:
        name = pyren_encode(Param.getAttribute("name"))
        value = pyren_encode(Param.getAttribute("value"))

        ScmParam[name] = value

    kb = KBHit()

    mainText = get_message("TexteTitre")
    important = get_message("TexteConsigne")
    tilt = get_message("TexteValeurInclinaison")
    degreeSymbol = get_message("TexteDegre")
    value2, datastr2 = ecu.get_pr(ScmParam["ParametreInclinaison"])

    clear_screen()
    print(pyren_encode(header))
    print(mainText)
    print("*" * 80)
    print()
    print(important)
    print()

    ch = input("Do you want to continue? <yes/no> ")
    while (ch.upper() != "YES") and (ch.upper() != "NO"):
        ch = input("Do you want to continue? <yes/no> ")
    if ch.upper() != "YES":
        return

    clear_screen()
    cmd = ecu.get_ref_cmd(get_message("Commande1"))
    resVal = ScmParam["ParametreCommande1"]
    print("*" * 80)
    responce = ecu.run_cmd(ScmParam["Commande1"], resVal)
    print("*" * 80)
    if "NR" in responce:
        print(get_message("TexteProcedureInterompue"))
    else:
        print(get_message("TexteInitialisationEffectuee"))
    print()
    print(tilt, pyren_encode(":"), value2, degreeSymbol)
    print()

    ch = input("Press ENTER to exit")
    return
