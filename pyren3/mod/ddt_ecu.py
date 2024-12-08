#!/usr/bin/env python3

import operator
import os
import queue
import string
import sys
import threading
import time
import xml.etree.ElementTree as et
from datetime import datetime

from mod import config, db_manager, ddt_utils
from mod.ddt_data import DecuDatas
from mod.ddt_request import DecuRequests
from mod.mod_elm import AllowedList

if config.OS != "android":
    import tkinter as tk


def trim(st):
    res = "".join(char for char in st if char in string.printable)
    return res.strip()


eculist = None
ecudump = {}  # {'request':'response'}


class CommandQueue(queue.Queue):
    def _init(self, maxsize):
        self.queue = set()

    def _put(self, item):
        self.queue.add(item)

    def _get(self):
        return self.queue.pop()

    def __contains__(self, item):
        with self.mutex:
            return item in self.queue

    def clear(self):
        self.queue.clear()


class DDTECU:
    elm = None  # elm class
    screen = None  # screen class
    cecu = None  # chosen ecu
    ecufname = ""
    requests = {}
    datas = {}
    req4data = {}
    cmd4data = {}
    req4sent = {}
    langmap = {}
    defaultEndian = "Big"
    sentRequests = []
    BaudRate = "500000"
    Multipoint = "1"

    rotaryCommandsQueue = None  # input queue
    rotaryResultsQueue = None  # output queue
    rotaryThread = None
    rotaryRunAlloved = None  # thread Event
    rotaryTerminate = None  # thread Event
    elmAccess = None  # thread Lock object

    def __init__(self, cecu):
        global eculist

        self.elm = 0
        self.cecu = cecu
        self.ecufname = ""
        self.requests = {}
        self.datas = {}
        self.req4data = {}  # requests for reading the data
        self.cmd4data = {}  # requests for writing the data
        self.req4sent = {}  # request-object with 'sent' bytes
        self.langmap = {}
        self.BaudRate = "500000"
        self.Multipoint = "1"

    def __del__(self):
        try:
            del self.elm
            del self.cecu
            del self.ecufname
            del self.requests
            del self.datas
            del self.req4data
            del self.cmd4data
            del self.req4sent
            del self.langmap
            del self.BaudRate
            del self.Multipoint
            del self.rotaryRunAlloved
            del self.rotaryTerminate
            del self.rotaryCommandsQueue
            del self.rotaryResultsQueue
            del self.elmAccess
        except:
            print("Exception in DDTECU __del__")
            pass

    def initRotary(self):
        self.rotaryCommandsQueue = CommandQueue()
        self.rotaryResultsQueue = CommandQueue()

        self.rotaryRunAlloved = threading.Event()
        self.rotaryRunAlloved.set()

        self.rotaryTerminate = threading.Event()
        self.rotaryTerminate.clear()

        self.elmAccess = threading.Lock()

        self.rotaryThread = threading.Thread(target=self.rotary)
        self.rotaryThread.setDaemon(True)
        self.rotaryThread.start()

    def rotary(self):
        """worker for rotary thread
        it makes periodic data read from"""

        while not self.rotaryTerminate.isSet():
            while self.rotaryRunAlloved.isSet():
                if not self.rotaryCommandsQueue.empty():
                    req = self.rotaryCommandsQueue.get_nowait()

                    # 1. get current value from cache
                    prev_rsp = self.elm.getFromCache(req)
                    self.elm.delFromCache(req)

                    # 2. aquire ELM
                    self.elmAccess.acquire()

                    # 3. send request

                    rsp = self.elm.request(req, positive="", cache=True)

                    # 4. relase ELM
                    self.elmAccess.release()

                    if self.rotaryResultsQueue.qsize() < 64:
                        if prev_rsp != rsp or req not in self.sentRequests:
                            self.rotaryResultsQueue.put((req, rsp))

                    if req not in self.sentRequests:
                        self.sentRequests.append(req)

                else:
                    if config.opt_demo:
                        time.sleep(0.1)

        # print "Update thread terminated"

    def putToRotary(self, req):
        self.rotaryCommandsQueue.put(req)
        return ""

    def setELM(self, elm):
        if self.elm != None:
            del self.elm
        if elm != None:
            self.elm = elm

    def setLangMap(self, langmap):
        self.langmap = langmap

    def translate(self, data):
        # get data instance
        if data in list(self.datas.keys()):
            d = self.datas[data]
        else:
            return data

        # find appropriate request r
        if data in list(self.req4data.keys()) and self.req4data[data] in list(
            self.requests.keys()
        ):
            r = self.requests[self.req4data[data]]
        else:
            return data

        sentBytes = r.SentBytes
        startByte = r.ReceivedDI[data].FirstByte
        startBit = r.ReceivedDI[data].BitOffset
        bitLength = d.BitsCount

        if bitLength % 8:
            startBit = 7 - startBit
            if r.ReceivedDI[data].Endian == "Big":
                startBit = 7 - startBit
        else:
            startBit = 0

        key = "%s:%s:%s:%s" % (sentBytes, str(startByte), str(startBit), str(bitLength))

        if key in list(self.langmap.keys()):
            return self.langmap[key]
        else:
            return data

    def scanECU(self):
        global eculist

        # local variables
        vehTypeCode = ""
        Address = ""
        DiagVersion = ""
        Supplier = ""
        Soft = ""
        Version = ""
        hash = ""

        # try to get response on 2180 command
        print("Getting ID from 2180")
        self.clearELMcache()
        IdRsp = self.elm.request(req="2180", positive="61", cache=False)
        print("IdRsp:", IdRsp)

        """      0         1         2         3         4         5         6         7      """
        """      01234567890123456789012345678901234567890123456789012345678901234567890123456"""
        # IdRsp = '61 80 77 01 20 98 43 11 33 36 38 10 09 60 14 44 52 AD 00 14 00 00 81 22 00 00'
        """                           -- --------                ----- -----                  """
        """              DiagVersion--+      |                     |     +--Version           """
        """                        Supplier--+                     +--Soft                    """

        Address = self.cecu["dst"]

        if "vehTypeCode" in list(self.cecu.keys()):
            vehTypeCode = self.cecu["vehTypeCode"]

        if len(IdRsp) > 59:
            DiagVersion = str(int(IdRsp[21:23], 16))
            # if len(DiagVersion)==1 : DiagVersion = '0'+DiagVersion
            Supplier = trim(IdRsp[24:32].replace(" ", ""))
            Supplier = bytes.fromhex(Supplier).decode("utf-8")
            Soft = trim(IdRsp[48:53].replace(" ", ""))
            Version = trim(IdRsp[54:59].replace(" ", ""))
        else:
            print("Getting ID from 22xx")
            self.clearELMcache()

            rule = "replace"
            # rule = 'ignore' may be a bit better in some cases

            # DiagVersion F1A0
            IdRsp_F1A0 = self.elm.request(req="22F1A0", positive="62", cache=False)
            if len(IdRsp_F1A0) > 8 and "NR" not in IdRsp_F1A0:
                DiagVersion = str(int(IdRsp_F1A0[9:11], 16))
            # if len(DiagVersion)==1 : DiagVersion = '0'+DiagVersion

            # Supplier F18A
            IdRsp_F18A = self.elm.request(req="22F18A", positive="62", cache=False)
            if len(IdRsp_F18A) > 8 and "NR" not in IdRsp_F18A:
                Supplier = trim(IdRsp_F18A[9:].replace(" ", ""))
                Supplier = bytes.fromhex(Supplier).decode("utf-8", rule)

            # Soft F194
            IdRsp_F194 = self.elm.request(req="22F194", positive="62", cache=False)
            if len(IdRsp_F194) > 8 and "NR" not in IdRsp_F194:
                Soft = trim(IdRsp_F194[9:].replace(" ", ""))
                Soft = bytes.fromhex(Soft).decode("utf-8", rule)

            # Version F195
            IdRsp_F195 = self.elm.request(req="22F195", positive="62", cache=False)
            if len(IdRsp_F195) > 8 and "NR" not in IdRsp_F195:
                Version = trim(IdRsp_F195[9:].replace(" ", ""))
                Version = bytes.fromhex(Version).decode("utf-8", rule)

        hash = Address + DiagVersion + Supplier + Soft + Version

        print(
            'Address="%s" DiagVersion="%s" Supplier="%s" Soft="%s" Version="%s"'
            % (Address, DiagVersion, Supplier, Soft, Version)
        )

        eculist = ddt_utils.loadECUlist()

        # ddt_utils.searchddtroot()

        if len(config.opt_ddtxml) > 0:
            fname = config.opt_ddtxml
            self.ecufname = config.ddtroot + "/ecus/" + fname
        else:
            problist = ecuSearch(
                vehTypeCode, Address, DiagVersion, Supplier, Soft, Version, eculist
            )

            while 1:
                print("You may enter the file name by yourself or left empty to exit")
                if len(problist) != 1:
                    fname = input("File name:")
                else:
                    fname = input("File name [" + problist[0] + "]:")
                    if len(fname) == 0:
                        fname = problist[0]

                fname = fname.strip()
                if len(fname):
                    self.ecufname = "ecus/" + fname
                    if db_manager.file_in_ddt(self.ecufname):
                        break
                    else:
                        print("No such file :", self.ecufname)
                else:
                    print("Empty file name")
                    return

        self.loadXml()

    def loadXml(self, xmlfile=""):
        if len(xmlfile):
            self.ecufname = xmlfile

        if not db_manager.file_in_ddt(self.ecufname):
            print("No such file:", self.ecufname)
            return

        # Load XML
        tree = et.parse(db_manager.get_file_from_ddt(self.ecufname))
        root = tree.getroot()

        ns = {
            "ns0": "http://www-diag.renault.com/2002/ECU",
            "ns1": "http://www-diag.renault.com/2002/screens",
        }

        # print et.dump(root)

        try:
            funcs = root.findall("ns0:Target/ns0:Function", ns)
            if funcs:
                for fun in funcs:
                    self.Addr = fun.attrib["Address"]
                    if len(self.Addr):
                        self.Addr = hex(int(self.Addr))[2:]
        except:
            self.Addr = None

        cans = root.findall("ns0:Target/ns0:CAN", ns)  # xdoc.findall("CAN")
        if cans:
            for can in cans:
                self.BaudRate = can.attrib["BaudRate"]  # can.attrib["BaudRate")
                self.Multipoint = can.attrib["Multipoint"]  # can.attrib["Multipoint")

        print("Loading requests")
        rq_class = DecuRequests(self.requests, root)
        print("Loading datas")
        dt_class = DecuDatas(self.datas, root)

        for r in list(self.requests.values()):
            self.req4sent[r.SentBytes] = r.Name
            for di in list(r.ReceivedDI.values()):
                if di.Ref or di.Name not in list(self.req4data.keys()):
                    self.req4data[di.Name] = r.Name
            for di in list(r.SentDI.values()):
                if di.Name not in list(self.cmd4data.keys()):
                    self.cmd4data[di.Name] = r.Name

    def saveDump(self):
        """save responses from all 21xx, 22xxxx commands"""

        xmlname = self.ecufname.split("/")[-1]
        if xmlname.upper().endswith(".XML"):
            xmlname = xmlname[:-4]

        dumpname = "./dumps/" + str(int(time.time())) + "_" + xmlname + ".txt"
        df = open(dumpname, "wt")

        self.elm.clear_cache()

        im = " from " + str(len(list(self.requests.keys())))
        i = 0
        for request in list(self.requests.values()):
            i = i + 1
            print("\r\t\t\t\r", str(i) + im, end=" ")
            sys.stdout.flush()
            if request.SentBytes[:2] in AllowedList + ["17", "19"]:
                if request.SentBytes[:2] == "19" and request.SentBytes[:2] != "1902":
                    continue
                if request.SentBytes[:2] == "22" and len(request.SentBytes) < 6:
                    continue
                pos = chr(ord(request.SentBytes[0]) + 4) + request.SentBytes[1]
                rsp = self.elm.request(request.SentBytes, pos, False)
                if ":" in rsp:
                    continue
                df.write("%s:%s\n" % (request.SentBytes, rsp))

        print()
        df.close()

    def loadDump(self, dumpname=""):
        """load saved dump for demo mode"""

        global ecudump

        ecudump = {}

        xmlname = self.ecufname.split("/")[-1]
        if xmlname.upper().endswith(".XML"):
            xmlname = xmlname[:-4]

        if len(dumpname) == 0 or not os.path.exists(dumpname):
            flist = []

            for root, dirs, files in os.walk("./dumps"):
                for f in files:
                    if ("_" + xmlname + ".") in f:
                        flist.append(f)

            if len(flist) == 0:
                return
            flist.sort()
            dumpname = os.path.join("./dumps/", flist[-1])

        # debug
        print("Dump name:", dumpname)

        config.dumpName = dumpname
        df = open(dumpname, "rt")
        lines = df.readlines()
        df.close()

        for l in lines:
            l = l.strip().replace("\n", "")
            if l.count(":") == 1:
                req, rsp = l.split(":")
                ecudump[req] = rsp

        self.elm.setDump(ecudump)

    def clearELMcache(self):
        self.elm.clear_cache()
        self.sentRequests = []

    def elmRequest(self, req, delay="0", positive="", cache=True):
        """dispath requests to elm"""
        if req.startswith("10"):
            self.elm.startSession = req

        if type(delay) is str:
            delay = int(delay)

        # strange definition of delays in ddt database
        if delay > 0 and delay < 1000:
            delay = 1000

        self.elmAccess.acquire()
        rsp = self.elm.request(req, positive, cache, serviceDelay=delay)
        self.elmAccess.release()

        # log this request to ddt log
        if self.screen != None and (not cache or req not in self.sentRequests):
            tmstr = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            self.screen.addToLog(tmstr + ">" + req + "  Rcvd:" + rsp)

        # cache it
        if cache and req not in self.sentRequests:
            self.sentRequests.append(req)

        return rsp

    def getValue(self, data, auto=True, request=None, response=None):
        """extract and format value"""

        # debug
        # print 'getValue entry point : ', '\n\tdata:', data, '\n\tauto:',  auto, '\n\treq:', request, '\n\tres:', response

        # first get hex value
        hv = self.getHex(data, auto, request, response)

        if hv == config.none_val:
            return config.none_val

        # get data instance
        if data in list(self.datas.keys()):
            d = self.datas[data]
        else:
            return hv
            # return 'NoDatasItem'

        # list
        if len(list(d.List.keys())):
            listIndex = int(hv, 16)
            if listIndex in list(d.List.keys()):
                hv = hex(listIndex)[2:]
                return hv + ":" + d.List[listIndex]
            else:
                return hv

        # scaled
        if d.Scaled:
            # conver to int
            p = int(hv, 16)
            # if it negative signed value
            if d.signed and p > (2 ** (d.BitsCount - 1) - 1):
                p = p - 2**d.BitsCount
            # calculate the formula
            res = (p * float(d.Step) + float(d.Offset)) / float(d.DivideBy)
            # format the result
            if len(d.Format) and "." in d.Format:
                acc = len(d.Format.split(".")[1])
                fmt = "%." + str(acc) + "f"
                res = fmt % (res)
            res = str(res)
            # remove '.0' from the end
            if res.endswith(".0"):
                res = res[:-2]
            # add units and return
            return res + " " + d.Unit

        # just bytes
        if d.BytesASCII:
            res = bytes.fromhex(hv).decode("utf-8", "replace")

            if not all(c in string.printable for c in res):
                res = hv

            # debug
            # print '>>>>>>>>>>',hv
            # print '#'*50
            # for line in traceback.format_stack():
            #  print(line.strip())

            return res

        return hv

    def getHex(self, data, auto=True, request=None, response=None):
        """extract hex value from response"""

        # debug
        # print 'getHex entry point : ', '\n\tdata:', data, '\n\tauto:',  auto, '\n\treq:', request, '\n\tres:', response

        # d will be a data instace
        if data in list(self.datas.keys()):
            d = self.datas[data]
        else:
            if data not in list(
                self.requests.keys()
            ):  # special case when no DataName in Display
                return config.none_val

        # find appropriate request r
        if request == None:
            if data in list(self.req4data.keys()) and self.req4data[data] in list(
                self.requests.keys()
            ):
                r = self.requests[self.req4data[data]]
            else:
                if data in list(
                    self.requests.keys()
                ):  # special case when no DataName in Display
                    r = self.requests[data]
                else:
                    return config.none_val
        else:
            r = request

        # check if command only for manual send or require parameters
        if (
            auto
            and (r.ManuelSend or len(list(r.SentDI.keys())) > 0)
            and data not in list(r.SentDI.keys())
        ):
            return config.none_val

        # protect not expert mode
        if (
            (r.SentBytes[:2] not in AllowedList)
            and not config.opt_exp
            and data not in list(r.SentDI.keys())
        ):
            return config.none_val

        # if response not defined as an argument
        if response == None:
            # send new request or get response from cache
            resp = self.elmRequest(r.SentBytes)
        else:
            resp = response

        if data not in list(
            self.datas.keys()
        ):  # special case when no DataName in Display
            return resp

        # format and check the response
        resp = resp.strip().replace(" ", "")
        if not all(c in string.hexdigits for c in resp):
            resp = ""
        resp = " ".join(a + b for a, b in zip(resp[::2], resp[1::2]))

        # prepare parameters for extraction
        if data in list(r.ReceivedDI.keys()):
            littleEndian = True if r.ReceivedDI[data].Endian == "Little" else False
            sb = r.ReceivedDI[data].FirstByte - 1
            sbit = r.ReceivedDI[data].BitOffset
        else:
            littleEndian = True if r.SentDI[data].Endian == "Little" else False
            sb = r.SentDI[data].FirstByte - 1
            sbit = r.SentDI[data].BitOffset

        bits = d.BitsCount
        bytes = (bits + sbit - 1) // 8 + 1
        if littleEndian:
            rshift = sbit
        else:
            rshift = ((bytes + 1) * 8 - (bits + sbit)) % 8

        # check length of response
        if (sb * 3 + bytes * 3 - 1) > (len(resp)):
            return config.none_val

        # extract hex
        hexval = resp[sb * 3 : (sb + bytes) * 3 - 1]
        hexval = hexval.replace(" ", "")

        # shift and mask
        val = (int(hexval, 16) >> int(rshift)) & (2**bits - 1)

        # format result
        hexval = hex(val)[2:]
        # remove 'L'
        if hexval[-1:].upper() == "L":
            hexval = hexval[:-1]
        # add left zero if need
        if len(hexval) % 2:
            hexval = "0" + hexval

        # check bytescount
        if len(hexval) / 2 < d.BytesCount:
            hexval = "00" * (d.BytesCount - len(hexval) // 2) + hexval
            # debug
            # print '#', d.BytesCount, ':', hexval

        # revert byte order if little endian
        if littleEndian:
            a = hexval
            b = ""
            if not len(a) % 2:
                for i in range(0, len(a), 2):
                    b = a[i : i + 2] + b
                hexval = b

        return hexval

    def getParamExtr(self, parName, iValues, dValues):
        result = "\nTerminal command hint\n\n"

        # get DataItem instance
        if parName not in list(self.datas.keys()):
            return "Error finding datas"

        # get data
        d = self.datas[parName]

        # finding read request
        rr = None
        for r in list(self.requests.values()):
            if parName in list(r.ReceivedDI.keys()) and r.SentBytes[:2] in ["21", "22"]:
                rr = r
                break

        rcm = rr.SentBytes[:2]
        lid = r.SentBytes[2:].upper()

        if rcm == "21":
            wcm = "3B" + lid
        else:
            wcm = "2E" + lid

        # finding write request
        wr = None
        for r in list(self.requests.values()):
            if parName in list(r.SentDI.keys()) and r.SentBytes.upper().startswith(wcm):
                wr = r
                break

        if rr == None:
            return "Didn't find command for DataRead"

        if wr == None:
            result += "Didn't find command for DataWrite\n\n"

        rdi = rr.ReceivedDI[parName]
        if wr != None:
            sdi = wr.SentDI[parName]

            if rr.MinBytes != len(wr.SentBytes) // 2:
                result += "Commands for DataRead and DataWrite have different length"

            if (
                rdi.FirstByte != sdi.FirstByte
                or rdi.BitOffset != sdi.BitOffset
                or rdi.Endian != sdi.Endian
            ):
                result += "Data not in the same place in DataRead and DataWrite"

        # get value
        if d.Name in list(iValues.keys()):
            value = iValues[d.Name].get().strip()
        elif d.Name in list(dValues.keys()):
            value = dValues[d.Name].get().strip()
        else:
            value = 0
        value = self.getValueFromInput(d, value)
        # value = self.getHex(d.Name, value)

        # prepare parameters for extraction
        littleEndian = True if rdi.Endian == "Little" else False
        sb = rdi.FirstByte - 1
        bits = d.BitsCount
        sbit = rdi.BitOffset
        bytes = (bits + sbit - 1) // 8 + 1
        if littleEndian:
            lshift = sbit
        else:
            lshift = ((bytes + 1) * 8 - (bits + sbit)) % 8

        # shift value on bit offset
        try:
            val = int(value, 16)
        except:
            return 'ERROR: Wrong HEX value in parametr (%s) : "%s"' % (d.Name, value)
        val = (val & (2**bits - 1)) << lshift
        value = hex(val)[2:]
        # remove 'L'
        if value[-1:].upper() == "L":
            value = value[:-1]
        # add left zero if need
        if len(value) % 2:
            value = "0" + value

        # check hex
        if value.upper().startswith("0X"):
            value = value[2:]
        value = value.zfill(bytes * 2).upper()
        if not all(c in string.hexdigits for c in value) and len(value) == bytes * 2:
            return "ERROR: Wrong value in parametr:%s (it should have %d bytes)" % (
                d.Name,
                d.BytesCount,
            )

        mask = (2**bits - 1) << lshift
        # remove '0x'
        hmask = hex(mask)[2:].upper()
        # remove 'L'
        if hmask[-1:].upper() == "L":
            hmask = hmask[:-1]
        hmask = hmask[-bytes * 2 :].zfill(bytes * 2)

        func_params = (
            " "
            + lid
            + " "
            + str(rr.MinBytes)
            + " "
            + str(rdi.FirstByte)
            + " "
            + hmask
            + " "
            + value
            + "\n"
        )
        func_params_xor = (
            " "
            + lid
            + " "
            + str(rr.MinBytes)
            + " "
            + str(rdi.FirstByte)
            + " "
            + hmask
            + " "
            + hmask
            + "\n"
        )

        for f in ["exit_if", "exit_if_not"]:
            result += f + func_params
        if wr != None:
            result += "set_bits" + func_params
            result += "xor_bits" + func_params_xor

        return result

    def getValueFromInput(self, d, value):
        # list
        if len(list(d.List.keys())) and ":" in value:
            value = value.split(":")[0]

        # scaled
        if d.Scaled:
            # if there is units then remove them
            if " " in value:
                value = value.split(" ")[0]
            # check 0x
            if value.upper().startswith("0X"):
                value = value[2:]
            else:  # calculate reverse formula
                if not all(
                    (
                        c in string.digits
                        or c == "."
                        or c == ","
                        or c == "-"
                        or c == "e"
                        or c == "E"
                    )
                    for c in value
                ):
                    return (
                        "ERROR: Wrong value in parametr:%s (it should have %d bytes), be decimal or starts with 0x for hex"
                        % (d.Name, d.BytesCount)
                    )
                flv = (float(value) * float(d.DivideBy) - float(d.Offset)) / float(
                    d.Step
                )
                value = hex(int(flv))

        # ascii
        if d.BytesASCII:
            hst = ""
            if len(value) < (d.BitsCount // 8):
                value += " " * (d.BitsCount // 8 - len(value))
            for c in value:
                hst = hst + hex(ord(c))[2:].zfill(2)
            value = hst

        return value

    def packValues(self, requestName, iValues):
        """pack values from iValues to command"""
        """ return string                                                  """
        """ if cathe the error then return string begining with ERROR: word"""
        """ else return command in hex                                     """

        # get request instance
        r = self.requests[requestName]

        # get command pattern
        cmdPatt = r.SentBytes

        # for every DataItem
        for sdi in list(r.SentDI.values()):

            # get DataItem instance
            d = self.datas[sdi.Name]
            if d.Name not in list(iValues.keys()):
                print("WARNING: not defined value:%s" % d.Name)
                continue
                # return 'ERROR: not defined value:%s' % d.Name

            # get value
            value = iValues[d.Name].get().strip()
            value = self.getValueFromInput(d, value)

            ## list
            # if len(d.List.keys()) and ':' in value:
            #  value = value.split(':')[0]
            #
            ## scaled
            # if d.Scaled:
            #  #if there is units then remove them
            #  if ' ' in value:
            #    value = value.split(' ')[0]
            #  #check 0x
            #  if value.upper().startswith('0X'):
            #    value = value[2:]
            #  else:  #calculate reverse formula
            #    if not all((c in string.digits or c=='.' or c==',' or c=='-' or c=='e' or c=='E') for c in value):
            #      return 'ERROR: Wrong value in parametr:%s (it should have %d bytes), be decimal or starts with 0x for hex' % (d.Name, d.BytesCount)
            #    flv = (float( value )*float(d.DivideBy) - float(d.Offset))/float(d.Step)
            #    value = hex(int(flv))
            #
            ## ascii
            # if d.BytesASCII:
            #  hst = ''
            #  for c in value:
            #    hst = hst + hex(ord(c))[2:].zfill(2)
            #  value = hst

            # prepare parameters for extraction
            littleEndian = True if sdi.Endian == "Little" else False
            sb = sdi.FirstByte - 1
            bits = d.BitsCount
            sbit = sdi.BitOffset
            bytes = (bits + sbit - 1) // 8 + 1
            if littleEndian:
                lshift = sbit
            else:
                lshift = ((bytes + 1) * 8 - (bits + sbit)) % 8

            # shift value on bit offset
            try:
                val = int(value, 16)
            except:
                return 'ERROR: Wrong HEX value in parametr (%s) : "%s"' % (
                    d.Name,
                    value,
                )
            val = (val & (2**bits - 1)) << lshift
            value = hex(val)[2:]
            # remove 'L'
            if value[-1:].upper() == "L":
                value = value[:-1]
            # add left zero if need
            if len(value) % 2:
                value = "0" + value

            # check hex
            if value.upper().startswith("0X"):
                value = value[2:]
            value = value.zfill(bytes * 2).upper()
            if (
                not all(c in string.hexdigits for c in value)
                and len(value) == bytes * 2
            ):
                return "ERROR: Wrong value in parametr:%s (it should have %d bytes)" % (
                    d.Name,
                    d.BytesCount,
                )

            # prepare base and mask
            base = cmdPatt[sb * 2 : (sb + bytes) * 2]
            binbase = int(base, 16)
            binvalue = int(value, 16)
            mask = (2**bits - 1) << lshift

            # shift and mask
            binvalue = binbase ^ (mask & binbase) | binvalue

            # remove '0x'
            value = hex(binvalue)[2:].upper()
            # remove 'L'
            if value[-1:].upper() == "L":
                value = value[:-1]
            value = value[-bytes * 2 :].zfill(bytes * 2)

            cmdPatt = cmdPatt[0 : sb * 2] + value + cmdPatt[(sb + bytes) * 2 :]

        return cmdPatt

    def getValueForConfig_second_cmd(self, d, first_cmd):
        # sometimes the same parameter may be accesible thru 2E and 3B

        res = "ERROR"
        rcmd = ""
        for c in list(self.requests.keys()):
            if c == first_cmd:
                continue
            if d in list(self.requests[c].ReceivedDI.keys()):
                rcmd = c
                break

        if rcmd == "":
            # debug
            # print res, d, self.req4data.keys ()
            return "ERROR"

        if self.datas[d].BytesASCII:
            res = self.getValue(d, request=self.requests[rcmd])
        else:
            gh = self.getHex(d, request=self.requests[rcmd])
            if gh != config.none_val:
                res = "0x" + gh
            else:
                res = gh

        # debug
        # print 'getValueForConfig_second_cmd', d, self.requests[rcmd].SentBytes, res

        return res

    def getValueForConfig(self, d):
        res = "ERROR"

        if d in list(self.req4data.keys()):
            rcmd = self.req4data[d]
        else:
            return res

        if self.datas[d].BytesASCII:
            res = self.getValue(d, request=self.requests[rcmd])
        else:
            gh = self.getHex(d, request=self.requests[rcmd])
            if gh != config.none_val:
                res = "0x" + gh
            else:
                res = gh

        if res == config.none_val:  # try to find second command
            res = self.getValueForConfig_second_cmd(d, rcmd)

        return res

    def makeConf(self, indump=False, annotate=False):
        """try to make config (3B,2E) from current values
        return string list"""

        config = []
        conf_v = {}
        config_ann = []

        # check for duplication
        all_did = set()
        dup_did = set()

        for r in sorted(list(self.requests.values()), key=lambda x: x.SentBytes):
            if r.SentBytes[0:2].upper() == "3B":
                if r.SentBytes[2:4].upper() in all_did:
                    dup_did.add(r.SentBytes[2:4].upper())
                all_did.add(r.SentBytes[2:4].upper())
            if r.SentBytes[0:2].upper() == "2E":
                if r.SentBytes[2:6].upper() in all_did:
                    dup_did.add(r.SentBytes[2:6].upper())
                all_did.add(r.SentBytes[2:6].upper())

        if len(dup_did) > 0:
            config_ann.append("### WARNING " * 3 + "###")
            config_ann.append("# Commands have more then one parameter set")
            # second pass
            for r in sorted(list(self.requests.values()), key=lambda x: x.SentBytes):
                if (
                    r.SentBytes[0:2].upper() == "3B"
                    and r.SentBytes[2:4].upper() in dup_did
                ):
                    config_ann.append("# " + r.SentBytes)
                if (
                    r.SentBytes[0:2].upper() == "2E"
                    and r.SentBytes[2:6].upper() in dup_did
                ):
                    config_ann.append("# " + r.SentBytes)
            config_ann.append("### WARNING " * 3 + "###")
            config_ann.append("")

        sentValues = {}
        # for r in self.requests.values ():
        for r in sorted(list(self.requests.values()), key=lambda x: x.SentBytes):
            if (
                not (
                    r.SentBytes[0:2].upper() == "3B" or r.SentBytes[0:2].upper() == "2E"
                )
                or len(r.SentDI) == 0
            ):
                continue

            if annotate:
                config_ann.append("#" * 60)
                config_ann.append("# " + r.Name)

            # debug
            # print '\n','#'*10,r.SentBytes, r.Name

            # update all variables from SentDI
            sentValues.clear()
            for di in sorted(
                list(r.SentDI.values()), key=lambda x: x.FirstByte * 8 + x.BitOffset
            ):
                d = di.Name

                if indump:
                    if d in list(self.req4data.keys()):
                        first_cmd = self.req4data[d]
                        i_r_cmd = self.requests[self.req4data[d]].SentBytes
                        if i_r_cmd not in list(self.elm.ecudump.keys()) or (
                            i_r_cmd in list(self.elm.ecudump.keys())
                            and self.elm.ecudump[i_r_cmd] == ""
                        ):
                            # try to find second
                            second_is = False
                            for c in list(self.requests.keys()):
                                if c == first_cmd:
                                    continue
                                if d in list(self.requests[c].ReceivedDI.keys()):
                                    # self.req4data[d] = c  # may be removed
                                    second_is = True
                                    break
                            if not second_is:
                                continue

                val = self.getValueForConfig(d)

                if "ERROR" in val:
                    continue

                sentValues[d] = tk.StringVar()
                sentValues[d].set(val)
                conf_v[d] = val

                if annotate:  # and config.opt_verbose:
                    val_ann = self.getValue(d)
                    config_ann.append("##     " + d + " = " + val_ann)

            if len(sentValues) != len(r.SentDI):
                # check that there is two params and the first argument is a list
                if len(r.SentDI) == 2 and r.SentBytes[0:2].upper() == "3B":
                    SDIs = sorted(
                        list(r.SentDI.values()),
                        key=operator.attrgetter("FirstByte", "BitOffset"),
                    )
                    if len(self.datas[SDIs[0].Name].List) > 0:
                        for list_el_key in list(self.datas[SDIs[0].Name].List.keys()):
                            list_el_val = self.datas[SDIs[0].Name].List[list_el_key]
                            found = False
                            fdk = ""
                            for datas_keys in list(self.datas.keys()):
                                if datas_keys in list_el_val:
                                    if len(datas_keys) > len(fdk):
                                        fdk = datas_keys
                                    found = True
                            if found:
                                # debug
                                # print '>>>>>>>>', fdk, '(', hex(list_el_key), ') =',self.getValueForConfig( fdk )
                                if SDIs[0].Name not in list(sentValues.keys()):
                                    sentValues[SDIs[0].Name] = tk.StringVar()
                                sentValues[SDIs[0].Name].set(hex(list_el_key))
                                if SDIs[1].Name not in list(sentValues.keys()):
                                    sentValues[SDIs[1].Name] = tk.StringVar()
                                sentValues[SDIs[1].Name].set(
                                    self.getValueForConfig(fdk)
                                )
                                conf_v[SDIs[1].Name] = self.getValueForConfig(fdk)
                                sendCmd = self.packValues(r.Name, sentValues)
                                config.append(sendCmd)
                                if annotate:
                                    config_ann.append(sendCmd)
                                    config_ann.append("")
                continue
            else:
                sendCmd = self.packValues(r.Name, sentValues)
                if "ERROR" in sendCmd:
                    continue
                config.append(sendCmd)
                if annotate:
                    config_ann.append(sendCmd)
                    config_ann.append("")

        sentValues.clear()

        # debug
        # print config
        # print '*'*50
        # print conf_v
        # print '*'*50

        if annotate:
            return config_ann, conf_v
        else:
            return config, conf_v

    def bukva(self, bt, l, sign=False):
        S1 = chr((bt - l) % 26 + ord("A"))
        ex = int(bt - l) // 26
        if ex:
            S2 = chr((ex - 1) % 26 + ord("A"))
            S1 = S2 + S1
        if sign:
            S1 = "signed(" + S1 + ")"
        return S1

    def get_ddt_pid(
        self,
        l_Scaled,
        l_BitsCount,
        l_Endian,
        l_FirstByte,
        l_BitOffset,
        l_signed,
        l_Step,
        l_Offset,
        l_DivideBy,
        l_SentBytes,
    ):
        # print l_Scaled, l_BitsCount, l_Endian, l_FirstByte, l_BitOffset

        l = len(l_SentBytes) // 2 + 1
        sb = int(l_FirstByte)
        bits = int(l_BitsCount)
        sbit = int(l_BitOffset)
        bytes = (bits + sbit - 1) // 8 + 1
        rshift = ((bytes + 1) * 8 - (bits + sbit)) % 8
        mask = str(2**bits - 1)
        sign = l_signed

        equ = self.bukva(sb, l, sign)

        if l_Endian.upper() == "BIG":
            if bytes == 2:
                equ = self.bukva(sb, l, sign) + "*256+" + self.bukva(sb + 1, l)
            if bytes == 3:
                equ = (
                    self.bukva(sb, l, sign)
                    + "*65536+"
                    + self.bukva(sb + 1, l)
                    + "*256+"
                    + self.bukva(sb + 2, l)
                )
            if bytes == 4:
                equ = (
                    self.bukva(sb, l, sign)
                    + "*16777216+"
                    + self.bukva(sb + 1, l)
                    + "*65536+"
                    + self.bukva(sb + 2, l)
                    + "*256+"
                    + self.bukva(sb + 3, l)
                )
        else:
            if bytes == 2:
                equ = self.bukva(sb + 1, l, sign) + "*256+" + self.bukva(sb, l)
            if bytes == 3:
                equ = (
                    self.bukva(sb + 2, l, sign)
                    + "*65536+"
                    + self.bukva(sb + 1, l)
                    + "*256+"
                    + self.bukva(sb, l)
                )
            if bytes == 4:
                equ = (
                    self.bukva(sb + 3, l, sign)
                    + "*16777216+"
                    + self.bukva(sb + 2, l)
                    + "*65536+"
                    + self.bukva(sb + 1, l)
                    + "*256+"
                    + self.bukva(sb, l)
                )

        if len(equ) > 2:
            if equ[0] == "(" and equ[-1] == ")":
                pass
            else:
                equ = "(" + equ + ")"

        if bits % 8:
            smask = "&" + mask
        else:
            smask = ""

        if bits == 1:
            equ = "{" + equ + ":" + str(rshift) + "}"
        elif rshift == 0:
            equ = equ + smask
        else:
            equ = "(" + equ + ">" + str(rshift) + ")" + smask

        if len(equ) > 2:
            if (equ[0] == "(" and equ[-1] == ")") or (equ[0] == "{" and equ[-1] == "}"):
                pass
            else:
                equ = "(" + equ + ")"

        if l_Scaled:
            if l_Step != 1:
                equ = equ + "*" + str(l_Step)
            if l_Offset != 0:
                if l_Offset > 0:
                    equ = equ + "+" + str(l_Offset)
                else:
                    equ = equ + str(l_Offset)
                if l_DivideBy != 1:
                    equ = "(" + equ + ")"
            if l_DivideBy != 1:
                equ = equ + "/" + str(l_DivideBy)

        return equ


def minDist(a, b):
    """calculate distance between strings"""
    """ a - readen value                   """
    """ b - pattern from eculist           """

    d = 0
    if a == b:
        return d

    try:
        d = abs(int(a, 16) - int(b, 16))
        return d
    except:
        d = 0

    l = min(len(a), len(b))
    for i in range(0, l):
        if b[i] != "?":
            d = d + abs(ord(a[i]) - ord(b[i]))

    return d


def distance(a, b):
    """calculate distance between strings"""
    """ normalized to length of string     """
    """ a - readen value                   """
    """ b - pattern from eculist           """

    d = 0

    # align length
    if len(a) < len(b):
        a = a + " " * (len(b) - len(a))
    else:
        b = b + " " * (len(a) - len(b))

    # humming distance
    l = len(a)
    for i in range(0, l):
        if b[i] != "?" and ord(a[i]) != ord(b[i]):
            d = d + 1

    # normalize to length of string
    if d:
        d = d / l

    return d


def AutoIdents_distance(DiagVersion, Supplier, Soft, Version, ai):
    # normalize supplier in such cases
    # DiagVersion="12" Supplier="746" Soft="2470" Version="A600"
    # DiagVersion="12" Supplier="39324d" Soft="0052" Version="0400"
    try:
        if (
            len(ai["Supplier"]) == 6
            and len(ai["Soft"]) == 4
            and len(ai["Version"]) == 4
        ):
            ai["Supplier"] = bytes.fromhex(ai["Supplier"]).decode("utf-8")
    except:
        # catch not hex supplier with len 6
        pass

    d = distance(DiagVersion, ai["DiagVersion"]) * 0.35
    d = d + distance(Supplier, ai["Supplier"]) * 0.35
    d = d + distance(Soft, ai["Soft"]) * 0.15
    d = d + distance(Version, ai["Version"]) * 0.15

    return round(d, 4)


def ecuSearch(
    vehTypeCode, Address, DiagVersion, Supplier, Soft, Version, el, interactive=True
):

    # fix address problem for Nav
    if Address == "57":
        Address = "58"

    if Address not in list(el.keys()):
        return []

    ela = el[Address]
    if interactive:
        print(Address, "#", ela["FuncName"])

    t = ela["targets"]
    cand = {}
    min = 0xFFFFFFFF
    kOther = ""
    minOther = 0xFFFFFFFF

    for k in list(t.keys()):
        for ai in t[k]["AutoIdents"]:
            dist = AutoIdents_distance(DiagVersion, Supplier, Soft, Version, ai)

            if vehTypeCode.upper() in t[k]["Projects"] or dist == 0:
                if k not in list(cand.keys()):
                    cand[k] = 0xFFFFFFFF
                if dist < cand[k]:
                    cand[k] = dist
                if dist < min:
                    min = dist
            else:
                if dist < minOther:
                    minOther = dist
                    kOther = k

    if interactive:
        print("#" * 40)
        for k in list(cand.keys()):
            print("%7s - %s" % (cand[k], k))
            if cand[k] > min:
                del cand[k]
        print("#" * 40)

    if len(cand) == 0 and kOther != "":
        cand[kOther] = minOther

    return list(dict(sorted(cand.items(), key=lambda x: x[1])).keys())
