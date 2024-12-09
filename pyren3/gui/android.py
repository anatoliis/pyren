import re

from pyren3 import config
from pyren3.enums import Command
from pyren3.runner import run
from pyren3.settings import Settings
from pyren3.utils import getLangList, getPathList, update_from_gitlab

try:
    import androidhelper as android
except ImportError:
    try:
        import android
    except ImportError:
        pass


class AndroidGui:
    save = None
    pl = []
    ll = []
    csvl = []

    def cmd_Mon(self):
        self.saveSettings()
        self.droid.fullDismiss()
        run(self.save, Command.MON)

    def cmd_Check(self):
        self.saveSettings()
        self.droid.fullDismiss()
        run(self.save, Command.CHECK)

    def cmd_Demo(self):
        self.saveSettings()
        self.droid.fullDismiss()
        run(self.save, Command.DEMO)

    def cmd_Scan(self):
        self.saveSettings()
        self.droid.fullDismiss()
        run(self.save, Command.SCAN)

    def cmd_Start(self):
        self.saveSettings()
        self.droid.fullDismiss()
        run(self.save, Command.PYREN)

    def cmd_Term(self):
        self.saveSettings()
        self.droid.fullDismiss()
        run(self.save, Command.TERM)

    def cmd_PIDs(self):
        self.saveSettings()
        self.droid.fullDismiss()
        run(self.save, Command.PIDS)

    def cmd_Update(self):
        res = update_from_gitlab()
        if res == 0:
            self.droid.makeToast("Done")
        elif res == 1:
            self.droid.makeToast("No connection with gitlab.com")
        elif res == 2:
            self.droid.makeToast("UnZip error")

    def saveSettings(self):
        self.save.path = self.pl[
            int(self.droid.fullQueryDetail("sp_version").result["selectedItemPosition"])
        ]
        self.save.lang = self.ll[
            int(
                self.droid.fullQueryDetail("sp_language").result["selectedItemPosition"]
            )
        ]
        self.save.csv_option = self.csvl[
            int(self.droid.fullQueryDetail("sp_csv").result["selectedItemPosition"])
        ]

        if self.droid.fullQueryDetail("rb_bt").result["checked"] == "false":
            self.save.port = "192.168.0.10:35000"
        else:
            portName = self.dev_list[
                int(
                    self.droid.fullQueryDetail("in_wifi").result["selectedItemPosition"]
                )
            ]
            upPortName = portName.upper().split(";")[0]
            MAC = ""
            if (
                re.match(
                    r"^[0-9A-F]{2}:[0-9A-F]{2}:[0-9A-F]{2}:[0-9A-F]{2}:[0-9A-F]{2}:[0-9A-F]{2}$",
                    upPortName,
                )
                or re.match(r"^[0-9A-F]{4}.[0-9A-F]{4}.[0-9A-F]{4}$", upPortName)
                or re.match(r"^[0-9A-F]{12}$", upPortName)
            ):
                upPortName = upPortName.replace(":", "").replace(".", "")
                MAC = ":".join(a + b for a, b in zip(upPortName[::2], upPortName[1::2]))
            self.save.port = MAC + ";" + "BT"

        self.save.speed = "38400"

        self.save.log_name = self.droid.fullQueryDetail("in_logname").result["text"]

        if self.droid.fullQueryDetail("cb_log").result["checked"] == "false":
            self.save.log = False
        else:
            self.save.log = True

        if self.droid.fullQueryDetail("cb_cfc").result["checked"] == "false":
            self.save.cfc = False
        else:
            self.save.cfc = True

        if self.droid.fullQueryDetail("cb_n1c").result["checked"] == "false":
            self.save.n1c = False
        else:
            self.save.n1c = True

        if self.droid.fullQueryDetail("cb_si").result["checked"] == "false":
            self.save.si = False
        else:
            self.save.si = True

        if self.droid.fullQueryDetail("cb_csv").result["checked"] == "false":
            self.save.csv = False
        else:
            self.save.csv = True

        if self.droid.fullQueryDetail("cb_dump").result["checked"] == "false":
            self.save.dump = False
        else:
            self.save.dump = True

        if self.droid.fullQueryDetail("cb_can2").result["checked"] == "false":
            self.save.can2 = False
        else:
            self.save.can2 = True

        self.save.options = self.droid.fullQueryDetail("in_options").result["text"]

        self.save.save()

    def loadSettings(self):
        pl = getPathList()
        if self.save.path in pl:
            pl.insert(0, pl.pop(pl.index(self.save.path)))
        self.droid.fullSetList("sp_version", pl)
        self.pl = pl

        ll = getLangList()
        if self.save.lang in ll:
            ll.insert(0, ll.pop(ll.index(self.save.lang)))
        self.droid.fullSetList("sp_language", ll)
        self.ll = ll

        csvl = config.CSV_OPTIONS
        if self.save.csv_option in csvl:
            csvl.insert(0, csvl.pop(csvl.index(self.save.csv_option)))
        self.droid.fullSetList("sp_csv", csvl)
        self.csvl = csvl

        if self.save.port == "":
            self.save.port = "192.168.0.10:35000;WiFi"
            self.dev_list.append(self.save.port)
        if self.save.port.upper().endswith("BT"):
            MAC = ""
            if ";" in self.save.port:
                MAC = self.save.port.split(";")[0]
            for d in self.dev_list:
                if MAC in d:
                    self.dev_list.insert(0, self.dev_list.pop(self.dev_list.index(d)))

            self.droid.fullSetProperty("rb_bt", "checked", "true")
            self.droid.fullSetProperty("rb_wifi", "checked", "false")
            self.droid.fullSetList("in_wifi", self.dev_list)
        else:
            self.droid.fullSetProperty("rb_bt", "checked", "false")
            self.droid.fullSetProperty("rb_wifi", "checked", "true")
            self.droid.fullSetList("in_wifi", self.dev_list)

        self.droid.fullSetProperty("in_logname", "text", self.save.log_name)
        if self.save.log:
            self.droid.fullSetProperty("cb_log", "checked", "true")
        else:
            self.droid.fullSetProperty("cb_log", "checked", "false")

        if self.save.cfc:
            self.droid.fullSetProperty("cb_cfc", "checked", "true")
        else:
            self.droid.fullSetProperty("cb_cfc", "checked", "false")

        if self.save.n1c:
            self.droid.fullSetProperty("cb_n1c", "checked", "true")
        else:
            self.droid.fullSetProperty("cb_n1c", "checked", "false")

        if self.save.si:
            self.droid.fullSetProperty("cb_si", "checked", "true")
        else:
            self.droid.fullSetProperty("cb_si", "checked", "false")

        if self.save.csv:
            self.droid.fullSetProperty("cb_csv", "checked", "true")
        else:
            self.droid.fullSetProperty("cb_csv", "checked", "false")

        if self.save.dump:
            self.droid.fullSetProperty("cb_dump", "checked", "true")
        else:
            self.droid.fullSetProperty("cb_dump", "checked", "false")

        if self.save.can2:
            self.droid.fullSetProperty("cb_can2", "checked", "true")
        else:
            self.droid.fullSetProperty("cb_can2", "checked", "false")

        self.droid.fullSetProperty("in_options", "text", self.save.options)

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
                android:id="@+id/tx_Versions"
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:layout_alignParentTop="true"
                android:text="Version"/>
            <Spinner
                android:id="@+id/sp_version"
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:layout_alignParentLeft="true"
                android:layout_below="@+id/tx_Versions" />
            <TextView
                android:id="@+id/tx_language"
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:layout_alignParentLeft="true"
                android:layout_below="@+id/sp_version"
                android:text="DB language" />
            <Spinner
                android:id="@+id/sp_language"
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:layout_below="@id/tx_language"/>
            <TextView
                android:id="@+id/tx_elm"
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:layout_alignParentLeft="true"
                android:layout_below="@+id/sp_language"
                android:text="ELM327" />
            <RadioGroup
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:orientation="horizontal"
                android:layout_below="@id/tx_elm"
                android:id="@+id/radioGroup">
                <RadioButton
                    android:id="@id/rb_bt"
                    android:layout_width="wrap_content"
                    android:layout_height="match_parent"
                    android:checked="true"
                    android:text="BT" />
                <RadioButton
                    android:id="@id/rb_wifi"
                    android:layout_width="wrap_content"
                    android:layout_height="wrap_content"
                    android:checked="false"
                    android:text="WiFi" />
            </RadioGroup>
            <Spinner
                android:id="@+id/in_wifi"
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:layout_alignParentRight="true"
                android:layout_below="@id/tx_elm"
                android:layout_toRightOf="@id/radioGroup"
                android:layout_marginLeft="20dp" />
            <TextView
                android:id="@+id/tx_log"
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:layout_alignParentLeft="true"
                android:layout_below="@+id/radioGroup"
                android:text="Log" />
            <CheckBox
                android:id="@+id/cb_log"
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:layout_below="@id/tx_log"
                android:layout_marginLeft="20dp"
                android:layout_marginRight="20dp"
                android:layout_toRightOf="@+id/tx_log"/>
            <EditText
                android:id="@+id/in_logname"
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:layout_below="@id/tx_log"
                android:layout_toRightOf="@+id/cb_log"
                android:ems="10"
                android:text="log.txt" />
            <TextView
                android:id="@+id/tx_csv"
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:layout_alignParentLeft="true"
                android:layout_below="@+id/in_logname"
                android:text="Data logging" />
            <CheckBox
                android:id="@+id/cb_csv"
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:layout_below="@id/tx_csv"
                android:layout_marginRight="20dp"
                android:layout_alignLeft="@+id/cb_log" />
            <Spinner
                android:id="@+id/sp_csv"
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:layout_below="@id/tx_csv"
                android:layout_toRightOf="@+id/cb_csv" />
            <TextView
                android:id="@+id/tx_can"
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:layout_below="@id/sp_csv"
                android:text="CAN parameters" />
            <CheckBox
                android:id="@+id/cb_cfc"
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:layout_below="@id/tx_can"
                android:layout_toRightOf="@id/tx_can"
                android:text="--cfc" />
            <CheckBox
                android:id="@+id/cb_n1c"
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:layout_alignBottom="@id/cb_cfc"
                android:layout_toRightOf="@id/cb_cfc"
                android:layout_marginLeft="40dp"
                android:text="--n1c" />
            <TextView
                android:id="@+id/tx_iso"
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:layout_below="@id/cb_cfc"
                android:layout_alignParentLeft="true"
                android:text="K-line parameters" />
            <CheckBox
                android:id="@+id/cb_si"
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:layout_below="@id/tx_iso"
                android:layout_alignLeft="@id/cb_cfc"
                android:text="--si (Prefer SlowInit)" />
            <TextView
                android:id="@+id/tx_options"
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:layout_below="@id/cb_si"
                android:layout_alignParentLeft="true"
                android:text="Other options" />    
            <CheckBox
                android:id="@+id/cb_dump"
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:layout_below="@id/tx_options"
                android:layout_toRightOf="@id/tx_options"
                android:text="Dump" />
            <CheckBox
                android:id="@+id/cb_can2"
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:layout_toRightOf="@id/cb_dump"
                android:layout_alignBottom="@id/cb_dump"
                android:layout_marginLeft="60dp"
                android:text="CAN2" />    
             <EditText
                android:id="@+id/in_options"
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:layout_below="@+id/cb_dump"
                android:layout_centerHorizontal="true"
                android:ems="10"
                android:inputType="textPersonName" />
            <Button
                android:id="@+id/bt_start"
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:layout_alignParentLeft="true"
                android:layout_below="@id/in_options"
                android:text="Start" />
            <Button
                android:id="@+id/bt_scan"
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:layout_toRightOf="@id/bt_start"
                android:layout_below="@id/in_options"
                android:text="Scan" />
            <Button
                android:id="@+id/bt_demo"
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:layout_below="@id/in_options"
                android:layout_toRightOf="@id/bt_scan"
                android:text="Demo" />
            <Button
                android:id="@+id/bt_check"
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:layout_below="@id/bt_start"
                android:layout_alignParentRight="true"
                android:text="ChkELM" />
            <Button
                android:id="@+id/bt_mon"
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:layout_below="@id/bt_start"
                android:layout_toLeftOf="@id/bt_check"
                android:text="Monitor" />
            <Button
                android:id="@+id/bt_term"
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:layout_below="@id/bt_start"
                android:layout_toLeftOf="@+id/bt_mon"
                android:text="Macro" />
            <Button
                android:id="@+id/bt_pids"
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:layout_below="@id/bt_start"
                android:layout_toLeftOf="@+id/bt_term"
                android:text="PIDs" />
            <Button
                android:id="@+id/bt_update"
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:layout_alignParentRight="true"
                android:layout_below="@id/in_options"
                android:text="Update" />
        </RelativeLayout>

    </ScrollView>

</RelativeLayout>"""

    def eventloop(self):
        while True:
            event = self.droid.eventWait(50).result
            if event is None:
                continue
            if event["name"] == "click":
                id = event["data"]["id"]
                if id == "bt_start":
                    self.cmd_Start()
                elif id == "bt_scan":
                    self.cmd_Scan()
                elif id == "bt_demo":
                    self.cmd_Demo()
                elif id == "bt_check":
                    self.cmd_Check()
                elif id == "bt_mon":
                    self.cmd_Mon()
                elif id == "bt_term":
                    self.cmd_Term()
                elif id == "bt_pids":
                    self.cmd_PIDs()
                elif id == "bt_update":
                    self.cmd_Update()

    def __init__(self):
        self.save = Settings()
        try:
            self.droid = android.Android()
            self.droid.fullShow(self.lay)
            self.dev_list = ["192.168.0.10:35000;WiFi"]
            try:
                tmp = self.droid.bluetoothGetBondedDevices().result
                for i in range(0, len(tmp), 2):
                    self.dev_list.append(tmp[i] + ";" + tmp[i + 1])
            except Exception:
                pass
            self.loadSettings()
            self.eventloop()
        finally:
            self.droid.fullDismiss()

    def __del__(self):
        self.droid.fullDismiss()


def main():
    AndroidGui()
