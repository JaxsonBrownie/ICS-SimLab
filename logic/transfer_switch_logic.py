import time

# note that "physical_values" is a dictionary of all the values defined in the JSON
# the keys are defined in the JSON
def logic(register_values, physical_values, interval):
    # initial values
    physical_values["transfer_switch_state"] = False
    transfer_switch_state = False
    
    while True:
        # find the right register for the transfer switch
        for register in register_values["coil"]:
            if register["address"] == 100:
                transfer_switch_state = register["value"]

        # set the physical hil
        physical_values["transfer_switch_state"] = transfer_switch_state

        time.sleep(0.1)
