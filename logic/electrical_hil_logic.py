import time

# note that "physical_values" is a dictionary of all the values defined in the JSON
# the keys are defined in the JSON
def logic(physical_values, interval):
    # initial values
    physical_values["solar_power"] = 69

    while True:
        # implement solar power simulation
        physical_values["solar_power"] -= 1
        
        time.sleep(interval)
