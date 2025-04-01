import time

# note that "physical_values" is a dictionary of all the values defined in the JSON
# the keys are defined in the JSON
def logic(register_values, physical_values, interval):
    while True:
        physical_values["transfer_switch_state"] = not physical_values["transfer_switch_state"]
        time.sleep(interval)
