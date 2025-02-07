#!/usr/bin/env python3
import xml.dom.minidom

from mod_ecu_mnemonic import *


def get_parameter(pr, mn, se, elm, calc, dataids={}):

    comp = pr.computation
    comp = comp.replace("&amp;", "&")
    comp = comp.strip()

    for m in sorted(pr.mnemolist, key=len, reverse=True):

        if dataids and mn[m].request.startswith("22"):
            val = get_SnapShotMnemonic(mn[m], se, elm, dataids)
        else:
            val = get_mnemonic(mn[m], se, elm)
        if mn[m].type == "SNUM8" and int(val, 16) > 0x7F:
            val = str(int(val, 16) - 0x100)
        elif mn[m].type == "SNUM16" and int(val, 16) > 0x7FFF:
            val = str(int(val, 16) - 0x10000)
        elif mn[m].type == "SNUM32" and int(val, 16) > 0x7FFFFFFF:
            val = str(int(val, 16) - 0x100000000)
        else:
            val = "0x" + val

        comp = comp.replace(m, val)

    pr.value = calc.calculate(comp)

    if "." in str(pr.value):
        pr.value = "%10.2f" % float(pr.value)
    csv_data = str(pr.value)

    tmpmin = str(pr.min)
    tmpmax = str(pr.max)
    if tmpmin.strip() == "0" and tmpmax.strip() == "0":
        tmpmin = ""
        tmpmax = ""

    return (
        "%-6s %-50s %5s %10s %-10s %-5s"
        % (pr.codeMR, pr.label, tmpmin, pr.value, pr.unit, tmpmax),
        pr.helps,
        csv_data,
    )


class ecu_parameter:

    name = ""
    agcdRef = ""
    codeMR = ""
    mask = ""
    label = ""
    unit = ""
    type = ""
    min = 0
    value = 0
    max = 0
    format = 0
    domains = []
    helps = []
    computation = ""
    mnemolist = []

    def __str__(self):
        hlps = "["
        for h in self.helps:
            hlps += "'" + h + "'\n"
        hlps += "]"
        out = """
  name    = %s
  agcdRef = %s
  codeMR  = %s
  mask    = %s
  label   = %s
  unit    = %s
  type    = %s
  min     = %s
  value   = %s
  max     = %s
  format  = %s
  domains     = %s
  helps       = %s
  computation = %s
  mnemolist   = %s
    """ % (
            self.name,
            self.agcdRef,
            self.codeMR,
            self.mask,
            self.label,
            self.unit,
            self.type,
            self.min,
            self.value,
            self.max,
            self.format,
            str(self.domains),
            hlps,
            self.computation,
            str(self.mnemolist),
        )
        return pyren_encode(out)

    def __init__(self, pr, opt, tran):
        self.name = pr.getAttribute("name")
        self.agcdRef = pr.getAttribute("agcdRef")
        self.codeMR = pr.getAttribute("codeMR")

        Mask = pr.getElementsByTagName("Mask")
        if Mask:
            self.mask = Mask.item(0).getAttribute("value")

        Label = pr.getElementsByTagName("Label")
        codetext = Label.item(0).getAttribute("codetext")
        defaultText = Label.item(0).getAttribute("defaultText")
        self.label = ""
        if codetext:
            if codetext in list(tran.keys()):
                self.label = tran[codetext]
            elif defaultText:
                self.label = defaultText

        Unit = pr.getElementsByTagName("Unit")
        if Unit:
            codetext = Unit.item(0).getAttribute("codetext")
            defaultText = Unit.item(0).getAttribute("defaultText")
            self.unit = ""
            if codetext:
                if codetext in list(tran.keys()):
                    self.unit = tran[codetext]
                elif defaultText:
                    self.unit = defaultText

        format_tmp = pr.getElementsByTagName("Format")
        if format_tmp:
            format = format_tmp.item(0).firstChild.nodeValue

        Limits = pr.getElementsByTagName("Limits")
        if Limits:
            self.min = Limits.item(0).getAttribute("min")
            self.max = Limits.item(0).getAttribute("max")

        self.domains = []
        Domains = pr.getElementsByTagName("Domains")
        if Domains:
            for dm in Domains:
                Domain = dm.getElementsByTagName("Domain")
                if Domain:
                    domain = Domain.item(0).firstChild.nodeValue
                    self.domains.append(domain)

        self.helps = []
        Helps = pr.getElementsByTagName("Helps")
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
                        self.helps.append(line + "\n")

        xmlstr = opt["Parameter\\" + self.name]
        odom = xml.dom.minidom.parseString(xmlstr.encode("utf-8"))
        odoc = odom.documentElement

        self.computation = ""
        Computation = odoc.getElementsByTagName("Computation")
        if Computation:
            for cmpt in Computation:
                self.type = cmpt.getAttribute("type")
                tmp = cmpt.getElementsByTagName("Value").item(0).firstChild.nodeValue
                self.computation = tmp.replace(" ", "").replace("&amp;", "&")

                self.mnemolist = []
                Mnemo = cmpt.getElementsByTagName("Mnemo")
                if Mnemo:
                    for mn in Mnemo:
                        self.mnemolist.append(mn.getAttribute("name"))


class ecu_parameters:

    def __init__(self, parameter_list, mdoc, opt, tran):
        Parameters = mdoc.getElementsByTagName("Parameter")
        if Parameters:
            for pr in Parameters:
                parameter = ecu_parameter(pr, opt, tran)
                parameter_list[parameter.name] = parameter
