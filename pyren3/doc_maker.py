#!/usr/bin/env python3
import argparse
import copy
import os
import sys
import xml.etree.ElementTree as et

import config
from mod_db_manager import find_dbs
from mod_dfg import ClassDfg
from mod_elm import ELM
from mod_mtc import acf_MTC_compare_doc, acf_buildFull, acf_get_mtc
from mod_optfile import optfile
from mod_scan_ecus import ScanEcus
from mod_utils import chk_dir_tree, get_vin

style = """
div.zdiagnostic {
	background-color	:	white;
}

div.testgrp {
	border-style		: 	outset;
}

div.test1 {
	color				:	Black;
}

div.caution {
	border-style		: 	solid;
	border-color		: 	red;
	color				:	red;
}

div.warning {
	border-style		: 	solid;
	border-color		: 	red;
	color				:	red;
}

div.note {
	border-style		: 	solid;
	border-color		: 	blue;
	color				:	blue;
}

div.action {
	padding-left		:	100px;
	padding-right		:	100px;
	margin-left			:	100px;
	margin-right		:	100px;
	background-color	:	White;
	border-style		: 	solid;
}

h6.ref {
	text-align			:	right;
}

h4.result {
	padding-left		:	50px;
}

p.RN {
	color				: 	Blue;
}

table.table {
    border				: 	1px solid black;
}

th.row_h {
    border				: 	1px solid black;
    background-color	:	LightGray;
}

td.row_d {
    border				: 	1px solid black;
}

"""

# global variables

table_header = False
dfg_ds = {}


def get_ref(ff, pref):
    notfound = True
    for l in ff:
        if l.startswith(pref):
            notfound = False
            break
    if notfound:
        return pref
    return l[:-4]


def getTitleAndRef(path, ff, root, title, l, rc=0):

    if rc > 3:
        print(l)
        return root, title

    title_el = root.find("title")
    ref = title_el.find("xref")
    pref = ref.attrib["sie-id"]

    notfound = True
    for l in ff:
        if l.startswith(pref):
            tree = et.parse(path + l)
            root = tree.getroot()
            notfound = False
            break
    if notfound:  # then will try without mtc filter
        lf = os.listdir(path)
        for l in lf:
            if l.startswith(pref):
                tree = et.parse(path + l)
                root = tree.getroot()
                break
        return root, title
    title_el = root.find("title")
    title = title_el.text.strip()

    if title == "":
        root, title = getTitleAndRef(path, ff, root, title, l, rc + 1)
    return root, title


def convert_xml(root, h_t, fns, ff, lid):
    global table_header

    for e in root.iter():
        if root.tag != "servinfo" and root.tag == e.tag:
            continue

        if "v" in list(e.attrib.keys()):
            continue

        e.set("v", 1)

        if e.tag == "servinfo":
            et.SubElement(h_t, "h6", attrib={"class": "ref"}).text = e.attrib["id"]
            et.SubElement(h_t, "h6", attrib={"class": "ref"}).text = e.attrib[
                "sieconfigid"
            ]

        elif e.tag == "title" and e.text:
            if fns[4] != "000000":
                title = "DTC" + fns[4] + " " + e.text
                fns[4] = "000000"
            else:
                title = e.text
            et.SubElement(h_t, "h2", attrib={"class": "title"}).text = title

        elif e.tag == "result":
            et.SubElement(h_t, "h4", attrib={"class": "result"}).text = e.text

        elif e.tag == "question":
            et.SubElement(h_t, "h4", attrib={"class": "question"}).text = e.text

        elif e.tag == "xref":
            et.SubElement(h_t, "br")
            et.SubElement(
                h_t,
                "a",
                attrib={"class": "xref", "href": "#" + get_ref(ff, e.attrib["sie-id"])},
            ).text = e.attrib["ref"]

        elif e.tag == "intxref":
            et.SubElement(
                h_t,
                "a",
                attrib={"class": "intxref", "href": "#" + lid + e.attrib["refid"]},
            ).text = ">>>>>>>"

        elif e.tag == "RN-END-PROCEDURE":
            et.SubElement(h_t, "a", attrib={"href": "#home"}).text = "Up"

        elif e.tag == "RN-CLIP-DISPLAY-DEFAULTS":
            et.SubElement(h_t, "p", attrib={"class": "RN"}).text = (
                "RN-CLIP-DISPLAY-DEFAULTS " + e.attrib["DOMAIN-DESC"]
            )

        elif e.tag == "RN-CLIP-ERASE-ALL-DEFAULTS":
            et.SubElement(h_t, "p", attrib={"class": "RN"}).text = (
                "RN-CLIP-ERASE-ALL-DEFAULTS " + e.attrib["DOMAIN-DESC"]
            )

        elif e.tag == "RN-CLIP-DISPLAY":
            et.SubElement(h_t, "p", attrib={"class": "RN"}).text = (
                "RN-CLIP-DISPLAY Domain:("
                + e.attrib["DOMAIN-DESC"]
                + ") "
                + e.attrib["STATE-OR-PARAMETER-CODE"]
                + "-"
                + e.attrib["STATE-OR-PARAMETER-NAME"]
            )

        elif e.tag == "RN-RDC-ACCESS":
            if "RDC-ELEMENT-REF" in list(
                e.attrib.keys()
            ) and "RDC-ELEMENT-DESC" in list(e.attrib.keys()):
                et.SubElement(h_t, "p", attrib={"class": "RN"}).text = (
                    "RN-RDC-ACCESS RDC-ELEMENT-REF:"
                    + e.attrib["RDC-ELEMENT-REF"]
                    + " RDC-ELEMENT-DESC:"
                    + e.attrib["RDC-ELEMENT-DESC"]
                )
            else:
                et.SubElement(h_t, "p", attrib={"class": "RN"}).text = "RN-RDC-ACCESS "

        elif e.tag == "RN-CLIP-LAUNCH-ACTUATOR":
            et.SubElement(h_t, "p", attrib={"class": "RN"}).text = (
                "RN-CLIP-LAUNCH-ACTUATOR Domain:("
                + e.attrib["DOMAIN-DESC"]
                + ") "
                + e.attrib["ACTUATOR-CODE"]
                + "-"
                + e.attrib["ACTUATOR-DESC"]
            )

        elif e.tag == "RN-NTSE-ACCESS":
            et.SubElement(h_t, "p", attrib={"class": "RN"}).text = "RN-NTSE-ACCESS"
            et.SubElement(h_t, "p", attrib={"class": "RN"}).text = (
                "WIRING-DIAGRAM-TYPE:" + e.attrib["WIRING-DIAGRAM-TYPE"]
            )
            et.SubElement(h_t, "p", attrib={"class": "RN"}).text = (
                "PRIMARY-WIRING-DIAGRAM-REF:" + e.attrib["PRIMARY-WIRING-DIAGRAM-REF"]
            )
            et.SubElement(h_t, "p", attrib={"class": "RN"}).text = (
                "PRIMARY-WIRING-DIAGRAM-DESC:" + e.attrib["PRIMARY-WIRING-DIAGRAM-DESC"]
            )
            if "SIGNAL-CODE-REF" in list(
                e.attrib.keys()
            ) and "SIGNAL-CODE-DESC" in list(e.attrib.keys()):
                et.SubElement(h_t, "p", attrib={"class": "RN"}).text = (
                    "SIGNAL-CODE-REF:" + e.attrib["SIGNAL-CODE-REF"]
                )
                et.SubElement(h_t, "p", attrib={"class": "RN"}).text = (
                    "SIGNAL-CODE-DESC:" + e.attrib["SIGNAL-CODE-DESC"]
                )

        elif e.tag == "list1":
            ni = et.SubElement(h_t, "ul", attrib={"class": "list1"})
            convert_xml(e, ni, fns, ff, lid)

        elif e.tag == "list1-A":
            ni = et.SubElement(h_t, "ul", attrib={"class": "list1-A"})
            convert_xml(e, ni, fns, ff, lid)

        elif e.tag == "list1-B":
            ni = et.SubElement(h_t, "ul", attrib={"class": "list1-B"})
            convert_xml(e, ni, fns, ff, lid)

        elif e.tag == "list1-D":
            ni = et.SubElement(h_t, "ul", attrib={"class": "list1-D"})
            convert_xml(e, ni, fns, ff, lid)

        elif e.tag == "list2":
            ni = et.SubElement(h_t, "ul", attrib={"class": "list2"})
            convert_xml(e, ni, fns, ff, lid)

        elif e.tag == "list2-A":
            ni = et.SubElement(h_t, "ul", attrib={"class": "list1-A"})
            convert_xml(e, ni, fns, ff, lid)

        elif e.tag == "list2-B":
            ni = et.SubElement(h_t, "ul", attrib={"class": "list2-B"})
            convert_xml(e, ni, fns, ff, lid)

        elif e.tag == "list2-D":
            ni = et.SubElement(h_t, "ul", attrib={"class": "list2-D"})
            convert_xml(e, ni, fns, ff, lid)

        elif e.tag == "list3":
            ni = et.SubElement(h_t, "ul", attrib={"class": "list3"})
            convert_xml(e, ni, fns, ff, lid)

        elif e.tag == "list3-A":
            ni = et.SubElement(h_t, "ul", attrib={"class": "list3-A"})
            convert_xml(e, ni, fns, ff, lid)

        elif e.tag == "list3-B":
            ni = et.SubElement(h_t, "ul", attrib={"class": "list3-B"})
            convert_xml(e, ni, fns, ff, lid)

        elif e.tag == "list3-D":
            ni = et.SubElement(h_t, "ul", attrib={"class": "list3-D"})
            convert_xml(e, ni, fns, ff, lid)

        elif e.tag == "item":
            ni = et.SubElement(h_t, "li", attrib={"class": "item"})
            convert_xml(e, ni, fns, ff, lid)

        elif e.tag == "item-A":
            ni = et.SubElement(h_t, "li", attrib={"class": "item-A"})
            convert_xml(e, ni, fns, ff, lid)

        elif e.tag == "item-B":
            ni = et.SubElement(h_t, "li", attrib={"class": "item-B"})
            convert_xml(e, ni, fns, ff, lid)

        elif e.tag == "item-D":
            ni = et.SubElement(h_t, "li", attrib={"class": "item-D"})
            convert_xml(e, ni, fns, ff, lid)

        elif e.tag == "ptxt":
            ni = et.SubElement(h_t, "p", attrib={"class": "ptxt"})
            ni.text = e.text
            convert_xml(e, ni, fns, ff, lid)

        elif e.tag == "zdiagnostic":
            ni = et.SubElement(
                h_t, "div", attrib={"class": "zdiagnostic", "id": lid + e.attrib["id"]}
            )
            convert_xml(e, ni, fns, ff, lid)

        elif e.tag == "testgrp":
            ni = et.SubElement(
                h_t, "div", attrib={"class": "testgrp", "id": lid + e.attrib["id"]}
            )
            convert_xml(e, ni, fns, ff, lid)

        elif e.tag == "topic":
            ni = et.SubElement(
                h_t, "div", attrib={"class": "topic", "id": lid + e.attrib["id"]}
            )
            convert_xml(e, ni, fns, ff, lid)

        elif e.tag == "servinfosub":
            ni = et.SubElement(
                h_t, "div", attrib={"class": "servinfosub", "id": lid + e.attrib["id"]}
            )
            convert_xml(e, ni, fns, ff, lid)

        elif e.tag == "caution":
            ni = et.SubElement(h_t, "div", attrib={"class": "caution"})
            et.SubElement(ni, "p", attrib={"class": "ptxt"}).text = "Caution!!!"
            convert_xml(e, ni, fns, ff, lid)

        elif e.tag == "warning":
            ni = et.SubElement(h_t, "div", attrib={"class": "warning"})
            et.SubElement(ni, "p", attrib={"class": "ptxt"}).text = "Warning!!!"
            convert_xml(e, ni, fns, ff, lid)

        elif e.tag == "note":
            ni = et.SubElement(h_t, "div", attrib={"class": "note"})
            et.SubElement(ni, "p", attrib={"class": "ptxt"}).text = "Note!!!"
            convert_xml(e, ni, fns, ff, lid)

        elif e.tag == "test1":
            ni = et.SubElement(h_t, "div", attrib={"class": "test1"})
            convert_xml(e, ni, fns, ff, lid)

        elif e.tag == "action":
            ni = et.SubElement(h_t, "div", attrib={"class": "action"})
            convert_xml(e, ni, fns, ff, lid)

        elif e.tag == "table":
            ni = et.SubElement(h_t, "table", attrib={"class": "table"})
            convert_xml(e, ni, fns, ff, lid)

        elif e.tag == "thead":
            table_header = True
            convert_xml(e, h_t, fns, ff, lid)
            table_header = False

        elif e.tag == "row":
            ni = et.SubElement(h_t, "tr", attrib={"class": "row"})
            convert_xml(e, ni, fns, ff, lid)

        elif e.tag == "entry":
            if table_header:
                ni = et.SubElement(h_t, "th", attrib={"class": "row_h"})
            else:
                ni = et.SubElement(h_t, "td", attrib={"class": "row_d"})
            convert_xml(e, ni, fns, ff, lid)


def save_to_separate_file(nel, dtc):

    t_doc = et.Element("html")
    t_h_h = et.SubElement(t_doc, "head")
    t_h_b = et.SubElement(t_doc, "body")

    et.SubElement(t_h_h, "meta", charset="utf-8")
    et.SubElement(t_h_h, "style").text = style

    t_h_b.append(nel)

    tree = et.ElementTree(t_doc)
    tree.write(
        "./doc/" + dtc + ".htm",
        encoding="UTF-8",
        xml_declaration=True,
        default_namespace=None,
        method="html",
    )


def process_xml(path, l, ff):
    tree = et.parse(path + l)
    root = tree.getroot()

    try:
        title = root.find("title").text.strip()
    except Exception:
        title = ""

    if title == "":  # check id documents refers to another
        try:
            root, title = getTitleAndRef(path, ff, root, title, l)
        except Exception:
            pass

    lid = l[:-4]

    # process document
    fns = lid.split("_")

    if fns[4] != "000000":
        title = "DTC" + fns[4] + " " + title

    dtc_id = ""
    if fns[4] != "000000" and fns[5] == "104":
        dtc_id = fns[4]

    dtc_id_106 = ""
    if fns[4] != "000000" and fns[5] == "106":
        dtc_id_106 = fns[4]

    nel = et.Element("div")
    et.SubElement(nel, "hr", attrib={"id": lid})

    if dtc_id != "":
        et.SubElement(nel, "a", attrib={"href": "#home", "id": dtc_id}).text = "Up"
    else:
        et.SubElement(nel, "a", attrib={"href": "#home"}).text = "Up"

    convert_xml(root, nel, fns, ff, lid)

    if dtc_id_106 != "" and config.OPT_SD:
        save_to_separate_file(nel, dtc_id_106)

    return nel, lid, title


def f_symptom(dfg_fet, ff, of, pref, fetname, path):

    global dfg_ds

    fet_o = et.Element("div", attrib={"id": pref})
    et.SubElement(fet_o, "hr")
    et.SubElement(fet_o, "h1").text = fetname

    fet_t = et.Element("div")  # text

    for s in dfg_fet["symptomId"]:
        for l in ff:
            if l.startswith(s):
                nel, lid, title = process_xml(path, l, ff)
                if l in of:
                    of.remove(l)
                    fet_t.append(nel)
                cop = et.SubElement(fet_o, "p")
                et.SubElement(cop, "a", href="#" + lid).text = title

    et.SubElement(fet_o, "hr")
    fet_o.append(fet_t)
    et.SubElement(fet_o, "hr")
    return fet_o


def f_features(dfg_fun, ff, of, pref, funname, path):

    fun_o = et.Element("div", attrib={"id": pref})
    et.SubElement(fun_o, "hr")
    et.SubElement(fun_o, "h1").text = funname

    fun_t = et.Element("div")  # text

    for ek in list(dfg_fun["feature"].keys()):
        if dfg_fun["feature"][ek]["codetext"] in list(config.LANGUAGE_DICT.keys()):
            fetname = config.LANGUAGE_DICT[dfg_fun["feature"][ek]["codetext"]]
        else:
            fetname = dfg_fun["feature"][ek]["codetext"]
        pref = dfg_fun["feature"][ek]["id_ppc"]

        fet_text = f_symptom(dfg_fun["feature"][ek], ff, of, pref, fetname, path)

        cop = et.SubElement(fun_o, "p")
        et.SubElement(cop, "a", href="#" + pref).text = fetname
        fun_t.append(fet_text)

    et.SubElement(fun_o, "hr")
    fun_o.append(fun_t)
    et.SubElement(fun_o, "hr")
    return fun_o


def f_functions(dfg_dom, ff, of, pref, domname, path):

    dom_o = et.Element("div", attrib={"id": pref})
    et.SubElement(dom_o, "hr")
    et.SubElement(dom_o, "h1").text = domname

    dom_t = et.Element("div")  # text

    # collect DTC
    dom_dtc_o = et.Element("div", attrib={"id": pref + "_dtc"})
    for l in ff:
        if l.startswith(pref):
            fns = l.split("_")
            if fns[4] != "000000":
                nel, lid, title = process_xml(path, l, ff)
                of.remove(l)
                cop = et.SubElement(dom_dtc_o, "p")
                et.SubElement(cop, "a", href="#" + lid).text = title
                dom_t.append(nel)

    cop = et.SubElement(dom_o, "p")
    et.SubElement(cop, "a", href="#" + pref + "_dtc").text = "DTC"

    # collect Parameters
    dom_par_o = et.Element("div", attrib={"id": pref + "_par"})
    for l in ff:
        if l.startswith(pref):
            fns = l.split("_")
            if fns[5] == "102":
                nel, lid, title = process_xml(path, l, ff)
                of.remove(l)
                cop = et.SubElement(dom_par_o, "p")
                et.SubElement(cop, "a", href="#" + lid).text = title
                dom_t.append(nel)

    cop = et.SubElement(dom_o, "p")
    et.SubElement(cop, "a", href="#" + pref + "_par").text = "Parameters"

    for fk in list(dfg_dom["function"].keys()):
        if dfg_dom["function"][fk]["codetext"] in list(config.LANGUAGE_DICT.keys()):
            funname = config.LANGUAGE_DICT[dfg_dom["function"][fk]["codetext"]]
        else:
            funname = dfg_dom["function"][fk]["codetext"]
        pref = dfg_dom["function"][fk]["id_ppc"]

        fun_text = f_features(dfg_dom["function"][fk], ff, of, pref, funname, path)

        cop = et.SubElement(dom_o, "p")
        et.SubElement(cop, "a", href="#" + pref).text = funname
        dom_t.append(fun_text)

    et.SubElement(dom_o, "hr")
    dom_o.append(dom_dtc_o)
    et.SubElement(dom_o, "hr")
    dom_o.append(dom_par_o)
    et.SubElement(dom_o, "hr")
    dom_o.append(dom_t)
    et.SubElement(dom_o, "hr")
    return dom_o


def generate_html(path, mtc, vin, dfg, date_madc):

    global style

    try:
        lf = os.listdir(path)
    except Exception:
        print("ERROR: path not found: ", path)
        exit()

    doc = et.Element("html")
    h_h = et.SubElement(doc, "head")
    h_b = et.SubElement(doc, "body")
    h_o = et.SubElement(h_b, "div", attrib={"id": "home"})  # bookmarks
    h_t = et.SubElement(h_b, "div")  # text

    et.SubElement(h_h, "meta", charset="utf-8")
    et.SubElement(h_h, "style").text = style

    et.SubElement(h_o, "hr")
    et.SubElement(h_o, "h4", attrib={"align": "right"}).text = "pyren"
    et.SubElement(h_o, "h1", attrib={"align": "center"}).text = dfg.defaultText
    et.SubElement(h_o, "h1", attrib={"align": "center"}).text = "VIN : " + vin
    et.SubElement(h_o, "h1", attrib={"align": "center"}).text = date_madc
    et.SubElement(h_o, "h4").text = "MTC : " + " ".join(mtc)
    et.SubElement(h_o, "hr")

    i = 0
    print("\nPass 1:")
    ff = []
    for l in sorted(lf):
        print("\r\tDone:" + str(1 + int(i * 100.0 / len(lf))) + "%", end=" ")
        sys.stdout.flush()
        i = i + 1

        try:
            tree = et.parse(path + l)
            root = tree.getroot()
            sieconfigid = root.attrib["sieconfigid"]
            ma = acf_MTC_compare_doc(sieconfigid, mtc)
            if ma:  # document complines to MTC filter
                ff.append(l)
        except:
            print("Error in file:", path + l)

    ilen = len(ff)
    of = copy.deepcopy(ff)

    print("\nPass 2:")

    for dk in list(dfg.domain.keys()):
        print(
            "\r\tDone:" + str(int((ilen - len(of)) * 100.0 / ilen)) + "%" + " " * 10,
            end=" ",
        )
        sys.stdout.flush()

        if dfg.domain[dk]["codetext"] in list(config.LANGUAGE_DICT.keys()):
            domname = config.LANGUAGE_DICT[dfg.domain[dk]["codetext"]]
        else:
            domname = dfg.domain[dk]["defaultText"]
        pref = dfg.domain[dk]["id_ppc"]

        dom_text = f_functions(dfg.domain[dk], ff, of, pref, domname, path)

        h_t.append(dom_text)
        cop = et.SubElement(h_o, "p")
        et.SubElement(cop, "a", href="#" + pref).text = domname

    # collect others
    oth_o = et.Element("div", attrib={"id": pref + "_oth"})
    tf = copy.deepcopy(of)
    for l in tf:
        try:
            nel, lid, title = process_xml(path, l, ff)
        except:
            print(l)
        of.remove(l)
        cop = et.SubElement(oth_o, "p")
        et.SubElement(cop, "a", href="#" + lid).text = title
        h_t.append(nel)

    cop = et.SubElement(h_o, "p")
    et.SubElement(cop, "a", href="#" + pref + "_oth").text = "Other"

    et.SubElement(h_o, "hr")

    h_o.append(oth_o)

    tree = et.ElementTree(doc)
    tree.write(
        "./doc/" + vin + ".htm",
        encoding="UTF-8",
        xml_declaration=True,
        default_namespace=None,
        method="html",
    )
    print("\r\tDone:100%")


vin_opt = ""
allvin = ""


def opt_parser():
    """Parsing of command line parameters. User should define at least com port name"""

    global vin_opt
    global allvin

    parser = argparse.ArgumentParser(description="Tool for view DocDb")

    parser.add_argument("-p", help="ELM327 com port name", dest="port", default="")

    parser.add_argument(
        "-s",
        help="com port speed configured on ELM {38400[default],57600,115200,230400,500000} DEPRECATED",
        dest="speed",
        default="38400",
    )

    parser.add_argument(
        "-r",
        help="com port rate during diagnostic session {38400[default],57600,115200,230400,500000}",
        dest="rate",
        default="38400",
    )

    parser.add_argument(
        "--si", help="try SlowInit first", dest="si", default=False, action="store_true"
    )

    parser.add_argument(
        "-L",
        help="language option {RU[default],GB,FR,IT,...}",
        dest="lang",
        default="RU",
    )

    parser.add_argument(
        "--sd", help="separate doc files", dest="sd", default=False, action="store_true"
    )

    parser.add_argument(
        "--cfc",
        help="turn off automatic FC and do it by script",
        dest="cfc",
        default=False,
        action="store_true",
    )

    parser.add_argument("--log", help="log file name", dest="logfile", default="")

    parser.add_argument("--vin", help="vin number", dest="vinnum", default="")

    parser.add_argument(
        "--scan",
        help="scan ECUs even if savedEcus.p file exists",
        dest="scan",
        default=False,
        action="store_true",
    )

    parser.add_argument(
        "--demo",
        help="for debuging purpose. Work without car and ELM",
        dest="demo",
        default=False,
        action="store_true",
    )

    parser.add_argument(
        "--allvin",
        help="generate file with all VIN numbers for platform",
        dest="allvin",
        default="",
    )

    options = parser.parse_args()

    # if not options.port and config.os != 'android':
    #  parser.print_help()
    #  iterator = sorted(list(list_ports.comports()))
    #  print ""
    #  print "Available COM ports:"
    #  for port, desc, hwid in iterator:
    #    print "%-30s \n\tdesc: %s \n\thwid: %s" % (port,desc,hwid)
    #  print ""
    #  exit(2)
    # else:
    config.OPT_PORT = options.port
    config.OPT_SPEED = int(options.speed)
    config.OPT_RATE = int(options.rate)
    config.OPT_LANG = options.lang
    config.OPT_LOG = options.logfile
    config.OPT_DEMO = options.demo
    config.OPT_SCAN = options.scan
    config.OPT_SI = options.si
    config.OPT_CFC0 = options.cfc
    config.OPT_SD = options.sd
    vin_opt = options.vinnum
    allvin = options.allvin


def main():
    """Main function

    1) if ../BVMEXTRACTION doesn't exist then  config.opt_demo=True which means that we would not guide with MTC
       and will show all options
    2) if not demo mode and savedVIN.txt exists and not scan then check savedVIN.txt
       else getVIN
    3) if len(vin)==0 then demo mode
    """

    global dfg_ds
    global vin_opt
    global allvin

    opt_parser()

    chk_dir_tree()
    find_dbs()

    if allvin != "":
        acf_buildFull(allvin)
        exit()

    """If MTC database does not exists then demo mode"""
    if not os.path.exists("../BVMEXTRACTION"):
        config.OPT_DEMO = True

    print("Loading language ")
    sys.stdout.flush()

    # loading language data
    lang = optfile("Location/DiagOnCAN_" + config.OPT_LANG + ".bqm", True)
    config.LANGUAGE_DICT = lang.dict
    print("Done")

    # finding zip
    # zipf = "../DocDB_"+config.opt_lang+".7ze"
    # if not os.path.exists(zipf):
    #  zipf = "../DocDB_GB.7ze"
    #  if not os.path.exists(zipf):
    #    zipFileList = glob.glob("../DocDB_*.7ze")
    #    if len(zipFileList)==0:
    #      print "\n\nERROR!!!!  Can't find any ../DocDB_*.7ze file"
    #      exit()
    #    zipf = zipFileList[0]

    vin = ""
    if vin_opt == "" and (
        not config.OPT_DEMO and (config.OPT_SCAN or not os.path.exists("savedVIN.txt"))
    ):
        print("Opening ELM")
        elm = ELM(config.OPT_PORT, config.OPT_SPEED, config.OPT_LOG)

        # change serial port baud rate
        if config.OPT_SPEED < config.OPT_RATE and not config.OPT_DEMO:
            elm.port.soft_boudrate(config.OPT_RATE)

        print("Loading ECUs list")
        scan_ecus = ScanEcus(elm)  # Prepare a list of all ecus

        saved_ecus_file_name = "savedEcus.p"

        if config.OPT_DEMO and len(config.OPT_ECU_ID) > 0:
            # demo mode with a predefined ecu list
            scan_ecus.read_uces_file(read_all=True)
            scan_ecus.detected_ecus = []
            for i in config.OPT_ECU_ID.split(","):
                if i in list(scan_ecus.all_ecus.keys()):
                    scan_ecus.all_ecus[i]["ecuname"] = i
                    scan_ecus.all_ecus[i]["idf"] = scan_ecus.all_ecus[i]["ModelId"][2:4]
                    if scan_ecus.all_ecus[i]["idf"][0] == "0":
                        scan_ecus.all_ecus[i]["idf"] = scan_ecus.all_ecus[i]["idf"][1]
                    scan_ecus.all_ecus[i]["pin"] = "can"
                    scan_ecus.detected_ecus.append(scan_ecus.all_ecus[i])
        else:
            if not os.path.isfile(saved_ecus_file_name) or config.OPT_SCAN:
                # choosing model
                scan_ecus.choose_model(
                    config.OPT_CAR
                )  # choose model of car for doing full scan

            # Do this check every time
            scan_ecus.scan_all_ecus()  # First scan of all ecus

        de = scan_ecus.detected_ecus

        print("Reading VINs")
        vin = get_vin(de, elm)

    elif vin_opt == "" and os.path.exists("savedVIN.txt"):
        with open("savedVIN.txt") as vin_file:
            vin_lines = vin_file.readlines()
            for vin_line in vin_lines:
                vin_line = vin_line.strip()
                if "#" in vin_line:
                    continue
                if len(vin_line) == 17:
                    vin = vin_line.upper()
                    break

    elif vin_opt != "":
        vin = vin_opt

    if len(vin) != 17:
        print("Can't find any valid VIN. Switch to demo")
        config.OPT_DEMO = True
    else:
        print("\tVIN     :", vin)

    # find and load MTC
    vindata = ""
    mtcdata = ""
    refdata = ""
    platform = ""
    if vin != "":
        vindata, mtcdata, refdata, platform = acf_get_mtc(vin, prefer_file=True)

        if vindata == "" or mtcdata == "" or refdata == "":
            print("ERROR!!! Can't find MTC data in database")
            config.OPT_DEMO = True

        print("\tPlatform:", platform)

        mtc = (
            mtcdata.replace(" ", "")
            .replace("\n", "")
            .replace("\r", "")
            .replace("\t", "")
            .split(";")
        )
        vda = vindata.split(";")[3].split(":")[1].split("/")
        mtc = mtc + vda
        mtcdata = ";".join(mtc)
        date_madc = vindata.split(";")[4]

    # choose and load DFG
    dfg = ClassDfg(platform)

    if dfg.tcom == "146":
        dfg.tcom = "159"
        dfg.dfgFile = dfg.dfgFile.replace("DFG_146", "DFG_159")
    elif dfg.tcom == "135":
        dfg.tcom = "147"
        dfg.dfgFile = dfg.dfgFile.replace("DFG_135", "DFG_147")

    dfg.load_dfg()

    dfg_ds = dfg.dataSet

    generate_html(
        "../DocDB_" + config.OPT_LANG + "/DocDb" + dfg.tcom + "/SIE/",
        mtcdata.split(";"),
        vin,
        dfg,
        date_madc,
    )


if __name__ == "__main__":
    main()
