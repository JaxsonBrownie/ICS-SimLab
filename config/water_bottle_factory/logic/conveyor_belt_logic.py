import time

# note that "physical_values" is a dictionary of all the values defined in the JSON
# the keys are defined in the JSON
def logic(register_values, physical_values, interval):
    converyor_state = False
    while True:
        for register in register_values["coil"]:
            if register["address"] == 30:
                converyor_state = register["value"]

        physical_values["conveyor_belt_engine_state"] = converyor_state

        time.sleep(interval)