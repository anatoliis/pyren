import sys
import tkinter as tk
import tkinter.filedialog
import tkinter.font
import tkinter.messagebox
import tkinter.ttk as ttk

from pyren3.enums import Command
from pyren3.mod import config
from pyren3.runner import run
from pyren3.settings import Settings
from pyren3.utils import getLangList, getPathList, getPortList, update_from_gitlab


class DesktopGui(tk.Frame):
    save = None

    def guiDestroy(self):
        self.root.eval("::ttk::CancelRepeat")
        self.root.destroy()

    def cmd_Mon(self):
        self.saveSettings()
        self.guiDestroy()
        run(self.save, Command.MON)

    def cmd_Check(self):
        self.saveSettings()
        self.guiDestroy()
        run(self.save, Command.CHECK)

    def cmd_Demo(self):
        self.saveSettings()
        self.guiDestroy()
        run(self.save, Command.DEMO)

    def cmd_Scan(self):
        self.saveSettings()
        self.guiDestroy()
        run(self.save, Command.SCAN)

    def cmd_Start(self):
        self.saveSettings()
        self.guiDestroy()
        run(self.save, Command.PYREN)

    def cmd_DDT(self):
        self.saveSettings()
        self.guiDestroy()
        run(self.save, Command.DDT)

    def cmd_Term(self):
        self.saveSettings()
        self.guiDestroy()
        run(self.save, Command.TERM)

    def cmd_Update(self):
        res = update_from_gitlab()
        if res == 0:
            tkinter.messagebox.showinfo("Information", "Done")
        elif res == 1:
            tkinter.messagebox.showerror("Error", "No connection with gitlab.com")
        elif res == 2:
            tkinter.messagebox.showerror("Error", "UnZip error")

    def saveSettings(self):
        self.save.path = self.var_path.get()
        self.save.port = self.var_port.get().split(";")[0]
        self.save.lang = self.var_lang.get()
        self.save.speed = self.var_speed.get()
        self.save.log = self.var_log.get()
        self.save.log_name = self.var_logName.get()
        self.save.cfc = self.var_cfc.get()
        self.save.n1c = self.var_n1c.get()
        self.save.si = self.var_si.get()
        self.save.csv = self.var_csv.get()
        self.save.csv_option = self.var_csvOption.get()
        self.save.dump = self.var_dump.get()
        self.save.can2 = self.var_can2.get()
        self.save.options = self.var_otherOptions.get()
        self.save.save()

    def loadSettings(self):
        self.var_si.set(self.save.si)
        self.var_cfc.set(self.save.cfc)
        self.var_n1c.set(self.save.n1c)
        self.var_csv.set(self.save.csv)
        self.var_csvOption.set(self.save.csv_option)
        self.var_can2.set(self.save.can2)
        self.var_dump.set(self.save.dump)
        self.var_lang.set(self.save.lang)
        self.var_path.set(self.save.path)
        self.var_port.set(self.save.port)
        self.var_speed.set(self.save.speed)
        self.var_otherOptions.set(self.save.options)
        self.var_log.set(self.save.log)
        self.var_logName.set(self.save.log_name)

        self.var_speedList = [
            "38400",
            "115200",
            "230400",
            "500000",
            "1000000",
            "2000000",
        ]
        self.var_langList = getLangList()
        self.var_pathList = getPathList()
        self.var_portList = getPortList()
        self.var_csvOptions = config.CSV_OPTIONS

        if len(self.var_path.get()) == 0:
            self.var_path.set(self.var_pathList[0])

        if len(self.var_lang.get()) == 0:
            ll = self.var_langList
            if "RU" in ll:
                self.var_lang.set("RU")
            elif "GB" in ll:
                self.var_lang.set("GB")
            else:
                self.var_lang.set(ll[0])

        if len(self.var_port.get()) == 0:
            for p in self.var_portList:
                self.var_port.set(p)
                if "OBD" in p:
                    break

    def __init__(self):
        self.save = Settings()
        self.root = tk.Tk()
        self.root.option_add("*Dialog.msg.font", r"Courier\ New 10")
        self.root.geometry("500x500")
        tk.Frame.__init__(self, self.root)

        self.var_can2 = tk.BooleanVar()
        self.var_dump = tk.BooleanVar()
        self.var_log = tk.BooleanVar()
        self.var_csv = tk.BooleanVar()

        self.var_cfc = tk.BooleanVar()
        self.var_n1c = tk.BooleanVar()
        self.var_si = tk.BooleanVar()

        self.var_langList = []
        self.var_pathList = []
        self.var_portList = []
        self.var_speedList = []

        self.var_lang = tk.StringVar()
        self.var_path = tk.StringVar()
        self.var_port = tk.StringVar()
        self.var_speed = tk.StringVar()
        self.var_csvOption = tk.StringVar()

        self.var_logName = tk.StringVar()
        self.var_otherOptions = tk.StringVar()

        self.loadSettings()

        self.root.title("Pyren Launcher")
        self.style = tkinter.ttk.Style()
        self.style.theme_use("classic")

        if sys.platform == "win32":
            self.style.theme_use("winnative")
        self.style.configure(".", background="#d9d9d9")
        self.style.configure(".", foreground="#000000")
        self.style.configure(".", font="TkDefaultFont")
        self.style.map(".", background=[("selected", "#d9d9d9"), ("active", "#d9d9d9")])

        self.root.geometry("500x500+0+28")
        self.root.title("Pyren launcher")
        self.root.configure(background="#d9d9d9")
        self.root.configure(highlightbackground="#d9d9d9")
        self.root.configure(highlightcolor="black")

        self.lPathSelector = tk.LabelFrame(self.root)
        self.lPathSelector.place(relx=0.02, rely=0.0, relheight=0.13, relwidth=0.46)
        self.lPathSelector.configure(relief=tk.GROOVE)
        self.lPathSelector.configure(foreground="black")
        self.lPathSelector.configure(text="""Version""")
        self.lPathSelector.configure(background="#d9d9d9")
        self.lPathSelector.configure(highlightbackground="#d9d9d9")
        self.lPathSelector.configure(highlightcolor="black")
        self.lPathSelector.configure(width=230)

        self.lDBLanguage = tk.LabelFrame(self.root)
        self.lDBLanguage.place(relx=0.02, rely=0.14, relheight=0.13, relwidth=0.46)
        self.lDBLanguage.configure(relief=tk.GROOVE)
        self.lDBLanguage.configure(foreground="black")
        self.lDBLanguage.configure(text="""DB Language""")
        self.lDBLanguage.configure(background="#d9d9d9")
        self.lDBLanguage.configure(highlightbackground="#d9d9d9")
        self.lDBLanguage.configure(highlightcolor="black")
        self.lDBLanguage.configure(width=100)

        self.lPortSelector = tk.LabelFrame(self.root)
        self.lPortSelector.place(relx=0.5, rely=0.0, relheight=0.27, relwidth=0.48)
        self.lPortSelector.configure(relief=tk.GROOVE)
        self.lPortSelector.configure(foreground="black")
        self.lPortSelector.configure(text="""Port""")
        self.lPortSelector.configure(background="#d9d9d9")
        self.lPortSelector.configure(highlightbackground="#d9d9d9")
        self.lPortSelector.configure(highlightcolor="black")
        self.lPortSelector.configure(width=240)

        self.lPortSpeed = tk.LabelFrame(self.root)
        self.lPortSpeed.place(relx=0.52, rely=0.12, relheight=0.13, relwidth=0.44)
        self.lPortSpeed.configure(relief=tk.GROOVE)
        self.lPortSpeed.configure(foreground="black")
        self.lPortSpeed.configure(text="""Port Speed (only for USB-ELM)""")
        self.lPortSpeed.configure(background="#d9d9d9")
        self.lPortSpeed.configure(highlightbackground="#d9d9d9")
        self.lPortSpeed.configure(highlightcolor="black")
        self.lPortSpeed.configure(width=220)

        self.lOptions = tk.LabelFrame(self.root)
        self.lOptions.place(relx=0.02, rely=0.69, relheight=0.13, relwidth=0.96)
        self.lOptions.configure(relief=tk.GROOVE)
        self.lOptions.configure(foreground="black")
        self.lOptions.configure(text="""Other options""")
        self.lOptions.configure(background="#d9d9d9")
        self.lOptions.configure(highlightbackground="#d9d9d9")
        self.lOptions.configure(highlightcolor="black")
        self.lOptions.configure(width=480)

        self.lLog = tk.LabelFrame(self.root)
        self.lLog.place(relx=0.5, rely=0.28, relheight=0.135, relwidth=0.48)
        self.lLog.configure(relief=tk.GROOVE)
        self.lLog.configure(foreground="black")
        self.lLog.configure(text="""ELM Log""")
        self.lLog.configure(background="#d9d9d9")
        self.lLog.configure(highlightbackground="#d9d9d9")
        self.lLog.configure(highlightcolor="black")
        self.lLog.configure(width=230)

        self.lCAN = tk.LabelFrame(self.root)
        self.lCAN.place(relx=0.02, rely=0.43, relheight=0.25, relwidth=0.46)
        self.lCAN.configure(relief=tk.GROOVE)
        self.lCAN.configure(foreground="black")
        self.lCAN.configure(text="""CAN""")
        self.lCAN.configure(background="#d9d9d9")
        self.lCAN.configure(highlightbackground="#d9d9d9")
        self.lCAN.configure(highlightcolor="black")
        self.lCAN.configure(width=230)

        self.lCSV = tk.LabelFrame(self.root)
        self.lCSV.place(relx=0.02, rely=0.28, relheight=0.135, relwidth=0.46)
        self.lCSV.configure(relief=tk.GROOVE)
        self.lCSV.configure(foreground="black")
        self.lCSV.configure(text="""Data logging""")
        self.lCSV.configure(background="#d9d9d9")
        self.lCSV.configure(highlightbackground="#d9d9d9")
        self.lCSV.configure(highlightcolor="black")
        self.lCSV.configure(width=240)

        self.lKWP = tk.LabelFrame(self.root)
        self.lKWP.place(relx=0.5, rely=0.43, relheight=0.125, relwidth=0.48)
        self.lKWP.configure(relief=tk.GROOVE)
        self.lKWP.configure(foreground="black")
        self.lKWP.configure(text="""K-Line""")
        self.lKWP.configure(background="#d9d9d9")
        self.lKWP.configure(highlightbackground="#d9d9d9")
        self.lKWP.configure(highlightcolor="black")
        self.lKWP.configure(width=240)

        self.mCFC = tk.Message(self.root)
        self.mCFC.place(relx=0.08, rely=0.5, relheight=0.06, relwidth=0.1)
        self.mCFC.configure(background="#d9d9d9")
        self.mCFC.configure(foreground="#000000")
        self.mCFC.configure(highlightbackground="#d9d9d9")
        self.mCFC.configure(highlightcolor="black")
        self.mCFC.configure(text="""--cfc""")
        self.mCFC.configure(width=40)

        self.mN1C = tk.Message(self.root)
        self.mN1C.place(relx=0.08, rely=0.57, relheight=0.06, relwidth=0.1)
        self.mN1C.configure(background="#d9d9d9")
        self.mN1C.configure(foreground="#000000")
        self.mN1C.configure(highlightbackground="#d9d9d9")
        self.mN1C.configure(highlightcolor="black")
        self.mN1C.configure(text="""--n1c""")
        self.mN1C.configure(width=40)

        self.mSI = tk.Message(self.root)
        self.mSI.place(relx=0.56, rely=0.48, relheight=0.03, relwidth=0.08)
        self.mSI.configure(background="#d9d9d9")
        self.mSI.configure(foreground="#000000")
        self.mSI.configure(highlightbackground="#d9d9d9")
        self.mSI.configure(highlightcolor="black")
        self.mSI.configure(text="""--si""")
        self.mSI.configure(width=40)

        self.mCAN = tk.Message(self.root)
        self.mCAN.place(relx=0.18, rely=0.48, relheight=0.18, relwidth=0.28)
        self.mCAN.configure(background="#d9d9d9")
        self.mCAN.configure(foreground="#000000")
        self.mCAN.configure(highlightbackground="#d9d9d9")
        self.mCAN.configure(highlightcolor="black")
        self.mCAN.configure(
            text="""CFC - enable soft flow control (recommended)          N1C - disable L1 cache (not recommended)"""
        )
        self.mCAN.configure(width=142)

        self.mKWP = tk.Message(self.root)
        self.mKWP.place(relx=0.64, rely=0.46, relheight=0.08, relwidth=0.3)
        self.mKWP.configure(background="#d9d9d9")
        self.mKWP.configure(foreground="#000000")
        self.mKWP.configure(highlightbackground="#d9d9d9")
        self.mKWP.configure(highlightcolor="black")
        self.mKWP.configure(
            text="""Try Slow Init before Fast Init. It may helps with old ECUs"""
        )
        self.mKWP.configure(width=152)

        self.logName = tk.Entry(self.root)
        self.logName.place(relx=0.58, rely=0.33, relheight=0.06, relwidth=0.37)
        self.logName.configure(background="white")
        self.logName.configure(font="TkFixedFont")
        self.logName.configure(foreground="#000000")
        self.logName.configure(highlightbackground="#d9d9d9")
        self.logName.configure(highlightcolor="black")
        self.logName.configure(insertbackground="black")
        self.logName.configure(selectbackground="#c4c4c4")
        self.logName.configure(selectforeground="black")
        self.logName.configure(textvariable=self.var_logName)

        self.cbLog = tk.Checkbutton(self.root)
        self.cbLog.place(relx=0.52, rely=0.325, relheight=0.07, relwidth=0.06)
        self.cbLog.configure(activebackground="#d9d9d9")
        self.cbLog.configure(activeforeground="#000000")
        self.cbLog.configure(background="#d9d9d9")
        self.cbLog.configure(foreground="#000000")
        self.cbLog.configure(highlightbackground="#d9d9d9")
        self.cbLog.configure(highlightcolor="black")
        self.cbLog.configure(justify=tk.LEFT)
        self.cbLog.configure(variable=self.var_log)
        # self.cbLog.configure(variable=self.che40)

        self.cbCFC = tk.Checkbutton(self.lCAN)
        self.cbCFC.place(relx=0.04, rely=0.17, relheight=0.29, relwidth=0.13)
        self.cbCFC.configure(activebackground="#d9d9d9")
        self.cbCFC.configure(activeforeground="#000000")
        self.cbCFC.configure(background="#d9d9d9")
        self.cbCFC.configure(foreground="#000000")
        self.cbCFC.configure(highlightbackground="#d9d9d9")
        self.cbCFC.configure(highlightcolor="black")
        self.cbCFC.configure(justify=tk.LEFT)
        self.cbCFC.configure(variable=self.var_cfc)
        # self.cbCFC.configure(variable=self.che43)

        self.cbN1C = tk.Checkbutton(self.lCAN)
        self.cbN1C.place(relx=0.04, rely=0.48, relheight=0.29, relwidth=0.13)
        self.cbN1C.configure(activebackground="#d9d9d9")
        self.cbN1C.configure(activeforeground="#000000")
        self.cbN1C.configure(background="#d9d9d9")
        self.cbN1C.configure(foreground="#000000")
        self.cbN1C.configure(highlightbackground="#d9d9d9")
        self.cbN1C.configure(highlightcolor="black")
        self.cbN1C.configure(justify=tk.LEFT)
        self.cbN1C.configure(variable=self.var_n1c)
        # self.cbN1C.configure(variable=self.che44)

        self.cbSI = tk.Checkbutton(self.lKWP)
        self.cbSI.place(relx=0.04, rely=0.15, relheight=0.43, relwidth=0.13)
        self.cbSI.configure(activebackground="#d9d9d9")
        self.cbSI.configure(activeforeground="#000000")
        self.cbSI.configure(background="#d9d9d9")
        self.cbSI.configure(foreground="#000000")
        self.cbSI.configure(highlightbackground="#d9d9d9")
        self.cbSI.configure(highlightcolor="black")
        self.cbSI.configure(justify=tk.LEFT)
        self.cbSI.configure(variable=self.var_si)
        # self.cbSI.configure(variable=self.che45)

        self.cbCSV = tk.Checkbutton(self.lCSV)
        self.cbCSV.place(relx=0.05, rely=0.24, relheight=0.4, relwidth=0.1)
        self.cbCSV.configure(activebackground="#d9d9d9")
        self.cbCSV.configure(activeforeground="#000000")
        self.cbCSV.configure(background="#d9d9d9")
        self.cbCSV.configure(foreground="#000000")
        self.cbCSV.configure(highlightbackground="#d9d9d9")
        self.cbCSV.configure(highlightcolor="black")
        self.cbCSV.configure(justify=tk.LEFT)
        self.cbCSV.configure(variable=self.var_csv)

        self.lDump = tk.LabelFrame(self.root)
        self.lDump.place(relx=0.5, rely=0.56, relheight=0.12, relwidth=0.10)
        self.lDump.configure(relief=tk.GROOVE)
        self.lDump.configure(foreground="black")
        self.lDump.configure(text="""Dump""")
        self.lDump.configure(background="#d9d9d9")
        self.lDump.configure(highlightbackground="#d9d9d9")
        self.lDump.configure(highlightcolor="black")
        self.lDump.configure(width=60)

        self.lCAN2 = tk.LabelFrame(self.root)
        self.lCAN2.place(relx=0.62, rely=0.56, relheight=0.12, relwidth=0.10)
        self.lCAN2.configure(relief=tk.GROOVE)
        self.lCAN2.configure(foreground="black")
        self.lCAN2.configure(text="""CAN 2""")
        self.lCAN2.configure(background="#d9d9d9")
        self.lCAN2.configure(highlightbackground="#d9d9d9")
        self.lCAN2.configure(highlightcolor="black")
        self.lCAN2.configure(width=60)

        self.cbDump = tk.Checkbutton(self.lDump)
        self.cbDump.place(relx=0.265, rely=0.18, relheight=0.55, relwidth=0.5)
        self.cbDump.configure(activebackground="#d9d9d9")
        self.cbDump.configure(activeforeground="#000000")
        self.cbDump.configure(background="#d9d9d9")
        self.cbDump.configure(foreground="#000000")
        self.cbDump.configure(highlightbackground="#d9d9d9")
        self.cbDump.configure(highlightcolor="black")
        self.cbDump.configure(variable=self.var_dump)
        # self.cbDump.configure(variable=self.che41)
        self.cbDump.configure(width=34)

        self.cbCAN2 = tk.Checkbutton(self.lCAN2)
        self.cbCAN2.place(relx=0.28, rely=0.18, relheight=0.55, relwidth=0.5)
        self.cbCAN2.configure(activebackground="#d9d9d9")
        self.cbCAN2.configure(activeforeground="#000000")
        self.cbCAN2.configure(background="#d9d9d9")
        self.cbCAN2.configure(foreground="#000000")
        self.cbCAN2.configure(highlightbackground="#d9d9d9")
        self.cbCAN2.configure(highlightcolor="black")
        self.cbCAN2.configure(variable=self.var_can2)
        # self.cbCAN2.configure(variable=self.che42)
        self.cbCAN2.configure(width=34)

        self.Options = tk.Entry(self.root)
        self.Options.place(relx=0.04, rely=0.74, relheight=0.06, relwidth=0.92)
        self.Options.configure(background="white")
        self.Options.configure(font="TkFixedFont")
        self.Options.configure(foreground="#000000")
        self.Options.configure(highlightbackground="#d9d9d9")
        self.Options.configure(highlightcolor="black")
        self.Options.configure(insertbackground="black")
        self.Options.configure(selectbackground="#c4c4c4")
        self.Options.configure(selectforeground="black")
        self.Options.configure(textvariable=self.var_otherOptions)

        self.btnStart = tk.Button(self.root)
        self.btnStart.place(relx=0.01, rely=0.84, height=22, width=100)
        self.btnStart.configure(activebackground="#d9d9d9")
        self.btnStart.configure(activeforeground="#000000")
        self.btnStart.configure(background="#d9d9d9")
        self.btnStart.configure(command=self.cmd_Start)
        self.btnStart.configure(foreground="#000000")
        self.btnStart.configure(highlightbackground="#d9d9d9")
        self.btnStart.configure(highlightcolor="black")
        self.btnStart.configure(text="""Start pyren""")
        self.btnStart.configure(width=70)

        self.btnDDT = tk.Button(self.root)
        self.btnDDT.place(relx=0.01, rely=0.91, height=22, width=100)
        self.btnDDT.configure(activebackground="#d9d9d9")
        self.btnDDT.configure(activeforeground="#000000")
        self.btnDDT.configure(background="#d9d9d9")
        self.btnDDT.configure(command=self.cmd_DDT)
        self.btnDDT.configure(foreground="#000000")
        self.btnDDT.configure(highlightbackground="#d9d9d9")
        self.btnDDT.configure(highlightcolor="black")
        self.btnDDT.configure(text="""Start DDT""")
        self.btnDDT.configure(width=70)

        self.btnScan = tk.Button(self.root)
        self.btnScan.place(relx=0.21, rely=0.84, height=22, width=100)
        self.btnScan.configure(activebackground="#d9d9d9")
        self.btnScan.configure(activeforeground="#000000")
        self.btnScan.configure(background="#d9d9d9")
        self.btnScan.configure(command=self.cmd_Scan)
        self.btnScan.configure(foreground="#000000")
        self.btnScan.configure(highlightbackground="#d9d9d9")
        self.btnScan.configure(highlightcolor="black")
        self.btnScan.configure(text="""Scan""")
        self.btnScan.configure(width=70)

        self.btnDemo = tk.Button(self.root)
        self.btnDemo.place(relx=0.41, rely=0.84, height=22, width=100)
        self.btnDemo.configure(activebackground="#d9d9d9")
        self.btnDemo.configure(activeforeground="#000000")
        self.btnDemo.configure(background="#d9d9d9")
        self.btnDemo.configure(command=self.cmd_Demo)
        self.btnDemo.configure(foreground="#000000")
        self.btnDemo.configure(highlightbackground="#d9d9d9")
        self.btnDemo.configure(highlightcolor="black")
        self.btnDemo.configure(text="""Demo""")
        self.btnDemo.configure(width=82)

        self.btnCheck = tk.Button(self.root)
        self.btnCheck.place(relx=0.61, rely=0.84, height=22, width=100)
        self.btnCheck.configure(activebackground="#d9d9d9")
        self.btnCheck.configure(activeforeground="#000000")
        self.btnCheck.configure(background="#d9d9d9")
        self.btnCheck.configure(command=self.cmd_Check)
        self.btnCheck.configure(foreground="#000000")
        self.btnCheck.configure(highlightbackground="#d9d9d9")
        self.btnCheck.configure(highlightcolor="black")
        self.btnCheck.configure(text="""Check ELM""")

        self.btnMon = tk.Button(self.root)
        self.btnMon.place(relx=0.81, rely=0.84, height=22, width=90)
        self.btnMon.configure(activebackground="#d9d9d9")
        self.btnMon.configure(activeforeground="#000000")
        self.btnMon.configure(background="#d9d9d9")
        self.btnMon.configure(command=self.cmd_Mon)
        self.btnMon.configure(foreground="#000000")
        self.btnMon.configure(highlightbackground="#d9d9d9")
        self.btnMon.configure(highlightcolor="black")
        self.btnMon.configure(text="""Monitor""")

        self.btnMac = tk.Button(self.root)
        self.btnMac.place(relx=0.81, rely=0.91, height=22, width=90)
        self.btnMac.configure(activebackground="#d9d9d9")
        self.btnMac.configure(activeforeground="#000000")
        self.btnMac.configure(background="#d9d9d9")
        self.btnMac.configure(command=self.cmd_Term)
        self.btnMac.configure(foreground="#000000")
        self.btnMac.configure(highlightbackground="#d9d9d9")
        self.btnMac.configure(highlightcolor="black")
        self.btnMac.configure(text="""Macro""")

        self.btnUpg = tk.Button(self.root)
        self.btnUpg.place(relx=0.41, rely=0.91, height=22, width=100)
        self.btnUpg.configure(activebackground="#d9d9d9")
        self.btnUpg.configure(activeforeground="#000000")
        self.btnUpg.configure(background="#d9d9d9")
        self.btnUpg.configure(command=self.cmd_Update)
        self.btnUpg.configure(foreground="#000000")
        self.btnUpg.configure(highlightbackground="#d9d9d9")
        self.btnUpg.configure(highlightcolor="black")
        self.btnUpg.configure(text="""Update""")

        self.pathList = tkinter.ttk.Combobox(self.root)
        self.pathList.place(relx=0.04, rely=0.05, relheight=0.06, relwidth=0.41)
        self.pathList.configure(values=["./pyren09a", "./pyren09a"])
        self.pathList.configure(values=self.var_pathList)
        self.pathList.configure(textvariable=self.var_path)
        self.pathList.configure(takefocus="")

        self.portList = tkinter.ttk.Combobox(self.root)
        self.portList.place(relx=0.52, rely=0.05, relheight=0.06, relwidth=0.43)
        self.portList.configure(values=self.var_portList)
        self.portList.configure(textvariable=self.var_port)
        self.portList.configure(takefocus="")

        self.speedList = tkinter.ttk.Combobox(self.root)
        self.speedList.place(relx=0.54, rely=0.17, relheight=0.06, relwidth=0.41)
        self.speedList.configure(values=self.var_speedList)
        self.speedList.configure(textvariable=self.var_speed)
        self.speedList.configure(takefocus="")

        self.csvList = tkinter.ttk.Combobox(self.root)
        self.csvList.place(relx=0.10, rely=0.33, relheight=0.06, relwidth=0.35)
        self.csvList.configure(values=self.var_csvOptions)
        self.csvList.configure(textvariable=self.var_csvOption)
        self.csvList.configure(takefocus="")

        self.langList = tkinter.ttk.Combobox(self.root)
        self.langList.place(relx=0.04, rely=0.185, relheight=0.06, relwidth=0.41)
        self.langList.configure(values=self.var_langList)
        self.langList.configure(textvariable=self.var_lang)
        self.langList.configure(takefocus="")

        self.root.focus_force()
        self.root.focus_set()
        self.root.mainloop()

    def __del__(self):
        pass


def main():
    DesktopGui()
