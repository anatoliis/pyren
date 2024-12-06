#!/usr/bin/env python3

import config
from mod_elm import DNAT, ELM, SNAT

############## change me ################

ecu_functional_address = "26"
config.OPT_PORT = "bt"

#########################################


# config.opt_demo    = True
config.OPT_SPEED = 38400
config.OPT_LOG = "simpl.txt"

print("Opening ELM")
elm = ELM(config.OPT_PORT, config.OPT_SPEED, True)

print("Init    ELM")
elm.init_can()

TXa = DNAT[ecu_functional_address]
RXa = SNAT[ecu_functional_address]
elm.current_address = TXa

print(elm.cmd("at sh " + TXa))
print(elm.cmd("at cra " + RXa))
print(elm.cmd("at fc sh " + TXa))
print(elm.cmd("at fc sd 30 00 00"))  # status BS STmin
print(elm.cmd("at fc sm 1"))
print(elm.cmd("at sp 6"))
print(elm.cmd("10C0"))
