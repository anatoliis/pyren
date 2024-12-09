import xml.dom.minidom

from pyren3 import config
from pyren3.mod import db_manager
from pyren3.mod.utils import KBHit, clearScreen


def run(elm, ecu, command, data):
    clearScreen()
    header = "[" + command.codeMR + "] " + command.label

    ScmSet = {}
    ScmParam = {}

    def get_message(msg):
        if msg in list(ScmParam.keys()):
            value = ScmParam[msg]
        else:
            value = msg
        if value.isdigit() and value in list(config.LANGUAGE_DICT.keys()):
            value = config.LANGUAGE_DICT[value]
        return value

    def get_message_by_id(id):
        if id.isdigit() and id in list(config.LANGUAGE_DICT.keys()):
            value = config.LANGUAGE_DICT[id]
        return value

    DOMTree = xml.dom.minidom.parse(db_manager.get_file_from_clip(data))
    ScmRoom = DOMTree.documentElement

    ScmParams = ScmRoom.getElementsByTagName("ScmParam")

    for Param in ScmParams:
        name = Param.getAttribute("name")
        value = Param.getAttribute("value")

        ScmParam[name] = value

    kb = KBHit()

    mainText = get_message("TexteTitre")
    important = get_message("TexteConsigne")
    tilt = get_message("TexteValeurInclinaison")
    degreeSymbol = get_message("TexteDegre")
    value2, datastr2 = ecu.get_pr(ScmParam["ParametreInclinaison"])

    clearScreen()
    print(header)
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

    clearScreen()
    cmd = ecu.get_ref_cmd(get_message("Commande1"))
    resVal = ScmParam["ParametreCommande1"]
    print("*" * 80)
    response = ecu.run_cmd(ScmParam["Commande1"], resVal)
    print("*" * 80)
    if "NR" in response:
        print(get_message("TexteProcedureInterompue"))
    else:
        print(get_message("TexteInitialisationEffectuee"))
    print()
    print(tilt, ":", value2, degreeSymbol)
    print()

    ch = input("Press ENTER to exit")
    return
