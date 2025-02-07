#! /usr/bin/env python3
#  -*- coding: utf-8 -*-
#
# GUI module generated by PAGE version 4.19
#  in conjunction with Tcl version 8.6
#    Dec 11, 2018 11:56:10 PM MSK  platform: Darwin


help = """  Battary SOH (State Of Health)

1) Use only USB ELM327 adapter. BT and WiFi adapters are not compatible.
2) Connect an adapter to the OBD outlet
3) Turn on ignition but not start the engine
4) Select the port with adapter
5) Enter current outdoor temperature in celsious
6) Press "Start" button. The voltage should be shown.
7) Calibrate the voltage if needed
8) Start the engine
9) Now the SOH coefficient should be shown instead of voltage

SOH > 0 The battery is good
SOH < 0 The battery is bad

"""

import datetime
import sys
import time

try:
    import tkinter as tk
    import tkinter.messagebox
except ImportError:
    import tkinter as tk
    import tkinter.messagebox

try:
    import tkinter.ttk

    py3 = False
except ImportError:
    import tkinter.ttk as ttk

    py3 = True

try:
    import serial
    from serial.tools import list_ports
except ImportError:
    print("\n\n\n\tPlease install pyserial module")
    sys.exit()

from mod_elm import ELM
import config


def set_Tk_var():
    global combobox
    global atcv
    global batTemp

    combobox = tk.StringVar()

    atcv = tk.StringVar()
    atcv.set("12.00")

    batTemp = tk.StringVar()
    batTemp.set("")


def init(top, gui, *args, **kwargs):
    global w, top_level, root
    w = gui
    top_level = top
    root = top


def destroy_window():
    # Function which closes the window.
    global top_level
    top_level.destroy()
    top_level = None


def vp_start_gui():
    """Starting point when module is the main routine."""
    global val, w, root
    root = tk.Tk()
    root.resizable(width=False, height=False)
    set_Tk_var()
    top = tl(root)
    init(root, top)
    root.mainloop()


def vp_exit_gui():
    global val, w, root
    root.destroy()
    root = None


w = None


def getPortList():
    ret = []
    iterator = sorted(list(list_ports.comports()))
    for port, desc, hwid in iterator:
        try:
            de = str(desc.encode("ascii", "ignore"))
            ret.append(port + ";" + de)
        except:
            ret.append(port + ";")
    # if '192.168.0.10:35000;WiFi' not in ret:
    #  ret.append('192.168.0.10:35000;WiFi')
    # else:
    #  ret = ['BT','192.168.0.10:35000']
    return ret


class tl:

    cw = 630
    ch = 415
    tab = 20
    xmax = 2
    ymax = 15.0
    pre_len = 0.2  # seconds
    startThr = 1  # start threshold

    v0 = 0
    v1 = 0
    v2 = 0
    T0 = 0  # T0 = T1 - pre_len
    T1 = 0  # Time of engine start (first valley)
    T2 = 0  # second valley

    def cmd_Help(self):
        tkinter.messagebox.showinfo("INFO", help)

    def volt_extr(self, s):
        s = s.upper()
        r = 0.0
        for l in s.split("\n")[1:]:
            if "." in l and l[-1] == "V":
                r = float(l[:-1])
                return r
        return r

    def cmd_Start(self):

        global batTemp

        p_name = self.port_name.get().split(";")[0]
        if p_name.strip() == "":
            if batTemp.get() == "":
                tkinter.messagebox.showinfo(
                    "INFO", "Select ELM port and enter the temperature. "
                )
            else:
                tkinter.messagebox.showinfo("INFO", "Select ELM port. ")
            return

        if batTemp.get() == "":
            tkinter.messagebox.showinfo("INFO", "Enter the temperature. ")
            return

        self.l_volt.config(fg="black", bg="#d9d9d9")
        self.CV.delete("all")
        self.axis(self.top)
        self.showHistory()

        # start ELM
        try:
            config.OPT_SPEED = 38400
            config.OPT_RATE = 230400
            self.elm = ELM(p_name, config.OPT_SPEED, "")
            self.elm.port.soft_boudrate(config.OPT_RATE)
        except:
            tkinter.messagebox.showinfo(
                "INFO", "ELM is not connected or incompatible. "
            )
            return

        rsp = self.elm.send_raw("ATWS")
        t0 = int(round(time.time() * 1000))
        rsp = self.elm.send_raw("ATRV")
        t2 = int(round(time.time() * 1000))

        rt = t2 - t0
        if rt > 50:
            tkinter.messagebox.showinfo(
                "ERROR", "Connection is too slow. Use USB-ELM327 "
            )
            return

        self.BTN_Start.config(state="disabled")
        self.BTN_Calib.config(state="normal")

        phase = 0
        prefix = [0] * 256
        u = 256
        data = []
        cvolt = 0.0

        while phase < 2:
            try:
                pvolt = cvolt
                cvolt = self.volt_extr(self.elm.send_raw("ATRV"))
                t1 = t2
                t2 = int(round(time.time() * 1000))
            except:
                tkinter.messagebox.showinfo("ERROR", "Unknown response from ELM ")
                self.BTN_Start.config(state="normal")
                self.BTN_Calib.config(state="disabled")
                del self.elm
                return

            if phase == 0:
                u = u + 2
                if u > 255:
                    u = 0
                prefix[u] = t2 / 1000.0
                prefix[u + 1] = cvolt
                if u % 10 == 0:
                    self.v_volt.set("%.2f" % cvolt + "V")
                    self.FR1.update()
                if (t2 - t1) < 50 and (pvolt - cvolt) > self.startThr:
                    # engine start detected
                    self.TS = t1
                    u_beg = u
                    while prefix[u] >= (t2 / 1000.0 - self.pre_len):
                        u = u - 2
                        if u_beg < 0:
                            u_beg = 254
                        if u == u_beg:
                            u = u + 2
                            if u == 256:
                                u = 0
                            break
                    t0 = prefix[u] * 1000
                    while u != u_beg:
                        data.append(prefix[u])
                        data.append(prefix[u + 1])
                        u = u + 2
                        if u == 256:
                            u = 0
                    data.append(prefix[u])
                    data.append(prefix[u + 1])
                    phase = 1
            elif phase == 1:
                if (t2 - t0) > self.xmax * 1000:
                    break
                data.append(t2 / 1000.0)
                data.append(cvolt)

        self.BTN_Start.config(state="normal")
        self.BTN_Calib.config(state="disabled")
        del self.elm

        new_line = {}
        new_line["at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_line["temp"] = int(batTemp.get())
        new_line["volt"] = data
        self.drowLine(new_line, False)
        new_line["soh"] = self.SOH

        fo = open("history.txt", "a")
        fo.write(
            "{'at':'"
            + str(new_line["at"])
            + "','soh':"
            + str(new_line["soh"])
            + ",'temp':"
            + str(new_line["temp"])
            + ",'volt':"
            + str(new_line["volt"])
            + "}\n"
        )
        fo.close()

    def cmd_Exit(self):
        vp_exit_gui()

    def cmd_Calibrate(self):
        global atcv

        cv = atcv.get()

        self.elm.send_raw("ATCV" + cv.replace(".", ""))
        self.elm.send_raw("ATRV")

    def __init__(self, top=None):
        """This class configures and populates the toplevel window.
        top is the toplevel containing window."""
        _bgcolor = "#d9d9d9"  # X11 color: 'gray85'
        _fgcolor = "#000000"  # X11 color: 'black'
        _compcolor = "#d9d9d9"  # X11 color: 'gray85'
        _ana2color = "#ececec"  # Closest X11 color: 'gray92'
        self.style = tkinter.ttk.Style()
        if sys.platform == "win32":
            self.style.theme_use("winnative")
        self.style.configure(".", background=_bgcolor)
        self.style.configure(".", foreground=_fgcolor)
        self.style.configure(".", font="TkDefaultFont")
        self.style.map(
            ".", background=[("selected", _compcolor), ("active", _ana2color)]
        )

        self.top = top

        top.geometry("640x480+268+100")
        top.title("SOH check")
        top.configure(background="#d9d9d9")
        top.configure(height="480")
        top.configure(highlightbackground="#d9d9d9")
        top.configure(highlightcolor="black")
        top.configure(width="640")

        self.FR1 = tk.Frame(top)
        self.FR1.place(relx=0.0, rely=0.0, relheight=0.125, relwidth=1.0)
        self.FR1.configure(relief="groove")
        self.FR1.configure(borderwidth="2")
        self.FR1.configure(relief="groove")
        self.FR1.configure(background="#d9d9d9")
        self.FR1.configure(highlightbackground="#d9d9d9")
        self.FR1.configure(highlightcolor="black")
        self.FR1.configure(width=685)

        self.Label1 = tk.Label(self.FR1)
        self.Label1.place(relx=0.0, rely=0.04, height=24, width=45)
        self.Label1.configure(activebackground="#f9f9f9")
        self.Label1.configure(activeforeground="black")
        self.Label1.configure(background="#d9d9d9")
        self.Label1.configure(foreground="#000000")
        self.Label1.configure(highlightbackground="#d9d9d9")
        self.Label1.configure(highlightcolor="black")
        self.Label1.configure(text="""ELM""")
        self.Label1.configure(width=45)

        self.port_name = tk.StringVar()
        self.CB_Port = tkinter.ttk.Combobox(self.FR1)
        self.CB_Port.place(relx=0.07, rely=0.03, relheight=0.45, relwidth=0.3)
        self.CB_Port.configure(textvariable=combobox)
        self.CB_Port.configure(values=getPortList())
        self.CB_Port.configure(textvariable=self.port_name)
        self.CB_Port.configure(width=116)
        self.CB_Port.configure(takefocus="")

        self.v_volt = tk.StringVar()
        self.v_volt.set("00.00V")
        self.l_volt = tk.Label(
            self.FR1, textvariable=self.v_volt, bg="#d9d9d9", fg="black"
        )
        self.l_volt.place(relx=0.55, rely=0.0, height=55, width=130)
        self.l_volt.config(font=("Courier 28"))

        self.Label2 = tk.Label(self.FR1)
        self.Label2.place(relx=0.23, rely=0.583, height=14, width=55)
        self.Label2.configure(activebackground="#f9f9f9")
        self.Label2.configure(activeforeground="black")
        self.Label2.configure(background="#d9d9d9")
        self.Label2.configure(foreground="#000000")
        self.Label2.configure(highlightbackground="#d9d9d9")
        self.Label2.configure(highlightcolor="black")
        self.Label2.configure(text="""ATCV""")
        self.Label2.configure(width=55)

        self.ENT_Calib = tk.Entry(self.FR1)
        self.ENT_Calib.place(relx=0.3, rely=0.46, height=27, relwidth=0.072)
        self.ENT_Calib.configure(background="white")
        self.ENT_Calib.configure(font="TkFixedFont")
        self.ENT_Calib.configure(foreground="#000000")
        self.ENT_Calib.configure(highlightbackground="#d9d9d9")
        self.ENT_Calib.configure(highlightcolor="black")
        self.ENT_Calib.configure(insertbackground="black")
        self.ENT_Calib.configure(selectbackground="#c4c4c4")
        self.ENT_Calib.configure(selectforeground="black")
        self.ENT_Calib.configure(textvariable=atcv)

        self.BTN_Calib = tk.Button(self.FR1)
        self.BTN_Calib.place(relx=0.38, rely=0.5, height=22, width=81)
        self.BTN_Calib.configure(activebackground="#ececec")
        self.BTN_Calib.configure(activeforeground="#000000")
        self.BTN_Calib.configure(background="#d9d9d9")
        self.BTN_Calib.configure(foreground="#000000")
        self.BTN_Calib.configure(highlightbackground="#d9d9d9")
        self.BTN_Calib.configure(highlightcolor="black")
        self.BTN_Calib.configure(text="""Calibrate""")
        self.BTN_Calib.config(state="disabled")
        self.BTN_Calib.configure(command=self.cmd_Calibrate)

        self.BTN_Start = tk.Button(self.FR1)
        self.BTN_Start.place(relx=0.773, rely=0.083, height=22, width=51)
        self.BTN_Start.configure(activebackground="#ececec")
        self.BTN_Start.configure(activeforeground="#000000")
        self.BTN_Start.configure(background="#d9d9d9")
        self.BTN_Start.configure(foreground="#000000")
        self.BTN_Start.configure(highlightbackground="#d9d9d9")
        self.BTN_Start.configure(highlightcolor="black")
        self.BTN_Start.configure(text="""Start""")
        self.BTN_Start.configure(command=self.cmd_Start)

        self.BTN_Exit = tk.Button(self.FR1)
        self.BTN_Exit.place(relx=0.875, rely=0.083, height=22, width=51)
        self.BTN_Exit.configure(activebackground="#ececec")
        self.BTN_Exit.configure(activeforeground="#000000")
        self.BTN_Exit.configure(background="#d9d9d9")
        self.BTN_Exit.configure(foreground="#000000")
        self.BTN_Exit.configure(highlightbackground="#d9d9d9")
        self.BTN_Exit.configure(highlightcolor="black")
        self.BTN_Exit.configure(text="""Exit""")
        self.BTN_Exit.configure(command=self.cmd_Exit)

        self.BTN_Help = tk.Button(self.FR1)
        self.BTN_Help.place(relx=0.875, rely=0.5, height=22, width=51)
        self.BTN_Help.configure(activebackground="#ececec")
        self.BTN_Help.configure(activeforeground="#000000")
        self.BTN_Help.configure(background="#d9d9d9")
        self.BTN_Help.configure(foreground="#000000")
        self.BTN_Help.configure(highlightbackground="#d9d9d9")
        self.BTN_Help.configure(highlightcolor="black")
        self.BTN_Help.configure(text="""Help""")
        self.BTN_Help.config(state="active")
        self.BTN_Help.configure(command=self.cmd_Help)

        self.Label3 = tk.Label(self.FR1)
        self.Label3.place(relx=0.0, rely=0.583, height=14, width=95)
        self.Label3.configure(background="#d9d9d9")
        self.Label3.configure(foreground="#000000")
        self.Label3.configure(text="""Temperature""")
        self.Label3.configure(width=95)

        self.ENT_Temper = tk.Entry(self.FR1)
        self.ENT_Temper.place(relx=0.14, rely=0.46, height=27, relwidth=0.072)
        self.ENT_Temper.configure(background="white")
        self.ENT_Temper.configure(font="TkFixedFont")
        self.ENT_Temper.configure(foreground="#000000")
        self.ENT_Temper.configure(highlightbackground="#d9d9d9")
        self.ENT_Temper.configure(highlightcolor="black")
        self.ENT_Temper.configure(insertbackground="black")
        self.ENT_Temper.configure(selectbackground="#c4c4c4")
        self.ENT_Temper.configure(selectforeground="black")
        self.ENT_Temper.configure(textvariable=batTemp)

        self.CV = tk.Canvas(top)
        self.CV.place(relx=0.0, rely=0.125, relheight=0.871, relwidth=1.0)
        self.CV.configure(background="#ffffff")
        self.CV.configure(borderwidth="2")
        self.CV.configure(highlightbackground="#d9d9d9")
        self.CV.configure(highlightcolor="black")
        self.CV.configure(insertbackground="black")
        self.CV.configure(relief="ridge")
        self.CV.configure(selectbackground="#c4c4c4")
        self.CV.configure(selectforeground="black")
        self.CV.configure(width=640)

        self.axis(top)
        self.showHistory()

    def showHistory(self):

        try:
            hf = open("./history.txt", "r")
        except:
            return

        line_num = 0
        for l in hf.readlines():
            line_num = line_num + 1
            if l.strip().startswith("{"):
                try:
                    hist_obj = eval(l.strip())
                except:
                    print("ERROR in line: ", line_num)
                    continue

                self.drowLine(hist_obj, True)

    def drowLine(self, line, hist=True):

        if hist:
            f = "lightgray"
        else:
            f = "blue"

        if len(line["volt"]) < 4:
            return

        ty = self.tab
        tx = self.tab
        xmax = self.xmax
        ymax = self.ymax
        xm = (self.cw - 2.0 * tx) // xmax
        ym = (self.ch - 2.0 * ty) // ymax

        i = 0
        count = len(line["volt"]) // 2 - 1
        st = float(line["volt"][0])
        while i < (count - 1):
            i = i + 1
            x0 = float(line["volt"][(i - 1) * 2]) - st
            y0 = float(line["volt"][(i - 1) * 2 + 1])
            x1 = float(line["volt"][i * 2]) - st
            y1 = float(line["volt"][i * 2 + 1])
            self.CV.create_line(
                tx + x0 * xm,
                ty + (ymax - y0) * ym,
                tx + x1 * xm,
                ty + (ymax - y1) * ym,
                width=1,
                fill=f,
            )

        # if hist:
        #    return

        self.findPoints(line)

        x = tx + (self.T1 - st) * xm
        y = ty + (ymax - self.V1) * ym
        self.CV.create_oval(x - 5, y - 5, x + 5, y + 5, fill="red")
        x = tx + (self.T2 - st) * xm
        y = ty + (ymax - self.V2) * ym
        self.CV.create_oval(x - 5, y - 5, x + 5, y + 5, fill="red")

    def findPoints(self, line):

        global batTemp

        try:
            Tc = int(batTemp.get())
        except:
            Tc = int(line["temp"])

        # average interval among points
        interval = (line["volt"][-2] - line["volt"][0]) / len(line["volt"]) * 2

        # points in 50ms (take in to account only odds)
        # 50ms radius of zone for local min/max
        radius = int(0.1 / interval) * 2 + 1

        self.T0 = line["volt"][0]
        u = 2
        mean = 0
        count = 0
        while (line["volt"][u - 1] - line["volt"][u + 1]) < self.startThr and u < len(
            line["volt"]
        ):
            mean += line["volt"][u - 1]
            count += 1
            u += 2
        self.V0 = mean // count

        # find first min
        smin = min(list(line["volt"][u - 5 : u + radius : 2]))
        while line["volt"][u + 1] != smin:
            u += 2
        self.T1 = line["volt"][u]
        self.V1 = smin

        # find first max
        while (
            line["volt"][u + 1] < max(list(line["volt"][u - 1 : u + radius : 2]))
            and u < len(line["volt"]) - radius - 1
        ):
            u += 2

        # find second min
        while (
            line["volt"][u + 1] > min(list(line["volt"][u - 1 : u + radius : 2]))
            and u < len(line["volt"]) - radius - 1
        ):
            u += 2
        self.T2 = line["volt"][u]
        self.V2 = line["volt"][u + 1]

        self.vth1 = 0
        tpol = [
            2.40384615e-09,
            -7.79428904e-08,
            -6.37383450e-06,
            8.12208625e-05,
            1.06745338e-02,
            1.97290210e-01,
        ]
        for i in range(6):
            self.vth1 = self.vth1 + tpol[i] * (Tc ** (5 - i))

        self.vth2 = (self.V0 - self.V1) * 0.07 - 0.23

        self.vth = self.vth1 + self.vth2

        self.SOH = (self.V2 - self.V1) - self.vth

        self.v_volt.set("%.2f" % self.SOH)
        self.FR1.update()

        if self.SOH > 0:
            self.l_volt.config(fg="black", bg="green")
        else:
            self.l_volt.config(fg="black", bg="red")

        print((self.V2 - self.V1) / (self.T2 - self.T1) / 8 * 100, self.V1, self.V2)
        return

    def axis(self, top):

        ty = self.tab
        tx = self.tab
        xmax = self.xmax
        ymax = self.ymax
        xm = (self.cw - 2.0 * tx) // xmax
        ym = (self.ch - 2.0 * ty) // ymax

        x = 0
        while x <= self.xmax:
            if x == 0:
                self.CV.create_line(tx + x * xm, ty, tx + x * xm, self.ch - ty, width=1)
            else:
                self.CV.create_line(
                    tx + x * xm,
                    ty,
                    tx + x * xm,
                    self.ch - ty,
                    width=0,
                    dash=(5, 5),
                    fill="lightgray",
                )

            self.CV.create_text(
                tx + x * xm,
                self.ch - ty // 2.0,
                text=str(x)[:4],
                justify=tk.CENTER,
                font="Verdana 8",
            )
            x = x + 0.2

        y = 0
        while y <= 15:
            if y == 0:
                self.CV.create_line(
                    tx,
                    ty + (ymax - y) * ym,
                    self.cw - ty,
                    ty + (ymax - y) * ym,
                    width=1,
                )
            else:
                self.CV.create_line(
                    tx,
                    ty + (ymax - y) * ym,
                    self.cw - ty,
                    ty + (ymax - y) * ym,
                    width=0,
                    dash=(5, 5),
                    fill="lightgray",
                )

            self.CV.create_text(
                ty // 2, ty + (ymax - y) * ym, text=str(y), font="Verdana 8"
            )
            y = y + 1


if __name__ == "__main__":
    vp_start_gui()
