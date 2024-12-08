"""
Scenarium usage example

Name of this script should be exactly the same as in scenaruim URL but with '.py' extension

URL  -  scm:scen_ecri_codevin#scen_ecri_codevin_xxxxx.xml

'run' procedure will be executed by pyren script
 
"""

import xml.dom.minidom

from pyren3.mod import config, db_manager
from pyren3.mod.utils import clearScreen


def run(elm, ecu, command, data):
    """
    MAIN function of scenarium

    Parameters:
        elm     - refernce to adapter class
        ecu     - reference to ecu class
        command - refernce to the command this scenarium belongs to
        data    - name of xml file with parameters from scenarium URL
    """

    clearScreen()
    header = "[" + command.codeMR + "] " + command.label

    ScmSet = {}
    ScmParam = {}

    def get_message(msg):
        if msg in list(ScmParam.keys()):
            value = ScmParam[msg]
        else:
            value = msg
        if value.isdigit() and value in list(config.language_dict.keys()):
            value = config.language_dict[value]
        return value

    def get_message_by_id(id):
        if id.isdigit() and id in list(config.language_dict.keys()):
            value = config.language_dict[id]
        return value

    #
    #      Data file parsing
    #
    DOMTree = xml.dom.minidom.parse(db_manager.get_file_from_clip(data))
    ScmRoom = DOMTree.documentElement

    ScmParams = ScmRoom.getElementsByTagName("ScmParam")

    for Param in ScmParams:
        name = Param.getAttribute("name")
        value = Param.getAttribute("value")
        ScmParam[name] = value

    #
    #     Get IDs
    #
    value1, datastr1 = ecu.get_id(ScmParam["ref_C_2180"])
    value2, datastr2 = ecu.get_id(ScmParam["ref_C_21FE"])
    value3, datastr3 = ecu.get_id(ScmParam["ref_C_22F187"])
    value4, datastr4 = ecu.get_id(ScmParam["ref_C_22F18E"])

    res = ecu.ecudata["idf"] + ":"
    if len(value1) == 10:
        res += value1 + ","
    if len(value2) == 10:
        res += value2 + ","
    if len(value3) == 10:
        res += value3 + ","
    if len(value4) == 10:
        res += value4 + ","
    if res.endswith(","):
        res = res[:-1]

    print("## This info intended to be used as a value of --ref parameter of acf.py ##")
    print()
    print(res)
    print()

    ch = input("Press ENTER to continue")
