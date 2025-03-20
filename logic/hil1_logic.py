import time

# note that "physical_values" is a dictionary of all the values defined in the JSON
def logic(physical_values, interval):
    physical_values["static_ground"] = True

    while True:
        physical_values["static_ground"] = not physical_values["static_ground"]
        #print(f"LOGIC {physical_values['static_ground']}")
        time.sleep(interval)
