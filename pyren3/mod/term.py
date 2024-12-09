import os
import re
import string
import sys
import time

from pyren3 import config
from pyren3.mod import utils
from pyren3.mod.elm import ELM, dnat, pyren_time, snat

macro = {}
var = {}
cmd_delay = 0
stack = []

auto_macro = ""
auto_dia = False
debug_mode = False

key_pressed = ""

if config.OS == "nt":
    import colorama

    colorama.init()
else:
    try:
        import androidhelper as android

        config.OS = "android"
    except Exception:
        try:
            import android

            config.OS = "android"
        except Exception:
            pass

if config.OS != "android":
    from serial.tools import list_ports


def init_macro():
    global macro
    macro = {}


def init_var():
    global var
    var = {}
    # predefined variables
    var["$addr"] = "7A"
    var["$txa"] = "7E0"
    var["$rxa"] = "7E8"
    var["$prompt"] = "ELM"


def pars_macro(file):
    global macro
    global var

    print("openning file:", file)
    f = open(file, "rt")
    lines = f.readlines()
    f.close()

    macroname = ""
    macrostrings = []
    line_num = 0
    for l in lines:
        line_num += 1
        l = l.split("#")[0]  # remove comments
        l = l.strip()
        if l == "":
            continue
        if "{" in l:
            if macroname == "":
                literals = l.split("{")
                macroname = literals[0].strip()
                macroname = macroname.replace(" ", "_").replace("\t", "_")
                macrostrings = []
                if len(literals) > 1 and literals[1] != "":
                    macrostrings.append(literals[1])
                continue
            else:
                print("Error: empty macro name in line:", line_num)
                macro = {}
                var = {}
                return
        if "}" in l:
            if macroname != "":
                literals = l.split("}")
                cmd = literals[0].strip()
                if cmd != "":
                    macrostrings.append(cmd)
                macro[macroname] = macrostrings
                macroname = ""
                macrostrings = []
                continue
            else:
                print("Error: unexpected end of macro in line:", line_num)
                macro = {}
                var = {}
                return
        m = re.search("\$\S+\s*=\s*\S+", l)
        if m and macroname == "":
            # variable definition
            r = m.group(0).replace(" ", "").replace("\t", "")
            rl = r.split("=")
            var[rl[0]] = rl[1]
        else:
            macrostrings.append(l)


def load_macro(mf=""):
    """
    dynamically loaded macro should have .txt extension and placed in ./macro directory
    """

    if mf == "":
        for root, dirs, files in os.walk("./macro"):
            for mfile in files:
                if mfile.endswith(".txt"):
                    full_path = os.path.join("./macro/", mfile)
                    pars_macro(full_path)
    else:
        pars_macro(mf)


def print_help():
    """
    [h]elp                 - this help
    [q]uit, [e]xit, end    - exit from terminal
    wait|sleep x           - wait x seconds
    """
    global var
    global macro

    print(print_help.__doc__)

    print("Variables:")
    for v in list(var.keys()):
        print("  " + v + " = " + var[v])
    print()
    print("Macros:")
    for m in list(macro.keys()):
        print("  " + m)
    print()


def optParser():
    """Parsing of command line parameters. User should define at least com port name"""

    import argparse

    global auto_macro
    global auto_dia
    global debug_mode

    parser = argparse.ArgumentParser(description="pyRen terminal")

    parser.add_argument("-p", help="ELM327 com port name", dest="port", default="")

    parser.add_argument(
        "-r",
        help="com port rate during diagnostic session {38400[default],57600,115200,230400,500000}",
        dest="rate",
        default="38400",
    )

    parser.add_argument(
        "-m",
        help="macro file name",
        dest="macro",
        default="",
    )

    parser.add_argument("--log", help="log file name", dest="logfile", default="")

    parser.add_argument(
        "--demo",
        help="for debuging purpose. Work without car and ELM",
        dest="demo",
        default=False,
        action="store_true",
    )

    parser.add_argument(
        "--si", help="try SlowInit first", dest="si", default=False, action="store_true"
    )

    parser.add_argument(
        "--cfc",
        help="turn off automatic FC and do it by script",
        dest="cfc",
        default=False,
        action="store_true",
    )

    parser.add_argument(
        "--caf",
        help="turn on CAN Auto Formatting. Available only for OBDLink",
        dest="caf",
        default=True,
        action="store_true",
    )

    parser.add_argument(
        "--n1c",
        help="turn off L1 cache",
        dest="n1c",
        default=False,
        action="store_true",
    )

    parser.add_argument(
        "-vv",
        "--verbose",
        help="show verbose output (unused)",
        dest="verb",
        default=False,
        action="store_true",
    )

    parser.add_argument(
        "--dialog",
        help="show dialog for selecting macro",
        dest="dia",
        default=False,
        action="store_true",
    )

    parser.add_argument(
        "--debug",
        help="for debug purpose only",
        dest="dbg",
        default=False,
        action="store_true",
    )

    parser.add_argument(
        "--minordtc",
        help="use to show all DTCs without checking computation formula",
        dest="minordtc",
        default=False,
        action="store_true",
    )

    options = parser.parse_args()

    if not options.port and config.OS != "android":
        parser.print_help()
        iterator = sorted(list(list_ports.comports()))
        print("")
        print("Available COM ports:")
        for port, desc, hwid in iterator:
            print("%-30s \n\tdesc: %s \n\thwid: %s" % (port, desc, hwid))
        print("")
        exit(2)
    else:
        config.opt_port = options.port
        config.opt_rate = int(options.rate)
        config.opt_speed = int(options.rate)
        auto_macro = options.macro
        config.opt_log = options.logfile
        config.opt_demo = options.demo
        config.opt_si = options.si
        config.opt_cfc0 = options.cfc
        config.opt_caf = options.caf
        config.opt_n1c = options.n1c
        config.opt_minordtc = options.minordtc
        auto_dia = options.dia
        debug_mode = options.dbg


class FileChooser:
    lay = """<?xml version="1.0" encoding="utf-8"?>
<RelativeLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent"
    android:layout_height="wrap_content" >

    <ScrollView
        android:layout_width="fill_parent"
        android:layout_height="fill_parent" >

        <RelativeLayout
            android:id="@+id/launcher"
            xmlns:android="http://schemas.android.com/apk/res/android"
            android:layout_width="fill_parent"
            android:layout_height="wrap_content">

            <TextView
                android:id="@+id/tx_folder"
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:layout_alignParentTop="true"
                android:layout_marginTop="20dp"
                android:text="Folder"/>
            <Spinner
                android:id="@+id/sp_folder"
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:layout_alignParentLeft="true"
                android:layout_below="@+id/tx_folder"/>

            <TextView
                android:id="@+id/tx_macro"
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:layout_alignParentLeft="true"
                android:layout_marginTop="20dp"
                android:layout_below="@+id/sp_folder"
                android:text="Macro" />
            <Spinner
                android:id="@+id/sp_macro"
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:layout_below="@id/tx_macro"/>

            <Button
                android:id="@+id/bt_exit"
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:layout_alignParentLeft="true"
                android:layout_marginTop="50dp"
                android:layout_below="@id/sp_macro"
                android:text="Exit" />

            <Button
                android:id="@+id/bt_start"
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:layout_marginTop="50dp"
                android:layout_marginLeft="100dp"
                android:layout_below="@id/sp_macro"
                android:layout_toRightOf="@id/bt_exit"
                android:text="Start" />

        </RelativeLayout>

    </ScrollView>

</RelativeLayout>"""
    droid = None
    folderList = []
    macroList = []

    def newFolderSelected(self):
        self.macroList = []
        fo = self.folder
        self.macroList = [
            f
            for f in os.listdir(fo)
            if os.path.isfile(fo + f) and f.lower().endswith(".cmd")
        ]
        self.droid.fullSetList("sp_macro", self.macroList)

    def eventloop(self):
        while True:
            sf = self.folderList[
                int(
                    self.droid.fullQueryDetail("sp_folder").result[
                        "selectedItemPosition"
                    ]
                )
            ]
            if sf != self.folder:
                self.folder = sf
                self.newFolderSelected()
            event = self.droid.eventWait(50).result
            if event is None:
                continue
            if event["name"] == "click":
                id = event["data"]["id"]
                if id == "bt_start":
                    ma = self.macroList[
                        int(
                            self.droid.fullQueryDetail("sp_macro").result[
                                "selectedItemPosition"
                            ]
                        )
                    ]
                    return sf + ma
                if id == "bt_exit":
                    sys.exit()

    def __init__(self):
        fo = "./macro/"
        self.folderList = [
            fo + f + "/" for f in os.listdir(fo) if os.path.isdir(fo + f)
        ]
        self.folder = fo

    def choose(self):
        try:
            import androidhelper as android

            config.OS = "android"
        except:
            try:
                import android

                config.OS = "android"
            except:
                pass

        if config.OS != "android":
            try:
                # Python2
                import tkinter as tk
                import tkinter.ttk
                import tkinter.filedialog as filedialog
            except ImportError:
                # Python3
                import tkinter as tk
                import tkinter.ttk as ttk
                import tkinter.filedialog as filedialog

            root = tk.Tk()
            root.withdraw()

            my_filetypes = [("command files", ".cmd")]

            fname = filedialog.askopenfilename(
                parent=root,
                initialdir="./macro",
                title="Please select a file:",
                filetypes=my_filetypes,
            )

            return fname

        else:
            try:
                self.droid = android.Android()
                self.droid.fullShow(self.lay)
                self.folderList.insert(0, "./macro/")
                self.droid.fullSetList("sp_folder", self.folderList)
                return self.eventloop()
            finally:
                self.droid.fullDismiss()


def play_macro(mname, elm):
    global macro
    global var
    global stack

    if mname in stack:
        print("Error: recursion prohibited:", mname)
        return
    else:
        stack.append(mname)

    for l in macro[mname]:

        if l in list(macro.keys()):
            play_macro(l, elm)
            continue

        proc_line(l, elm)

    stack.remove(mname)


def run_init_function(mname, elm):
    global var

    if mname in ["init_can_250", "can250", "init_can_500", "can500"]:
        elm.init_can()
        if mname in ["init_can_250", "can250"]:
            elm.set_can_addr(var["$addr"], {"brp": "1"})
        else:
            elm.set_can_addr(var["$addr"], {})
    elif mname in ["init_iso_slow", "slow", "init_iso_fast", "fast"]:
        elm.init_iso()
        if mname in ["init_iso_slow", "slow"]:
            elm.set_iso_addr(var["$addr"], {"protocol": "PRNA2000"})
        else:
            elm.set_iso_addr(var["$addr"], {})
    else:
        print(("Unrecognized init command: ", mname))


def term_cmd(c, elm):
    global var
    rsp = elm.request(c, cache=False)
    # rsp = elm.cmd(rcmd)
    var["$lastResponse"] = rsp
    return rsp


def bit_cmd(l, elm, fnc="set_bits"):
    global var

    error_msg1 = """ERROR: command should have 5 parameters: 
    <command> <lid> <rsp_len> <offset> <hex mask> <hex value>
        <lid> - ECUs local identifier. Length should be 2 simbols for KWP or 4 for CAN
        <rsp_len> - lengt of command response including positive response bytes, equals MinBytes from ddt db
        <offset> - offeset in bytes to first changed byte (starts from 1 not 0) 
        <hex mask> - bit mask for changed bits, 1 - changable, 0 - untachable
        <hex value> - bit value
    <hex mask> and <hex value> should have equal length
    
    """
    error_msg2 = """ERROR: command should have 6 parameters: 
    <command> <lid> <rsp_len> <offset> <hex mask> <hex value> <label>
        <lid> - ECUs local identifier. Length should be 2 simbols for KWP or 4 for CAN
        <rsp_len> - lengt of command response including positive response bytes, equals MinBytes from ddt db
        <offset> - offeset in bytes to first changed byte (starts from 1 not 0) 
        <hex mask> - bit mask for changed bits, 1 - changable, 0 - untachable
        <hex value> - bit value
        <label> - label to go
    <hex mask> and <hex value> should have equal length

    """

    error_msg3 = """ERROR: command should have 4 or 7 parameters: 
    <command> <lid> <rsp_len> <offset> <hex mask> <hex value> <label>
        <lid> - ECUs local identifier. Length should be 2 simbols for KWP or 4 for CAN
        <rsp_len> - lengt of command response including positive response bytes, equals MinBytes from ddt db
        <offset> - offeset in bytes to first changed byte (starts from 1 not 0) 
        <hex mask> - bit mask for changed bits, 1 - changable, 0 - untachable
        <val step> - value step
        <val offset> - value offset
        <val divider> - value divider

    """
    if fnc not in ["set_bits", "xor_bits", "exit_if", "exit_if_not"] and fnc not in [
        "goto_if",
        "goto_if_not",
        "value",
    ]:
        print("\nERROR: Unknown function\n")
        return

    par = l.strip().split(" ")

    if fnc in ["set_bits", "xor_bits", "exit_if", "exit_if_not"]:
        error_msg = error_msg1
        if len(par) != 5:
            print(error_msg)
            return

    if fnc in ["goto_if", "goto_if_not"]:
        error_msg = error_msg2
        if len(par) != 6:
            print(error_msg)
            return

    if fnc in ["value"]:
        error_msg = error_msg3
        if len(par) == 4:
            par = par + ["1", "0", "1"]
        if len(par) != 7:
            print(error_msg)
            return

    try:
        lid = par[0].strip()
        lng = int(par[1].strip())
        off = int(par[2].strip()) - 1
        mask = par[3].strip()
        val = par[4].strip()
        if fnc in ["goto_if", "goto_if_not"]:
            go = par[5].strip()
        if fnc in ["value"]:
            val = "0" * len(mask)
            stp = par[4].strip()
            ofs = par[5].strip()
            div = par[6].strip()
    except:
        print(error_msg)
        return

    if len(lid) in [2, 4] and off >= 0 and off <= lng:
        if fnc not in ["value"] and (len(mask) != len(val)):
            print(error_msg)
            return
    else:
        print(error_msg)
        return

    if len(lid) == 2:  # KWP
        rcmd = "21" + lid
    else:  # CAN
        rcmd = "22" + lid

    rsp = term_cmd(rcmd, elm)
    rsp = rsp.replace(" ", "")[: lng * 2].upper()

    if fnc not in ["value"]:
        print("read  value:", rsp)

    if len(rsp) != lng * 2:
        print("\nERROR: Length is unexpected\n")
        if fnc.startswith("exit"):
            sys.exit()
        return

    if not all(c in string.hexdigits for c in rsp):
        if fnc.startswith("exit"):
            sys.exit()
        print("\nERROR: Wrong simbol in response\n")
        return

    pos_rsp = ("6" + rcmd[1:]).upper()
    if not rsp.startswith(pos_rsp):
        if fnc.startswith("exit"):
            sys.exit()
        print("\nERROR: Not positive response\n")
        return

    diff = 0
    i = 0
    int_val = 0
    while i < len(mask) // 2:
        c_by = int(rsp[(off + i) * 2 : (off + i) * 2 + 2], 16)
        c_ma = int(mask[i * 2 : i * 2 + 2], 16)
        c_va = int(val[i * 2 : i * 2 + 2], 16)

        if fnc == "xor_bits":
            n_by = c_by ^ (c_va & c_ma)
        elif fnc == "set_bits":
            n_by = (c_by & ~c_ma) | c_va
        else:
            n_by = c_by & c_ma
            int_val = int_val * 256 + n_by
            if (c_by & c_ma) != (c_va & c_ma):
                diff += 1
            i += 1
            continue

        str_n_by = hex(n_by & 0xFF).upper()[2:].zfill(2)

        n_rsp = rsp[0 : (off + i) * 2] + str_n_by + rsp[(off + i + 1) * 2 :]
        rsp = n_rsp
        i += 1

    if fnc == "exit_if":
        if diff == 0:
            print("Match. Exit")
            sys.exit()
        else:
            print("Not match. Continue")
            return

    if fnc == "exit_if_not":
        if diff != 0:
            print("Not match. Exit")
            sys.exit()
        else:
            print("Match. Continue")
            return

    if fnc == "goto_if":
        if diff == 0:
            print("Match. goto:", go)
            return go
        else:
            print("Not match. Continue")
            return

    if fnc == "goto_if_not":
        if diff != 0:
            print("Not match. goto:", go)
            return go
        else:
            print("Match. Continue")
            return

    if fnc == "value":
        res = (int_val * float(stp) + float(ofs)) / float(div)
        var["$rawValue"] = str(int_val)
        var["$scaledValue"] = str(res)
        var["$hexValue"] = hex(int_val)[2:].upper()
        print(
            "# LID(",
            lid,
            ") $rawValue =",
            var["$rawValue"],
            " $scaledValue =",
            var["$scaledValue"],
            " $hexValue =",
            var["$hexValue"],
        )
        return

    if rsp[:2] == "61":
        wcmd = "3B" + rsp[2:]
    elif rsp[:2] == "62":
        wcmd = "2E" + rsp[2:]

    print("write value:", wcmd)
    print(term_cmd(wcmd, elm))


def wait_kb(ttw):
    global key_pressed

    st = pyren_time()
    kb = utils.KBHit()

    while pyren_time() < (st + ttw):
        if kb.kbhit():
            key_pressed = kb.getch()
        time.sleep(0.1)

    kb.set_normal_term()


def proc_line(l, elm):
    global macro
    global var
    global cmd_delay
    global key_pressed

    if "#" in l:
        l = l.split("#")[0]

    l = l.strip()

    if l.startswith(":"):
        print(l)
        return

    if len(l) == 0:
        return

    if l in ["q", "quit", "e", "exit", "end"]:
        sys.exit()

    if l in ["h", "help", "?"]:
        print_help()
        return

    if l in ["var"]:
        print("\n###### Variables #####")
        for v in var.keys():
            print(f"# {v:20} = {var[v]}")
        return

    if l in ["cls"]:
        utils.clearScreen()
        return

    if len(l) > 2 and l[0:3] in ["ini", "can", "slo", "fas"]:
        run_init_function(l, elm)
        return
    elif l in list(macro.keys()):
        play_macro(l, elm)
        return

    # find veriable usage
    m = re.search(".+(\$\S+)", l)
    if m:
        while m:
            vu = m.group(1)
            if vu in list(var.keys()):
                l = re.sub("\\" + vu, var[vu], l)
            else:
                print("Error: unknown variable", vu)
                return
            m = re.search(".+(\$\S+)", l)
        print("#(subst)", l)

    m = re.search("\$\S+\s*=\s*\S+", l)
    if m:
        # find variable definition
        r = m.group(0).replace(" ", "").replace("\t", "")
        rl = r.split("=")
        var[rl[0]] = rl[1]
        if rl[0] == "$addr":
            if var["$addr"].upper() in list(dnat.keys()):
                var["$txa"] = dnat[var["$addr"].upper()]
                var["$rxa"] = snat[var["$addr"].upper()]
                elm.currentaddress = var["$addr"].upper()
        return

    l_parts = l.split()
    if len(l_parts) > 0 and l_parts[0] in ["wait", "sleep"]:
        try:
            wait_kb(float(l_parts[1]))
            return
        except:
            pass

    if len(l_parts) > 0 and l_parts[0] in ["ses", "session"]:
        try:
            elm.startSession = l_parts[1]
            l = l_parts[1]
        except:
            pass

    if len(l_parts) > 0 and l_parts[0] in ["delay"]:
        cmd_delay = float(l_parts[1])
        return

    if l.lower().startswith("set_bits"):
        bit_cmd(l.lower()[8:], elm, fnc="set_bits")
        return

    if l.lower().startswith("xor_bits"):
        bit_cmd(l.lower()[8:], elm, fnc="xor_bits")
        return

    if l.lower().startswith("exit_if_not"):
        bit_cmd(l.lower()[11:], elm, fnc="exit_if_not")
        return

    if l.lower().startswith("exit_if"):
        bit_cmd(l.lower()[7:], elm, fnc="exit_if")
        return

    if l.lower().startswith("goto_if_not"):
        go = bit_cmd(l.lower()[11:], elm, fnc="goto_if_not")
        return go

    if l.lower().startswith("goto_if"):
        go = bit_cmd(l.lower()[7:], elm, fnc="goto_if")
        return go

    if l.lower().startswith("if_key"):
        if len(l_parts) != 3 or l_parts[1] != key_pressed:
            return
        else:
            key_pressed = ""
            return l_parts[2]

    if l.lower().startswith("value"):
        val = bit_cmd(l.lower()[5:], elm, fnc="value")
        return

    if len(l_parts) > 0 and l_parts[0] in ["go", "goto"]:
        print(l)
        return l_parts[1]

    if len(l_parts) > 0 and l_parts[0] in ["var", "variable"]:
        print(l)
        return

    if l.lower().startswith("_"):
        print(elm.send_raw(l[1:]))
    else:
        print(term_cmd(l, elm))

    if cmd_delay > 0:
        print("# delay:", cmd_delay)
        wait_kb(cmd_delay)


def main():
    global auto_macro
    global auto_dia
    global debug_mode
    global macro
    global var

    utils.chkDirTree()

    init_macro()
    init_var()
    load_macro()

    optParser()

    print("Opening ELM")
    elm = ELM(config.opt_port, config.opt_speed, True)

    # change serial port baud rate
    if not config.opt_demo and elm.port and elm.port.portType == 0:
        if config.opt_speed < config.opt_rate:
            elm.port.soft_boudrate(config.opt_rate)

    elm.currentaddress = "7A"
    elm.currentprotocol = "can"

    cmd_lines = []
    cmd_ref = 0

    if auto_dia:
        fname = FileChooser().choose()
        # debug
        # fname = './macro/test/test.cmd'
        if len(fname) > 0:
            f = open(fname, "rt")
            cmd_lines = f.readlines()
            f.close()

    if debug_mode:
        config.opt_demo = True
        elm.loadDump("./dumps/term_test.txt")
        fname = "./macro/test/test.cmd"
        if len(fname) > 0:
            f = open(fname, "rt")
            cmd_lines = f.readlines()
            f.close()

    if auto_macro != "":
        if len(auto_macro) > 2 and auto_macro[0:3] in ["ini", "can", "slo", "fas"]:
            run_init_function(auto_macro, elm)
        elif auto_macro in list(macro.keys()):
            play_macro(auto_macro, elm)
        else:
            print("Error: unknown macro name:", auto_macro)

    while True:
        print(var["$addr"] + ":" + var["$txa"] + ":" + var["$prompt"] + "#", end=" ")
        if len(cmd_lines) == 0:
            l = input()
        else:
            if cmd_ref < len(cmd_lines):
                l = cmd_lines[cmd_ref].strip()
                cmd_ref += 1
            else:
                cmd_lines = []
                l = "# end of command file"
            print(l)

        goto = proc_line(l, elm)

        if goto and len(cmd_lines):
            c_str = 0
            for c in cmd_lines:
                if c.startswith(":"):
                    if goto == c[1:].strip():
                        cmd_ref = c_str
                        break
                c_str += 1


if __name__ == "__main__":
    main()
