#!/usr/bin/env python3
"""
Scenarium usage example

Name of this script should be exactly the same as in scenaruim URL but with '.py' extension

URL  -  scm:scen_ecri_calinj1#scen_ecri_calinj1_xxxxx.xml

'run' procedure will be executed by pyren script
 
"""

import re
import xml.dom.minidom

import config
import mod_db_manager
import mod_ecu_mnemonic
from mod_utils import clear_screen, pyren_encode


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

    def get_message(msg, encode=1):
        if msg in list(ScmParam.keys()):
            value = ScmParam[msg]
        else:
            value = msg
        if value.isdigit() and value in list(config.LANGUAGE_DICT.keys()):
            if encode:
                value = pyren_encode(config.LANGUAGE_DICT[value])
            else:
                value = config.LANGUAGE_DICT[value]
        return value

    def get_message_by_id(id, encode=1):
        if id.isdigit() and id in list(config.LANGUAGE_DICT.keys()):
            if encode:
                value = pyren_encode(config.LANGUAGE_DICT[id])
            else:
                value = config.LANGUAGE_DICT[id]
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
        if len(Set.attributes) != 1:
            setname = pyren_encode(config.LANGUAGE_DICT[Set.getAttribute("name")])
            ScmParams = Set.getElementsByTagName("ScmParam")

            for Param in ScmParams:
                name = pyren_encode(Param.getAttribute("name"))
                value = pyren_encode(Param.getAttribute("value"))

                ScmSet[setname] = value
                ScmParam[name] = value

    confirm = get_message_by_id("19800")
    missing_data_message = get_message_by_id("882")
    title = get_message("Title")
    messageInfo = get_message("Message1")
    succesMessage = get_message("CommandFinished")
    failMessage = get_message("CommandImpossible")

    mnemonics = ecu.get_ref_id(ScmParam["default"]).mnemolist

    if mnemonics[0][-2:] > mnemonics[1][-2:]:
        mnemo1 = mnemonics[1]
        mnemo2 = mnemonics[0]
    else:
        mnemo1 = mnemonics[0]
        mnemo2 = mnemonics[1]

    byteFrom = int(mnemo1[-2:])
    byteTo = int(re.findall("\d+", mnemo2)[1])
    byteCount = byteTo - byteFrom - 1
    resetBytes = byteCount * "00"
    params_to_send_length = int(mnemo2[-2:])

    mnemo1Data = mod_ecu_mnemonic.get_mnemonic(
        ecu.Mnemonics[mnemo1], ecu.Services, elm, 1
    )
    mnemo2Data = mod_ecu_mnemonic.get_mnemonic(
        ecu.Mnemonics[mnemo2], ecu.Services, elm, 1
    )

    paramsToSend = mnemo1Data + resetBytes + mnemo2Data

    fap_command_sids = ecu.get_ref_cmd(ScmParam["Cmde1"]).serviceID
    if len(fap_command_sids) and not config.OPT_DEMO:
        for sid in fap_command_sids:
            if len(ecu.Services[sid].params):
                if (
                    len(ecu.Services[sid].startReq + paramsToSend) // 2
                    != params_to_send_length
                ):
                    input(missing_data_message + "\n\nPress ENTER to exit")
                    return

    clear_screen()

    print(title)
    print("*" * 80)
    print(messageInfo)
    print("*" * 80)
    print()
    ch = input(confirm + " <YES/NO>: ")
    while (ch.upper() != "YES") and (ch.upper() != "NO"):
        ch = input(confirm + " <YES/NO>: ")
    if ch.upper() != "YES":
        return

    clear_screen()

    print()
    response = ecu.run_cmd(ScmParam["Cmde1"], paramsToSend)
    print()

    if "NR" in response:
        print(failMessage)
    else:
        print(succesMessage)

    print()
    ch = input("Press ENTER to exit")
    return
