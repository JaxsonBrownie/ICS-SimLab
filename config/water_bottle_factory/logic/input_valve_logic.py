import time

# note that "physical_values" is a dictionary of all the values defined in the JSON
# the keys are defined in the JSON
def logic(register_values, physical_values, interval):
    valve_state = False
    while True:
        for register in register_values["coil"]:
            if register["address"] == 20:
                valve_state = register["value"]

        physical_values["tank_input_valve_state"] = valve_state

        time.sleep(interval)