from pyren3 import config
from pyren3.mod.elm import ELM, dnat, snat

############## change me ################

ecu_functional_address = "26"
config.PORT = "bt"

#########################################


# config.opt_demo    = True
config.SPEED = 38400
config.LOG = "simpl.txt"

print("Opening ELM")
elm = ELM(config.PORT, config.SPEED, True)

print("Init    ELM")
elm.init_can()

TXa = dnat[ecu_functional_address]
RXa = snat[ecu_functional_address]
elm.currentaddress = TXa

print(elm.cmd("at sh " + TXa))
print(elm.cmd("at cra " + RXa))
print(elm.cmd("at fc sh " + TXa))
print(elm.cmd("at fc sd 30 00 00"))  # status BS STmin
print(elm.cmd("at fc sm 1"))
print(elm.cmd("at sp 6"))
print(elm.cmd("10C0"))
# print elm.cmd("3BA00A00")
