#!/usr/bin/env python3

from mod.utils import pyren_encode


class Option:
    MTC = ""
    VW = ""
    VR = ""
    TW = ""
    TR1 = ""
    TR2 = ""
    ECA = ""
    MW = ""
    MR = ""
    TEX = ""
    APV = ""
    USI = ""
    MOD = ""

    def __str__(self):
        out = (
            'MTC="%s" ValueWrite="%s" ValueRead="%s" TrameWrite="%s" TrameRead1="%s" TrameRead2="%s" Ecart="%s" MasqueWrite="%s" MasqueRead="%s" Text="%s" APV="%s" Usine="%s" Mod="%s"'
            % (
                self.MTC,
                self.VW,
                self.VR,
                self.TW,
                self.TR1,
                self.TR2,
                self.ECA,
                self.MW,
                self.MR,
                self.TEX,
                self.APV,
                self.USI,
                self.MOD,
            )
        )
        return pyren_encode(out)

    def __init__(self, op):
        self.MTC = op.attrib["MTC"]
        self.VW = op.attrib["ValueWrite"]
        self.VR = op.attrib["ValueRead"]
        self.TW = op.attrib["TrameWrite"]
        self.TR1 = op.attrib["TrameRead1"]
        self.TR2 = op.attrib["TrameRead2"]
        self.ECA = op.attrib["Ecart"]
        self.MW = op.attrib["MasqueWrite"]
        self.MR = op.attrib["MasqueRead"]
        self.TEX = op.attrib["Text"]
        self.APV = op.attrib["APV"]
        self.USI = op.attrib["Usine"]
        self.MOD = op.attrib["Mod"]


class DecuConfig:
    kabs = []
    opts = []
    DI = ""
    TA = ""
    TE = ""
    FE = ""
    RW = ""
    DW = ""
    RR = ""
    DR = ""

    def __str__(self):
        # debug
        # print "^"*10, self.DI

        sd = ""
        for s in self.opts:
            sd = sd + "\n" + str(s)
        for k in self.kabs:
            # k = k.strip()
            try:
                sd = sd + "\nKAbsence:" + pyren_encode(k)
            except:
                print("<" + k + ">")

        out = """
  DiagItem      = %s
  Taille        = %s
  Text          = %s
  Feature       = %s
  RequestWrite  = %s
  DataWrite     = %s
  RequestRead   = %s
  DataRead      = %s
  Options/KAbs  = %s
    """ % (
            self.DI,
            self.TA,
            self.TE,
            self.FE,
            self.RW,
            self.DW,
            self.RR,
            self.DR,
            sd,
        )
        return pyren_encode(out)

    def __init__(self, cf):
        ns = {
            "ns0": "http://www-diag.renault.com/2002/ECU",
            "ns1": "http://www-diag.renault.com/2002/screens",
        }

        self.DI = cf.attrib["DiagItem"]
        self.TA = cf.attrib["Taille"]
        self.TE = cf.attrib["Text"]
        self.FE = cf.attrib["Feature"]
        self.RW = cf.attrib["RequestWrite"]
        self.DW = cf.attrib["DataWrite"]
        self.RR = cf.attrib["RequestRead"]
        self.DR = cf.attrib["DataRead"]

        self.opts = []
        Options = cf.findall("ns0:Option", ns)
        if Options:
            for op in Options:
                option = Option(op)
                self.opts.append(option)

        self.kabs = []
        KAbsence = cf.findall("ns0:KAbsence", ns)
        if KAbsence:
            for ka in KAbsence:
                kab = ka.attrib["MTC"]
                self.kabs.append(kab)


class DecuConfigs:
    def __init__(self, config_list, xdoc):
        # try to find default endian

        ns = {
            "ns0": "http://www-diag.renault.com/2002/ECU",
            "ns1": "http://www-diag.renault.com/2002/screens",
        }

        conf = xdoc.findall("ns0:Target/ns0:Configs", ns)
        if len(conf) == 0:
            conf = xdoc.findall("Configs")
        try:
            Configs = conf[0].findall("ns0:Config", ns)
        except:
            Configs = conf[0].findall("Config")
        if Configs:
            for cf in Configs:
                config = DecuConfig(cf)
                config_list.append(config)
                # print config
