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
    settings = None
    paths_list = []
    language_list = []
    csv_options_list = []

    def cmd(self, command: Command):
        self.save_settings()
        self.droid.fullDismiss()
        run(self.settings, command)

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

    def cmd_term(self):
        self.cmd(Command.TERM)

    def cmd_pids(self):
        self.cmd(Command.PIDS)

    def cmd_update(self):
        res = update_from_gitlab()
        if res == 0:
            self.droid.makeToast("Done")
        elif res == 1:
            self.droid.makeToast("No connection with gitlab.com")
        elif res == 2:
            self.droid.makeToast("UnZip error")

    def save_settings(self):
        self.settings.path = self.paths_list[
            int(self.droid.fullQueryDetail("sp_version").result["selectedItemPosition"])
        ]
        self.settings.lang = self.language_list[
            int(
                self.droid.fullQueryDetail("sp_language").result["selectedItemPosition"]
            )
        ]
        self.settings.csv_option = self.csv_options_list[
            int(self.droid.fullQueryDetail("sp_csv").result["selectedItemPosition"])
        ]

        if self.droid.fullQueryDetail("rb_bt").result["checked"] == "false":
            self.settings.port = "192.168.0.10:35000"
        else:
            port_name = self.devices_list[
                int(
                    self.droid.fullQueryDetail("in_wifi").result["selectedItemPosition"]
                )
            ]
            port_name_upper = port_name.upper().split(";")[0]
            mac_addr = ""
            if (
                re.match(
                    r"^[0-9A-F]{2}:[0-9A-F]{2}:[0-9A-F]{2}:[0-9A-F]{2}:[0-9A-F]{2}:[0-9A-F]{2}$",
                    port_name_upper,
                )
                or re.match(r"^[0-9A-F]{4}.[0-9A-F]{4}.[0-9A-F]{4}$", port_name_upper)
                or re.match(r"^[0-9A-F]{12}$", port_name_upper)
            ):
                port_name_upper = port_name_upper.replace(":", "").replace(".", "")
                mac_addr = ":".join(
                    a + b for a, b in zip(port_name_upper[::2], port_name_upper[1::2])
                )
            self.settings.port = mac_addr + ";" + "BT"

        self.settings.speed = "38400"

        self.settings.log_name = self.droid.fullQueryDetail("in_logname").result["text"]

        if self.droid.fullQueryDetail("cb_log").result["checked"] != "false":
            self.settings.log = False
        else:
            self.settings.log = True

        if self.droid.fullQueryDetail("cb_cfc").result["checked"] == "false":
            self.settings.cfc = False
        else:
            self.settings.cfc = True

        if self.droid.fullQueryDetail("cb_n1c").result["checked"] == "false":
            self.settings.n1c = False
        else:
            self.settings.n1c = True

        if self.droid.fullQueryDetail("cb_si").result["checked"] == "false":
            self.settings.si = False
        else:
            self.settings.si = True

        if self.droid.fullQueryDetail("cb_csv").result["checked"] == "false":
            self.settings.csv = False
        else:
            self.settings.csv = True

        if self.droid.fullQueryDetail("cb_dump").result["checked"] == "false":
            self.settings.dump = False
        else:
            self.settings.dump = True

        if self.droid.fullQueryDetail("cb_can2").result["checked"] == "false":
            self.settings.can2 = False
        else:
            self.settings.can2 = True

        self.settings.options = self.droid.fullQueryDetail("in_options").result["text"]

        self.settings.save()

    def load_settings(self):
        paths_list = getPathList()
        if self.settings.path in paths_list:
            paths_list.insert(0, paths_list.pop(paths_list.index(self.settings.path)))
        self.droid.fullSetList("sp_version", paths_list)
        self.paths_list = paths_list

        language_list = getLangList()
        if self.settings.lang in language_list:
            language_list.insert(
                0, language_list.pop(language_list.index(self.settings.lang))
            )
        self.droid.fullSetList("sp_language", language_list)
        self.language_list = language_list

        csv_options_list = config.CSV_OPTIONS
        if self.settings.csv_option in csv_options_list:
            csv_options_list.insert(
                0,
                csv_options_list.pop(csv_options_list.index(self.settings.csv_option)),
            )
        self.droid.fullSetList("sp_csv", csv_options_list)
        self.csv_options_list = csv_options_list

        if self.settings.port == "":
            self.settings.port = "192.168.0.10:35000;WiFi"
            self.devices_list.append(self.settings.port)

        if self.settings.port.upper().endswith("BT"):
            MAC = ""
            if ";" in self.settings.port:
                MAC = self.settings.port.split(";")[0]
            for d in self.devices_list:
                if MAC in d:
                    self.devices_list.insert(
                        0, self.devices_list.pop(self.devices_list.index(d))
                    )

            self.droid.fullSetProperty("rb_bt", "checked", "true")
            self.droid.fullSetProperty("rb_wifi", "checked", "false")
            self.droid.fullSetList("in_wifi", self.devices_list)
        else:
            self.droid.fullSetProperty("rb_bt", "checked", "false")
            self.droid.fullSetProperty("rb_wifi", "checked", "true")
            self.droid.fullSetList("in_wifi", self.devices_list)

        self.droid.fullSetProperty("in_logname", "text", self.settings.log_name)
        if self.settings.log:
            self.droid.fullSetProperty("cb_log", "checked", "true")
        else:
            self.droid.fullSetProperty("cb_log", "checked", "false")

        if self.settings.cfc:
            self.droid.fullSetProperty("cb_cfc", "checked", "true")
        else:
            self.droid.fullSetProperty("cb_cfc", "checked", "false")

        if self.settings.n1c:
            self.droid.fullSetProperty("cb_n1c", "checked", "true")
        else:
            self.droid.fullSetProperty("cb_n1c", "checked", "false")

        if self.settings.si:
            self.droid.fullSetProperty("cb_si", "checked", "true")
        else:
            self.droid.fullSetProperty("cb_si", "checked", "false")

        if self.settings.csv:
            self.droid.fullSetProperty("cb_csv", "checked", "true")
        else:
            self.droid.fullSetProperty("cb_csv", "checked", "false")

        if self.settings.dump:
            self.droid.fullSetProperty("cb_dump", "checked", "true")
        else:
            self.droid.fullSetProperty("cb_dump", "checked", "false")

        if self.settings.can2:
            self.droid.fullSetProperty("cb_can2", "checked", "true")
        else:
            self.droid.fullSetProperty("cb_can2", "checked", "false")

        self.droid.fullSetProperty("in_options", "text", self.settings.options)

    layout = """<?xml version="1.0" encoding="utf-8"?>
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

    def event_loop(self):
        while True:
            event = self.droid.eventWait(50).result
            if event is None:
                continue
            if event["name"] == "click":
                event_id = event["data"]["id"]
                if event_id == "bt_start":
                    self.cmd_start()
                elif event_id == "bt_scan":
                    self.cmd_scan()
                elif event_id == "bt_demo":
                    self.cmd_demo()
                elif event_id == "bt_check":
                    self.cmd_check()
                elif event_id == "bt_mon":
                    self.cmd_mon()
                elif event_id == "bt_term":
                    self.cmd_term()
                elif event_id == "bt_pids":
                    self.cmd_pids()
                elif event_id == "bt_update":
                    self.cmd_update()

    def __init__(self):
        self.settings = Settings()
        try:
            self.droid = android.Android()
            self.droid.fullShow(self.layout)
            self.devices_list = ["192.168.0.10:35000;WiFi"]
            try:
                bonded_devices = self.droid.bluetoothGetBondedDevices().result
                for i in range(0, len(bonded_devices), 2):
                    self.devices_list.append(
                        bonded_devices[i] + ";" + bonded_devices[i + 1]
                    )
            except Exception:
                pass
            self.load_settings()
            self.event_loop()
        finally:
            self.droid.fullDismiss()

    def __del__(self):
        self.droid.fullDismiss()


def main():
    AndroidGui()
