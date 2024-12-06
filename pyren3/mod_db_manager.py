#!/usr/bin/env python3
import glob
import os
import re
import shutil
import zipfile

import config

db_dir_list = [".", ".."]


def find_dbs():
    clip_found = False

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

    if clip_found:
        print("CLIP DB :", config.CLIP_ROOT)

    # check cache version
    version_file_path = "./cache/version3.txt"
    if not os.path.isfile(version_file_path):
        # if the cache has an old version, then we should clear it
        for root, dirs, files in os.walk("./cache"):
            for sfile in files:
                if sfile.startswith("ver") or sfile.startswith("FG"):
                    full_path = os.path.join("./cache", sfile)
                    os.remove(full_path)
        save_db_ver(version_file_path)
    else:
        version_file = open(version_file_path, "rt")
        version_line = version_file.readline().strip().split(":")
        if version_line[0] != config.CLIP_ROOT:
            save_db_ver(version_file_path)
            # if the cache has an old version, then we should clear it
            for root, dirs, files in os.walk("./cache"):
                for sfile in files:
                    if (
                        sfile.startswith("FG")
                        or sfile.startswith("SG")
                        or sfile.startswith("DiagOnCAN")
                    ):
                        full_path = os.path.join("./cache", sfile)
                        os.remove(full_path)

    if not clip_found:
        print("ERROR: CLIP DB not found")
        exit()


def save_db_ver(version_file_name: str) -> None:
    # create a new version file
    with open(version_file_name, "w") as version_file:
        version_file.write(":".join([config.CLIP_ROOT, ".."]) + "\n")
        version_file.write("Do not remove me if you have v0.9.q or above.\n")


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

    if config.CLIP_ARC != "":
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


if __name__ == "__main__":
    find_dbs()
