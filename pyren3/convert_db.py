#!/usr/bin/env python3

import glob
import zipfile
from io import BytesIO

from mod_optfile import *

if __name__ == "__main__":
    zipoutput = BytesIO()

    if len(sys.argv) < 2:
        print("Usage : convert_db.py [path/to/GenAppli]")
        exit()

    if not os.path.exists("./cache"):
        os.makedirs("./cache")

    if os.path.exists("pyrendata.zip"):
        os.remove("pyrendata.zip")

    mod_db_manager.find_DBs()

    inputpath = sys.argv[1]
    ecudir = os.path.join(inputpath, "EcuRenault")
    vehicledir = os.path.join(inputpath, "Vehicles")
    locationdir = os.path.join(inputpath, "Location")

    ecufiles = glob.glob(os.path.join(ecudir, "*.xml"))
    fbsessionfiles = glob.glob(os.path.join(ecudir, "Sessions", "FB*.xml"))
    fbsessionfiles += glob.glob(os.path.join(ecudir, "Sessions", "FG*.xml"))
    fgsessionfiles = glob.glob(os.path.join(ecudir, "Sessions", "SG*.xml"))
    vehiclesfiles = glob.glob(os.path.join(vehicledir, "*.xml"))
    dfgfiles = glob.glob(os.path.join(vehicledir, "DFG", "*.xml"))
    locationsfiles = glob.glob(os.path.join(locationdir, "*.bqm"))
    scnerariosfiles = glob.glob(os.path.join(ecudir, "Scenarios", "*.xml"))

    with zipfile.ZipFile(
        zipoutput, mode="w", compression=zipfile.ZIP_DEFLATED, allowZip64=True
    ) as zf:
        for vf in scnerariosfiles:
            print("Processing file ", vf)
            f = open(vf, "rb")
            data = f.read()
            zf.writestr(
                os.path.join("EcuRenault", "Scenarios", os.path.basename(vf)), data
            )

        for vf in vehiclesfiles:
            print("Processing file ", vf)
            f = open(vf, "rb")
            data = f.read()
            zf.writestr(os.path.join("Vehicles", os.path.basename(vf)), data)

        for vf in dfgfiles:
            print("Processing file ", vf)
            f = open(vf, "rb")
            data = f.read()
            zf.writestr(os.path.join("Vehicles", "DFG", os.path.basename(vf)), data)

        for vf in ecufiles:
            vf = vf[:-4] + vf[-4:].lower()
            print("Processing file ", vf)
            f = open(vf, "rb")
            data = f.read()
            zf.writestr(os.path.join("EcuRenault", os.path.basename(vf)), data)

        for vf in fbsessionfiles:
            vf = vf[:-4] + vf[-4:].lower()
            print("Processing file ", vf)
            f = open(vf, "rb")
            data = f.read()
            zf.writestr(
                os.path.join("EcuRenault", "Sessions", os.path.basename(vf)), data
            )

        for vf in locationsfiles:
            print("Processing file ", vf)
            try:
                while len(vf) and vf[0] in [".", "/", "\\"]:
                    vf = vf[1:]
                optf = Optfile(vf, cache=False)
            except:
                print("Skipping file ", vf)
                continue
            data = pickle.dumps(optf.dict)
            zf.writestr(
                os.path.join("Location", os.path.basename(vf).replace(".bqm", ".p")),
                data,
            )

        for vf in fgsessionfiles:
            vf = vf[:-4] + vf[-4:].lower()
            print("Processing file ", vf)
            try:
                while len(vf) and vf[0] in [".", "/", "\\"]:
                    vf = vf[1:]
                optf = Optfile(vf, cache=False)
            except:
                print("Skipping file ", vf)
                continue
            data = pickle.dumps(optf.dict)
            zf.writestr(
                os.path.join(
                    "EcuRenault",
                    "Sessions",
                    os.path.basename(vf).replace("FG", "UG").replace(".xml", ".p"),
                ),
                data,
            )

    with open("pyrendata.zip", "wb") as zf:
        zf.write(zipoutput.getvalue())
