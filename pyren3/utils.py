import os
import shutil

from serial.tools import list_ports

from pyren3 import config


def update_from_gitlab():
    try:
        import os
        import zipfile
        import urllib.request, urllib.error, urllib.parse
        import ssl

        try:
            _create_unverified_https_context = ssl._create_unverified_context
        except AttributeError:
            # Legacy Python that doesn't verify HTTPS certificates by default
            pass
        else:
            # Handle target environment that doesn't support HTTPS verification
            ssl._create_default_https_context = _create_unverified_https_context

        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        h_user_agent = {
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.3"
        }
        req = urllib.request.Request(
            "https://gitlab.com/py_ren/pyren/-/archive/pyren3/pyren-pyren3.zip",
            headers=h_user_agent,
        )
        filedata = urllib.request.urlopen(req, context=ctx, timeout=10)
        datatowrite = filedata.read()

        with open("./pyren-pyren3.zip", "wb") as f:
            f.write(datatowrite)
    except Exception:
        return 1

    try:
        if os.path.isfile("./pyren-pyren3.zip"):
            with zipfile.ZipFile("./pyren-pyren3.zip") as zip_file:
                for src in zip_file.namelist():
                    if src.endswith("exe"):
                        continue
                    arcname = src.replace("/", os.path.sep)
                    if os.path.altsep:
                        arcname = arcname.replace(os.path.altsep, os.path.sep)
                    arcname = os.path.splitdrive(arcname)[1].split(os.path.sep)[0]
                    rootDirLen = len(arcname) + 1
                    dst = src[rootDirLen:]
                    filename = os.path.basename(src)
                    if not filename:
                        if dst and not os.path.exists(dst):
                            os.makedirs(dst)
                        continue

                    source = zip_file.open(src)
                    target = open(dst, "wb")
                    with source, target:
                        shutil.copyfileobj(source, target)
    except Exception:
        os.remove("./pyren-pyren3.zip")
        return 2

    os.remove("./pyren-pyren3.zip")

    return 0


def getPathList():
    return [
        "./" + f
        for f in os.listdir(".")
        if os.path.isdir("./" + f)
        and f.lower().startswith("pyren")
        and os.path.isfile("./" + f + "/pyren3.py")
    ]


def getLangList():
    return [
        "AL",
        "CNT",
        "CO",
        "CR",
        "CZ",
        "DK",
        "EL",
        "FI",
        "FR",
        "GB",
        "HG",
        "IT",
        "JP",
        "NG",
        "NL",
        "PL",
        "PO",
        "RO",
        "RU",
        "SD",
        "SL",
        "SP",
        "TR",
    ]


def getPortList():
    ret = []
    if config.OS == "android":
        if config.JNIUS_MODE:
            from jnius import autoclass

            BluetoothAdapter = autoclass("android.bluetooth.BluetoothAdapter")

            try:
                paired_devices = (
                    BluetoothAdapter.getDefaultAdapter().getBondedDevices().toArray()
                )
                for device in paired_devices:
                    desc = device.getName()
                    de = str(desc.encode("ascii", "ignore"))
                    ret.append("BT;" + de)
            except Exception:
                ret.append("BT;")
            return ret

        iterator = sorted(list(list_ports.comports()))
        for port, desc, hwid in iterator:
            try:
                de = str(desc.encode("ascii", "ignore"))
                ret.append(port + ";" + de)
            except Exception:
                ret.append(port + ";")
        if "192.168.0.10:35000;WiFi" not in ret:
            ret.append("192.168.0.10:35000;WiFi")
    else:
        ret = ["BT", "192.168.0.10:35000"]
    return ret
