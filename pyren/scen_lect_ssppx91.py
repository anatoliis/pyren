#!/usr/bin/env python
"""
Scenarium usage example

Name of this script should be exactly the same as in scenaruim URL but with '.py' extension

URL  -  scm:scen_ecri_calinj1#scen_ecri_calinj1_xxxxx.xml

'run' procedure will be executed by pyren script
 
"""

import os
import sys
import re
import time
import string
import mod_globals
import mod_utils
import mod_ecu
import mod_db_manager
from mod_utils import KBHit
from mod_utils import pyren_encode
from mod_utils import clearScreen
from mod_utils import ASCIITOHEX
from mod_utils import StringToIntToHex
from mod_utils import Choice
from collections import OrderedDict
import xml.dom.minidom


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
    ScmParam = OrderedDict()

    def get_message(msg, encode=True):
        if msg in list(ScmParam.keys()):
            value = ScmParam[msg]
        else:
            value = msg
        if value.isdigit() and value in list(mod_globals.language_dict.keys()):
            if encode:
                value = pyren_encode(mod_globals.language_dict[value])
            else:
                value = mod_globals.language_dict[value]
        return value

    def get_message_by_id(id, encode=True):
        if id.isdigit() and id in list(mod_globals.language_dict.keys()):
            if encode:
                value = pyren_encode(mod_globals.language_dict[id])
            else:
                value = mod_globals.language_dict[id]
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
            setname = pyren_encode(mod_globals.language_dict[Set.getAttribute("name")])
            ScmParams = Set.getElementsByTagName("ScmParam")

            for Param in ScmParams:
                name = pyren_encode(Param.getAttribute("name"))
                value = pyren_encode(Param.getAttribute("value"))

                ScmSet[setname] = value
                ScmParam[name] = value

    kb = KBHit()

    confirm = get_message_by_id("19800")
    confirmCodes = get_message_by_id("17571")
    resultMessage = get_message("TxtResult")
    title = get_message("TextTitre", False)
    stateLabel = get_message_by_id("804")
    finishedInfo = get_message_by_id("15902")
    messageInfo = get_message("MessageScr1", False)
    readCodeMessage = get_message_by_id("17884")
    codeInfo = get_message("TxtInformation")
    codeRed = codeInfo.split("-")[1].strip()
    codeOrange = codeInfo.split("-")[2].strip()
    codeGreen = codeInfo.split("-")[3].strip()
    oneValveText = get_message_by_id("14964", False)
    fourValveText = get_message_by_id("14966", False)

    NR10 = get_message("Nack10")
    NR11 = get_message("NackServiceNotSupported")
    NR12 = get_message("NackSubFunctionNotSupported")
    NR21 = get_message("NackBusyRepeatRequest")
    NR22 = get_message("NackConditionsNotCorrect")
    NR23 = get_message("Nack23")
    NR33 = get_message("NackSecurityAccessDenied")
    NR35 = get_message("NackInvalidKey")
    NR78 = get_message("NackResponsePending")
    NR80 = get_message("Nack80")
    NRFF = get_message("NackUnknown")

    negrsp = {
        "10": NR10,
        "11": NR11,
        "12": NR12,
        "21": NR21,
        "22": NR22,
        "23": NR23,
        "33": NR33,
        "35": NR35,
        "78": NR78,
        "80": NR80,
        "FF": NRFF,
    }

    searchInProgress = []
    searchInProgress.append(get_message("Label_AVG_En_Cours"))
    searchInProgress.append(get_message("Label_AVD_En_Cours"))
    searchInProgress.append(get_message("Label_ARD_En_Cours"))
    searchInProgress.append(get_message("Label_ARG_En_Cours"))
    searchFinished = []
    searchFinished.append(get_message("Label_AVG_Terminee"))
    searchFinished.append(get_message("Label_AVD_Terminee"))
    searchFinished.append(get_message("Label_ARD_Terminee"))
    searchFinished.append(get_message("Label_ARG_Terminee"))
    summerFLCode = ecu.get_id(ScmParam["ID_AVG_ETE"], 1)
    summerFRCode = ecu.get_id(ScmParam["ID_AVD_ETE"], 1)
    summerRRCode = ecu.get_id(ScmParam["ID_ARD_ETE"], 1)
    summerRLCode = ecu.get_id(ScmParam["ID_ARG_ETE"], 1)
    winterFLCode = ecu.get_id(ScmParam["ID_AVG_HIVER"], 1)
    winterFRCode = ecu.get_id(ScmParam["ID_AVD_HIVER"], 1)
    winterRRCode = ecu.get_id(ScmParam["ID_ARD_HIVER"], 1)
    winterRLCode = ecu.get_id(ScmParam["ID_ARG_HIVER"], 1)
    summerTyreCodes = [summerFLCode, summerFRCode, summerRRCode, summerRLCode]
    winterTyreCodes = [winterFLCode, winterFRCode, winterRRCode, winterRLCode]
    tyreCodes = []
    tyreCodes.extend(summerTyreCodes)
    tyreCodes.extend(winterTyreCodes)
    tyresLabels = []
    tyresLabels.append(get_message("Label_CodeAVG", False))
    tyresLabels.append(get_message("Label_CodeAVD", False))
    tyresLabels.append(get_message("Label_CodeARD", False))
    tyresLabels.append(get_message("Label_CodeARG", False))
    value1, datastr1 = ecu.get_st(ScmParam["State_ET469"])
    tariningCmdResp = ecu.Services[
        ecu.get_ref_cmd(ScmParam["CmndRoutineTraining"]).serviceID[0]
    ].simpleRsp

    currentTyreSet = ""
    lastCodeStatus = ""

    notUpdatedText = []
    notUpdatedText.append(title)
    notUpdatedText.append("*" * 80)
    notUpdatedText.append(messageInfo)
    notUpdatedText.append("*" * 80)
    notUpdatedText.append(datastr1)
    notUpdatedText.append("*" * 80)
    tyreCodesTable = []
    if get_message("Text_ET469_ETE", False) in datastr1:
        summerTyresSet = True
        tyreCodesTable.append("%-50s %-20s" % (tyresLabels[0], summerTyreCodes[0]))
        tyreCodesTable.append("%-50s %-20s" % (tyresLabels[1], summerTyreCodes[1]))
        tyreCodesTable.append("%-50s %-20s" % (tyresLabels[2], summerTyreCodes[2]))
        tyreCodesTable.append("%-50s %-20s" % (tyresLabels[3], summerTyreCodes[3]))
        currentTyreSet = summerTyreCodes
    else:
        summerTyresSet = False
        tyreCodesTable.append("%-50s %-20s" % (tyresLabels[0], winterTyreCodes[0]))
        tyreCodesTable.append("%-50s %-20s" % (tyresLabels[1], winterTyreCodes[1]))
        tyreCodesTable.append("%-50s %-20s" % (tyresLabels[2], winterTyreCodes[2]))
        tyreCodesTable.append("%-50s %-20s" % (tyresLabels[3], winterTyreCodes[3]))
        currentTyreSet = winterTyreCodes
    notUpdatedText = notUpdatedText + tyreCodesTable
    notUpdatedText.append("*" * 80)

    buttons = OrderedDict()
    buttons[1] = get_message_by_id("14964", False)
    buttons[2] = get_message_by_id("14966", False)
    buttons[3] = title
    buttons["exit"] = "<exit>"

    def sendTrainingCmd():
        resp = ecu.run_cmd(ScmParam["CmndRoutineTraining"])
        clearScreen()
        if tariningCmdResp not in resp and not mod_globals.opt_demo:
            nrCode = resp[resp.find("NR") - 3 : resp.find("NR")]
            print()
            if "NR" in resp:
                print(negrsp[resp[resp.find("NR") - 3 : resp.find("NR")]])
                print("")
            else:
                print(negrsp["FF"])
            print()
            input("Press any key to exit")
            return False
        else:
            return True

    def writeCodes(codes):
        ch = input(confirmCodes + " <YES/NO>: ")
        while (ch.upper() != "YES") and (ch.upper() != "NO"):
            ch = input(confirmCodes + " <YES/NO>: ")
        if ch.upper() != "YES":
            print()
            return
        print()
        print("*" * 80)
        rsp = ecu.run_cmd("VP003", codes)
        print("*" * 80)
        print()

    def generateScreen(title, codes):
        screen = ""
        screenPartOne = []
        screenPartOne.append(title)
        screenPartOne.append("*" * 80)
        screenPartOne.append(datastr1)
        screenPartOne.append("*" * 80)
        integratedLines = []
        for num in range(len(tyreCodesTable)):
            try:
                integratedLines.append(tyreCodesTable[num] + codes[num])
            except:
                integratedLines.append(tyreCodesTable[num])
        integratedScreen = screenPartOne + integratedLines
        for lines in integratedScreen:
            screen = screen + pyren_encode(lines) + "\n"
        return screen

    def writeOneValve():
        selectedValve = ""
        selectedValveKey = ""
        screen = generateScreen(oneValveText, [])
        valveLabelsDict = OrderedDict()
        for lb in range(4):
            valveLabelsDict[lb] = tyresLabels[lb]
        valveLabelsDict["exit"] = "<exit>"

        clearScreen()
        print(screen)
        print()
        choice = Choice(
            list(valveLabelsDict.values()), get_message_by_id("14127").replace(".", ":")
        )

        clearScreen()
        print(screen)
        print()
        for key, value in valveLabelsDict.items():
            if choice[0] == "<exit>":
                return
            if value == choice[0]:
                selectedValve = valveLabelsDict[key]
                selectedValveKey = key

        userCode = input(pyren_encode(selectedValve) + ": ").upper()
        while not len(userCode) == 6 or not all(
            c in string.hexdigits for c in userCode
        ):
            if not len(userCode) == 6:
                print("Valve code should be 6 characters long.")
            else:
                print("Illegal characters in the valve code")
            userCode = input(pyren_encode(selectedValve) + ": ").upper()

        paramToSend = ""
        if summerTyresSet:
            for code in range(len(summerTyreCodes)):
                if code == selectedValveKey:
                    paramToSend += userCode
                else:
                    paramToSend += summerTyreCodes[code]
        else:
            for code in range(len(winterTyreCodes)):
                if code == selectedValveKey:
                    paramToSend += userCode
                else:
                    paramToSend += winterTyreCodes[code]

        clearScreen()
        print(screen)
        print()
        print(pyren_encode(tyreCodesTable[selectedValveKey]), userCode)
        print()
        writeCodes(paramToSend)

    def writeFourValves():
        userCodes = []
        screen = generateScreen(fourValveText, [])

        clearScreen()
        print(screen)
        ch = input(confirm + " <YES/NO>: ")
        while (ch.upper() != "YES") and (ch.upper() != "NO"):
            ch = input(confirm + " <YES/NO>: ")
        if ch.upper() != "YES":
            print()
            return

        clearScreen()
        print(screen)
        for num in range(len(tyresLabels)):
            userCode = input(tyresLabels[num] + ": ").upper()
            while not len(userCode) == 6 or not all(
                c in string.hexdigits for c in userCode
            ):
                if not len(userCode) == 6:
                    print("Valve code should be 6 characters long.")
                else:
                    print("Illegal characters in the valve code")
                userCode = input(tyresLabels[num] + ": ").upper()
            userCodes.append(userCode)
            clearScreen()
            screen = generateScreen(fourValveText, userCodes)
            print(screen)

        paramToSend = ""
        for code in userCodes:
            paramToSend += code
        writeCodes(paramToSend)

    def valvesTraining():
        readCodes = OrderedDict()
        if not sendTrainingCmd():
            return

        tb = time.time()
        while 1:
            readCode = ecu.get_id(ScmParam["ID_Code_Valves"], 1)
            value2, datastr2 = ecu.get_st(ScmParam["State_ET002"])
            oldScreen = ""
            for lines in notUpdatedText:
                oldScreen = oldScreen + pyren_encode(lines) + "\n"

            clearScreen()
            print(oldScreen)
            try:
                print(stateLabel + ": " + searchInProgress[len(readCodes)])
            except:
                input("More than 4 tyres codes, aborting.")
                return
            print()
            print("*" * 80)

            if (
                pyren_encode(value2)
                == pyren_encode(mod_globals.language_dict[ScmParam["StateNO"]])
                and len(readCodes) < 4
            ):
                print("%-50s %-20s" % (readCodeMessage, pyren_encode(readCode)))
                print()
                print("No codes read")
            elif (
                pyren_encode(value2)
                == pyren_encode(mod_globals.language_dict[ScmParam["StateYES"]])
                and len(readCodes) < 4
            ):
                print("%-50s %-20s" % (readCodeMessage, pyren_encode(readCode)))
                print()

                if readCode != "000000" and readCode not in list(readCodes.keys()):
                    if not readCode in tyreCodes:
                        lastCodeStatus = codeRed
                    elif readCode == currentTyreSet[len(readCodes)]:
                        lastCodeStatus = codeGreen
                    else:
                        lastCodeStatus = codeOrange
                    readCodes[readCode] = readCode

                print(lastCodeStatus)
                print()

                for code in range(len(readCodes)):
                    print(
                        "%-60s %-8s"
                        % (
                            searchFinished[code],
                            pyren_encode(readCodes[list(readCodes.keys())[code]]),
                        )
                    )

            print("*" * 80)
            print()
            print("Press any key to exit")
            print()
            time.sleep(int(ScmParam["Tempo2"]) / 1000)
            tc = time.time()
            if (tc - tb) > int(ScmParam["Tempo1"]) / 1000:
                tb = time.time()
                if not sendTrainingCmd():
                    return
            if len(readCodes) == 4:
                break
            if kb.kbhit():
                return

        print(finishedInfo)
        print()
        paramToSend = ""
        for code in list(readCodes.keys()):
            paramToSend += code
        if "ERROR" in paramToSend:
            input("Data downloading went wrong. Aborting.")
            return
        writeCodes(paramToSend)

    print(get_message_by_id("19830"))
    print()
    choice = Choice(list(buttons.values()), "Choose :")
    for key, value in buttons.items():
        if choice[0] == "<exit>":
            return
        if value == choice[0]:
            if key == 1:
                writeOneValve()
            elif key == 2:
                writeFourValves()
            elif key == 3:
                valvesTraining()
            input("Press any key to exit")
            return
