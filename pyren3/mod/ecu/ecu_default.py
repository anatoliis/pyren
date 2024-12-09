import string
import xml.dom.minidom

from pyren3.mod import config
from pyren3.mod.ecu.mnemonic import get_mnemonic, get_mnemonicDTC
from pyren3.mod.ecu.screen import EcuScreenDataRef
from pyren3.mod.ecu.service import executeService


def get_default_std_a(df, mn, se, elm, calc, getDTCmnemo):
    # get defaults from ECU
    resp = ""
    elm.cmd("at st fa")
    elm.cmd("at at 0")
    if len(mn[getDTCmnemo].sids) > 0:
        for sid in mn[getDTCmnemo].sids:
            service = se[sid]
            resp = executeService(service, elm, [], "", False)
    # resp = elm.request( mn[getDTCmnemo].request, mn[getDTCmnemo].positive, True, mn[getDTCmnemo].delay )
    elm.cmd("at at 1")
    # print "Request:"+mn[getDTCmnemo].request+" Positive:"+mn[getDTCmnemo].positive+" Response:"+resp+'\n'

    resp = resp.strip().replace(" ", "")
    if not all(c in string.hexdigits for c in resp):
        resp = ""
    resp = " ".join(a + b for a, b in zip(resp[::2], resp[1::2]))

    descr = {}  # would contains descriptions of every defaults with key equal HEX
    helps = {}  # would contains help strings of every defaults with key equal HEX
    dtcs = []  # would contains DTCs hex

    if not resp.startswith(mn[getDTCmnemo].positive) or len(resp) < 6:
        return dtcs, descr, helps

    numberOfDTCs = int(resp[3:5], 16)

    DTCs = resp[6:]  # strip the header
    while len(DTCs) >= 8 and numberOfDTCs > 0:  # for every default
        dtc = DTCs[:6].replace(" ", "")
        status = DTCs[6:8]
        numberOfDTCs = numberOfDTCs - 1

        if dtc not in list(df.keys()):
            DTCs = DTCs[9:]
            continue

        # Check is default exists

        comp = df[dtc].computation
        comp = comp.replace("&amp;", "&")
        for m in sorted(df[dtc].mnemolistComp, key=len, reverse=True):
            hex_val = get_mnemonicDTC(mn[m], "57 01 " + DTCs)
            comp = comp.replace(m, "0x" + hex_val)
        isExists = calc.calculate(comp)

        if not config.opt_minordtc:
            if isExists == 0:  # ignore error if it's definition does not exist
                DTCs = DTCs[9:]
                continue

        # Check if the default is alive

        infoPeriod = df[dtc].interpInfoPeri

        if len(infoPeriod.strip()) != 0:
            infoPeriod = infoPeriod.replace("&amp;", "&")
            for m in sorted(df[dtc].mnemolistIP, key=len, reverse=True):
                hex_val = get_mnemonicDTC(mn[m], "57 01 " + DTCs)
                infoPeriod = infoPeriod.replace(m, "0x" + hex_val)
            df[dtc].status = calc.calculate(infoPeriod)
        else:
            df[dtc].status = 2  # I'm not sure that it is right

        # if the self.status eq 1 then default is alive
        # if the self.status eq 2 then default is memorised
        if not config.opt_minordtc:
            if df[dtc].status == 0:  # ignore error if it's definition does not exist
                DTCs = DTCs[9:]
                continue

        isAlive = ""
        if df[dtc].status == 1:
            isAlive = config.language_dict.get("16882", "ALIVE")
        else:
            isAlive = config.language_dict.get("646", "MEMORISED")
        # if not config.opt_minordtc:
        #  if df[dtc].status==0: 		     #ignore error if it's definition does not exist
        #    DTCs = DTCs[9:]
        #    continue

        # Now get the interpretation

        comp = df[dtc].interpInfoComp

        if len(comp.strip()) != 0:
            comp = comp.replace("&amp;", "&")
            for m in sorted(df[dtc].mnemolistIC, key=len, reverse=True):
                hex_val = get_mnemonicDTC(mn[m], "57 01 " + DTCs)
                comp = comp.replace(m, "0x" + hex_val)
            chr_val = calc.calculate(comp)
        else:
            chr_val = ""  # I'm no sure that it is right

        if str(chr_val) in list(df[dtc].caracter.keys()):
            interpretation = df[dtc].caracter[str(chr_val)]
        else:
            interpretation = ""

        description = df[dtc].label
        if config.OS == "android":
            defstr = "%-6s(DTC%-6s) %-41s %-6s %-10s" % (
                df[dtc].agcdRef,
                dtc + status,
                description,
                interpretation,
                isAlive,
            )
        else:
            defstr = "%-6s(DTC%-6s) %-50s %-6s %-10s" % (
                df[dtc].agcdRef,
                dtc + status,
                description,
                interpretation,
                isAlive,
            )

        hlpstr = ""
        if len(df[dtc].helps):
            for l in sorted(df[dtc].helps):
                hlpstr = hlpstr + "\t" + l + "\n"

        DTCs = DTCs[9:]

        dtcs.append(dtc + status)
        descr[dtc + status] = defstr
        helps[dtc + status] = hlpstr

    return dtcs, descr, helps


def get_default_std_b(df, mn, se, elm, calc, getDTCmnemo):
    # get defaults from ECU
    resp = ""
    elm.cmd("at st fa")
    elm.cmd("at at 0")
    if len(mn[getDTCmnemo].sids) > 0:
        for sid in mn[getDTCmnemo].sids:
            service = se[sid]
            resp = executeService(service, elm, [], "", False)
    # resp = elm.request( mn[getDTCmnemo].request, mn[getDTCmnemo].positive, True, mn[getDTCmnemo].delay )
    elm.cmd("at at 1")
    # print "Request:"+mn[getDTCmnemo].request+" Positive:"+mn[getDTCmnemo].positive+" Response:"+resp+'\n'

    resp = resp.strip().replace(" ", "")
    if not all(c in string.hexdigits for c in resp):
        resp = ""
    resp = " ".join(a + b for a, b in zip(resp[::2], resp[1::2]))

    descr = {}  # would contains descriptions of every defaults with key equal HEX
    helps = {}  # would contains help strings of every defaults with key equal HEX
    dtcs = []  # would contains DTCs hex

    if not resp.startswith(mn[getDTCmnemo].positive) or len(resp) < 6:
        return dtcs, descr, helps

    DTCs = resp[9:]  # strip the header
    while len(DTCs) >= 11:  # for every default
        dtc = DTCs[:6].replace(" ", "")
        dtcType = DTCs[6:8]
        dtcStatus = DTCs[9:11]

        if dtc not in list(df.keys()):
            DTCs = DTCs[12:]
            continue

        # Check is default exists
        comp = df[dtc].computation
        comp = comp.replace("&amp;", "&")
        for m in sorted(df[dtc].mnemolistComp, key=len, reverse=True):
            hex_val = get_mnemonicDTC(mn[m], "59 02 FF " + DTCs)
            comp = comp.replace(m, "0x" + hex_val)
        isExists = calc.calculate(comp)

        if not config.opt_minordtc:
            if isExists == 0:  # ignore error if it's definition does not exist
                DTCs = DTCs[12:]
                continue

        # Check if the default is alive

        infoPeriod = df[dtc].interpInfoPeri

        if len(infoPeriod.strip()) != 0:
            infoPeriod = infoPeriod.replace("&amp;", "&")
            for m in sorted(df[dtc].mnemolistIP, key=len, reverse=True):
                hex_val = get_mnemonicDTC(mn[m], "59 02 FF " + DTCs)
                infoPeriod = infoPeriod.replace(m, "0x" + hex_val)
            df[dtc].status = calc.calculate(infoPeriod)
        else:
            df[dtc].status = 2  # I'm not sure that it is right

        # if the self.status eq 1 then default is alive
        # if the self.status eq 2 then default is memorised
        if not config.opt_minordtc:
            if df[dtc].status == 0:  # ignore error if it's definition does not exist
                DTCs = DTCs[12:]
                continue

        isAlive = ""
        if df[dtc].status == 1:
            isAlive = config.language_dict.get("16882", "ALIVE")  # ALIVE
        else:
            isAlive = config.language_dict.get("646", "MEMORISED")  # MEMORISED
        # if df[dtc].status==0:      #ignore error if it's definition does not exist
        #   DTCs = DTCs[12:]
        #   continue

        # Now get the interpretation

        comp = df[dtc].interpInfoComp

        if len(comp.strip()) != 0:
            comp = comp.replace("&amp;", "&")
            for m in sorted(df[dtc].mnemolistIC, key=len, reverse=True):
                hex_val = get_mnemonicDTC(mn[m], "59 02 FF " + DTCs)
                comp = comp.replace(m, "0x" + hex_val)
            chr_val = calc.calculate(comp)
        else:
            chr_val = ""  # I'm no sure that it is right

        if str(chr_val) in list(df[dtc].caracter.keys()):
            interpretation = df[dtc].caracter[str(chr_val)]
        else:
            interpretation = ""

        description = df[dtc].label

        if config.OS == "android":
            defstr = "DTC%-6s (%s) %-41s %-6s %-10s" % (
                dtc + dtcType,
                df[dtc].agcdRef,
                description,
                interpretation,
                isAlive,
            )
        else:
            defstr = "DTC%-6s (%s) %-50s %-6s %-10s" % (
                dtc + dtcType,
                df[dtc].agcdRef,
                description,
                interpretation,
                isAlive,
            )

        stBitsDef = [
            "warningIndicatorRequested",
            "testNotCompletedThisOperationCycle",
            "testFailedSinceLastClear",
            "testNotCompletedSinceLastClear",
            "confirmedDTC",
            "pendingDTC",
            "testFailedThisOperationCycle",
            "testFailed",
        ]

        hlpstr = ""
        if len(df[dtc].helps):
            for l in sorted(df[dtc].helps):
                if l.split(":")[0] == interpretation:
                    hlpstr = hlpstr + "\t" + l + "\n"

        if config.opt_verbose:
            stBits = "{0:0>8b}".format(int(dtcStatus, 16))
            hlpstr = (
                hlpstr + "\t----------- Status byte: " + dtcStatus + " -----------\n"
            )
            for i in range(0, 8):
                hlpstr = hlpstr + "\t%-35s : %s\n" % (stBitsDef[i], stBits[i])

        DTCs = DTCs[12:]

        dtcs.append(dtc + dtcType)
        descr[dtc + dtcType] = defstr
        helps[dtc + dtcType] = hlpstr

    return dtcs, descr, helps


def get_default_failflag(df, mn, se, elm, calc):
    descr = {}  # would contains descriptions of every defaults with key equal HEX
    helps = {}  # would contains help strings of every defaults with key equal HEX
    dtcs = []  # would contains DTCs hex

    for dtc in sorted(df.keys()):

        # Check is default exists

        comp = df[dtc].computation
        comp = comp.replace("&amp;", "&")
        for m in sorted(df[dtc].mnemolistComp, key=len, reverse=True):
            hex_val = get_mnemonic(mn[m], se, elm)
            comp = comp.replace(m, "0x" + hex_val)
        isExists = calc.calculate(comp)
        if isExists == 0:
            continue  # it is not a problem

        # value = ""
        # if str(tmp_val).encode("utf-8") in df[dtc].caracter.keys():
        #  value = df[dtc].caracter[str(tmp_val).encode("utf-8")]
        # else:
        #  value = ""
        #
        # description = df[dtc].label
        # value = " "*(16-len(value)/2) + value

        # Check if the default is alive

        infoPeriod = df[dtc].interpInfoPeri

        # there is some defaults without interpInfoPeriod I do not know what to do
        if len(infoPeriod.strip()) == 0:
            continue

        infoPeriod = infoPeriod.replace("&amp;", "&")
        for m in sorted(df[dtc].mnemolistIP, key=len, reverse=True):
            hex_val = get_mnemonic(mn[m], se, elm)
            infoPeriod = infoPeriod.replace(m, "0x" + hex_val)

        df[dtc].status = calc.calculate(infoPeriod)

        # if the self.status eq 1 then default is alive
        # if the self.status eq 2 then default is memorised
        if df[dtc].status == 0:  # it is not a problem
            continue
        isAlive = ""
        if df[dtc].status == 1:
            isAlive = config.language_dict.get("16882", "ALIVE")  # ALIVE
        else:
            isAlive = config.language_dict.get("646", "MEMORISED")  # MEMORISED

        # Now get the interpretation

        interp = df[dtc].interpInfoComp

        # the next line is author comment
        # there is some defaults without interpInfoComp I do not know what to do
        if len(interp.strip()) == 0:
            interpretation = ""
        else:
            interp = interp.replace("&amp;", "&")
            for m in sorted(df[dtc].mnemolistIC, key=len, reverse=True):
                hex_val = get_mnemonic(mn[m], se, elm)
                interp = interp.replace(m, "0x" + hex_val)

            tmp_interp = calc.calculate(interp)

            interpretation = ""
            if str(tmp_interp) in list(df[dtc].caracter.keys()):
                interpretation = df[dtc].caracter[str(tmp_interp)]
            else:
                interpretation = ""

        description = df[dtc].label
        if config.OS == "android":
            defstr = "%-6s %-41s %-6s %-10s" % (
                df[dtc].agcdRef,
                description,
                interpretation,
                isAlive,
            )
        else:
            defstr = "%-6s %-50s %-6s %-10s" % (
                df[dtc].agcdRef,
                description,
                interpretation,
                isAlive,
            )

        hlpstr = ""
        if len(df[dtc].helps):
            for l in sorted(df[dtc].helps):
                hlpstr = hlpstr + "\t" + l + "\n"

        dtcs.append(dtc)
        descr[dtc] = defstr
        helps[dtc] = hlpstr

    return dtcs, descr, helps


class EcuDefault:
    name = ""
    code = ""
    agcdRef = ""
    codeMR = ""
    mask = ""
    label = ""
    status = 0
    datarefs = []
    memDatarefs = []
    helps = []
    caracter = {}
    interpInfoPeri = ""
    mnemolistIP = []
    interpInfoComp = ""
    mnemolistIC = []
    computation = ""
    mnemolistComp = []

    def __init__(self, df, opt, tran):
        self.name = df.getAttribute("name")
        self.agcdRef = df.getAttribute("agcdRef")
        self.codeMR = df.getAttribute("codeMR")

        Mask = df.getElementsByTagName("Mask")
        if Mask:
            self.mask = Mask.item(0).getAttribute("value")

        Label = df.getElementsByTagName("Label")
        codetext = Label.item(0).getAttribute("codetext")
        defaultText = Label.item(0).getAttribute("defaultText")
        self.label = ""
        if codetext:
            if codetext in list(tran.keys()):
                self.label = tran[codetext]
            elif defaultText:
                self.label = defaultText

        self.datarefs = []
        CurrentInfo = df.getElementsByTagName("CurrentInfo")
        if CurrentInfo:
            for ci in CurrentInfo:
                DataRef = ci.getElementsByTagName("DataRef")
                if DataRef:
                    for dr in DataRef:
                        dataref = EcuScreenDataRef(dr)
                        self.datarefs.append(dataref)

        self.memDatarefs = []
        MemorisedInfo = df.getElementsByTagName("MemorisedInfo")
        if MemorisedInfo:
            for mi in MemorisedInfo:
                DataRef = mi.getElementsByTagName("DataRef")
                if DataRef:
                    for dr in DataRef:
                        dataref = EcuScreenDataRef(dr)
                        self.memDatarefs.append(dataref)

        self.helps = []
        Helps = df.getElementsByTagName("Helps")
        if Helps:
            for hl in Helps:
                Lines = hl.getElementsByTagName("Line")
                if Lines:
                    for ln in Lines:
                        line = ""
                        Label = ln.getElementsByTagName("Label")
                        if Label:
                            for la in Label:
                                codetext = la.getAttribute("codetext")
                                defaultText = la.getAttribute("defaultText")
                                if codetext:
                                    if codetext in list(tran.keys()):
                                        line = line + tran[codetext]
                                    elif defaultText:
                                        line = line + defaultText
                        self.helps.append(line)

        self.caracter = {}
        Caracterisation = df.getElementsByTagName("Caracterisation")
        if Caracterisation:
            for cor in Caracterisation:
                Correspondance = cor.getElementsByTagName("Correspondance")
                if Correspondance:
                    for co in Correspondance:
                        ivalue = co.getAttribute("value")
                        codetext = co.getAttribute("codetext")
                        defaultText = co.getAttribute("defaultText")
                        itext = ""
                        if codetext:
                            if codetext in list(tran.keys()):
                                itext = tran[codetext]
                            elif defaultText:
                                itext = defaultText
                            self.caracter[ivalue] = itext

        xmlstr = opt[self.name]
        odom = xml.dom.minidom.parseString(xmlstr.encode("utf-8"))
        odoc = odom.documentElement

        tmp = odoc.getAttribute("codeDTC")
        if tmp != "":
            self.code = hex(int(tmp)).replace("0x", "").zfill(4).upper()
        else:
            self.code = self.agcdRef

        self.computation = ""
        Computation = odoc.getElementsByTagName("Computation")
        if Computation:
            for cmpt in Computation:
                tmp = cmpt.getElementsByTagName("Value").item(0).firstChild.nodeValue
                self.computation = tmp.replace(" ", "").replace("&amp;", "&")

                self.mnemolistComp = []
                Mnemo = cmpt.getElementsByTagName("Mnemo")
                if Mnemo:
                    for mn in Mnemo:
                        self.mnemolistComp.append(mn.getAttribute("name"))

        self.interpInfoComp = ""
        Interpretation = odoc.getElementsByTagName("Interpretation")
        if Interpretation:
            for itp in Interpretation:
                if itp.getAttribute("name") == "InfoComp":
                    tmp = itp.getElementsByTagName("Value").item(0).firstChild.nodeValue
                    self.interpInfoComp = tmp.replace(" ", "").replace("&amp;", "&")

                    self.mnemolistIC = []
                    Mnemo = itp.getElementsByTagName("Mnemo")
                    if Mnemo:
                        for mn in Mnemo:
                            self.mnemolistIC.append(mn.getAttribute("name"))
                if itp.getAttribute("name") == "InfoPeriod":
                    tmp = itp.getElementsByTagName("Value").item(0).firstChild.nodeValue
                    self.interpInfoPeri = tmp.replace(" ", "").replace("&amp;", "&")

                    self.mnemolistIP = []
                    Mnemo = itp.getElementsByTagName("Mnemo")
                    if Mnemo:
                        for mn in Mnemo:
                            self.mnemolistIP.append(mn.getAttribute("name"))


class EcuDefaults:
    def __init__(self, default_list, mdoc, opt, tran):
        Defaults = mdoc.getElementsByTagName("Default")
        if Defaults:
            for df in Defaults:
                default = EcuDefault(df, opt, tran)
                default_list[default.code] = default

    def getDTCCommands(self, mdoc, opt, ecu_type):
        eraserCommandName = ""
        extractDTCmnemo = ""

        Eraser = mdoc.getElementsByTagName("Eraser").item(0)
        if Eraser:
            eraserCommandName = (
                Eraser.getElementsByTagName("DataRef").item(0).getAttribute("name")
            )
            xmlstr = opt["Command\\" + eraserCommandName]
            odom = xml.dom.minidom.parseString(xmlstr.encode("utf-8"))
            odoc = odom.documentElement

        #    if ecu_type=='STD_A':
        #      xmlstr = opt['ExtractCode']
        #      odom = xml.dom.minidom.parseString( xmlstr.encode( "utf-8" ) )
        #      odoc = odom.documentElement
        #      Mnemo = odom.getElementsByTagName("Mnemo").item(0)
        #      if Mnemo:
        #        extractDTCmnemo = Mnemo.getAttribute("name")
        #
        #    if ecu_type=='STD_B' or ecu_type=='UDS':
        #      xmlstr = opt['ExtractDBDTCCode']
        #      odom = xml.dom.minidom.parseString( xmlstr.encode( "utf-8" ) )
        #      odoc = odom.documentElement
        #      Mnemo = odom.getElementsByTagName("Mnemo").item(0)
        #      if Mnemo:
        #        extractDTCmnemo = Mnemo.getAttribute("name")

        xmlstr = ""
        if "ExtractDBDTCCode" in list(opt.keys()):
            xmlstr = opt["ExtractDBDTCCode"]
        elif "ExtractCode" in list(opt.keys()):
            xmlstr = opt["ExtractCode"]

        if len(xmlstr) > 0 and (
            ecu_type == "STD_A" or ecu_type == "STD_B" or ecu_type == "UDS"
        ):
            odom = xml.dom.minidom.parseString(xmlstr.encode("utf-8"))
            odoc = odom.documentElement
            Mnemo = odom.getElementsByTagName("Mnemo").item(0)
            if Mnemo:
                extractDTCmnemo = Mnemo.getAttribute("name")

        print("Eraser command name :" + eraserCommandName)
        print("DTC extractor mnemo :" + extractDTCmnemo)
        return extractDTCmnemo, eraserCommandName
