#!/usr/bin/env python3
"""
   module contains class for working with ELM327
   version: 010922
"""
import os
import re
import socket
import string
import sys
import threading
import time
from collections import OrderedDict
from datetime import datetime

import config
import serial
from serial.tools import list_ports

# List of commands which may require opening another Developer session (option --dev)
DEV_LIST = ["27", "28", "2E", "30", "31", "32", "34", "35", "36", "37", "3B", "3D"]

# List of commands allowed in any mode
ALLOWED_LIST = ["12", "19", "1A", "21", "22", "23"]

# Max frame burst for Flow Control
MAX_BURST = 0x7

#  Functional_2_CAN address translation tables for Renault cars
SNAT = {
    "01": "760",
    "02": "724",
    "04": "762",
    "06": "791",
    "07": "771",
    "08": "778",
    "09": "7EB",
    "0D": "775",
    "0E": "76E",
    "0F": "770",
    "11": "7C9",
    "12": "7C3",
    "13": "732",
    "1A": "731",
    "1B": "7AC",
    "1C": "76B",
    "1E": "768",
    "23": "773",
    "24": "77D",
    "25": "700",
    "26": "765",
    "27": "76D",
    "28": "7D7",
    "29": "764",
    "2A": "76F",
    "2B": "735",
    "2C": "772",
    "2E": "7BC",
    "2F": "76C",
    "32": "776",
    "3A": "7D2",
    "3C": "7DB",
    "40": "727",
    "46": "7CF",
    "47": "7A8",
    "4D": "7BD",
    "50": "738",
    "51": "763",
    "57": "767",
    "58": "767",
    "59": "734",
    "5B": "7A5",
    "5D": "18DAF25D",
    "60": "18DAF160",
    "61": "7BA",
    "62": "7DD",
    "63": "73E",
    "64": "7D5",
    "66": "739",
    "67": "793",
    "68": "77E",
    "6B": "7B5",
    "6E": "7E9",
    "77": "7DA",
    "78": "7BD",
    "79": "7EA",
    "7A": "7E8",
    "7C": "77C",
    "81": "761",
    "82": "7AD",
    "86": "7A2",
    "87": "7A0",
    "91": "7ED",
    "93": "7BB",
    "95": "7EC",
    "97": "7C8",
    "A1": "76C",
    "A5": "725",
    "A6": "726",
    "A7": "733",
    "A8": "7B6",
    "C0": "7B9",
    "D1": "7EE",
    "D2": "18DAF1D2",
    "D3": "7EE",
    "DE": "69C",
    "DF": "5C1",
    "E0": "58B",
    "E1": "5BA",
    "E2": "5BB",
    "E3": "4A7",
    "E4": "757",
    "E6": "484",
    "E7": "7EC",
    "E8": "5C4",
    "E9": "762",
    "EA": "4B3",
    "EB": "5B8",
    "EC": "5B7",
    "ED": "704",
    "F7": "736",
    "F8": "737",
    "FA": "77B",
    "FD": "76F",
    "FE": "76C",
    "FF": "7D0",
}

DNAT = {
    "01": "740",
    "02": "704",
    "04": "742",
    "06": "790",
    "07": "751",
    "08": "758",
    "09": "7E3",
    "0D": "755",
    "0E": "74E",
    "0F": "750",
    "11": "7C3",
    "12": "7C9",
    "13": "712",
    "1A": "711",
    "1B": "7A4",
    "1C": "74B",
    "1E": "748",
    "23": "753",
    "24": "75D",
    "25": "70C",
    "26": "745",
    "27": "74D",
    "28": "78A",
    "29": "744",
    "2A": "74F",
    "2B": "723",
    "2C": "752",
    "2E": "79C",
    "2F": "74C",
    "32": "756",
    "3A": "7D6",
    "3C": "7D9",
    "40": "707",
    "46": "7CD",
    "47": "788",
    "4D": "79D",
    "50": "718",
    "51": "743",
    "57": "747",
    "58": "747",
    "59": "714",
    "5B": "785",
    "5D": "18DA5DF2",
    "60": "18DA60F1",
    "61": "7B7",
    "62": "7DC",
    "63": "73D",
    "64": "7D4",
    "66": "719",
    "67": "792",
    "68": "75A",
    "6B": "795",
    "6E": "7E1",
    "77": "7CA",
    "78": "79D",
    "79": "7E2",
    "7A": "7E0",
    "7C": "75C",
    "81": "73F",
    "82": "7AA",
    "86": "782",
    "87": "780",
    "91": "7E5",
    "93": "79B",
    "95": "7E4",
    "97": "7D8",
    "A1": "74C",
    "A5": "705",
    "A6": "706",
    "A7": "713",
    "A8": "796",
    "C0": "799",
    "D1": "7E6",
    "D2": "18DAD2F1",
    "D3": "7E6",
    "DE": "6BC",
    "DF": "641",
    "E0": "60B",
    "E1": "63A",
    "E2": "63B",
    "E3": "73A",
    "E4": "74F",
    "E6": "622",
    "E7": "7E4",
    "E8": "644",
    "E9": "742",
    "EA": "79A",
    "EB": "638",
    "EC": "637",
    "ED": "714",
    "F7": "716",
    "F8": "717",
    "FA": "75B",
    "FD": "74F",
    "FE": "74C",
    "FF": "7D0",
}

# Code snippet from https://github.com/rbei-etas/busmaster
# Negative responses
NEGATIVE_RESPONSES = {
    "10": "NR: General Reject",
    "11": "NR: Service Not Supported",
    "12": "NR: SubFunction Not Supported",
    "13": "NR: Incorrect Message Length Or Invalid Format",
    "21": "NR: Busy Repeat Request",
    "22": "NR: Conditions Not Correct Or Request Sequence Error",
    "23": "NR: Routine Not Complete",
    "24": "NR: Request Sequence Error",
    "31": "NR: Request Out Of Range",
    "33": "NR: Security Access Denied- Security Access Requested  ",
    "35": "NR: Invalid Key",
    "36": "NR: Exceed Number Of Attempts",
    "37": "NR: Required Time Delay Not Expired",
    "40": "NR: Download not accepted",
    "41": "NR: Improper download type",
    "42": "NR: Can not download to specified address",
    "43": "NR: Can not download number of bytes requested",
    "50": "NR: Upload not accepted",
    "51": "NR: Improper upload type",
    "52": "NR: Can not upload from specified address",
    "53": "NR: Can not upload number of bytes requested",
    "70": "NR: Upload Download NotAccepted",
    "71": "NR: Transfer Data Suspended",
    "72": "NR: General Programming Failure",
    "73": "NR: Wrong Block Sequence Counter",
    "74": "NR: Illegal Address In Block Transfer",
    "75": "NR: Illegal Byte Count In Block Transfer",
    "76": "NR: Illegal Block Transfer Type",
    "77": "NR: Block Transfer Data Checksum Error",
    "78": "NR: Request Correctly Received-Response Pending",
    "79": "NR: Incorrect ByteCount During Block Transfer",
    "7E": "NR: SubFunction Not Supported In Active Session",
    "7F": "NR: Service Not Supported In Active Session",
    "80": "NR: Service Not Supported In Active Diagnostic Mode",
    "81": "NR: Rpm Too High",
    "82": "NR: Rpm Too Low",
    "83": "NR: Engine Is Running",
    "84": "NR: Engine Is Not Running",
    "85": "NR: Engine RunTime TooLow",
    "86": "NR: Temperature Too High",
    "87": "NR: Temperature Too Low",
    "88": "NR: Vehicle Speed Too High",
    "89": "NR: Vehicle Speed Too Low",
    "8A": "NR: Throttle/Pedal Too High",
    "8B": "NR: Throttle/Pedal Too Low",
    "8C": "NR: Transmission Range In Neutral",
    "8D": "NR: Transmission Range In Gear",
    "8F": "NR: Brake Switch(es)NotClosed (brake pedal not pressed or not applied)",
    "90": "NR: Shifter Lever Not In Park ",
    "91": "NR: Torque Converter Clutch Locked",
    "92": "NR: Voltage Too High",
    "93": "NR: Voltage Too Low",
}


def log_timestamp_str():
    return datetime.now().strftime("%x %H:%M:%S.%f")[:21].ljust(21, "0")


def pyren_time():
    if (sys.version_info[0] * 100 + sys.version_info[1]) > 306:
        return time.perf_counter_ns() / 1e9
    return time.time()


# noinspection PyBroadException,PyUnresolvedReferences
class Port:
    """This is a serial port or a TCP-connection
    if portName looks like a 192.168.0.10:35000
    then it is Wi-Fi and we should open tcp connection
    else try to open serial port
    """

    port_type = 0  # 0-serial 1-tcp/bt 2-androidBlueTooth
    ip_addr = "192.168.0.10"
    tcp_port = 35000
    port_name = ""
    port_timeout = 5  # Don't change it here. Change in ELM class

    droid = None
    btcid = None

    hdr = None

    kaLock = False
    rwLock = False
    lastReadTime = 0
    # ka_timer = None

    at_keep_alive = 2  # period of sending AT during inactivity

    def __init__(self, port_name, speed, port_timeout):

        self.port_timeout = port_timeout

        port_name = port_name.strip()

        mac = None
        port_name_upper = port_name.upper()
        if (
            re.match(
                r"^[0-9A-F]{2}:[0-9A-F]{2}:[0-9A-F]{2}:[0-9A-F]{2}:[0-9A-F]{2}:[0-9A-F]{2}$",
                port_name_upper,
            )
            or re.match(r"^[0-9A-F]{4}.[0-9A-F]{4}.[0-9A-F]{4}$", port_name_upper)
            or re.match(r"^[0-9A-F]{12}$", port_name_upper)
        ):
            port_name_upper = port_name_upper.replace(":", "").replace(".", "")
            mac = ":".join(
                a + b for a, b in zip(port_name_upper[::2], port_name_upper[1::2])
            )

        if mac:
            try:
                self.macaddr = port_name
                self.channel = 1
                self.port_type = 1
                self.hdr = socket.socket(
                    socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM
                )
                self.hdr.settimeout(10)
                self.hdr.connect((self.macaddr, self.channel))
                self.hdr.setblocking(True)
            except Exception as e:
                print(" \n\nERROR: Can't connect to BT adapter\n\n", e)
                config.OPT_DEMO = True
                sys.exit()
        elif re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{1,5}$", port_name):
            try:
                self.ip_addr, self.tcp_port = port_name.split(":")
                self.tcp_port = int(self.tcp_port)
                self.port_type = 1
                self.hdr = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.hdr.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                self.hdr.settimeout(3)
                self.hdr.connect((self.ip_addr, self.tcp_port))
                self.hdr.setblocking(True)
            except:
                print(" \n\nERROR: Can't connect to WiFi ELM\n\n")
                config.OPT_DEMO = True
                sys.exit()
        else:
            self.port_name = port_name
            self.port_type = 0
            try:
                self.hdr = serial.Serial(
                    self.port_name, baudrate=speed, timeout=port_timeout
                )
            except:  # serial.SerialException:
                print("ELM not connected or wrong COM port defined.")
                iterator = sorted(list(list_ports.comports()))
                print("")
                print("Available COM ports:")
                for port, desc, hwid in iterator:
                    print("%-30s \n\tdesc: %s \n\thwid: %s" % (port, desc, hwid))
                print("")
                config.OPT_DEMO = True
                exit()
            # print self.hdr.BAUDRATES
            self.check_elm()

        # self.elm_at_KeepAlive ()

    def __del__(self):
        pass
        # if self.ka_timer:
        #    self.ka_timer.cancel ()

    def reinit(self):
        """
        Need for wifi adapters with short connection timeout
        """
        if self.port_type != 1:
            return

        if not hasattr(self, "macaddr"):
            self.hdr.close()
            self.hdr = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.hdr.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            self.hdr.connect((self.ip_addr, self.tcp_port))
            self.hdr.setblocking(True)

        self.write("AT\r")
        self.expect(">", 1)

    """
    def elm_at_KeepAlive(self):
      
      try:
  
          if not self.rwLock and pyren_time() > self.lastReadTime + self.atKeepAlive:
        
            self.kaLock = True
            data = 'AT\r'
            try:
              if self.port_type == 1:
                self.hdr.sendall (data)
              elif self.port_type == 2:
                self.droid.bluetoothWrite (data)
              else:
                self.hdr.write (data)
        
              tb = pyren_time()  # start time
              tmpBuff = ""
              while True:
                if not config.opt_demo:
                  byte = self.read ()
                else:
                  byte = '>'
            
                if byte == '\r': byte = '\n'
            
                tmpBuff += byte
                tc = pyren_time()
                if '>' in tmpBuff:
                  return
                if (tc - tb) > 0.01:
                  return
            except:
              pass

      finally:
        self.lastReadTime = pyren_time()
        self.kaLock = False
        if self.ka_timer:
          self.ka_timer.cancel ()
        if self.atKeepAlive > 0:
          self.ka_timer = threading.Timer (self.atKeepAlive, self.elm_at_KeepAlive)
          self.ka_timer.setDaemon(True)
          self.ka_timer.start ()
    """

    def read(self):
        byte = ""
        try:
            if self.port_type == 1:
                try:
                    byte = self.hdr.recv(1)
                except:
                    pass
            elif self.port_type == 2:
                if self.droid.bluetoothReadReady(self.btcid).result:
                    byte = self.droid.bluetoothRead(1, self.btcid).result
            else:
                inInputBuffer = self.hdr.inWaiting()
                if inInputBuffer:
                    if config.OPT_OBD_LINK:
                        byte = self.hdr.read(inInputBuffer)
                    else:
                        byte = self.hdr.read(1)
        except:
            print()
            print("*" * 40)
            print("*       Connection to ELM was lost")
            config.OPT_DEMO = True

        if type(byte) == str:
            byte = byte.encode()

        return byte.decode("utf-8", "ignore")

    def write(self, data):

        # dummy sync
        self.rwLock = True
        i = 0
        while self.kaLock and i < 10:
            time.sleep(0.02)
            i = i + 1

        # data should be byte type
        if type(data) == str:
            data = data.encode()

        # try:
        if self.port_type == 1:
            try:
                rcv_bytes = self.hdr.sendall(data)
            except:
                self.reinit()
                rcv_bytes = self.hdr.sendall(data)
            return rcv_bytes
        elif self.port_type == 2:
            # return self.droid.bluetoothWrite(data , self.btcid)
            return self.droid.bluetoothWrite(data.decode("utf-8"), self.btcid)
        else:
            return self.hdr.write(data)

    def expect(self, pattern, time_out=1):

        tb = pyren_time()  # start time
        self.buff = ""
        try:
            while True:
                if not config.OPT_DEMO:
                    byte = self.read()
                else:
                    byte = ">"

                if "\r" in byte:
                    byte = byte.replace("\r", "\n")
                self.buff += byte
                tc = pyren_time()
                if pattern in self.buff:
                    self.lastReadTime = pyren_time()
                    self.rwLock = False
                    return self.buff
                if (tc - tb) > time_out:
                    self.lastReadTime = pyren_time()
                    self.rwLock = False
                    return self.buff + "TIMEOUT"
        except:
            self.rwLock = False
            pass
        self.lastReadTime = pyren_time()
        self.rwLock = False
        return ""

    def check_elm(self):

        self.hdr.timeout = 2

        for s in [38400, 115200, 230400, 500000, 1000000, 2000000]:
            print("\r\t\t\t\t\rChecking port speed:", s, end=" ")
            sys.stdout.flush()

            try:
                self.hdr.baudrate = s
                self.hdr.flushInput()
            except:
                continue

            self.write("\r")

            # search > string
            tb = pyren_time()  # start time
            self.buff = ""
            while True:
                if not config.OPT_DEMO:
                    byte = self.read()
                else:
                    byte = ">"
                self.buff += byte
                tc = pyren_time()
                if ">" in self.buff:
                    config.OPT_SPEED = s
                    print("\nStart COM speed: ", s)
                    self.hdr.timeout = self.port_timeout
                    return
                if (tc - tb) > 1:
                    break
        print("\nELM not responding")
        sys.exit()

    def soft_boudrate(self, boudrate):

        if config.OPT_DEMO:
            return

        if self.port_type == 1:  # wifi is not supported
            print("ERROR - wifi/bluetooth do not support changing boud rate")
            return

        # stop any read/write
        self.rwLock = False
        self.kaLock = False
        # if self.ka_timer:
        #    self.ka_timer.cancel ()

        print("Changing baud rate to:", boudrate, end=" ")

        if config.OPT_OBD_LINK:
            self.write("ST SBR " + str(boudrate) + "\r")
        else:
            if boudrate == 38400:
                self.write("at brd 68\r")
            elif boudrate == 57600:
                self.write("at brd 45\r")
            elif boudrate == 115200:
                self.write("at brd 23\r")
            elif boudrate == 230400:
                self.write("at brd 11\r")
            elif boudrate == 500000:
                self.write("at brd 8\r")

        # search OK
        tb = pyren_time()  # start time
        self.buff = ""
        while True:
            if not config.OPT_DEMO:
                byte = self.read()
            else:
                byte = "OK"
            if byte == "\r" or byte == "\n":
                self.buff = ""
                continue
            self.buff += byte
            tc = pyren_time()
            if "OK" in self.buff:
                break
            if (tc - tb) > 1:
                print("ERROR - command not supported")
                return

        self.hdr.timeout = 1
        self.hdr.baudrate = boudrate

        time.sleep(0.1)
        self.write("\r")

        # search >
        tb = pyren_time()  # start time
        self.buff = ""
        while True:
            if not config.OPT_DEMO:
                byte = self.read()
            else:
                byte = ">"
            if byte == "\r" or byte == "\n":
                self.buff = ""
                continue
            self.buff += byte
            tc = pyren_time()
            if ">" in self.buff:
                config.OPT_RATE = config.OPT_SPEED
                break
            if (tc - tb) > 1:
                print("ERROR - something went wrong. Let's back.")
                self.hdr.timeout = self.port_timeout
                self.hdr.baudrate = config.OPT_SPEED
                self.rwLock = False
                # disable at_keepalive
                # self.elm_at_KeepAlive ()
                return

        print("OK")
        self.rwLock = False
        # disable at_keepalive
        # self.elm_at_KeepAlive ()

        return


# noinspection PyUnusedLocal
class ELM:
    """ELM327 class"""

    port = 0
    lf = 0
    vf = 0

    keepAlive = 4  # send startSession to CAN after silence if startSession defined
    busLoad = 0  # I am sure than it should be zero
    srvs_delay = 0  # the delay next command requested by service
    last_cmd_time = 0  # time when last command was sent to bus
    port_timeout = 5  # timeout of port (com or tcp)
    elmTimeout = "FF"  # timeout set by ATST
    performance_mode_level = 1  # number of dataids, that can be sent in one 22 request

    # error counters
    error_frame = 0
    error_buffer_full = 0
    error_question = 0
    error_nodata = 0
    error_timeout = 0
    error_rx = 0
    error_can = 0

    response_time = 0
    screen_refresh_time = 0

    buff = ""
    current_protocol = ""
    current_sub_protocol = ""
    current_address = ""
    start_session_ = ""
    last_init_response = ""

    currentScreenDataIds = []  # dataids displayed on current screen
    rsp_cache = OrderedDict()  # cashes responses for current screen
    l1_cache = {}  # save number of frames in responces
    tmp_not_supported_commands = (
        {}
    )  # temporary list for requests that were positive and became negative for no reason
    not_supported_commands = {}  # save them to not slow down polling
    ecu_dump = {}  # for demo only. contains responses for all 21xx and 22xxxx requests

    ATR1 = True
    ATCFC0 = False

    # The next variables is used for fake adapter detection
    supportedCommands = 0
    unsupportedCommands = 0

    portName = ""

    lastMessage = ""

    monitor_thread = None
    monitor_callback = None
    monitor_send_allow = None
    run_allow_event = None
    dmf = None

    waitedFrames = ""
    end_waiting_frames = True
    rspLen = 0
    fToWait = 0

    def __init__(self, portName, speed, log, startSession="10C0"):

        self.portName = portName

        # debug
        # print 'Port Open'

        if not config.OPT_DEMO:
            self.port = Port(portName, speed, self.port_timeout)

        if len(config.OPT_LOG) > 0:  # and config.opt_demo==False:
            self.lf = open("./logs/elm_" + config.OPT_LOG, "at")
            self.vf = open("./logs/ecu_" + config.OPT_LOG, "at")

        if config.OPT_DEBUG and config.DEBUG_FILE is None:
            config.DEBUG_FILE = open("./logs/debug.txt", "at")

        self.last_cmd_time = 0
        self.ATCFC0 = config.OPT_CFC0

        if self.lf != 0:
            self.lf.write(
                "#" * 60
                + "\n#["
                + log_timestamp_str()
                + "] Check ELM type\n"
                + "#" * 60
                + "\n"
            )
            self.lf.flush()

        # check OBDLink
        elm_response = self.cmd("STI")
        if elm_response and "?" not in elm_response:
            firmware_version = elm_response.split(" ")[-1]
            try:
                firmware_version = firmware_version.split(".")
                version_number = int(
                    "".join(
                        [re.sub(r"\D", "", version) for version in firmware_version]
                    )
                )
            except Exception:
                input(
                    "\nCannot determine OBDLink version.\n"
                    + "OBDLink performance may be decreased.\n"
                    + "Press any key to continue...\n"
                )
            else:
                stpx_introduced_in_version_number = (
                    420  # STN1110 got STPX last in version v4.2.0
                )
                if version_number >= stpx_introduced_in_version_number:
                    config.OPT_OBD_LINK = True

            # check STN
            elm_response = self.cmd("STP 53")
            if "?" not in elm_response:
                config.OPT_STN = True

        # Max out the UART speed for the fastest polling rate
        if config.OPT_CSV and not config.OPT_DEMO:
            if config.OPT_OBD_LINK:
                self.port.soft_boudrate(2000000)
            elif self.port.port_type == 0:
                self.port.soft_boudrate(230400)

    def __del__(self):
        if not config.OPT_DEMO and not isinstance(self.port, int):
            print("*" * 40)
            print("*       RESETTING ELM")
            self.port.write("atz\r")
            self.port.at_keep_alive = 0
            if self.run_allow_event:
                self.run_allow_event.clear()
        print("*" * 40)
        print("* ")
        print("*       ERRORS STATISTIC")
        print("* ")
        print("* error_frame      = ", self.error_frame)
        print("* error_buffer_full = ", self.error_buffer_full)
        print("* error_question   = ", self.error_question)
        print("* error_nodata     = ", self.error_nodata)
        print("* error_timeout    = ", self.error_timeout)
        print("* error_rx         = ", self.error_rx)
        print("* error_can        = ", self.error_can)
        print("*")
        print("*       RESPONSE TIME (Average)")
        print("* ")
        print("* response_time    = ", "{0:.3f}".format(self.response_time))
        print("* ")
        print("*" * 40)
        print(self.lastMessage)

    def clear_cache(self):
        """Clear L2 cache before screen update"""
        # print 'Clearing L2 cache'
        self.rsp_cache = OrderedDict()

        # if not config.opt_demo:
        #  self.rsp_cache = {}

    def set_dump(self, ecu_dump):
        """define ecudum for demo mode"""
        self.ecu_dump = ecu_dump

    def load_dump(self, dump_name):

        print("Loading dump:", dump_name)

        df = open(dump_name, "rt")
        lines = df.readlines()
        df.close()

        ecu_dump = {}

        for l in lines:
            l = l.strip().replace("\n", "")
            if l.count(":") == 1:
                req, rsp = l.split(":")
                ecu_dump[req] = rsp

        self.set_dump(ecu_dump)

    def debug_monitor(self):
        byte = ""
        try:
            if self.dmf is None:
                self.dmf = open(os.path.join("./logs/", config.OPT_LOG), "rt")
            byte = self.dmf.read(1)
        except Exception:
            pass
        if not byte:
            self.dmf = None
            byte = " "

        if byte == "\n":
            time.sleep(0.001)

        return byte

    def monitor(self, callback, send_allow, c_t=0.1, c_f=10):
        self.monitor_callback = callback
        self.monitor_send_allow = send_allow

        coalescing_time = c_t
        coalescing_frames = c_f

        lst = pyren_time()  # last send time
        frame_buff = ""
        frame_buff_len = 0
        buff = ""

        if not config.OPT_DEMO:
            self.cmd("at h1")
            self.cmd("at d1")
            self.cmd("at s1")
            self.port.write("at ma\r\n")

        self.mlf = 0
        if not config.OPT_DEMO and len(config.OPT_LOG) > 0:
            self.mlf = open("./logs/" + config.OPT_LOG, "wt")

        while self.run_allow_event.isSet():
            if not config.OPT_DEMO:
                byte = self.port.read()
            else:
                byte = self.debug_monitor()

            ct = pyren_time()  # current time
            if (ct - lst) > coalescing_time:  # and frame_buff_len>0:
                if (
                    self.monitor_send_allow is None
                    or not self.monitor_send_allow.isSet()
                ):
                    self.monitor_send_allow.set()
                    # print 'time callback'
                    callback(frame_buff)
                    # print 'return from callback'
                lst = ct
                frame_buff = ""
                frame_buff_len = 0

            if len(byte) == 0:
                continue

            if byte == "\r" or byte == "\n":

                line = buff.strip()
                buff = ""

                if len(line) < 6:
                    continue

                if ":" in line:
                    line = line.split(":")[-1].strip()

                if ord(line[4:5]) < 0x31 or ord(line[4:5]) > 0x38:
                    continue

                dlc = int(line[4:5])

                if len(line) < (dlc * 3 + 5):
                    continue

                frame_buff = frame_buff + line + "\n"
                frame_buff_len = frame_buff_len + 1

                # save log
                if self.mlf:
                    # self.mlf.write (line + '\n')

                    # debug
                    self.mlf.write(log_timestamp_str() + " : " + line + "\n")

                if frame_buff_len >= coalescing_frames:
                    if (
                        self.monitor_send_allow is None
                        or not self.monitor_send_allow.isSet()
                    ):
                        self.monitor_send_allow.set()
                        # print 'frame callback'
                        callback(frame_buff)
                        # print 'return from callback'
                    lst = ct
                    frame_buff = ""
                    frame_buff_len = 0

                continue

            buff += byte
            if byte == ">":
                self.port.write("\r")

    def set_monitor_filter(self, filter_, mask):
        if config.OPT_DEMO or self.monitor_callback is None:
            return
        # if len(filter)!=3 or len(mask)!=3: return

        print()
        print("Filter : " + filter_)
        print("Mask   : " + mask)
        sys.stdout.flush()

        # stop monitor
        self.stop_monitor()

        if len(filter_) != 3 or len(mask) != 3 or filter_ == "000":
            self.cmd("at cf 000")
            self.cmd("at cm 000")
        else:
            self.cmd("at cf " + filter_)
            self.cmd("at cm " + mask)

        self.start_monitor(self.monitor_callback, self.monitor_send_allow)

    def start_monitor(self, callback, send_allow=None, c_t=0.1, c_f=10):
        if self.current_protocol != "can":
            print("Monitor mode is possible only on CAN bus")
            return
        self.run_allow_event = threading.Event()
        self.run_allow_event.set()
        self.monitor_thread = threading.Thread(
            target=self.monitor, args=(callback, send_allow, c_t, c_f)
        )
        self.monitor_thread.setDaemon(True)
        self.monitor_thread.start()

    def stop_monitor(self):
        if not config.OPT_DEMO:
            self.port.write("\r\n")
        self.run_allow_event.clear()
        time.sleep(0.2)
        if config.OPT_DEMO or self.monitor_callback is None:
            return

        tmp = self.port_timeout
        self.port_timeout = 0.3
        self.cmd("at")
        self.cmd("at h0")
        self.cmd("at d0")
        self.cmd("at s0")
        self.port_timeout = tmp

    def nr78_monitor(self, callback, send_allow, c_t=0.1, c_f=1):
        self.monitor_callback = callback
        self.monitor_send_allow = send_allow

        coalescing_time = c_t
        coalescing_frames = c_f

        lst = pyren_time()  # last send time
        frame_buffer = ""
        frame_buffer_len = 0
        buff = ""

        if not config.OPT_DEMO:
            self.port.write("at ma\r\n")

        while self.run_allow_event.isSet():
            # there should be no nr78 in demo mode
            # if not config.opt_demo:
            #    byte = self.port.read()
            # else:
            #    byte = self.debugMonitor()

            byte = self.port.read()

            ct = pyren_time()  # current time
            if (ct - lst) > coalescing_time:  # and frame_buffer_len>0:
                if (
                    self.monitor_send_allow is None
                    or not self.monitor_send_allow.isSet()
                ):
                    self.monitor_send_allow.set()
                    # print 'time callback'
                    callback(frame_buffer)
                    # print 'return from callback'
                lst = ct
                frame_buffer = ""
                frame_buffer_len = 0

            if len(byte) == 0:
                continue

            if byte == "\r" or byte == "\n":
                line = buff.strip()
                buff = ""
                if len(line) < 2:
                    continue
                if "atma" in line.replace(" ", "").lower():
                    continue
                if "stopped" in line.lower():
                    continue

                frame_buffer = frame_buffer + line + "\n"
                frame_buffer_len = frame_buffer_len + 1

                # save log
                if self.lf:
                    self.lf.write("mon: " + log_timestamp_str() + " : " + line + "\n")

                if frame_buffer_len >= coalescing_frames:
                    if (
                        self.monitor_send_allow is None
                        or not self.monitor_send_allow.isSet()
                    ):
                        self.monitor_send_allow.set()
                        # print 'frame callback'
                        callback(frame_buffer)
                        # print 'return from callback'
                    lst = ct
                    frame_buffer = ""
                    frame_buffer_len = 0

                continue

            buff += byte
            if byte == ">":
                self.port.write("\r")

    def nr78_start_monitor(self, callback, send_allow=None, c_t=0.1, c_f=1):
        if self.current_protocol != "can":
            print("Monitor mode is possible only on CAN bus")
            return
        self.run_allow_event = threading.Event()
        self.run_allow_event.set()
        self.monitor_thread = threading.Thread(
            target=self.nr78_monitor, args=(callback, send_allow, c_t, c_f)
        )
        self.monitor_thread.setDaemon(True)
        self.monitor_thread.start()

    def nr78_stop_monitor(self):
        if not config.OPT_DEMO:
            self.port.write("\r")
        self.run_allow_event.clear()
        time.sleep(0.2)
        if config.OPT_DEMO or self.monitor_callback is None:
            return

        tmp = self.port_timeout
        self.port_timeout = 0.3
        self.send_raw("AT")
        self.port_timeout = tmp

    def wait_frames_call_back(self, frames):
        for l in frames.split("\n"):
            l = l.strip()
            if len(l) == 0:
                continue
            l = l.replace(" ", "")
            if l[:4].upper() == "037F" and l[6:8] == "78":
                # wait again
                self.rspLen = 0
                self.fToWait = 0
                break

            self.waitedFrames = self.waitedFrames + l

            if l[:1] == "3":  # flow control
                self.end_waiting_frames = True

            elif l[:1] == "0":  # single frame
                n_bytes = int(l[1:2], 16)
                if n_bytes < 8:
                    self.rspLen = 1
                    self.fToWait = 0  # because we've received it
                else:
                    print("\n ERROR #1 in waitFramesCallBack")
                self.end_waiting_frames = True

            elif l[:1] == "1":  # first frame
                n_bytes = int(l[1:4], 16)
                n_bytes = n_bytes - 6  # because we've received the first frame
                self.rspLen = n_bytes // 7 + bool(n_bytes % 7)
                # self.fToWait = min(self.rspLen,MaxBurst)
                self.end_waiting_frames = True  # stop waiting and send FlowControl

            elif l[:1] == "2":  # consecutive frame
                self.rspLen = self.rspLen - 1
                self.fToWait = self.fToWait - 1
                if self.fToWait == 0:
                    self.end_waiting_frames = True

        self.monitor_send_allow.clear()
        return

    def waitFrames(self, timeout):

        self.waitedFrames = ""
        self.end_waiting_frames = False
        self.fToWait = min(self.rspLen, MAX_BURST)

        send_allow = threading.Event()
        send_allow.clear()
        self.nr78_start_monitor(self.wait_frames_call_back, send_allow, 0.1, 1)

        beg = pyren_time()

        while not self.end_waiting_frames and (pyren_time() - beg < timeout):
            time.sleep(0.01)

        # debug
        # print '>>>> ', self.waitedFrames
        self.nr78_stop_monitor()

        # debug
        # print '>>>> ', self.waitedFrames

        return self.waitedFrames

    def get_from_cache(self, req):
        if config.OPT_DEMO and req in list(self.ecu_dump.keys()):
            return self.ecu_dump[req]

        if req in list(self.rsp_cache.keys()):
            return self.rsp_cache[req]

        return ""

    def del_from_cache(self, req):
        if not config.OPT_DEMO and req in list(self.rsp_cache.keys()):
            del self.rsp_cache[req]

    def check_if_command_unsupported(self, req, res):
        if "NR" in res:
            nr = res.split(":")[1]
            if nr in ["12"]:
                if (
                    config.OPT_CSV_ONLY
                ):  # all unsupported commands must be removed immediately in csv_only mode
                    self.not_supported_commands[req] = res
                else:
                    if req in list(self.tmp_not_supported_commands.keys()):
                        del self.tmp_not_supported_commands[req]
                        self.not_supported_commands[req] = res
                    else:
                        self.tmp_not_supported_commands[req] = res
        else:
            if req in list(
                self.tmp_not_supported_commands.keys()
            ):  # if the previous response was negative and now it is positive
                del self.tmp_not_supported_commands[
                    req
                ]  # remove it from negative commands queue, because of false negative

    def request(self, req, positive="", cache=True, serviceDelay="0"):
        """Check if request is saved in L2 cache.
        If not then
          - make real request
          - convert response to one line
          - save in L2 cache
        returns response without consistency check
        """

        if config.OPT_DEMO and req in list(self.ecu_dump.keys()):
            return self.ecu_dump[req]

        if cache and req in list(self.rsp_cache.keys()):
            return self.rsp_cache[req]

        # send cmd
        rsp = self.cmd(req, int(serviceDelay))

        # parse response
        res = ""
        if self.current_protocol != "can":
            # Trivially reject first line (echo)
            rsp_split = rsp.split("\n")[1:]
            for s in rsp_split:
                if ">" not in s and len(s.strip()):
                    res += s.strip() + " "
        else:
            for s in rsp.split("\n"):
                if ":" in s:
                    res += s[2:].strip() + " "
                else:  # response consists only from one frame
                    if s.replace(" ", "").startswith(positive.replace(" ", "")):
                        res += s.strip() + " "

        rsp = res

        # populate L2 cache
        if req[:2] in ALLOWED_LIST:
            self.rsp_cache[req] = rsp

        # save log
        if self.vf != 0 and "NR" not in rsp:
            tmp_addr = self.current_address
            if self.current_address in list(DNAT.keys()):
                tmp_addr = DNAT[self.current_address]
            self.vf.write(
                log_timestamp_str() + ";" + tmp_addr + ";" + req + ";" + rsp + "\n"
            )
            self.vf.flush()

        return rsp

    # noinspection PyUnboundLocalVariable
    def cmd(self, command, service_delay=0):

        command = command.upper()

        # check if command not supported
        if command in list(self.not_supported_commands.keys()):
            return self.not_supported_commands[command]

        tb = pyren_time()  # start time

        # Ensure timegap between commands
        # dl = self.busLoad + self.srvsDelay - tb + self.lastCMDtime
        if (
            (tb - self.last_cmd_time) < (self.busLoad + self.srvs_delay)
        ) and command.upper()[:2] not in ["AT", "ST"]:
            time.sleep(self.busLoad + self.srvs_delay - tb + self.last_cmd_time)

        tb = pyren_time()  # renew start time

        # save current session
        save_session = self.start_session_

        # If we are on CAN and there was more than keepAlive seconds of silence
        # then send startSession command again
        if (tb - self.last_cmd_time) > self.keepAlive and len(self.start_session_) > 0:

            # log KeepAlive event
            if self.lf != 0:
                self.lf.write("#[" + log_timestamp_str() + "]" + "KeepAlive\n")
                self.lf.flush()

            # send keepalive
            # if not config.opt_demo:
            #  self.port.reinit() #experimental
            self.send_cmd(self.start_session_)
            self.last_cmd_time = pyren_time()  # for not to get into infinite loop

        # send command and check for ask to wait
        cmdrsp = ""
        rep_count = 3
        while rep_count > 0:
            rep_count = rep_count - 1
            no_negative_wait_response = True

            self.last_cmd_time = tc = pyren_time()
            cmdrsp = self.send_cmd(command)

            self.check_if_command_unsupported(
                command, cmdrsp
            )  # check if response for this command is NR:12

            # if command[0:2] not in AllowedList:
            #  break

            for line in cmdrsp.split("\n"):
                line = line.strip().upper()
                nr = ""
                if (
                    line.startswith("7F")
                    and len(line) == 8
                    and line[6:8] in list(NEGATIVE_RESPONSES.keys())
                ):
                    nr = line[6:8]
                if line.startswith("NR"):
                    nr = line.split(":")[1]
                if nr in ["21", "23"]:  # it is look like the ECU asked us to wait a bit
                    time.sleep(0.5)
                    no_negative_wait_response = False
                elif nr in ["78"]:
                    self.send_raw("at at 0")
                    self.send_raw("at st ff")
                    self.last_cmd_time = tc = pyren_time()
                    cmdrsp = self.send_cmd(command)
                    self.send_raw("at at 1")
                    break

            if no_negative_wait_response:
                break

        self.srvs_delay = float(service_delay) / 1000.0

        # check for negative response from k-line (CAN NR processed in send_can***)
        for line in cmdrsp.split("\n"):
            line = line.strip().upper()
            if (
                line.startswith("7F")
                and len(line) == 8
                and line[6:8] in list(NEGATIVE_RESPONSES.keys())
                and self.current_protocol != "can"
            ):
                # if not config.state_scan: print line, negrsp[line[6:8]]
                if self.lf != 0:
                    # tm = str (pyren_time())
                    self.lf.write(
                        "#["
                        + str(tc - tb)
                        + "] rsp:"
                        + line
                        + ":"
                        + NEGATIVE_RESPONSES[line[6:8]]
                        + "\n"
                    )
                    self.lf.flush()
                if self.vf != 0:
                    tmp_addr = self.current_address
                    if self.current_address in list(DNAT.keys()):
                        tmp_addr = DNAT[self.current_address]

                    self.vf.write(
                        log_timestamp_str()
                        + ";"
                        + tmp_addr
                        + ";"
                        + command
                        + ";"
                        + line
                        + ";"
                        + NEGATIVE_RESPONSES[line[6:8]]
                        + "\n"
                    )
                    self.vf.flush()

        return cmdrsp

    def send_cmd(self, command):

        command = command.upper()

        # deal with exceptions
        # boudrate 38400 not enough to read full information about errors
        if not config.OPT_OBD_LINK and len(command) == 6 and command[:4] == "1902":
            command = "1902AF"

        if command.upper()[:2] in ["AT", "ST"] or self.current_protocol != "can":
            return self.send_raw(command)

        if self.ATCFC0:
            return self.send_can_cfc0(command)
        else:
            if config.OPT_OBD_LINK:
                if config.OPT_CAF:
                    rsp = self.send_can_cfc_caf(command)
                else:
                    rsp = self.send_can_cfc(command)
            else:
                rsp = self.send_can(command)
            if (
                self.error_frame > 0 or self.error_buffer_full > 0
            ):  # then fallback to cfc0
                self.ATCFC0 = True
                self.cmd("at cfc0")
                rsp = self.send_can_cfc0(command)
            return rsp

    def send_can(self, command):
        command = command.strip().replace(" ", "").upper()
        isCommandInCache = command in list(self.l1_cache.keys())

        if len(command) == 0:
            return
        if len(command) % 2 != 0:
            return "ODD ERROR"
        if not all(c in string.hexdigits for c in command):
            return "HEX ERROR"

        # do framing
        raw_command = []
        cmd_len = int(len(command) // 2)
        if cmd_len < 8:  # single frame
            # check L1 cache here
            if isCommandInCache and int("0x" + self.l1_cache[command], 16) < 16:
                raw_command.append(
                    ("%0.2X" % cmd_len) + command + self.l1_cache[command]
                )
            else:
                raw_command.append(("%0.2X" % cmd_len) + command)
        else:
            # first frame
            raw_command.append("1" + ("%0.3X" % cmd_len)[-3:] + command[:12])
            command = command[12:]
            # consecutive frames
            frame_number = 1
            while len(command):
                raw_command.append("2" + ("%X" % frame_number)[-1:] + command[:14])
                frame_number = frame_number + 1
                command = command[14:]

        responses = []

        # send farmes
        for f in raw_command:
            # send next frame
            frsp = self.send_raw(f)
            # analyse response (1 phase)
            for s in frsp.split("\n"):
                if s.strip() == f:  # echo cancelation
                    continue
                s = s.strip().replace(" ", "")
                if len(s) == 0:  # empty string
                    continue
                if all(c in string.hexdigits for c in s):  # some data
                    if s[:1] == "3":  # flow control, just ignore it in this version
                        continue
                    responses.append(s)

        # analise response (2 phase)
        result = ""
        noerrors = True
        cframe = 0  # frame counter
        nbytes = 0  # number bytes in response
        nframes = 0  # numer frames in response

        if len(responses) == 0:  # no data in response
            return ""

        if (
            len(responses) > 1
            and responses[0].startswith("037F")
            and responses[0][6:8] == "78"
        ):
            responses = responses[1:]
            config.OPT_N1C = True

        if len(responses) == 1:  # single freme response
            if responses[0][:1] == "0":
                nbytes = int(responses[0][1:2], 16)
                nframes = 1
                result = responses[0][2 : 2 + nbytes * 2]
            else:  # wrong response (not all frames received)
                self.error_frame += 1
                noerrors = False
        else:  # multi frame response
            if responses[0][:1] == "1":  # first frame
                nbytes = int(responses[0][1:4], 16)
                nframes = nbytes // 7 + 1
                cframe = 1
                result = responses[0][4:16]
            else:  # wrong response (first frame omitted)
                self.error_frame += 1
                noerrors = False

            for fr in responses[1:]:
                if fr[:1] == "2":  # consecutive frames
                    tmp_fn = int(fr[1:2], 16)
                    if tmp_fn != (cframe % 16):  # wrong response (frame lost)
                        self.error_frame += 1
                        noerrors = False
                        continue
                    cframe += 1
                    result += fr[2:16]
                else:  # wrong response
                    self.error_frame += 1
                    noerrors = False

        # Check for negative
        if result[:2] == "7F":
            noerrors = False

        # populate L1 cache
        if noerrors and command[:2] in ALLOWED_LIST and not config.OPT_N1C:
            self.l1_cache[command] = str(hex(nframes))[2:].upper()

        if len(result) // 2 >= nbytes and noerrors:
            # trim padding
            result = result[: nbytes * 2]
            # split by bytes and return
            result = " ".join(a + b for a, b in zip(result[::2], result[1::2]))
            return result
        else:
            # check for negative response (repeat the same as in cmd())
            if result[:2] == "7F" and result[4:6] in list(NEGATIVE_RESPONSES.keys()):
                if self.vf != 0:
                    # debug
                    # print result

                    self.vf.write(
                        log_timestamp_str()
                        + ";"
                        + DNAT[self.current_address]
                        + ";"
                        + command
                        + ";"
                        + result
                        + ";"
                        + NEGATIVE_RESPONSES[result[4:6]]
                        + "\n"
                    )
                    self.vf.flush()
                return "NR:" + result[4:6] + ":" + NEGATIVE_RESPONSES[result[4:6]]
            else:
                return "WRONG RESPONSE"

    # Can be used only with OBDLink based ELM, wireless especially.
    def send_can_cfc_caf(self, command):
        if len(command) == 0:
            return
        if len(command) % 2 != 0:
            return "ODD ERROR"
        if not all(c in string.hexdigits for c in command):
            return "HEX ERROR"

        frsp = self.send_raw("STPX D:" + command + ",R:" + "1")

        responses = []

        for s in frsp.split("\n"):
            if s.strip()[:4] == "STPX":  # echo cancelation
                continue

            s = s.strip().replace(" ", "")
            if len(s) == 0:  # empty string
                continue

            responses.append(s)

        result = ""
        noerrors = True

        if len(responses) == 0:  # no data in response
            return ""

        nodataflag = False
        for s in responses:

            if "NO DATA" in s:
                nodataflag = True
                break

            if all(c in string.hexdigits for c in s):  # some data
                result = s

        # Check for negative
        if result[:2] == "7F":
            noerrors = False

        if noerrors:
            # split by bytes and return
            result = " ".join(a + b for a, b in zip(result[::2], result[1::2]))
            return result
        else:
            # check for negative response (repeat the same as in cmd())
            # debug
            # print "Size error: ", result
            if result[:2] == "7F" and result[4:6] in list(NEGATIVE_RESPONSES.keys()):
                if self.vf != 0:
                    self.vf.write(
                        log_timestamp_str()
                        + ";"
                        + DNAT[self.current_address]
                        + ";"
                        + command
                        + ";"
                        + result
                        + ";"
                        + NEGATIVE_RESPONSES[result[4:6]]
                        + "\n"
                    )
                    self.vf.flush()
                return "NR:" + result[4:6] + ":" + NEGATIVE_RESPONSES[result[4:6]]
            else:
                return "WRONG RESPONSE"

    # Can be used only with OBDLink based ELM
    def send_can_cfc(self, command):

        command = command.strip().replace(" ", "").upper()
        init_command = command

        if len(command) == 0:
            return
        if len(command) % 2 != 0:
            return "ODD ERROR"
        if not all(c in string.hexdigits for c in command):
            return "HEX ERROR"

        # do framing
        raw_command = []
        cmd_len = len(command) // 2
        if cmd_len < 8:  # single frame
            raw_command.append(("%0.2X" % cmd_len) + command)
        else:
            # first frame
            raw_command.append("1" + ("%0.3X" % cmd_len)[-3:] + command[:12])
            command = command[12:]
            # consecutive frames
            frame_number = 1
            while len(command):
                raw_command.append("2" + ("%X" % frame_number)[-1:] + command[:14])
                frame_number = frame_number + 1
                command = command[14:]

        responses = []

        # send frames
        BS = 1  # Burst Size
        ST = 0  # Frame Interval
        Fc = 0  # Current frame
        Fn = len(raw_command)  # Number of frames
        frsp = ""

        if raw_command[Fc].startswith("0") and init_command in list(
            self.l1_cache.keys()
        ):
            frsp = self.send_raw(
                "STPX D:" + raw_command[Fc] + ",R:" + self.l1_cache[init_command]
            )
        elif raw_command[Fc].startswith("1"):
            frsp = self.send_raw("STPX D:" + raw_command[Fc] + ",R:" + "1")
        else:
            frsp = self.send_raw("STPX D:" + raw_command[Fc])

        while Fc < Fn:
            tb = pyren_time()  # time of sending (ff)

            if raw_command[Fc][:1] != "2":
                Fc = Fc + 1

            # analyse response
            for s in frsp.split("\n"):

                if s.strip()[:4] == "STPX":  # echo cancelation
                    continue

                s = s.strip().replace(" ", "")
                if len(s) == 0:  # empty string
                    continue

                if all(c in string.hexdigits for c in s):  # some data
                    if s[:1] == "3":  # FlowControl

                        # extract Burst Size
                        BS = s[2:4]
                        if BS == "":
                            BS = "03"
                        BS = int(BS, 16)

                        # extract Frame Interval
                        ST = s[4:6]
                        if ST == "":
                            ST = "EF"
                        if ST[:1].upper() == "F":
                            ST = int(ST[1:2], 16) * 100
                        else:
                            ST = int(ST, 16)
                            # print 'BS:',BS,'ST:',ST
                        break  # go to sending consequent frames
                    else:
                        responses.append(s)
                        continue

            # sending consequent frames according to FlowControl
            frames_left = Fn - Fc
            cf = min({BS, frames_left})  # number of frames to send without response

            while cf > 0:
                burst_size_command = "".join(raw_command[Fc : Fc + cf])
                burst_size_command_last_frame = burst_size_command[
                    len("".join(raw_command[Fc : Fc + cf - 1])) :
                ]

                if burst_size_command_last_frame == raw_command[-1]:
                    if init_command in list(self.l1_cache.keys()):
                        burst_size_request = (
                            "STPX D:"
                            + burst_size_command
                            + ",R:"
                            + self.l1_cache[init_command]
                        )
                    else:
                        burst_size_request = "STPX D:" + burst_size_command
                else:
                    burst_size_request = "STPX D:" + burst_size_command + ",R:1"

                # Ensure time gap between frames according to FlowControl
                tc = pyren_time()  # current time
                self.screen_refresh_time += ST / 1000.0
                if (tc - tb) * 1000.0 < ST:
                    target_time = pyren_time() + (ST / 1000.0 - (tc - tb))
                    while pyren_time() < target_time:
                        pass
                tb = tc

                frsp = self.send_raw(burst_size_request)
                Fc = Fc + cf
                cf = 0
                if burst_size_command_last_frame == raw_command[-1]:
                    for s in frsp.split("\n"):
                        if s.strip()[:4] == "STPX":  # echo cancelation
                            continue
                        else:
                            responses.append(s)
                            continue

        result = ""
        noerrors = True
        cFrame = 0  # frame counter
        nBytes = 0  # number bytes in response
        nFrames = 0  # numer frames in response

        if len(responses) == 0:  # no data in response
            return ""

        if (
            len(responses) > 1
            and responses[0].startswith("037F")
            and responses[0][6:8] == "78"
        ):
            responses = responses[1:]

        if responses[0][:1] == "0":  # single frame (sf)
            nBytes = int(responses[0][1:2], 16)
            rspLen = nBytes
            nFrames = 1
            result = responses[0][2 : 2 + nBytes * 2]

        elif responses[0][:1] == "1":  # first frame (ff)
            nBytes = int(responses[0][1:4], 16)
            rspLen = nBytes
            nBytes = nBytes - 6  # we assume that it should be more then 7
            nFrames = 1 + nBytes // 7 + bool(nBytes % 7)
            cFrame = 1

            result = responses[0][4:16]

            while cFrame < nFrames:

                # analyse response
                nodataflag = False
                for s in responses:

                    if "NO DATA" in s:
                        nodataflag = True
                        break

                    s = s.strip().replace(" ", "")
                    if len(s) == 0:  # empty string
                        continue

                    if all(c in string.hexdigits for c in s):  # some data
                        # responses.append(s)
                        if s[:1] == "2":  # consecutive frames (cf)
                            tmp_fn = int(s[1:2], 16)
                            if tmp_fn != (cFrame % 16):  # wrong response (frame lost)
                                self.error_frame += 1
                                noerrors = False
                                continue
                            cFrame += 1
                            result += s[2:16]
                        continue

                if nodataflag:
                    break

        else:  # wrong response (first frame omitted)
            self.error_frame += 1
            noerrors = False

        # Check for negative
        if result[:2] == "7F":
            noerrors = False

        # populate L1 cache
        if noerrors and init_command[:2] in ALLOWED_LIST:
            self.l1_cache[init_command] = str(nFrames)

        if noerrors and len(result) // 2 >= nBytes:
            # trim padding
            result = result[: rspLen * 2]
            # split by bytes and return
            result = " ".join(a + b for a, b in zip(result[::2], result[1::2]))
            return result
        else:
            # check for negative response (repeat the same as in cmd())
            # debug
            # print "Size error: ", result
            if result[:2] == "7F" and result[4:6] in list(NEGATIVE_RESPONSES.keys()):
                if self.vf != 0:
                    self.vf.write(
                        log_timestamp_str()
                        + ";"
                        + DNAT[self.current_address]
                        + ";"
                        + command
                        + ";"
                        + result
                        + ";"
                        + NEGATIVE_RESPONSES[result[4:6]]
                        + "\n"
                    )
                    self.vf.flush()
                return "NR:" + result[4:6] + ":" + NEGATIVE_RESPONSES[result[4:6]]
            else:
                return "WRONG RESPONSE"

    def send_can_cfc0(self, command):

        command = command.strip().replace(" ", "").upper()

        if len(command) == 0:
            return
        if len(command) % 2 != 0:
            return "ODD ERROR"
        if not all(c in string.hexdigits for c in command):
            return "HEX ERROR"

        # do framing
        raw_command = []
        cmd_len = len(command) // 2
        if cmd_len < 8:  # single frame
            raw_command.append(("%0.2X" % cmd_len) + command)
        else:
            # first frame
            raw_command.append("1" + ("%0.3X" % cmd_len)[-3:] + command[:12])
            command = command[12:]
            # consecutive frames
            frame_number = 1
            while len(command):
                raw_command.append("2" + ("%X" % frame_number)[-1:] + command[:14])
                frame_number = frame_number + 1
                command = command[14:]

        responses = []

        # send frames
        BS = 1  # Burst Size
        ST = 0  # Frame Interval
        Fc = 0  # Current frame
        Fn = len(raw_command)  # Number of frames

        if Fn > 1 or len(raw_command[0]) > 15:
            # set elm timeout to minimum among 3 values
            #   1) 300ms constant
            #   2) 2 * self.response_time in ms
            #   3) 4.7s // (number of farmes in cmd) (5s session timeout - 300ms safety gap - 16ms windows timer discret)
            min_tout = min(
                300, 2 * self.response_time * 1000, 4700.0 // len(raw_command) - 16
            )
            if min_tout < 4:
                min_tout = 4  # not less then 4ms
            self.elmTimeout = hex(int(min_tout // 4))[2:].zfill(2)
            self.send_raw("ATST" + self.elmTimeout)
            self.send_raw("ATAT1")

        while Fc < Fn:

            # enable responses
            frsp = ""
            if not self.ATR1:
                frsp = self.send_raw("AT R1")
                self.ATR1 = True

            tb = pyren_time()  # time of sending (ff)

            if Fn > 1 and Fc == (
                Fn - 1
            ):  # set elm timeout to maximum for last response on long command
                self.send_raw("ATSTFF")
                self.send_raw("ATAT1")

            if (Fc == 0 or Fc == (Fn - 1)) and len(
                raw_command[Fc]
            ) < 16:  # first or last frame in command and len<16 (bug in ELM)
                frsp = self.send_raw(
                    raw_command[Fc] + "1"
                )  # we'll get only 1 frame: nr, fc, ff or sf
            else:
                frsp = self.send_raw(raw_command[Fc])

            # print '\nbp1:', raw_command[Fc]

            Fc = Fc + 1

            # analyse response
            # first pass. We have to left only response data frames
            s0 = []
            for s in frsp.upper().split("\n"):

                if (
                    s.strip()[: len(raw_command[Fc - 1])] == raw_command[Fc - 1]
                ):  # echo cancellation
                    continue

                s = s.strip().replace(" ", "")
                if len(s) == 0:  # empty string
                    continue

                if all(c in string.hexdigits for c in s):  # some data
                    s0.append(s)

            # second pass. Now we may check if 7Fxx78 is a last or not
            for s in s0:
                if s[:1] == "3":  # FlowControl
                    # extract Burst Size
                    BS = s[2:4]
                    if BS == "":
                        BS = "03"
                    BS = int(BS, 16)

                    # extract Frame Interval
                    ST = s[4:6]
                    if ST == "":
                        ST = "EF"
                    if ST[:1].upper() == "F":
                        ST = int(ST[1:2], 16) * 100
                    else:
                        ST = int(ST, 16)
                        # print 'BS:',BS,'ST:',ST
                    break  # go to sending consequent frames
                elif s[:4] == "037F" and s[6:8] == "78":  # NR:78
                    if len(s0) > 0 and s == s0[-1]:  # it should be the last one
                        r = self.waitFrames(6)
                        if len(r.strip()) > 0:
                            responses.append(r)
                    else:
                        continue  # ignore NR 78 if it is not the last
                else:
                    responses.append(s)
                    continue

            # sending consequent frames according to FlowControl

            cf = min(
                {BS - 1, (Fn - Fc) - 1}
            )  # number of frames to send without response

            # disable responses
            if cf > 0:
                if self.ATR1:
                    frsp = self.send_raw("at r0")
                    self.ATR1 = False

            while cf > 0:
                cf = cf - 1

                # Ensure time gap between frames according to FlowControl
                tc = pyren_time()  # current time
                if (tc - tb) * 1000.0 < ST:
                    time.sleep(ST / 1000.0 - (tc - tb))
                tb = tc

                frsp = self.send_raw(raw_command[Fc])
                Fc = Fc + 1

        # debug
        # print '\nbp8>',responses,'<\n'

        # now we are going to receive data. st or ff should be in responses[0]
        if len(responses) != 1:
            # print "Something went wrong. len responces != 1"
            return "WRONG RESPONSE"

        result = ""
        noErrors = True
        cFrame = 0  # frame counter
        nBytes = 0  # number bytes in response
        nFrames = 0  # numer frames in response

        if responses[0][:1] == "0":  # single frame (sf)
            nBytes = int(responses[0][1:2], 16)
            rspLen = nBytes
            nFrames = 1
            result = responses[0][2 : 2 + nBytes * 2]

        elif responses[0][:1] == "1":  # first frame (ff)
            nBytes = int(responses[0][1:4], 16)
            rspLen = nBytes
            nBytes = nBytes - 6  # we assume that it should be more then 7
            nFrames = 1 + nBytes // 7 + bool(nBytes % 7)
            cFrame = 1

            result = responses[0][4:16]

            # receiving consecutive frames
            # while len (result) / 2 < nBytes:
            while cFrame < nFrames:
                # now we should send ff
                sBS = hex(min({nFrames - cFrame, MAX_BURST}))[2:]
                frsp = self.send_raw("300" + sBS + "00" + sBS)

                # analyse response
                nodataflag = False
                for s in frsp.split("\n"):

                    if (
                        s.strip()[: len(raw_command[Fc - 1])] == raw_command[Fc - 1]
                    ):  # echo cancelation
                        continue

                    if "NO DATA" in s:
                        nodataflag = True
                        break

                    s = s.strip().replace(" ", "")
                    if len(s) == 0:  # empty string
                        continue

                    if all(c in string.hexdigits for c in s):  # some data
                        responses.append(s)
                        if s[:1] == "2":  # consecutive frames (cf)
                            tmp_fn = int(s[1:2], 16)
                            if tmp_fn != (cFrame % 16):  # wrong response (frame lost)
                                self.error_frame += 1
                                noErrors = False
                                continue
                            cFrame += 1
                            result += s[2:16]
                        continue

                if nodataflag:
                    break

        else:  # wrong response (first frame omitted)
            self.error_frame += 1
            noErrors = False

        if len(result) // 2 >= nBytes and noErrors and result[:2] != "7F":
            # trim padding
            result = result[: rspLen * 2]
            # split by bytes and return
            result = " ".join(a + b for a, b in zip(result[::2], result[1::2]))
            return result
        else:
            # check for negative response (repeat the same as in cmd())
            # debug
            # print "Size error: ", result
            if result[:2] == "7F" and result[4:6] in list(NEGATIVE_RESPONSES.keys()):
                if self.vf != 0:
                    self.vf.write(
                        log_timestamp_str()
                        + ";"
                        + DNAT[self.current_address]
                        + ";"
                        + command
                        + ";"
                        + result
                        + ";"
                        + NEGATIVE_RESPONSES[result[4:6]]
                        + "\n"
                    )
                    self.vf.flush()
                return "NR:" + result[4:6] + ":" + NEGATIVE_RESPONSES[result[4:6]]
            else:
                return "WRONG RESPONSE"

    def send_raw(self, command):

        command = command.upper()

        tb = pyren_time()  # start time

        # save command to log
        if self.lf != 0:
            self.lf.write(">[" + log_timestamp_str() + "]" + command + "\n")
            self.lf.flush()

        # send command
        if not config.OPT_DEMO:
            self.port.write(str(command + "\r").encode("utf-8"))  # send command

        # receive and parse responce
        while True:
            tc = pyren_time()
            if config.OPT_DEMO:
                break
            self.buff = self.port.expect(">", self.port_timeout)
            tc = pyren_time()
            if (tc - tb) > self.port_timeout and "TIMEOUT" not in self.buff:
                self.buff += "TIMEOUT"
            if "TIMEOUT" in self.buff:
                self.error_timeout += 1
                break
            if command in self.buff:
                break
            elif self.lf != 0:
                self.lf.write(
                    "<["
                    + log_timestamp_str()
                    + "]"
                    + self.buff
                    + "(shifted)"
                    + command
                    + "\n"
                )
                self.lf.flush()

        # count errors
        if "?" in self.buff:
            self.error_question += 1
        if "BUFFER FULL" in self.buff:
            self.error_buffer_full += 1
        if "NO DATA" in self.buff:
            self.error_nodata += 1
        if "RX ERROR" in self.buff:
            self.error_rx += 1
        if "CAN ERROR" in self.buff:
            self.error_can += 1

        roundtrip = tc - tb

        self.screen_refresh_time += roundtrip

        if command[0].isdigit() or command.startswith("STPX"):
            self.response_time = ((self.response_time * 9) + roundtrip) / 10

        # save responce to log
        if self.lf != 0:
            self.lf.write("<[" + str(round(roundtrip, 3)) + "]" + self.buff + "\n")
            self.lf.flush()

        return self.buff

    def close_protocol(self):
        self.cmd("atpc")

    def start_session(self, start_session_cmd):
        self.start_session_ = start_session_cmd
        if len(self.start_session_) > 0:
            self.last_init_response = self.cmd(self.start_session_)

    def check_answer(self, ans):
        if "?" in ans:
            self.unsupportedCommands += 1
        else:
            self.supportedCommands += 1

    def check_adapter(self):
        if config.OPT_DEMO:
            return
        if self.unsupportedCommands == 0:
            return

        if self.supportedCommands > 0:
            self.lastMessage = "\n\n\tFake adapter !!!\n\n"
        else:
            self.lastMessage = "\n\n\tBroken or unsupported adapter !!!\n\n"

    def init_can(self):
        if not config.OPT_DEMO:
            self.port.reinit()

        self.current_protocol = "can"
        self.current_address = "7e0"  # do not tuch
        self.start_session_ = ""
        self.last_cmd_time = 0
        self.l1_cache = {}
        self.not_supported_commands = {}

        if self.lf != 0:
            self.lf.write("#" * 60 + "\n# Init CAN\n" + "#" * 60 + "\n")
            self.lf.flush()

        # reset ELM
        elm_ver = self.cmd("at ws")
        self.check_answer(elm_ver)

        self.check_answer(self.cmd("at e1"))
        self.check_answer(self.cmd("at s0"))
        self.check_answer(self.cmd("at h0"))
        self.check_answer(self.cmd("at l0"))
        self.check_answer(self.cmd("at al"))

        if config.OPT_OBD_LINK and config.OPT_CAF and not self.ATCFC0:
            self.check_answer(self.cmd("AT CAF1"))
            self.check_answer(self.cmd("STCSEGR 1"))
            self.check_answer(self.cmd("STCSEGT 1"))
        else:
            self.check_answer(self.cmd("at caf0"))

        if self.ATCFC0:
            self.check_answer(self.cmd("at cfc0"))
        else:
            self.check_answer(self.cmd("at cfc1"))

        self.last_cmd_time = 0

    def set_can_500(self, addr="XXX"):
        if len(addr) == 3:
            if (
                config.OPT_CAN2 and config.OPT_STN
            ):  # for STN with FORD MS-CAN support and pinout changed by soldering
                self.cmd("STP 53")
                self.cmd("STPBR 500000")
                tmp_response = self.send_raw("0210C0")  # send anything
                if not "CAN ERROR" in tmp_response:
                    return
            self.cmd("at sp 6")
        else:
            if config.OPT_CAN2 and config.OPT_STN:
                self.cmd("STP 54")
                self.cmd("STPBR 500000")
                tmp_response = self.send_raw("0210C0")
                if not "CAN ERROR" in tmp_response:
                    return
            self.cmd("at sp 7")

    def set_can_250(self, addr="XXX"):
        if len(addr) == 3:
            if config.OPT_CAN2 and config.OPT_STN:
                self.cmd("STP 53")
                self.cmd("STPBR 250000")
                tmp_response = self.send_raw("0210C0")
                if not "CAN ERROR" in tmp_response:
                    return
            self.cmd("at sp 8")
        else:
            if config.OPT_CAN2 and config.OPT_STN:
                self.cmd("STP 54")
                self.cmd("STPBR 250000")
                tmp_response = self.send_raw("0210C0")
                if not "CAN ERROR" in tmp_response:
                    return
            self.cmd("at sp 9")

    def set_can_addr(self, addr, ecu):
        self.not_supported_commands = {}
        self.tmp_not_supported_commands = {}

        if self.current_protocol == "can" and self.current_address == addr:
            return

        if len(ecu.get("idTx", "")):
            DNAT[addr] = ecu["idTx"]
        if len(ecu.get("idRx", "")):
            SNAT[addr] = ecu["idRx"]

        if self.lf != 0:
            self.lf.write(
                "#" * 60
                + "\n#connect to: "
                + ecu.get("ecuname", "")
                + " Addr:"
                + addr
                + "\n"
                + "#" * 60
                + "\n"
            )
            self.lf.flush()

        self.current_protocol = "can"
        self.current_address = addr
        self.start_session_ = ""
        self.last_cmd_time = 0
        self.l1_cache = {}
        self.clear_cache()

        if addr in list(DNAT.keys()):
            TXa = DNAT[addr]
        else:
            TXa = "undefined"

        if addr in list(SNAT.keys()):
            RXa = SNAT[addr]
        else:
            RXa = "undefined"

        if len(TXa) == 8:  # 29bit CANId
            self.check_answer(self.cmd("at cp " + TXa[:2]))
            self.check_answer(self.cmd("at sh " + TXa[2:]))
        else:
            self.check_answer(self.cmd("at sh " + TXa))

        self.check_answer(self.cmd("at fc sh " + TXa))
        self.check_answer(self.cmd("at fc sd 30 00 00"))  # status BS STmin
        self.check_answer(self.cmd("at fc sm 1"))
        self.check_answer(self.cmd("at st ff"))  # reset adaptive timing step 1
        self.check_answer(self.cmd("at at 0"))  # reset adaptive timing step 2

        # some models of cars may have different CAN buses
        if (
            "brp" in list(ecu.keys()) and "1" in ecu["brp"] and "0" in ecu["brp"]
        ):  # double brp
            if self.lf != 0:
                self.lf.write(
                    "#" * 60
                    + "\n#    Double BRP, try CAN250 and then CAN500\n"
                    + "#" * 60
                    + "\n"
                )
                self.lf.flush()
            self.set_can_250(TXa)
            tmp_response = self.send_raw("0210C0")  # send any command
            if "CAN ERROR" in tmp_response:  # not 250!
                ecu["brp"] = "0"  # brp = 0
                self.set_can_500(TXa)
            else:  # 250!
                ecu["brp"] = "1"  # brp = 1
        else:  # not double brp
            if "brp" in list(ecu.keys()) and "1" in ecu["brp"]:
                self.set_can_250(TXa)
            else:
                self.set_can_500(TXa)

        self.check_answer(self.cmd("at at 1"))  # reset adaptive timing step 3
        self.check_answer(self.cmd("at cra " + RXa))

        if config.OPT_OBD_LINK and config.OPT_CAF:
            self.check_answer(self.cmd("STCFCPA " + TXa + ", " + RXa))

        self.check_adapter()

    def init_iso(self):
        if not config.OPT_DEMO:
            self.port.reinit()

        self.current_protocol = "iso"
        self.current_sub_protocol = ""
        self.current_address = ""
        self.start_session_ = ""
        self.last_cmd_time = 0
        self.last_init_response = ""
        self.not_supported_commands = {}

        if self.lf != 0:
            self.lf.write(
                "#" * 60
                + "\n#["
                + log_timestamp_str()
                + "] Init ISO\n"
                + "#" * 60
                + "\n"
            )
            self.lf.flush()
        self.check_answer(self.cmd("at ws"))
        self.check_answer(self.cmd("at e1"))
        self.check_answer(self.cmd("at s1"))
        self.check_answer(self.cmd("at l1"))
        self.check_answer(self.cmd("at d1"))

    def set_iso_addr(self, addr, ecu):

        self.not_supported_commands = {}
        self.tmp_not_supported_commands = {}

        if (
            self.current_protocol == "iso"
            and self.current_address == addr
            and self.current_sub_protocol == ecu.get("protocol", "")
        ):
            return

        if self.lf != 0:
            self.lf.write(
                "#" * 60
                + "\n#connect to: "
                + ecu.get("ecuname", "")
                + " Addr:"
                + addr
                + " Protocol:"
                + ecu.get("protocol", "")
                + "\n"
                + "#" * 60
                + "\n"
            )
            self.lf.flush()

        if self.current_protocol == "iso":
            self.check_answer(self.cmd("82"))  # close previous session

        self.current_protocol = "iso"
        self.current_sub_protocol = ecu.get("protocol", "")
        self.current_address = addr
        self.start_session_ = ""
        self.last_cmd_time = 0
        self.last_init_response = ""
        self.clear_cache()

        self.check_answer(self.cmd("at sh 81 " + addr + " f1"))  # set address
        self.check_answer(self.cmd("at sw 96"))  # wakeup message period 3 seconds
        self.check_answer(self.cmd("at wm 81 " + addr + " f1 3E"))  # set wakeup message
        # self.check_answer(self.cmd("at wm 82 "+addr+" f1 3E01"))       #set wakeup message
        self.check_answer(self.cmd("at ib10"))  # baud rate 10400
        self.check_answer(self.cmd("at st ff"))  # set timeout to 1 second
        self.check_answer(self.cmd("at at 0"))  # disable adaptive timing

        if "PRNA2000" in ecu.get("protocol", "").upper() or config.OPT_SI:
            self.cmd("at sp 4")  # slow init mode 4
            if len(ecu.get("slowInit", "")) > 0:
                self.cmd("at iia " + ecu["slowInit"])  # address for slow init
            response = self.last_init_response = self.cmd(
                "at si"
            )  # for slow init mode 4
            if "ERROR" in response and len(ecu.get("fastInit", "")) > 0:
                ecu["protocol"] = ""
                if self.lf != 0:
                    self.lf.write("### Try fast init\n")
                    self.lf.flush()

                    # if 'PRNA2000' not in ecu['protocol'].upper() :
        if "OK" not in self.last_init_response:
            self.cmd("at sp 5")  # fast init mode 5
            self.last_init_response = self.cmd("at fi")  # perform fast init mode 5
            # self.last_init_response = self.cmd("81")         #init bus

        self.check_answer(self.cmd("at at 1"))  # enable adaptive timing

        self.check_answer(self.cmd("81"))  # start session

        self.check_adapter()

    # check what is the maximum number of parameters that module can handle in one request
    def check_module_performance_level(self, data_ids):
        performance_levels = [3, 2]

        for level in performance_levels:
            is_level_accepted = self.check_performance_level(level, data_ids)
            if is_level_accepted:
                break

        if self.performance_mode_level == 3 and config.OPT_OBD_LINK:
            for level in reversed(
                list(range(4, 100))
            ):  # 26 - 1 = 25  parameters per page
                is_level_accepted = self.check_performance_level(level, data_ids)
                if is_level_accepted:
                    return

    def check_performance_level(self, level, data_ids):
        if len(data_ids) >= level:
            predicted_response_length = (
                2  # length of string ReadDataByIdentifier service byte - 0x22
            )
            did_number = 0
            param_to_send = ""

            if level > 3:  # Send multiframe command for more than 3 dataids
                # Some modules can return NO DATA if multi frame command is sent after some no activity time
                # Sending anything before main command usually helps that command to be accepted
                self.send_cmd("22" + list(data_ids.keys())[0] + "1")

            # while there is some dataids left and actual number of used dids
            # is lower than requeseted performance level
            while did_number < len(data_ids) and len(param_to_send) / 4 < level:
                # get another did
                did = list(data_ids)[did_number]
                did_number += 1

                # exclude did_supported_in_range did
                # sent seperatly - response provided
                # sent in multi did request - empty response
                # these are available only in injection module
                if not int("0x" + did, 16) % 0x20 and self.current_address == "7A":
                    continue

                # check if it is supported
                resp = self.request("22" + did)
                if not any(s in resp for s in ["?", "NR"]):
                    # add it to the list
                    param_to_send += did
                    predicted_response_length += (
                        len(self.get_from_cache("22" + did).replace(" ", "")) - 2
                    )

            # if module does not support any did, we cannot check performance level
            if not param_to_send:
                return False

            cmd = "22" + param_to_send
            resp = self.send_cmd(cmd).replace(" ", "")  # check response length first
            if (
                any(s in resp for s in ["?", "NR"])
                or len(resp) < predicted_response_length
            ):
                return False

            self.performance_mode_level = len(param_to_send) // 4
            return True
        return False

    def get_refresh_rate(self):
        refresh_rate = 0

        if not self.screen_refresh_time:
            return refresh_rate

        refresh_rate = 1 // self.screen_refresh_time
        self.screen_refresh_time = 0
        return refresh_rate

    def reset_elm(self):
        self.cmd("at z")
