import time
import sqlite3
from threading import Thread

# note that "physical_values" is a dictionary of all the values defined in the JSON
# the keys are defined in the JSON
def logic(physical_values, interval):

    # initial values
    physical_values["tank_level_value"] = 500
    physical_values["tank_input_valve_state"] = False
    physical_values["tank_output_valve_state"] = True
    physical_values["bottle_level_value"] = 0
    physical_values["bottle_distance_to_filler_value"] = 0
    physical_values["conveyor_belt_engine_state"] = False


    time.sleep(3)

    # start tank valve threads
    tank_thread = Thread(target=tank_valves_thread, args=(physical_values,), daemon=True)
    tank_thread.start()

    # start bottle filling thread
    bottle_thread = Thread(target=bottle_filling_thread, args=(physical_values,), daemon=True)
    bottle_thread.start()

    # printing thread
    #info_thread = Thread(target=print_values, args=(physical_values,), daemon=True)
    #info_thread.start()

    # block
    tank_thread.join()
    bottle_thread.join()
    #info_thread.join()

# define behaviour for the valves and tank level
def tank_valves_thread(physical_values):
    while True:
        if physical_values["tank_input_valve_state"] == True:
            physical_values["tank_level_value"] += 18

        if physical_values["tank_output_valve_state"] == True:
            physical_values["tank_level_value"] -= 6
        time.sleep(0.6)

# define bottle filling behaviour
def bottle_filling_thread(physical_values):
    while True:
        # fill bottle up if there's a bottle underneath the filler and the tank output is on
        if physical_values["tank_output_valve_state"] == True:
            if physical_values["bottle_distance_to_filler_value"] >= 0 and physical_values["bottle_distance_to_filler_value"] <= 30:
                physical_values["bottle_level_value"] += 6
        
        # move the conveyor (reset bottle and distance if needed)
        if physical_values["conveyor_belt_engine_state"] == True:
            physical_values["bottle_distance_to_filler_value"] -= 4
            
            if physical_values["bottle_distance_to_filler_value"] < 0:
                physical_values["bottle_distance_to_filler_value"] = 130
                physical_values["bottle_level_value"] = 0
        time.sleep(0.6)

# printing thread
def print_values(physical_values):
    while True:
        print(physical_values)

        time.sleep(0.1)