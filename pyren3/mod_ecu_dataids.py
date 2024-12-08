#!/usr/bin/env python3

from mod_ecu_service import EcuMnemoLocation
from mod_utils import pyren_encode


class EcuDataId:
    id = ""
    dataBitLength = ""
    mnemolocations = {}

    def __str__(self):
        ml = ""
        for k in list(self.mnemolocations.keys()):
            ml = ml + str(self.mnemolocations[k])

        out = """
  id             = %s
  dataBitLength  = %s
  mnemolocations = 
%s
    """ % (
            self.id,
            self.dataBitLength,
            ml,
        )
        return pyren_encode(out)

    def __init__(self, di, opt, tran):
        self.id = di.getAttribute("id")
        self.dataBitLength = di.getAttribute("dataBitLength")

        self.mnemolocations = {}

        MnemoLocations = di.getElementsByTagName("MnemoLocation")
        if MnemoLocations:
            for ml in MnemoLocations:
                mnemoloc = EcuMnemoLocation(ml)
                self.mnemolocations[mnemoloc.name] = mnemoloc


class EcuDataIds:
    def __init__(self, dataid_list, mdoc, opt, tran):
        DataIds = mdoc.getElementsByTagName("DataId")
        if DataIds:
            for di in DataIds:
                dataid = EcuDataId(di, opt, tran)
                dataid_list[dataid.id] = dataid
