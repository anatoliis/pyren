"""
Scenarium usage example

Name of this script should be exactly the same as in scenaruim URL but with '.py' extension

URL  -  scm:scen_lect_sondeO21#scen_lect_xxxxxx_xxxxx.xml

'run' procedure will be executed by pyren script
 
"""

import time
import xml.dom.minidom
from copy import deepcopy

from pyren3.mod import config, db_manager
from pyren3.mod.utils import KBHit, clearScreen


# def get_message( value ):
#  if value.isdigit() and value in config.language_dict.keys():
#    value =  config.language_dict[value]
#  print value


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

    ScmParam = {}
    ScmList_Etats = []
    ScmList_Messages = []
    ScmUSet = {}

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

    # read parameters
    ScmParams = ScmRoom.getElementsByTagName("ScmParam")

    for Param in ScmParams:
        name = Param.getAttribute("name")
        value = Param.getAttribute("value")

        ScmParam[name] = value

    # read ScmLists
    ScmLists = ScmRoom.getElementsByTagName("ScmList")

    for ScmList in ScmLists:
        listname = ScmList.getAttribute("name")
        ScmUSets = ScmList.getElementsByTagName("ScmUSet")

        ScmUSet = {}
        for Set in ScmUSets:
            ScmParams = Set.getElementsByTagName("ScmParam")
            for Param in ScmParams:
                name = Param.getAttribute("name")
                value = Param.getAttribute("value")
                ScmUSet[name] = value

            if listname.lower() == "etats":
                ScmList_Etats.append(deepcopy(ScmUSet))
            else:
                ScmList_Messages.append(deepcopy(ScmUSet))

    #
    #     Important information
    #
    clearScreen()
    print(header)
    print()
    print(get_message("TexteScenario"))
    print()
    print(get_message("TexteInformations"))
    print()
    print("*" * 80)
    print()
    print(get_message("TexteContenuInformationsE1"))
    print()
    print(get_message("TexteContenuInformationsE4"))
    print()
    print(get_message("TexteProcedureFin"))
    print()
    print("*" * 80)
    ch = input("Press ENTER to continue")

    #
    #     Check conditions
    #
    i = 1
    clearScreen()
    print(header)
    print()
    print("*" * 80)
    for etat in ScmList_Etats:
        print("Checking condition : ", i)
        i = i + 1
        print("*" * 80)
        state_ref = ecu.get_ref_st(etat["Index"])
        value1, datastr1 = ecu.get_st(etat["Index"])
        print(datastr1)
        if value1 != config.language_dict[etat["RefOK"]]:
            value2, datastr2 = ecu.get_st(etat["Donne1"])
            print(config.language_dict[etat["TexteSortie"]])
            print((datastr2))
            print("*" * 80)
            ch = input("Press ENTER to exit")
            # return

    #
    #     Ask permission to start
    #
    # clearScreen()
    print()
    print("*" * 80)
    print()
    print(header)
    print()
    ch = input("Are you ready to start the test? <yes/no>:")
    if ch.lower() != "yes":
        return

    #
    #     Start test
    #
    response = ecu.run_cmd(ScmParam["CommandeTestSonde"])

    #
    #     Main cycle
    #
    begin_time = time.time()
    Phase_state = ecu.get_ref_st(ScmParam["EtatComTer"])
    Result_state = ecu.get_ref_st(ScmParam["EtatResultatTest"])
    kb = KBHit()
    pfe = 0
    while 1:
        # get all values before showing them for avoid screen flickering
        value0, datastr0 = ecu.get_st(ScmParam["EtatComTer"])
        value1, datastr1 = ecu.get_st(ScmParam["EtatResultatTest"])
        phase = value0
        rescode = value1
        result = rescode
        for m in ScmList_Messages:
            if rescode in config.language_dict[m["Valeur"]]:
                result = config.language_dict[m["Texte"]]

        current_time = time.time()
        elapsed = int(current_time - begin_time)
        minutes, seconds = divmod(elapsed, 60)
        hours, minutes = divmod(minutes, 60)

        #
        #    Show process
        #
        clearScreen()
        print(header)
        print("\tTime   - ", "{hours:02d}:{minutes:02d}:{seconds:02d}".format(**vars()))
        print("\tPhase  - ", phase)
        print("*" * 90)
        print(datastr0)
        print(datastr1)
        print("*" * 90)
        if value0 == get_message_by_id("19532"):
            pfe = 1
            break
        print("Press Q to emergency exit")
        if kb.kbhit():
            c = kb.getch()
            if len(c) != 1:
                continue
            if c == "q" or c == "Q":
                kb.set_normal_term()
                break
        time.sleep(0.2)

    kb.set_normal_term()
    if pfe:
        print("\tPhase  - ", phase)
        print("\tResult - ", result)
        print("*" * 90)

    ch = input("Press ENTER to exit")
