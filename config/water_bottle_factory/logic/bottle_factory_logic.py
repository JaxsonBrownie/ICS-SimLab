import time
from threading import Thread

# note that "physical_values" is a dictionary of all the values defined in the JSON
# the keys are defined in the JSON
def logic(physical_values, interval):
    print("INTIAL")
    print(physical_values)
    # initial values
    physical_values["tank_level_value"] = 50
    physical_values["tank_input_valve_state"] = 0
    physical_values["tank_output_valve_state"] = 1

    time.sleep(3)

    # start simulation threads
    tank_thread = Thread(target=tank_valves_thread, args=(physical_values,), daemon=True)
    tank_thread.start()

    # block
    tank_thread.join()

# define behaviour for the tank level
#def tank_level_value_thread(physical_values):
#    while True:
#        physical_values["tank_level_value"] -= 3
#        time.sleep(0.5)

# define behaviour for the valves and tank level
def tank_valves_thread(physical_values):
    while True:
        if physical_values["tank_input_valve_state"] == True:
            physical_values["tank_level_value"] += 3

        if physical_values["tank_output_valve_state"] == True:
            physical_values["tank_level_value"] -= 1

        print(physical_values)
        time.sleep(0.5)