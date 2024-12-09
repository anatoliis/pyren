import sys
import tkinter as tk
import tkinter.filedialog
import tkinter.font
import tkinter.messagebox
import tkinter.ttk as ttk

from pyren3 import config
from pyren3.enums import Command
from pyren3.settings import Settings
from pyren3.utils import (
    get_executable,
    get_lang_list,
    get_path_list,
    get_port_list,
    update_from_gitlab,
)


class DesktopGui(tk.Frame):
    settings = None
    btn_height = 48
    btn_width = 160

    def gui_destroy(self):
        self.root.eval("::ttk::CancelRepeat")
        self.root.destroy()

    def cmd(self, command: Command):
        self.save_settings()
        self.gui_destroy()
        executable = get_executable(self.settings.path)
        executable(self.settings, command)

    def cmd_mon(self):
        self.cmd(Command.MON)

    def cmd_check(self):
        self.cmd(Command.CHECK)

    def cmd_demo(self):
        self.cmd(Command.DEMO)

    def cmd_scan(self):
        self.cmd(Command.SCAN)

    def cmd_start(self):
        self.cmd(Command.PYREN)

    def cmd_ddt(self):
        self.cmd(Command.DDT)

    def cmd_term(self):
        self.cmd(Command.TERM)

    @staticmethod
    def cmd_update():
        res = update_from_gitlab()
        if res == 0:
            tkinter.messagebox.showinfo("Information", "Done")
        elif res == 1:
            tkinter.messagebox.showerror("Error", "No connection with gitlab.com")
        elif res == 2:
            tkinter.messagebox.showerror("Error", "UnZip error")

    def save_settings(self):
        self.settings.path = self.var_path.get()
        self.settings.port = self.var_port.get().split(";")[0]
        self.settings.lang = self.var_lang.get()
        self.settings.speed = self.var_speed.get()
        self.settings.log = self.var_log.get()
        self.settings.log_name = self.var_log_name.get()
        self.settings.cfc = self.var_cfc.get()
        self.settings.n1c = self.var_n1c.get()
        self.settings.si = self.var_si.get()
        self.settings.csv = self.var_csv.get()
        self.settings.csv_option = self.var_csv_option.get()
        self.settings.dump = self.var_dump.get()
        self.settings.can2 = self.var_can2.get()
        self.settings.options = self.var_other_options.get()
        self.settings.save()

    def load_settings(self):
        self.var_si.set(self.settings.si)
        self.var_cfc.set(self.settings.cfc)
        self.var_n1c.set(self.settings.n1c)
        self.var_csv.set(self.settings.csv)
        self.var_csv_option.set(self.settings.csv_option)
        self.var_can2.set(self.settings.can2)
        self.var_dump.set(self.settings.dump)
        self.var_lang.set(self.settings.lang)
        self.var_path.set(self.settings.path)
        self.var_port.set(self.settings.port)
        self.var_speed.set(self.settings.speed)
        self.var_other_options.set(self.settings.options)
        self.var_log.set(self.settings.log)
        self.var_log_name.set(self.settings.log_name)

        self.var_speed_list = [
            "38400",
            "115200",
            "230400",
            "500000",
            "1000000",
            "2000000",
        ]
        self.var_lang_list = get_lang_list()
        self.var_path_list = get_path_list()
        self.var_port_list = get_port_list()
        self.var_csv_options = config.CSV_OPTIONS

        if len(self.var_path.get()) == 0:
            self.var_path.set(self.var_path_list[0])

        if len(self.var_lang.get()) == 0:
            language = self.var_lang_list
            if "RU" in language:
                self.var_lang.set("RU")
            elif "GB" in language:
                self.var_lang.set("GB")
            else:
                self.var_lang.set(language[0])

        if len(self.var_port.get()) == 0:
            for port in self.var_port_list:
                self.var_port.set(port)
                if "OBD" in port:
                    break

    def __init__(self):
        self.settings = Settings()
        self.root = tk.Tk()
        self.root.option_add("*Dialog.msg.font", r"Courier\ New 10")
        self.root.geometry("500x500+0+28")
        tk.Frame.__init__(self, self.root)

        self.var_can2 = tk.BooleanVar()
        self.var_dump = tk.BooleanVar()
        self.var_log = tk.BooleanVar()
        self.var_csv = tk.BooleanVar()

        self.var_cfc = tk.BooleanVar()
        self.var_n1c = tk.BooleanVar()
        self.var_si = tk.BooleanVar()

        self.var_lang_list = []
        self.var_path_list = []
        self.var_port_list = []
        self.var_speed_list = []

        self.var_lang = tk.StringVar()
        self.var_path = tk.StringVar()
        self.var_port = tk.StringVar()
        self.var_speed = tk.StringVar()
        self.var_csv_option = tk.StringVar()

        self.var_log_name = tk.StringVar()
        self.var_other_options = tk.StringVar()

        self.load_settings()

        self.root.title("Pyren Launcher")
        self.style = tkinter.ttk.Style()
        self.style.theme_use("clam")

        if sys.platform == "win32":
            self.style.theme_use("winnative")

        self.style.configure(".", background="#d9d9d9")
        self.style.configure(".", foreground="#000000")
        self.style.configure(".", font="TkDefaultFont")
        self.style.map(".", background=[("selected", "#d9d9d9"), ("active", "#d9d9d9")])

        self.root.geometry("800x800+0+28")
        self.root.title("Pyren launcher")
        self.root.configure(background="#d9d9d9")
        self.root.configure(highlightbackground="#d9d9d9")
        self.root.configure(highlightcolor="black")

        self.label_path_selector = tk.LabelFrame(self.root)
        self.label_path_selector.place(
            relx=0.02, rely=0.0, relheight=0.13, relwidth=0.46
        )
        self.label_path_selector.configure(relief=tk.GROOVE)
        self.label_path_selector.configure(foreground="black")
        self.label_path_selector.configure(text="""Version""")
        self.label_path_selector.configure(background="#d9d9d9")
        self.label_path_selector.configure(highlightbackground="#d9d9d9")
        self.label_path_selector.configure(highlightcolor="black")
        self.label_path_selector.configure(width=230)

        self.label_db_language = tk.LabelFrame(self.root)
        self.label_db_language.place(
            relx=0.02, rely=0.14, relheight=0.13, relwidth=0.46
        )
        self.label_db_language.configure(relief=tk.GROOVE)
        self.label_db_language.configure(foreground="black")
        self.label_db_language.configure(text="""DB Language""")
        self.label_db_language.configure(background="#d9d9d9")
        self.label_db_language.configure(highlightbackground="#d9d9d9")
        self.label_db_language.configure(highlightcolor="black")
        self.label_db_language.configure(width=100)

        self.label_port_selector = tk.LabelFrame(self.root)
        self.label_port_selector.place(
            relx=0.5, rely=0.0, relheight=0.27, relwidth=0.48
        )
        self.label_port_selector.configure(relief=tk.GROOVE)
        self.label_port_selector.configure(foreground="black")
        self.label_port_selector.configure(text="""Port""")
        self.label_port_selector.configure(background="#d9d9d9")
        self.label_port_selector.configure(highlightbackground="#d9d9d9")
        self.label_port_selector.configure(highlightcolor="black")
        self.label_port_selector.configure(width=240)

        self.label_port_speed = tk.LabelFrame(self.root)
        self.label_port_speed.place(relx=0.52, rely=0.12, relheight=0.13, relwidth=0.44)
        self.label_port_speed.configure(relief=tk.GROOVE)
        self.label_port_speed.configure(foreground="black")
        self.label_port_speed.configure(text="""Port Speed (only for USB-ELM)""")
        self.label_port_speed.configure(background="#d9d9d9")
        self.label_port_speed.configure(highlightbackground="#d9d9d9")
        self.label_port_speed.configure(highlightcolor="black")
        self.label_port_speed.configure(width=220)

        self.label_options = tk.LabelFrame(self.root)
        self.label_options.place(relx=0.02, rely=0.69, relheight=0.13, relwidth=0.96)
        self.label_options.configure(relief=tk.GROOVE)
        self.label_options.configure(foreground="black")
        self.label_options.configure(text="""Other options""")
        self.label_options.configure(background="#d9d9d9")
        self.label_options.configure(highlightbackground="#d9d9d9")
        self.label_options.configure(highlightcolor="black")
        self.label_options.configure(width=480)

        self.label_log = tk.LabelFrame(self.root)
        self.label_log.place(relx=0.5, rely=0.28, relheight=0.135, relwidth=0.48)
        self.label_log.configure(relief=tk.GROOVE)
        self.label_log.configure(foreground="black")
        self.label_log.configure(text="""ELM Log""")
        self.label_log.configure(background="#d9d9d9")
        self.label_log.configure(highlightbackground="#d9d9d9")
        self.label_log.configure(highlightcolor="black")
        self.label_log.configure(width=230)

        self.label_can = tk.LabelFrame(self.root)
        self.label_can.place(relx=0.02, rely=0.43, relheight=0.25, relwidth=0.46)
        self.label_can.configure(relief=tk.GROOVE)
        self.label_can.configure(foreground="black")
        self.label_can.configure(text="""CAN""")
        self.label_can.configure(background="#d9d9d9")
        self.label_can.configure(highlightbackground="#d9d9d9")
        self.label_can.configure(highlightcolor="black")
        self.label_can.configure(width=230)

        self.label_csv = tk.LabelFrame(self.root)
        self.label_csv.place(relx=0.02, rely=0.28, relheight=0.135, relwidth=0.46)
        self.label_csv.configure(relief=tk.GROOVE)
        self.label_csv.configure(foreground="black")
        self.label_csv.configure(text="""Data logging""")
        self.label_csv.configure(background="#d9d9d9")
        self.label_csv.configure(highlightbackground="#d9d9d9")
        self.label_csv.configure(highlightcolor="black")
        self.label_csv.configure(width=240)

        self.label_kwp = tk.LabelFrame(self.root)
        self.label_kwp.place(relx=0.5, rely=0.43, relheight=0.125, relwidth=0.48)
        self.label_kwp.configure(relief=tk.GROOVE)
        self.label_kwp.configure(foreground="black")
        self.label_kwp.configure(text="""K-Line""")
        self.label_kwp.configure(background="#d9d9d9")
        self.label_kwp.configure(highlightbackground="#d9d9d9")
        self.label_kwp.configure(highlightcolor="black")
        self.label_kwp.configure(width=240)

        self.message_cfc = tk.Message(self.root)
        self.message_cfc.place(relx=0.08, rely=0.5, relheight=0.06, relwidth=0.1)
        self.message_cfc.configure(background="#d9d9d9")
        self.message_cfc.configure(foreground="#000000")
        self.message_cfc.configure(highlightbackground="#d9d9d9")
        self.message_cfc.configure(highlightcolor="black")
        self.message_cfc.configure(text="""--cfc""")
        self.message_cfc.configure(width=40)

        self.message_n1c = tk.Message(self.root)
        self.message_n1c.place(relx=0.08, rely=0.57, relheight=0.06, relwidth=0.1)
        self.message_n1c.configure(background="#d9d9d9")
        self.message_n1c.configure(foreground="#000000")
        self.message_n1c.configure(highlightbackground="#d9d9d9")
        self.message_n1c.configure(highlightcolor="black")
        self.message_n1c.configure(text="""--n1c""")
        self.message_n1c.configure(width=40)

        self.message_slow_init = tk.Message(self.root)
        self.message_slow_init.place(
            relx=0.56, rely=0.48, relheight=0.03, relwidth=0.08
        )
        self.message_slow_init.configure(background="#d9d9d9")
        self.message_slow_init.configure(foreground="#000000")
        self.message_slow_init.configure(highlightbackground="#d9d9d9")
        self.message_slow_init.configure(highlightcolor="black")
        self.message_slow_init.configure(text="""--si""")
        self.message_slow_init.configure(width=40)

        self.message_can = tk.Message(self.root)
        self.message_can.place(relx=0.18, rely=0.48, relheight=0.18, relwidth=0.28)
        self.message_can.configure(background="#d9d9d9")
        self.message_can.configure(foreground="#000000")
        self.message_can.configure(highlightbackground="#d9d9d9")
        self.message_can.configure(highlightcolor="black")
        self.message_can.configure(
            text="""CFC - enable soft flow control (recommended)          N1C - disable L1 cache (not recommended)"""
        )
        self.message_can.configure(width=142)

        self.message_kwp = tk.Message(self.root)
        self.message_kwp.place(relx=0.64, rely=0.46, relheight=0.08, relwidth=0.3)
        self.message_kwp.configure(background="#d9d9d9")
        self.message_kwp.configure(foreground="#000000")
        self.message_kwp.configure(highlightbackground="#d9d9d9")
        self.message_kwp.configure(highlightcolor="black")
        self.message_kwp.configure(
            text="""Try Slow Init before Fast Init. It may helps with old ECUs"""
        )
        self.message_kwp.configure(width=152)

        self.log_name = tk.Entry(self.root)
        self.log_name.place(relx=0.58, rely=0.33, relheight=0.06, relwidth=0.37)
        self.log_name.configure(background="white")
        self.log_name.configure(font="TkFixedFont")
        self.log_name.configure(foreground="#000000")
        self.log_name.configure(highlightbackground="#d9d9d9")
        self.log_name.configure(highlightcolor="black")
        self.log_name.configure(insertbackground="black")
        self.log_name.configure(selectbackground="#c4c4c4")
        self.log_name.configure(selectforeground="black")
        self.log_name.configure(textvariable=self.var_log_name)

        self.check_log = tk.Checkbutton(self.root)
        self.check_log.place(relx=0.52, rely=0.325, relheight=0.07, relwidth=0.06)
        self.check_log.configure(activebackground="#d9d9d9")
        self.check_log.configure(activeforeground="#000000")
        self.check_log.configure(background="#d9d9d9")
        self.check_log.configure(foreground="#000000")
        self.check_log.configure(highlightbackground="#d9d9d9")
        self.check_log.configure(highlightcolor="black")
        self.check_log.configure(justify=tk.LEFT)
        self.check_log.configure(variable=self.var_log)

        self.check_cfc = tk.Checkbutton(self.label_can)
        self.check_cfc.place(relx=0.04, rely=0.17, relheight=0.29, relwidth=0.13)
        self.check_cfc.configure(activebackground="#d9d9d9")
        self.check_cfc.configure(activeforeground="#000000")
        self.check_cfc.configure(background="#d9d9d9")
        self.check_cfc.configure(foreground="#000000")
        self.check_cfc.configure(highlightbackground="#d9d9d9")
        self.check_cfc.configure(highlightcolor="black")
        self.check_cfc.configure(justify=tk.LEFT)
        self.check_cfc.configure(variable=self.var_cfc)

        self.check_n1c = tk.Checkbutton(self.label_can)
        self.check_n1c.place(relx=0.04, rely=0.48, relheight=0.29, relwidth=0.13)
        self.check_n1c.configure(activebackground="#d9d9d9")
        self.check_n1c.configure(activeforeground="#000000")
        self.check_n1c.configure(background="#d9d9d9")
        self.check_n1c.configure(foreground="#000000")
        self.check_n1c.configure(highlightbackground="#d9d9d9")
        self.check_n1c.configure(highlightcolor="black")
        self.check_n1c.configure(justify=tk.LEFT)
        self.check_n1c.configure(variable=self.var_n1c)

        self.check_slow_init = tk.Checkbutton(self.label_kwp)
        self.check_slow_init.place(relx=0.04, rely=0.15, relheight=0.43, relwidth=0.13)
        self.check_slow_init.configure(activebackground="#d9d9d9")
        self.check_slow_init.configure(activeforeground="#000000")
        self.check_slow_init.configure(background="#d9d9d9")
        self.check_slow_init.configure(foreground="#000000")
        self.check_slow_init.configure(highlightbackground="#d9d9d9")
        self.check_slow_init.configure(highlightcolor="black")
        self.check_slow_init.configure(justify=tk.LEFT)
        self.check_slow_init.configure(variable=self.var_si)

        self.check_scv = tk.Checkbutton(self.label_csv)
        self.check_scv.place(relx=0.05, rely=0.24, relheight=0.4, relwidth=0.1)
        self.check_scv.configure(activebackground="#d9d9d9")
        self.check_scv.configure(activeforeground="#000000")
        self.check_scv.configure(background="#d9d9d9")
        self.check_scv.configure(foreground="#000000")
        self.check_scv.configure(highlightbackground="#d9d9d9")
        self.check_scv.configure(highlightcolor="black")
        self.check_scv.configure(justify=tk.LEFT)
        self.check_scv.configure(variable=self.var_csv)

        self.label_dump = tk.LabelFrame(self.root)
        self.label_dump.place(relx=0.5, rely=0.56, relheight=0.12, relwidth=0.10)
        self.label_dump.configure(relief=tk.GROOVE)
        self.label_dump.configure(foreground="black")
        self.label_dump.configure(text="""Dump""")
        self.label_dump.configure(background="#d9d9d9")
        self.label_dump.configure(highlightbackground="#d9d9d9")
        self.label_dump.configure(highlightcolor="black")
        self.label_dump.configure(width=60)

        self.label_can2 = tk.LabelFrame(self.root)
        self.label_can2.place(relx=0.62, rely=0.56, relheight=0.12, relwidth=0.10)
        self.label_can2.configure(relief=tk.GROOVE)
        self.label_can2.configure(foreground="black")
        self.label_can2.configure(text="""CAN 2""")
        self.label_can2.configure(background="#d9d9d9")
        self.label_can2.configure(highlightbackground="#d9d9d9")
        self.label_can2.configure(highlightcolor="black")
        self.label_can2.configure(width=60)

        self.check_dump = tk.Checkbutton(self.label_dump)
        self.check_dump.place(relx=0.265, rely=0.18, relheight=0.55, relwidth=0.5)
        self.check_dump.configure(activebackground="#d9d9d9")
        self.check_dump.configure(activeforeground="#000000")
        self.check_dump.configure(background="#d9d9d9")
        self.check_dump.configure(foreground="#000000")
        self.check_dump.configure(highlightbackground="#d9d9d9")
        self.check_dump.configure(highlightcolor="black")
        self.check_dump.configure(variable=self.var_dump)
        self.check_dump.configure(width=34)

        self.check_can2 = tk.Checkbutton(self.label_can2)
        self.check_can2.place(relx=0.28, rely=0.18, relheight=0.55, relwidth=0.5)
        self.check_can2.configure(activebackground="#d9d9d9")
        self.check_can2.configure(activeforeground="#000000")
        self.check_can2.configure(background="#d9d9d9")
        self.check_can2.configure(foreground="#000000")
        self.check_can2.configure(highlightbackground="#d9d9d9")
        self.check_can2.configure(highlightcolor="black")
        self.check_can2.configure(variable=self.var_can2)
        self.check_can2.configure(width=34)

        self.options = tk.Entry(self.root)
        self.options.place(relx=0.04, rely=0.74, relheight=0.06, relwidth=0.92)
        self.options.configure(background="white")
        self.options.configure(font="TkFixedFont")
        self.options.configure(foreground="#000000")
        self.options.configure(highlightbackground="#d9d9d9")
        self.options.configure(highlightcolor="black")
        self.options.configure(insertbackground="black")
        self.options.configure(selectbackground="#c4c4c4")
        self.options.configure(selectforeground="black")
        self.options.configure(textvariable=self.var_other_options)

        self.btn_start = tk.Button(self.root)
        self.btn_start.place(
            relx=0.01, rely=0.84, height=self.btn_height, width=self.btn_width
        )
        self.btn_start.configure(activebackground="#d9d9d9")
        self.btn_start.configure(activeforeground="#000000")
        self.btn_start.configure(background="#d9d9d9")
        self.btn_start.configure(command=self.cmd_start)
        self.btn_start.configure(foreground="#000000")
        self.btn_start.configure(highlightbackground="#d9d9d9")
        self.btn_start.configure(highlightcolor="black")
        self.btn_start.configure(text="""Start pyren""")

        self.btn_ddt = tk.Button(self.root)
        self.btn_ddt.place(
            relx=0.01, rely=0.91, height=self.btn_height, width=self.btn_width
        )
        self.btn_ddt.configure(activebackground="#d9d9d9")
        self.btn_ddt.configure(activeforeground="#000000")
        self.btn_ddt.configure(background="#d9d9d9")
        self.btn_ddt.configure(command=self.cmd_ddt)
        self.btn_ddt.configure(foreground="#000000")
        self.btn_ddt.configure(highlightbackground="#d9d9d9")
        self.btn_ddt.configure(highlightcolor="black")
        self.btn_ddt.configure(text="""Start DDT""")

        self.btn_scan = tk.Button(self.root)
        self.btn_scan.place(
            relx=0.21, rely=0.84, height=self.btn_height, width=self.btn_width
        )
        self.btn_scan.configure(activebackground="#d9d9d9")
        self.btn_scan.configure(activeforeground="#000000")
        self.btn_scan.configure(background="#d9d9d9")
        self.btn_scan.configure(command=self.cmd_scan)
        self.btn_scan.configure(foreground="#000000")
        self.btn_scan.configure(highlightbackground="#d9d9d9")
        self.btn_scan.configure(highlightcolor="black")
        self.btn_scan.configure(text="""Scan""")
        self.btn_scan.configure(width=120)

        self.btn_demo = tk.Button(self.root)
        self.btn_demo.place(
            relx=0.41, rely=0.84, height=self.btn_height, width=self.btn_width
        )
        self.btn_demo.configure(activebackground="#d9d9d9")
        self.btn_demo.configure(activeforeground="#000000")
        self.btn_demo.configure(background="#d9d9d9")
        self.btn_demo.configure(command=self.cmd_demo)
        self.btn_demo.configure(foreground="#000000")
        self.btn_demo.configure(highlightbackground="#d9d9d9")
        self.btn_demo.configure(highlightcolor="black")
        self.btn_demo.configure(text="""Demo""")
        self.btn_demo.configure(width=120)

        self.btn_check = tk.Button(self.root)
        self.btn_check.place(
            relx=0.61, rely=0.84, height=self.btn_height, width=self.btn_width
        )
        self.btn_check.configure(activebackground="#d9d9d9")
        self.btn_check.configure(activeforeground="#000000")
        self.btn_check.configure(background="#d9d9d9")
        self.btn_check.configure(command=self.cmd_check)
        self.btn_check.configure(foreground="#000000")
        self.btn_check.configure(highlightbackground="#d9d9d9")
        self.btn_check.configure(highlightcolor="black")
        self.btn_check.configure(text="""Check ELM""")

        self.btn_mon = tk.Button(self.root)
        self.btn_mon.place(
            relx=0.81, rely=0.84, height=self.btn_height, width=self.btn_width
        )
        self.btn_mon.configure(activebackground="#d9d9d9")
        self.btn_mon.configure(activeforeground="#000000")
        self.btn_mon.configure(background="#d9d9d9")
        self.btn_mon.configure(command=self.cmd_mon)
        self.btn_mon.configure(foreground="#000000")
        self.btn_mon.configure(highlightbackground="#d9d9d9")
        self.btn_mon.configure(highlightcolor="black")
        self.btn_mon.configure(text="""Monitor""")

        self.btn_mac = tk.Button(self.root)
        self.btn_mac.place(
            relx=0.81, rely=0.91, height=self.btn_height, width=self.btn_width
        )
        self.btn_mac.configure(activebackground="#d9d9d9")
        self.btn_mac.configure(activeforeground="#000000")
        self.btn_mac.configure(background="#d9d9d9")
        self.btn_mac.configure(command=self.cmd_term)
        self.btn_mac.configure(foreground="#000000")
        self.btn_mac.configure(highlightbackground="#d9d9d9")
        self.btn_mac.configure(highlightcolor="black")
        self.btn_mac.configure(text="""Macro""")

        self.btn_upg = tk.Button(self.root)
        self.btn_upg.place(
            relx=0.41, rely=0.91, height=self.btn_height, width=self.btn_width
        )
        self.btn_upg.configure(activebackground="#d9d9d9")
        self.btn_upg.configure(activeforeground="#000000")
        self.btn_upg.configure(background="#d9d9d9")
        self.btn_upg.configure(command=self.cmd_update)
        self.btn_upg.configure(foreground="#000000")
        self.btn_upg.configure(highlightbackground="#d9d9d9")
        self.btn_upg.configure(highlightcolor="black")
        self.btn_upg.configure(text="""Update""")

        self.path_list = tkinter.ttk.Combobox(self.root)
        self.path_list.place(relx=0.04, rely=0.05, relheight=0.06, relwidth=0.41)
        self.path_list.configure(values=["./pyren09a", "./pyren09a"])
        self.path_list.configure(values=self.var_path_list)
        self.path_list.configure(textvariable=self.var_path)
        self.path_list.configure(takefocus="")

        self.port_list = tkinter.ttk.Combobox(self.root)
        self.port_list.place(relx=0.52, rely=0.05, relheight=0.06, relwidth=0.43)
        self.port_list.configure(values=self.var_port_list)
        self.port_list.configure(textvariable=self.var_port)
        self.port_list.configure(takefocus="")

        self.speed_list = tkinter.ttk.Combobox(self.root)
        self.speed_list.place(relx=0.54, rely=0.17, relheight=0.06, relwidth=0.41)
        self.speed_list.configure(values=self.var_speed_list)
        self.speed_list.configure(textvariable=self.var_speed)
        self.speed_list.configure(takefocus="")

        self.csv_list = tkinter.ttk.Combobox(self.root)
        self.csv_list.place(relx=0.10, rely=0.33, relheight=0.06, relwidth=0.35)
        self.csv_list.configure(values=self.var_csv_options)
        self.csv_list.configure(textvariable=self.var_csv_option)
        self.csv_list.configure(takefocus="")

        self.lang_list = tkinter.ttk.Combobox(self.root)
        self.lang_list.place(relx=0.04, rely=0.185, relheight=0.06, relwidth=0.41)
        self.lang_list.configure(values=self.var_lang_list)
        self.lang_list.configure(textvariable=self.var_lang)
        self.lang_list.configure(takefocus="")

        self.root.focus_force()
        self.root.focus_set()
        self.root.mainloop()


def main():
    DesktopGui()
