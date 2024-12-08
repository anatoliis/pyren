from mod import config, mod_elm

############## change me ################

ecu_functional_address = "26"
config.opt_port = "bt"

#########################################


# config.opt_demo    = True
config.opt_speed = 38400
config.opt_log = "simpl.txt"

print("Opening ELM")
elm = mod_elm.ELM(config.opt_port, config.opt_speed, True)

print("Init    ELM")
elm.init_can()

TXa = mod_elm.dnat[ecu_functional_address]
RXa = mod_elm.snat[ecu_functional_address]
elm.currentaddress = TXa

print(elm.cmd("at sh " + TXa))
print(elm.cmd("at cra " + RXa))
print(elm.cmd("at fc sh " + TXa))
print(elm.cmd("at fc sd 30 00 00"))  # status BS STmin
print(elm.cmd("at fc sm 1"))
print(elm.cmd("at sp 6"))
print(elm.cmd("10C0"))
# print elm.cmd("3BA00A00")
