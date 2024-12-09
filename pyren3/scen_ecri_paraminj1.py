#!/usr/bin/env python3
"""
Scenarium usage example

Name of this script should be exactly the same as in scenaruim URL but with '.py' extension

URL  -  scm:scen_ecri_calinj1#scen_ecri_calinj1_xxxxx.xml

'run' procedure will be executed by pyren script
 
"""

import xml.dom.minidom
import xml.etree.cElementTree as et
from collections import OrderedDict

from mod import config, db_manager
from mod.utils import Choice, clearScreen


class Ecus:
    vdiag = ""
    buttons = {}
    ncalib = ""

    def __init__(self, vd, nc, bt):
        self.vdiag = vd
        self.ncalib = nc
        self.buttons = bt


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
    ecusList = []
    correctEcu = ""
    vdiagExists = False
    ncalibExists = False

    def get_message(msg, encode=1):
        if msg in list(ScmParam.keys()):
            value = ScmParam[msg]
        else:
            value = msg
        if value.isdigit() and value in list(config.language_dict.keys()):
            if encode:
                value = config.language_dict[value]
            else:
                value = config.language_dict[value]
        return value

    def get_message_by_id(id, encode=1):
        if id.isdigit() and id in list(config.language_dict.keys()):
            if encode:
                value = config.language_dict[id]
            else:
                value = config.language_dict[id]
        return value

    #
    #      Data file parsing
    #
    DOMTree = xml.dom.minidom.parse(db_manager.get_file_from_clip(data))
    ScmRoom = DOMTree.documentElement

    root = et.parse(db_manager.get_file_from_clip(data)).getroot()

    ScmParams = ScmRoom.getElementsByTagName("ScmParam")

    for Param in ScmParams:
        name = Param.getAttribute("name")
        value = Param.getAttribute("value")

        ScmParam[name] = value

    ScmSets = ScmRoom.getElementsByTagName("ScmSet")

    for Set in ScmSets:
        if len(Set.attributes) != 1:
            setname = config.language_dict[Set.getAttribute("name")]
            ScmParams = Set.getElementsByTagName("ScmParam")

            for Param in ScmParams:
                name = Param.getAttribute("name")
                value = Param.getAttribute("value")

                ScmSet[setname] = value
                ScmParam[name] = value

    if "VDiag" in list(ScmParam.keys()):
        vdiagExists = True
        if "Ncalib" in list(ScmParam.keys()):
            ncalibExists = True

    # Get nested buttons with VDiag and Ncalib
    for vDiag in root:
        if vDiag.attrib["name"] == "VDiag":
            if len(list(vDiag.keys())) == 1:
                for vDiagName in vDiag:
                    if vDiagName:
                        for vDiagButtons in vDiagName:
                            buttons = OrderedDict()
                            if vDiagButtons.attrib["name"] == "Ncalib":
                                for ncalibName in vDiagButtons:
                                    for ncalibButtons in ncalibName:
                                        if ncalibButtons.attrib["name"] == "Buttons":
                                            for ncalibButton in ncalibButtons:
                                                buttons[ncalibButton.attrib["name"]] = (
                                                    ncalibButton.attrib["value"]
                                                )
                                            ecusList.append(
                                                Ecus(
                                                    vDiagName.attrib["name"],
                                                    ncalibName.attrib["name"],
                                                    buttons,
                                                )
                                            )
                                            buttons = OrderedDict()
                            else:
                                if vDiagButtons.attrib["name"] == "Buttons":
                                    for vDiagButton in vDiagButtons:
                                        buttons[vDiagButton.attrib["name"]] = (
                                            vDiagButton.attrib["value"]
                                        )
                                ecusList.append(
                                    Ecus(vDiagName.attrib["name"], "", buttons)
                                )

    # Get plain buttons with VDiag
    if vdiagExists:
        if not ncalibExists:
            vdiag = ""
            buttons = OrderedDict()
            for name in list(ScmParam.keys()):
                if name.startswith("InjectorsButton"):
                    if buttons:
                        ecusList.append(Ecus(vdiag, "", buttons))
                    buttons = OrderedDict()
                    vdiag = name[-2:]
                    buttons[name[:-2]] = ScmParam[name]
                if vdiag:
                    if name.endswith("Button" + vdiag):
                        buttons[name[:-2]] = ScmParam[name]
            ecusList.append(Ecus(vdiag, "", buttons))
    else:  # Get buttons without VDiag
        buttons = OrderedDict()
        found = False
        for name in list(ScmParam.keys()):
            if name == "InjectorsButton":
                buttons[name] = ScmParam[name]
                found = True
            if found:
                if name.endswith("Button"):
                    buttons[name] = ScmParam[name]
                else:
                    found = False
                    break
        ecusList.append(Ecus("", "", buttons))

    # Get correct buttons set
    if vdiagExists:
        value1, datastr1 = ecu.get_id(ScmParam["VDiag"])
        for ecuSet in ecusList:
            if ecuSet.vdiag == value1.upper():
                if ncalibExists:
                    if ecuSet.ncalib:
                        value2, datastr2 = ecu.get_id(ScmParam["Ncalib"])
                        if ecuSet.ncalib == value2.upper():
                            correctEcu = ecuSet
                            break
                        elif ecuSet.ncalib == "Other":
                            correctEcu = ecuSet
                            break
                    else:
                        correctEcu = ecuSet
                        break
                else:
                    correctEcu = ecuSet
                    break
    else:
        correctEcu = ecusList[0]

    if not correctEcu and config.opt_demo:
        correctEcu = ecusList[0]

    if vdiagExists:
        if not correctEcu:
            print("*" * 80)
            ch = input("Unknown diagnostic version. Press ENTER to exit")
            return

    # Prepare buttons
    buttons = OrderedDict()

    for bt in list(correctEcu.buttons.keys()):
        if bt == "InjectorsButton":
            if str(correctEcu.buttons[bt]) == "true":
                buttons[1] = get_message("Injectors", 0)
        if bt == "EGRValveButton":
            if str(correctEcu.buttons[bt]) == "true":
                buttons[2] = get_message("EGR_VALVE", 0)
        if bt == "InletFlapButton":
            if str(correctEcu.buttons[bt]) == "true":
                buttons[3] = get_message("INLET_FLAP", 0)
        if bt.startswith("Button"):
            if str(correctEcu.buttons[bt]) == "true":
                buttons[int(bt.strip("Button"))] = get_message(bt[:-6] + "Text", 0)
    buttons["loadDump"] = get_message_by_id("19802", 0)
    buttons["exit"] = "<exit>"

    # Get commands
    commands = {}

    for child in root:
        if child.attrib["name"] == "Commands":
            if len(list(child.keys())) == 1:
                for param in child:
                    serviceIDs = ecu.get_ref_cmd(param.attrib["value"]).serviceID
                    startReq = ""
                    for sid in serviceIDs:
                        if ecu.Services[sid].params:
                            startReq = ecu.Services[sid].startReq
                            break
                    commands[param.attrib["name"]] = {
                        "command": param.attrib["value"],
                        "startReq": startReq,
                    }

    # Get identifications
    identsList = OrderedDict()
    identsRangeKeys = OrderedDict()

    for param in list(ScmParam.keys()):
        if param.startswith("Idents") and param.endswith("Begin"):
            key = param[6:-5]
            begin = int(ScmParam["Idents" + key + "Begin"])
            end = int(ScmParam["Idents" + key + "End"])
            try:
                ecu.get_ref_id(ScmParam["Ident" + str(begin)]).mnemolist[
                    0
                ]  # 10529 ID114 doesn't exist
            except:
                continue
            else:
                for idnum in range(begin, end + 1):
                    identsList["D" + str(idnum)] = ScmParam["Ident" + str(idnum)]
                    if (
                        len(ecu.get_ref_id(ScmParam["Ident" + str(idnum)]).mnemolist)
                        > 1
                    ):
                        mnemonicsLen = [
                            int(ecu.Mnemonics[bitsLen].bitsLength)
                            for bitsLen in ecu.get_ref_id(
                                ScmParam["Ident" + str(idnum)]
                            ).mnemolist
                        ]
                        ecu.get_ref_id(ScmParam["Ident" + str(idnum)]).mnemolist = [
                            ecu.get_ref_id(ScmParam["Ident" + str(idnum)]).mnemolist[
                                mnemonicsLen.index(max(mnemonicsLen))
                            ]
                        ]
                frame = ecu.Mnemonics[
                    ecu.get_ref_id(identsList["D" + str(begin)]).mnemolist[0]
                ].request
                identsRangeKeys[key] = {"begin": begin, "end": end, "frame": frame}

    def getValuesToChange(resetItem):
        params = {}
        for child in root:
            if child.attrib["name"] == resetItem:
                if len(list(child.keys())) == 1:
                    for param in child:
                        params[param.attrib["name"].replace("D0", "D")] = param.attrib[
                            "value"
                        ]
        return params

    def takesParams(request):
        for cmd in list(commands.values()):
            if cmd["startReq"] == request:
                commandToRun = cmd["command"]
                return commandToRun

    def getValuesFromEcu(params):
        paramToSend = ""
        commandToRun = ""
        requestToFindInCommandsRequests = ""
        backupDict = {}

        try:
            idKeyToFindInRange = int((list(params.keys())[0]).replace("D", ""))
        except:
            return commandToRun, paramToSend
        else:
            for rangeK in list(identsRangeKeys.keys()):
                if (
                    identsRangeKeys[rangeK]["begin"]
                    <= idKeyToFindInRange
                    <= identsRangeKeys[rangeK]["end"]
                ):
                    requestToFindInCommandsRequests = (
                        "3B" + identsRangeKeys[rangeK]["frame"][-2:]
                    )
                    isTakingParams = takesParams(requestToFindInCommandsRequests)
                    if isTakingParams:
                        for k, v in params.items():
                            backupDict[k] = ecu.get_id(identsList[k], 1)
                            if v in list(identsList.keys()):
                                identsList[k] = ecu.get_id(identsList[v], 1)
                            else:
                                identsList[k] = v
                        for idKey in range(
                            identsRangeKeys[rangeK]["begin"],
                            identsRangeKeys[rangeK]["end"] + 1,
                        ):
                            if identsList["D" + str(idKey)].startswith("ID"):
                                identsList["D" + str(idKey)] = ecu.get_id(
                                    identsList["D" + str(idKey)], 1
                                )
                                backupDict["D" + str(idKey)] = identsList[
                                    "D" + str(idKey)
                                ]
                            paramToSend += identsList["D" + str(idKey)]
                        commandToRun = isTakingParams
                        break

            makeDump(commandToRun, backupDict)
            return commandToRun, paramToSend

    confirm = get_message_by_id("19800")
    successMessage = get_message("Message32")
    failMessage = get_message("MessageNACK")
    mainText = get_message("Title")
    inProgressMessage = get_message("CommandInProgressMessage")

    def resetInjetorsData(button, injectorsList):
        injectorsInfoMessage = get_message("Message21")
        response = ""
        clearScreen()

        print(mainText)
        print("*" * 80)
        print(buttons[button])
        print("*" * 80)
        print(injectorsInfoMessage)
        print("*" * 80)
        print()

        choice = Choice(list(injectorsList.keys()), "Choose :")
        if choice[0] == "<exit>":
            return

        clearScreen()

        print()
        response = ecu.run_cmd(injectorsList[choice[0]])
        print()

        if "NR" in response:
            print(failMessage)
        else:
            print(successMessage)

        print()
        ch = input("Press ENTER to exit")

    def afterEcuChange(title, button):
        params = getValuesToChange(title)
        infoMessage = get_message("Message262")
        mileageText = get_message_by_id("2110")
        mileageUnit = get_message_by_id("16521")

        clearScreen()
        print(mainText)
        print("*" * 80)
        print(buttons[button])
        print("*" * 80)
        print(infoMessage)
        print("*" * 80)
        print(get_message("MessageBox2"))
        print()
        ch = input(confirm + " <YES/NO>: ")
        if ch.upper() != "YES":
            return
        mileage = input(mileageText + " (" + mileageUnit + ")" + ": ")
        while not (mileage.isdigit() and 2 <= len(mileage) <= 6 and int(mileage) >= 10):
            print(get_message("MessageBox1"))
            print()
            mileage = input(mileageText + " (" + mileageUnit + ")" + ": ")

        clearScreen()

        print(mileageText + ": " + mileage + " " + mileageUnit)
        print()
        ch = input(confirm + " <YES/NO>: ")
        while (ch.upper() != "YES") and (ch.upper() != "NO"):
            ch = input(confirm + " <YES/NO>: ")
        if ch.upper() != "YES":
            return

        clearScreen()

        print()
        print(inProgressMessage)

        mileage = int(mileage)

        for paramkey in list(params.keys()):
            if params[paramkey] == "Mileage":
                mnemonics = ecu.get_ref_id(identsList[paramkey]).mnemolist[0]
                identValue = ecu.get_id(identsList[paramkey], 1)
                if identValue == "ERROR":
                    identValue = "00000000"
                hexval = "{0:0{1}X}".format(mileage, len(identValue))
                if ecu.Mnemonics[mnemonics].littleEndian == "1":
                    a = hexval
                    b = ""
                    if not len(a) % 2:
                        for i in range(0, len(a), 2):
                            b = a[i : i + 2] + b
                        hexval = b
                params[paramkey] = hexval

        command, paramToSend = getValuesFromEcu(params)

        if "ERROR" in paramToSend:
            input("Data downloading went wrong. Aborting.")
            return

        clearScreen()

        print()
        response = ecu.run_cmd(command, paramToSend)
        print()

        if "NR" in response:
            print(failMessage)
        else:
            print(successMessage)

        print()
        ch = input("Press ENTER to exit")

    def setGlowPlugsType(title, button):
        params = getValuesToChange(title)
        currentType = ecu.get_id(
            identsList[params["IdentToBeDisplayed"].replace("Ident", "D")], 1
        )
        slowTypeValue = get_message("ValueSlowParam")
        fastTypeValue = get_message("ValueFastParam")
        currentMessage = get_message_by_id("52676")
        slowMessage = get_message("Slow")
        fastMessage = get_message("Fast")
        notDefinedMessage = get_message("NotDefined")
        message2 = get_message("Message282")

        typesButtons = OrderedDict()

        typesButtons[get_message("Slow", 0)] = slowTypeValue
        typesButtons[get_message("Fast", 0)] = fastTypeValue
        typesButtons["<exit>"] = ""

        clearScreen()
        print(mainText)
        print("*" * 80)
        print(buttons[button])
        print("*" * 80)
        print(message2)
        print("*" * 80)
        print()
        if currentType == slowTypeValue:
            print(currentMessage + ": " + slowMessage)
        elif currentType == fastTypeValue:
            print(currentMessage + ": " + fastMessage)
        else:
            print(currentMessage + ": " + notDefinedMessage)
        print()

        choice = Choice(list(typesButtons.keys()), "Choose :")
        if choice[0] == "<exit>":
            return

        clearScreen()
        print()
        print(inProgressMessage)

        params[params["IdentToBeDisplayed"].replace("Ident", "D")] = typesButtons[
            choice[0]
        ]
        params.pop("IdentToBeDisplayed")

        command, paramToSend = getValuesFromEcu(params)

        if "ERROR" in paramToSend:
            input("Data downloading went wrong. Aborting.")
            return

        clearScreen()

        print()
        response = ecu.run_cmd(command, paramToSend)
        print()

        if "NR" in response:
            print(failMessage)
        else:
            print(successMessage)

        print()
        ch = input("Press ENTER to exit")

    def resetValues(title, button, defaultCommand):
        paramToSend = ""
        commandTakesParams = True
        params = getValuesToChange(title)

        clearScreen()

        print(mainText)
        print("*" * 80)
        print(buttons[button])
        print("*" * 80)
        if button == 4:
            print(get_message_by_id("55662"))
            print("*" * 80)
        if button == 5:
            print(get_message_by_id("55663"))
            print("*" * 80)
        print()
        ch = input(confirm + " <YES/NO>: ")
        while (ch.upper() != "YES") and (ch.upper() != "NO"):
            ch = input(confirm + " <YES/NO>: ")
        if ch.upper() != "YES":
            return

        clearScreen()
        print()
        print(inProgressMessage)

        command, paramToSend = getValuesFromEcu(params)

        if "ERROR" in paramToSend:
            input("Data downloading went wrong. Aborting.")
            return

        clearScreen()

        print()
        if command:
            response = ecu.run_cmd(command, paramToSend)
        else:
            response = ecu.run_cmd(defaultCommand)
        print()

        if "NR" in response:
            print(failMessage)
        else:
            print(successMessage)

        print()
        ch = input("Press ENTER to exit")

    def makeDump(cmd, idents):
        fileRoot = et.Element("ScmRoot")
        fileRoot.text = "\n    "

        cmdElement = et.Element("ScmParam", name="Command", value=cmd)
        cmdElement.tail = "\n    "
        fileRoot.insert(1, cmdElement)

        for k in idents:
            el = et.Element(
                "ScmParam", name="D" + "{:0>2}".format(k[1:]), value=idents[k]
            )
            el.tail = "\n    "
            fileRoot.insert(1, el)

        tree = et.ElementTree(fileRoot)
        tree.write(config.dumps_dir + ScmParam["FileName"])

    def loadDump():
        clearScreen()

        paramToSend = ""
        dumpScmParam = {}
        try:
            dumpData = open(config.dumps_dir + ScmParam["FileName"], "r")
        except:
            print(get_message_by_id("2194"))
            input()
            return

        dumpDOMTree = xml.dom.minidom.parse(dumpData)
        dumpScmRoot = dumpDOMTree.documentElement
        dumpScmParams = dumpScmRoot.getElementsByTagName("ScmParam")

        for Param in dumpScmParams:
            name = Param.getAttribute("name")
            value = Param.getAttribute("value")

            dumpScmParam[name] = value

        for k in sorted(dumpScmParam):
            if k != "Command":
                paramToSend += dumpScmParam[k]

        if "ERROR" in paramToSend:
            input("Data downloading went wrong. Aborting.")
            return

        print("*" * 80)
        print(get_message_by_id("19802"))
        print("*" * 80)
        print()

        ch = input(confirm + " <YES/NO>: ")
        while (ch.upper() != "YES") and (ch.upper() != "NO"):
            ch = input(confirm + " <YES/NO>: ")
        if ch.upper() != "YES":
            return

        clearScreen()

        print()
        response = ecu.run_cmd(dumpScmParam["Command"], paramToSend)
        print()

        if "NR" in response:
            print(failMessage)
        else:
            print(successMessage)

        print()
        ch = input("Press ENTER to exit")

    functions = OrderedDict()
    for cmdKey in list(commands.keys()):
        if cmdKey == "Cmd1":
            injectorsDict = OrderedDict()
            injectorsDict[get_message("Cylinder1", 0)] = commands["Cmd1"]["command"]
            injectorsDict[get_message("Cylinder2", 0)] = commands["Cmd2"]["command"]
            injectorsDict[get_message("Cylinder3", 0)] = commands["Cmd3"]["command"]
            injectorsDict[get_message("Cylinder4", 0)] = commands["Cmd4"]["command"]
            injectorsDict["<exit>"] = ""
            functions[1] = [1, injectorsDict]
        if cmdKey == "Cmd5":
            functions[2] = ["EGR_VALVE", 2, commands["Cmd5"]["command"]]
        if cmdKey == "Cmd6":
            functions[3] = ["INLET_FLAP", 3, commands["Cmd6"]["command"]]
        if cmdKey == "Cmd7":
            functions[4] = ["PARTICLE_FILTER", 4, commands["Cmd7"]["command"]]
            functions[5] = ["Button5ChangeData", 5, commands["Cmd7"]["command"]]
            functions[6] = ["Button6ChangeData", 6, commands["Cmd7"]["command"]]
        if cmdKey == "Cmd9":
            functions[8] = ["Button8DisplayData", 8]

    infoMessage = get_message("Message1")

    print(mainText)
    print()
    print(infoMessage)
    print()

    notSupported = [7]

    choice = Choice(list(buttons.values()), "Choose :")

    for key, value in buttons.items():
        if choice[0] == "<exit>":
            return
        if value == choice[0]:
            if key in notSupported:
                ch = input("\nNot Supported yet. Press ENTER to exit")
            elif key == "loadDump":
                loadDump()
            elif key == 1:
                resetInjetorsData(functions[key][0], functions[key][1])
            elif key == 6:
                afterEcuChange(functions[key][0], functions[key][1])
            elif key == 8:
                setGlowPlugsType(functions[key][0], functions[key][1])
            else:
                resetValues(functions[key][0], functions[key][1], functions[key][2])
            return
