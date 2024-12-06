#!/usr/bin/env python3
import config
from mod_elm import ELM

############## change me ################

ecu_functional_address = "7a"
config.OPT_PORT = "/dev/cu.usbserial-AH01J4BS"

#########################################


# config.opt_demo    = True
config.OPT_SPEED = 38400
config.OPT_LOG = "simpl.txt"

print("Opening ELM")
elm = ELM(config.OPT_PORT, config.OPT_SPEED, True)

print("Init    ELM")
print(elm.cmd("at z"))
elm.init_iso()

print(elm.cmd("at sh 80 " + ecu_functional_address + " f1"))
print(elm.cmd("at sw 96"))
print(elm.cmd("at wm 81 " + ecu_functional_address + " f1 3E"))
print(elm.cmd("at ib10"))
print(elm.cmd("at st ff"))
print(elm.cmd("at at 0"))

print(elm.cmd("at sp 5"))
print(elm.cmd("at fi"))

print(elm.cmd("at at 1"))
print(elm.cmd("at al"))
print(elm.cmd("at h1"))

print(elm.cmd("10C0"))
print(elm.cmd("2180"))
print(elm.cmd("2181"))
print(elm.cmd("17FF00"))
print(elm.cmd("01 02 03 04 05 06 07 08 09"))
