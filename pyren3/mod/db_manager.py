import glob
import os
import re
import shutil
import zipfile

from pyren3 import config

db_dir_list = [".", ".."]
android_dir_list = ["/mnt/sdcard/pyren"]


def find_DBs():
    global db_dir_list
    global android_dir_list

    clip_found = False
    ddt_found = False

    if config.OS == "android":
        db_dir_list = db_dir_list + android_dir_list

    for clip_dir in db_dir_list:
        if (
            os.path.exists(os.path.join(clip_dir, "Vehicles"))
            and os.path.exists(os.path.join(clip_dir, "Location"))
            and os.path.exists(os.path.join(clip_dir, "EcuRenault"))
        ):
            config.CLIP_ARC = ""
            config.CLIP_ROOT = clip_dir
            clip_found = True
            break
        arh_list = sorted(
            glob.glob(os.path.join(clip_dir, "pyrendata*.zip")), reverse=True
        )

        if len(arh_list):
            config.CLIP_ARC = zipfile.ZipFile(arh_list[0])
            config.CLIP_ROOT = arh_list[0]
            clip_found = True
            break

    if config.OS == "android":
        if not clip_found:
            print("ERROR: CLIP DB not found")
            exit()
        else:
            return

    for ddt_dir in db_dir_list:
        if os.path.exists(os.path.join(ddt_dir, "DDT2000data", "ecus")):
            config.DDT_ARC = ""
            config.DDT_ROOT = os.path.join(ddt_dir, "DDT2000data")
            ddt_found = True
            break
        arh_list = sorted(
            glob.glob(os.path.join(ddt_dir, "DDT2000data*.zip")), reverse=True
        )
        if len(arh_list):
            config.DDT_ARC = zipfile.ZipFile(arh_list[0])
            config.DDT_ROOT = arh_list[0]
            ddt_found = True
            break
        if os.path.exists(os.path.join(ddt_dir, "ecus")):
            config.DDT_ARC = ""
            config.DDT_ROOT = ddt_dir
            ddt_found = True
            break

    if clip_found:
        print("CLIP DB :", config.CLIP_ROOT)
    if ddt_found:
        print("DDT  DB :", config.DDT_ROOT)
        if config.OS != "android":
            config.DDT = True

    # check cache version
    verfilename = "./cache/version3.txt"
    if not os.path.isfile(verfilename):
        # if the cache has old version then we should clear it
        for root, dirs, files in os.walk("./cache"):
            for sfile in files:
                if (
                    sfile.startswith("ver")
                    or sfile.startswith("FG")
                    or sfile.startswith("ddt")
                ):
                    full_path = os.path.join("./cache", sfile)
                    os.remove(full_path)
        saveDBver(verfilename)
    else:
        verfile = open(verfilename, "rt")
        verline = verfile.readline().strip().split(":")
        if verline[0] != config.CLIP_ROOT:
            saveDBver(verfilename)
            # if the cache has old version then we should clear it
            for root, dirs, files in os.walk("./cache"):
                for sfile in files:
                    if (
                        sfile.startswith("FG")
                        or sfile.startswith("SG")
                        or sfile.startswith("DiagOnCAN")
                    ):
                        full_path = os.path.join("./cache", sfile)
                        os.remove(full_path)
        if verline[1] != config.DDT_ROOT:
            saveDBver(verfilename)
            # if the cache has old version then we should clear it
            for root, dirs, files in os.walk("./cache"):
                for sfile in files:
                    if sfile.startswith("ddt"):
                        full_path = os.path.join("./cache", sfile)
                        os.remove(full_path)

    if not clip_found and not ddt_found:
        print("ERROR: Neither CLIP nor DDT DB not found")
        exit()
    else:
        return


def saveDBver(verfilename):
    # create new version file
    verfile = open(verfilename, "w")
    verfile.write(":".join([config.CLIP_ROOT, config.DDT_ROOT]) + "\n")
    verfile.write("Do not remove me if you have v0.9.q or above.\n")
    verfile.close()


################### CLIP ###################


def get_file_list_from_clip(pattern):
    if config.CLIP_ARC == "":
        fl = glob.glob(os.path.join(config.CLIP_ROOT, pattern))
    else:
        if "*" in pattern:
            pattern = pattern.replace("*", r"\d{3}")
        file_list = config.CLIP_ARC.namelist()
        regex = re.compile(pattern)
        fl = list(filter(regex.search, file_list))
    res = []
    for i in fl:
        while len(i) and i[0] in [".", "/", "\\"]:
            i = i[1:]
        res.append(i)
    return res


def get_file_from_clip(filename):
    if (
        filename.lower().endswith("bqm")
        or "/sg" in filename.lower()
        or "\\sg" in filename.lower()
    ):
        mode = "rb"
    else:
        mode = "r"

    if config.OS == "android" or config.CLIP_ARC != "":
        mode = "r"

    if config.CLIP_ARC == "":
        # check encoding
        file = open(os.path.join(config.CLIP_ROOT, filename), "rb")
        bom = ord(file.read(1))
        if bom == 0xFF:
            encoding = "utf-16-le"
        elif bom == 0xFE:
            encoding = "utf-16-be"
        else:
            encoding = "utf-8"
        if mode == "rb":
            return open(os.path.join(config.CLIP_ROOT, filename), mode)
        else:
            return open(
                os.path.join(config.CLIP_ROOT, filename), mode, encoding=encoding
            )
    else:
        if filename.startswith("../"):
            filename = filename[3:]
        try:
            for an in config.CLIP_ARC.NameToInfo:
                if filename.lower() == an.lower():
                    filename = an
                    break
            f = config.CLIP_ARC.open(filename, mode)
            return f
        except Exception as e:
            # print(e)
            fn = filename.split("/")[-1]
            lfn = fn.lower()
            filename = filename.replace(fn, lfn)
            return config.CLIP_ARC.open(filename, mode)


def file_in_clip(pattern):
    if config.CLIP_ARC == "":
        pattern = os.path.join(config.CLIP_ROOT, pattern)
        return pattern in glob.glob(pattern)
    else:
        file_list = config.CLIP_ARC.namelist()
        for l in file_list:
            if pattern.lower() == l.lower():
                return l
        return ""


def extract_from_clip_to_cache(filename):
    if config.CLIP_ARC == "":
        print("Error in extract_from_clip_to_cache")
    else:
        source = config.CLIP_ARC.open(filename)
        target = open(os.path.join(config.CACHE_DIR, os.path.basename(filename)), "wb")
        with source, target:
            shutil.copyfileobj(source, target)


################### DDT ###################


def get_file_list_from_ddt(pattern):
    if config.DDT_ARC == "":
        return glob.glob(os.path.join(config.DDT_ROOT, pattern))
    else:
        file_list = config.DDT_ARC.namelist()
        regex = re.compile(pattern)
        return list(filter(regex.search, file_list))


def file_in_ddt(pattern):
    if config.DDT_ARC == "":
        li = glob.glob(os.path.join(config.DDT_ROOT, pattern))
    else:
        file_list = config.DDT_ARC.namelist()
        if "(" in pattern:
            pattern = pattern.replace("(", r"\(")
        if ")" in pattern:
            pattern = pattern.replace(")", r"\)")
        regex = re.compile(pattern)
        li = list(filter(regex.search, file_list))
    return len(li)


def path_in_ddt(pattern):
    if config.DDT_ARC == "":
        li = glob.glob(os.path.join(config.DDT_ROOT, pattern))
    else:
        file_list = config.DDT_ARC.namelist()
        regex = re.compile(pattern)
        li = list(filter(regex.search, file_list))
    if len(li) > 0:
        return True
    else:
        return False


def get_file_from_ddt(filename):
    if config.DDT_ARC == "":
        return open(os.path.join(config.DDT_ROOT, filename), "rb")
    else:
        return config.DDT_ARC.open(filename, "r")


def extract_from_ddt_to_cache(filename):
    targ_file = os.path.join(config.CACHE_DIR, filename)
    try:
        if config.DDT_ARC == "":
            source = open(os.path.join(config.DDT_ROOT, filename))
        else:
            source = config.DDT_ARC.open(filename)

        if not os.path.exists(os.path.dirname(targ_file)):
            os.makedirs(os.path.dirname(targ_file))

        target = open(targ_file, "wb")

        with source, target:
            shutil.copyfileobj(source, target)
        return targ_file
    except:
        return False


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    find_DBs()
