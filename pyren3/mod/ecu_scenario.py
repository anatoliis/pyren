import os
import re

from mod import config, db_manager


def playScenario(command, ecu, elm):
    services = ecu.Services

    path = "EcuRenault/Scenarios/"
    scenarioName, scenarioData = command.scenario.split("#")

    scenarioData = scenarioData[:-4] + ".xml"

    showable = False
    if scenarioName.lower().startswith("scm"):
        showable = True

    if showable:
        ecuNumberPattern = re.compile(r"\d{5}")
        ecuNumberIndex = ecuNumberPattern.search(scenarioData)
        if ecuNumberIndex:
            scenarioName = scenarioData[
                : scenarioData.find(ecuNumberIndex.group(0)) - 1
            ].lower()

    if os.path.isfile("./" + scenarioName + ".py"):
        scen = __import__(scenarioName)
        if config.clip_arc:
            scen.run(elm, ecu, command, "../" + path + scenarioData)
        else:
            scen.run(elm, ecu, command, "./" + path + scenarioData)
        return

    print("\nThere is scenarium. I do not support them!!!\n")
    if showable:
        ch = input("Press ENTER to exit or type [SHOW]: ")
    else:
        ch = input("Press ENTER to exit")

    if "show" not in ch.lower():
        return

    if not db_manager.file_in_clip(os.path.join(path, scenarioData)):
        return

    scenFile = db_manager.get_file_from_clip(os.path.join(path, scenarioData)).read()
    if isinstance(scenFile, (bytes, bytearray)):
        scenFile = scenFile.decode("utf-8", errors="ignore")
    lines = scenFile.split("\n")

    for l in lines:
        l = l.rstrip("\r")
        pa = re.compile(r"name=\"(\w+)\"\s+value=\"(\w+)\"")
        ma = pa.search(l)
        if ma:
            p_name = ma.group(1)
            p_value = ma.group(2)

            if p_value.isdigit() and p_value in list(config.language_dict.keys()):
                p_value = config.language_dict[p_value]

            print("  %-20s : %s" % (p_name, p_value))

        else:
            print(l)

    ch = input("Press ENTER to exit")

    return
