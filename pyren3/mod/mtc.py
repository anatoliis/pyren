import csv
import os
import shutil
import zipfile

from pyren3.mod import config
from pyren3.mod.utils import Choice


def acf_saveMTCtoFile(folder, vindata, mtcdata, refdata, platform):
    f = open(folder + "/vindata.txt", "wt")
    f.write(str(vindata))
    f.close()

    f = open(folder + "/refdata.txt", "wt")
    f.write(str(refdata))
    f.close()

    f = open(folder + "/platform.txt", "wt")
    f.write(str(platform))
    f.close()

    f = open(folder + "/mtcdata.txt", "wt")
    f.write("\n".join(sorted(mtcdata.split(";"))))
    f.close()

    SEFname = "savedEcus.p"
    if config.opt_can2:
        SEFname = "savedEcus2.p"

    if os.path.exists("./" + SEFname):
        shutil.copyfile("./" + SEFname, folder + "/" + SEFname)

    return


def acf_loadMTCfromFile(folder):
    f = open(folder + "/vindata.txt", "rt")
    vindata = f.read()
    f.close()

    f = open(folder + "/refdata.txt", "rt")
    refdata = f.read()
    f.close()

    f = open(folder + "/platform.txt", "rt")
    platform = f.read()
    f.close()

    f = open(folder + "/mtcdata.txt", "rt")
    tmp = f.read()
    f.close()
    mtcdata = ";".join(sorted(tmp.split("\n")))

    return vindata, mtcdata, refdata, platform


def acf_buildFull(platf):
    """compile all VINs in one file"""

    plDIR = "../BVMEXTRACTION/" + platf.upper()

    if not os.path.exists(plDIR):
        print("ERROR: Can't find the BVMEXTRACTION db")
        return

    mtc = {}
    mtc_name = "MTC.dat"
    for fn in os.listdir(plDIR):
        if fn.upper() == "MTC.DAT":
            mtc_name = fn
    mtcf = open(plDIR + "/" + mtc_name, "rt")
    mtc_list = csv.reader(mtcf, delimiter=";")
    for i in mtc_list:
        if i:
            mtc[int(i[0][:-4])] = i[1:]

    ref = {}
    ref_name = "REF.dat"
    for fn in os.listdir(plDIR):
        if fn.upper() == "REF.DAT":
            ref_name = fn
    if os.path.exists(plDIR + "/" + ref_name):
        reff = open(plDIR + "/" + ref_name, "rt")
        ref_list = csv.reader(reff, delimiter=";")
        for i in ref_list:
            if i:
                for item in range(len(i)):
                    i[item] = "".join(
                        [c if ord(c) < 128 else "X" for c in i[item]]
                    ).replace("XXX", "X")
                ref[int(i[0][:10])] = [i[0][11:]] + i[1:]

    all_vin = open(plDIR + "/all_vin.csv", "w")

    for root, dirs, files in os.walk(plDIR):
        for dir in dirs:
            if len(dir) != 3:
                continue
            VIN1 = dir
            cdir = os.path.join(plDIR, dir)
            print(cdir)
            for root, dirs, files in os.walk(cdir):
                for file in files:
                    zfname = file.split(".")[0]
                    if len(zfname) == 6:
                        if not file.lower().endswith(".dat"):
                            continue
                        zip = zipfile.ZipFile(os.path.join(root, file))
                        flist = zip.namelist()
                        for i in flist:
                            VIN2 = i.split(".")[0]
                            print("   " + VIN2)
                            zf = zip.open(i)
                            vin3list = zf.read().decode("utf-8")
                            zf.close()
                            for l in vin3list.split("\n"):
                                l = l.strip()
                                if len(l) == 0:
                                    continue
                                vr = l.split(";")
                                VIN = VIN1 + VIN2 + vr[0]
                                try:
                                    d = vr[4].split(":")[1].split(".")
                                    data = d[2] + d[1] + d[0]
                                except:
                                    pass
                                outl = (
                                    data
                                    + "#"
                                    + VIN
                                    + "#"
                                    + " ".join(vr[1:])
                                    + "#"
                                    + " ".join(mtc[int(vr[1])])
                                )
                                if vr[2] != "" and int(vr[2]) in ref.keys():
                                    outl += "#" + "_".join(ref[int(vr[2])])
                                all_vin.write(outl + "\n")
    all_vin.close()
    print("\n\n File: " + plDIR + "/all_vin.csv is build\n\n")


def acf_getMTC(VIN, preferFile=False):
    """getting MTC data from BVMEXTRACTION"""

    VIN1 = VIN[:3]
    VIN2 = VIN[3:9]
    VIN3 = VIN[9:]

    vindata = ""
    mtcdata = ""
    refdata = ""
    platform = ""
    vindir = ""

    # check and prepare folder for loading or saving data
    mtc_dir = "../MTCSAVE/" + VIN
    config.mtcdir = mtc_dir
    if not os.path.exists(mtc_dir):
        os.makedirs(mtc_dir)
    if not os.path.exists(mtc_dir + "/dumps"):
        os.makedirs(mtc_dir + "/dumps")
    if not os.path.exists(mtc_dir + "/scripts"):
        os.makedirs(mtc_dir + "/scripts")

    if os.path.exists(mtc_dir + "/mtcdata.txt"):
        if preferFile:
            vindata, mtcdata, refdata, platform = acf_loadMTCfromFile(mtc_dir)
            return vindata, mtcdata, refdata, platform
        print("\n" + "#" * 35)
        choice = Choice(["File", "DataBase"], "From where read MTC : ")
        print("\n" + "#" * 35)
        if choice[1] == "1":
            print("Loading data from file")
            vindata, mtcdata, refdata, platform = acf_loadMTCfromFile(mtc_dir)
            return vindata, mtcdata, refdata, platform

    print("Loading data from database")

    for root, dirs, files in os.walk("../BVMEXTRACTION"):
        for dir in dirs:
            if dir.upper() != VIN1:
                continue
            cdir = os.path.join(root, dir)
            # print cdir
            for root, dirs, files in os.walk(cdir):
                for file in files:
                    zfname = file.split(".")[0]
                    if len(zfname) == 6 and VIN2 >= zfname:
                        if not file.lower().endswith(".dat"):
                            continue
                        zip = zipfile.ZipFile(os.path.join(root, file))
                        flist = zip.namelist()
                        for i in flist:
                            if VIN2 in i:
                                # print '\t\t', i
                                zf = zip.open(i)
                                vin3list = zf.read()
                                zf.close()
                                for l in vin3list.split(b"\n"):
                                    if l.startswith(VIN3.encode("utf-8")):
                                        vindata = l
                                        break
                        if vindata != "":
                            break
                    if vindata != "":
                        break
                if vindata != "":
                    break
            if vindata != "":
                vindir = cdir
                break
        if vindata != "":
            break

    if type(vindata) == bytes:
        vindata = vindata.decode("utf-8")

    if vindata == "" or vindir == "":
        print("\n\nVIN has not found in databse\n\n")
        exit()
    vindir = vindir[:-3]
    platform = vindir[-4:-1]

    mtcdata = ""
    refdata = ""

    # check if there is an mtc file

    mtc_name = "MTC.dat"
    for fn in os.listdir(vindir):
        if fn.upper() == "MTC.DAT":
            mtc_name = fn
    mz = open(vindir + mtc_name, "r")
    mtclist = mz.read().split("\n")
    mz.close()
    for l in mtclist:
        if l.startswith(vindata.split(";")[1]):
            mtcdata = l

    try:
        ref_name = "REF.dat"
        for fn in os.listdir(vindir):
            if fn.upper() == "REF.DAT":
                ref_name = fn
        rz = open(vindir + ref_name, "r")
        reflist = rz.read().split("\n")
        rz.close()
        for l in reflist:
            if l.startswith(vindata.split(";")[2]):
                refdata = l
    except:
        print("\n\nREF.dat is absent!!!\n\n")

    mtcdata = mtcdata[len(vindata.split(";")[1]) + 1 :].strip()
    if mtcdata.endswith("."):
        mtcdata = mtcdata[:-1]
    refdata = refdata[len(vindata.split(";")[2]) + 1 :].strip()
    if refdata.endswith(";"):
        refdata = refdata[:-1]

    # saving data to files
    # print "Saving data from DB to "+mtc_dir
    acf_saveMTCtoFile(mtc_dir, vindata, mtcdata, refdata, platform)
    return vindata, mtcdata, refdata, platform


def acf_MTC_finde(mtc_tag, mtc):
    sauf = False
    result = False

    mtc_tag = mtc_tag.strip()

    if mtc_tag.startswith("SAUF"):
        sauf = True
        mtc_tag = mtc_tag[4:].strip()

    if mtc_tag in mtc:
        # if mtc_tag==mtc:
        result = True

    # print "finde:", mtc_tag, sauf, result

    if sauf:
        return not result
    else:
        return result


def acf_MTC_and(expr, mtc):
    """expr - expression with AND rules"""
    """ mtc - list of options           """
    """ and-operand in MTC expression """

    result = True

    and_list = expr.split("/")
    and_list = [x.strip() for x in and_list]

    for ande in and_list:
        interm_res = acf_MTC_finde(ande, mtc)
        result = result and interm_res

    return result


def acf_MTC_or(expr, mtc):
    """expr - expression with AND rules"""
    """ mtc - list of options           """
    """ and-operand in MTC expression """

    result = False

    or_list = expr.split(",")
    or_list = [x.strip() for x in or_list]

    for ore in or_list:
        interm_res = acf_MTC_finde(ore, mtc)
        result = result or interm_res

        if result:
            return result

    return result


def acf_MTC_compare(expr, mtc):
    """expr - expression with rules"""
    """ mtc - list of options       """
    """ this function match MTC-tag with MTC-expression"""

    result = True

    and_list = expr.split("/")
    and_list = [x.strip() for x in and_list]

    for ande in and_list:
        if "," in ande:
            interm_res = acf_MTC_or(ande, mtc)
        else:
            interm_res = acf_MTC_finde(ande, mtc)
        result = result and interm_res

    return result


def acf_MTC_compare_old(expr, mtc):
    """expr - expression with rules"""
    """ mtc - list of options       """
    """ this function match MTC-tag with MTC-expression"""

    result = False

    or_list = expr.split(",")
    or_list = [x.strip() for x in or_list]

    for ore in or_list:
        if "/" in ore:
            interm_res = acf_MTC_and(ore, mtc)
        else:
            interm_res = acf_MTC_finde(ore, mtc)
        result = result or interm_res

        if result:
            return result

    return result


def acf_MTC_compare_doc(sieconfigid, mtc):
    for sc in sieconfigid.split(" "):
        if acf_MTC_compare(sc, mtc):
            return True
    return False
