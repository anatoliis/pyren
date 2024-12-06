#!/usr/bin/env python3
import atexit
import os
import signal
import string
import subprocess
import sys

import mod_globals
from pyren3.mod_elm import ELM

try:
    import webbrowser
except ImportError:
    pass

# Snippet from http://home.wlu.edu/~levys/software/kbhit.py

import termios

from select import select


class KBHit:
    def __init__(self):
        self.set_get_character_term()

    def set_get_character_term(self):
        """Creates a KBHit object that you can call to do various keyboard things."""

        # Save the terminal settings
        self.file_desriptor = sys.stdin.fileno()
        self.new_term = termios.tcgetattr(self.file_desriptor)
        self.old_term = termios.tcgetattr(self.file_desriptor)

        # New terminal setting unbuffered
        self.new_term[3] = self.new_term[3] & ~termios.ICANON & ~termios.ECHO

        termios.tcsetattr(self.file_desriptor, termios.TCSANOW, self.new_term)

        # Support normal-terminal reset at exit
        atexit.register(self.set_normal_term)

    def set_normal_term(self):
        """Resets to normal terminal.  On Windows this is a no-op."""
        termios.tcsetattr(self.file_desriptor, termios.TCSANOW, self.old_term)

    @staticmethod
    def get_character():
        """Returns a keyboard character after kbhit() has been called.
        Should not be called in the same program as getarrow().
        """
        s = sys.stdin.read(1)

        if len(s) == 0 or ord(s) == 0 or ord(s) == 0xE0:
            s = sys.stdin.read(1)

        return s

    @staticmethod
    def get_arrow():
        """Returns an arrow-key code after kbhit() has been called. Codes are
        0 : up
        1 : right
        2 : down
        3 : left
        Should not be called in the same program as getch().
        """
        c = sys.stdin.read(3)[2]
        vals = [65, 67, 66, 68]

        return vals.index(ord(c.decode("utf-8")))

    @staticmethod
    def keyboard_hit():
        """Returns True if keyboard character was hit, False otherwise."""
        try:
            dr, _, _ = select([sys.stdin], [], [], 0)
        except Exception:
            return False
        else:
            return bool(dr)


def Choice(list, question):
    """Util for make simple choice"""
    d = {}
    c = 1
    exitNumber = 0
    for s in list:
        if s.lower() == "<up>" or s.lower() == "<exit>":
            exitNumber = c
            print("%-2s - %s" % ("Q", pyren_encode(s)))
            d["Q"] = s
        else:
            print("%-2s - %s" % (c, pyren_encode(s)))
            d[str(c)] = s
        c = c + 1

    while True:
        try:
            ch = input(question)
        except (KeyboardInterrupt, SystemExit):
            print()
            print()
            sys.exit()
        if ch == "q":
            ch = "Q"
        if ch == "cmd":
            mod_globals.opt_cmd = True
        if ch in d.keys():
            return [d[ch], ch]


def choice_long(list_: list[str], question: str, header: str = ""):
    """Util for make choice from long list"""
    d = {}
    char = 1
    page = 0
    page_size = 20

    for s in list_:
        if s.lower() == "<up>" or s.lower() == "<exit>":
            d["Q"] = s
        else:
            d[str(char)] = s
        char = char + 1

    while True:
        clear_screen()

        if len(header):
            print(pyren_encode(header))

        char = page * page_size
        for s in list_[page * page_size : (page + 1) * page_size]:
            char = char + 1
            if s.lower() == "<up>" or s.lower() == "<exit>":
                print("%-2s - %s" % ("Q", pyren_encode(s)))
            else:
                print("%-2s - %s" % (char, pyren_encode(s)))

        if len(list_) > page_size:
            if page > 0:
                print("%-2s - %s" % ("P", "<prev page>"))
            if (page + 1) * page_size < len(list_):
                print("%-2s - %s" % ("N", "<next page>"))

        while True:
            try:
                char = input(question)
            except (KeyboardInterrupt, SystemExit):
                print("\n\n")
                sys.exit()

            if char == "q":
                char = "Q"
            if char == "p":
                char = "P"
            if char == "n":
                char = "N"

            if char == "N" and (page + 1) * page_size < len(list_):
                page = page + 1
                break
            if char == "P" and page > 0:
                page = page - 1
                break

            if char == "cmd":
                mod_globals.opt_cmd = True
                print("mod_globals.opt_cmd set to 'True'")
            if char in d.keys():
                return [d[char], char]


def ChoiceFromDict(dict, question, showId=True):
    """Util for make choice from dictionary"""
    d = {}
    c = 1
    for k in sorted(dict.keys()):
        s = dict[k]
        if k.lower() == "<up>" or k.lower() == "<exit>":
            print("%s - %s" % ("Q", pyren_encode(s)))
            d["Q"] = k
        else:
            if showId:
                print("%s - (%s) %s" % (c, pyren_encode(k), pyren_encode(s)))
            else:
                print("%s - %s" % (c, pyren_encode(s)))
            d[str(c)] = k
        c = c + 1

    while True:
        try:
            char = input(question)
        except (KeyboardInterrupt, SystemExit):
            print("\n\n")
            sys.exit()
        if char == "q":
            char = "Q"
        if char in list(d.keys()):
            return [d[char], char]


def pyren_encode(inp):
    return inp


def pyren_decode(inp):
    return inp


def pyren_decode_i(inp):
    return inp.decode(sys.stdout.encoding, errors="ignore")


def clear_screen():
    # https://docs.microsoft.com/en-us/windows/console/console-virtual-terminal-sequences
    # [2J   - clear entire screen
    # [x;yH - move cursor to x:y
    sys.stdout.write(chr(27) + "[2J" + chr(27) + "[;H")


def up_screen():
    sys.stdout.write(chr(27) + "[;H")


def hex_vin_plus_crc(vin, plus_crc: bool = True):
    '''The VIN must be composed of 17 alphanumeric characters apart from "I" and "O"'''

    # VIN    ='VF1LM1B0H11111111'
    vin = vin.upper()
    hex_vin = ""
    crc = 0xFFFF

    for char in vin:  # for every byte in VIN
        b = ord(char)  # get ASCII
        hex_vin = hex_vin + hex(b)[2:].upper()
        for i in range(8):  # for every bit
            if (crc ^ b) & 0x1:
                crc = crc >> 1
                crc = crc ^ 0x8408
                b = b >> 1
            else:
                crc = crc >> 1
                b = b >> 1

    # invert
    crc = crc ^ 0xFFFF

    # swap bytes
    b1 = (crc >> 8) & 0xFF
    b2 = crc & 0xFF
    crc = ((b2 << 8) | b1) & 0xFFFF

    s_crc = hex(crc)[2:].upper()
    s_crc = "0" * (4 - len(s_crc)) + s_crc

    # result
    if plus_crc:
        return hex_vin + s_crc
    else:
        return hex_vin


# Test
if __name__ == "__main__":
    kb = KBHit()

    print("Hit any key, or ESC to exit")

    while True:
        if kb.keyboard_hit():
            c = kb.get_character()
            if ord(c) == 27:  # ESC
                break
            print(c)

    kb.set_normal_term()


# Convert ASCII to HEX


def ASCIITOHEX(ATH):

    ATH = ATH.upper()
    hexATH = "".join("{:02X}".format(ord(c)) for c in ATH)

    # Result
    return hexATH


# Convert ch str to int then to Hexadecimal digits


def StringToIntToHex(DEC):

    DEC = int(DEC)
    hDEC = hex(DEC)

    # Result
    return hDEC[2:].zfill(2).upper()


def load_dump_to_elm(ecu_name: str, elm: ELM):
    ecu_dump = {}

    files_list = []
    for root, dirs, files in os.walk("./dumps"):
        for file_ in files:
            if (ecu_name + ".txt") in file_:
                files_list.append(file_)

    if len(files_list) == 0:
        return
    files_list.sort()
    dump_name = os.path.join("./dumps/", files_list[-1])

    # debug
    print("Loading:", dump_name)

    df = open(dump_name, "rt")
    lines = df.readlines()
    df.close()

    for l in lines:
        l = l.strip().replace("\n", "")
        if ":" in l:
            req, rsp = l.split(":")
            ecu_dump[req] = rsp

    elm.setDump(ecu_dump)


def chk_dir_tree():
    """Check direcories"""
    if not os.path.exists("./cache"):
        os.makedirs("./cache")
    if not os.path.exists("./csv"):
        os.makedirs("./csv")
    if not os.path.exists("./logs"):
        os.makedirs("./logs")
    if not os.path.exists("./dumps"):
        os.makedirs("./dumps")
    if not os.path.exists("./macro"):
        os.makedirs("./macro")
    if not os.path.exists("./doc"):
        os.makedirs("./doc")
    if not os.path.exists("../MTCSAVE"):
        os.makedirs("../MTCSAVE")


def get_vin(de, elm, getFirst=False):
    """getting VINs from every ECU"""
    """    de  - list of detected ECUs  """
    """    elm - reference to ELM class """

    m_vin = set([])
    for e in de:

        # init elm
        if mod_globals.opt_demo:  # try to load dump
            load_dump_to_elm(e["ecuname"], elm)
        else:
            if e["pin"].lower() == "can":
                elm.init_can()
                elm.set_can_addr(e["dst"], e)
            else:
                elm.init_iso()
                elm.set_iso_addr(e["dst"], e)
            elm.start_session(e["startDiagReq"])

        # read VIN
        if e["stdType"].lower() == "uds":
            rsp = elm.request(req="22F190", positive="62", cache=False)[9:59]
        else:
            rsp = elm.request(req="2181", positive="61", cache=False)[6:56]

        try:
            vin = bytes.fromhex(rsp.replace(" ", "")).decode("utf-8")
        except:
            continue

        # debug
        # print e['dst'],' : ', vin

        if len(vin) == 17:
            m_vin.add(vin)
            if getFirst:
                return vin

    l_vin = m_vin

    if os.path.exists("savedVIN.txt"):
        with open("savedVIN.txt") as vinfile:
            vinlines = vinfile.readlines()
            for l in vinlines:
                l = l.strip()
                if "#" in l:
                    continue
                if len(l) == 17:
                    l_vin.add(l.upper())

    if len(l_vin) == 0 and not getFirst:
        print("ERROR!!! Can't find any VIN. Check connection")
        exit()

    if len(l_vin) < 2:
        try:
            ret = next(iter(l_vin))
        except:
            ret = ""
        return ret

    print("\nFound ", len(l_vin), " VINs\n")

    choice = Choice(l_vin, "Choose VIN : ")

    return choice[0]


def debug(tag: str, s: str) -> None:
    if mod_globals.opt_debug and mod_globals.debug_file is not None:
        mod_globals.debug_file.write("### " + tag + "\n")
        mod_globals.debug_file.write('"' + s + '"\n')


def is_hex(string_: str) -> bool:
    return all(char in string.hexdigits for char in string_)


def kill_server() -> None:
    if mod_globals.doc_server_proc is not None:
        os.kill(mod_globals.doc_server_proc.pid, signal.SIGTERM)


def show_doc(addr, id):
    if mod_globals.vin == "" and not mod_globals.opt_sd:
        return

    if mod_globals.doc_server_proc is None:
        mod_globals.doc_server_proc = subprocess.Popen(
            ["python3", "-m", "http.server", "59152"]
        )
        atexit.register(kill_server)

    if mod_globals.opt_sd and id != "":
        url = "http://127.0.0.1:59152/doc/" + id[1:] + ".htm"
    else:
        url = "http://127.0.0.1:59152/doc/" + mod_globals.vin + ".htm" + id
    webbrowser.open(url, new=0)
