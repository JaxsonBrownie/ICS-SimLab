import time
import random
from threading import Thread

# note that "physical_values" is a dictionary of all the values defined in the JSON
# the keys are defined in the JSON
def logic(input_registers, output_registers, state_update_callbacks):
    safe_range_perc = 5
    voltage_normal = 120
    tap_state = True

    # get register references
    voltage = input_registers["transformer_voltage_reading"]
    tap_change = input_registers["tap_change_command"]
    breaker_control_command = output_registers["breaker_control_command"]
    tap_position = output_registers["tap_position"]

    # set starting values
    tap_position["value"] = 7
    state_update_callbacks["tap_position"]()

    # randomly tap change in a new thread
    tapping_thread = Thread(target=tap_change_thread, args=(tap_position, state_update_callbacks), daemon=True)
    tapping_thread.start()

    # calcuate safe voltage threshold
    high_bound = voltage_normal + voltage_normal * (safe_range_perc / 100)
    low_bound = voltage_normal - voltage_normal * (safe_range_perc / 100)

    # create the breaker thread
    breaker_thread = Thread(target=breaker, args=(voltage, breaker_control_command, tap_position, state_update_callbacks, low_bound, high_bound), daemon=True)
    breaker_thread.start()

    while True:
        # implement tap change
        if tap_change["value"] == 1 and tap_state:
            tap_change(1, tap_position, state_update_callbacks)
            tap_state = False
        elif tap_change["value"] == 2 and tap_state:
            tap_change(-1, tap_position, state_update_callbacks)
            tap_state = False

        # wait for the tap changer to revert back to 0 before changing any position
        if tap_change["value"] == 0:
            tap_state = True
        
        time.sleep(0.1)


# a thread to implement automatic tap changes
def tap_change_thread(tap_position, state_update_callbacks):
    while True:
        tap = random.choice([-1, 1])
        tap_change(tap, tap_position, state_update_callbacks)

        time.sleep(5)
        

# a thread to implement the breaker
def breaker(voltage, breaker_control_command, tap_position, state_update_callbacks, low_bound, high_bound):
    time.sleep(3)

    while True:
        # implement breaker with safe range
        if voltage["value"] > high_bound:
            breaker_control_command["value"] = True
            state_update_callbacks["breaker_control_command"]()
            
            tap_change(-1, tap_position, state_update_callbacks)
            print("HIGH VOLTAGE - TAP BY -1")
            time.sleep(1)
        elif voltage["value"] < low_bound:
            breaker_control_command["value"] = True
            state_update_callbacks["breaker_control_command"]()

            tap_change(1, tap_position, state_update_callbacks)
            print("LOW VOLTAGE - TAP BY +1")
            time.sleep(1)
        else:
            breaker_control_command["value"] = False
            state_update_callbacks["breaker_control_command"]()

        
        time.sleep(1)


# a function for tap changing within range 0 - 17
def tap_change(tap, tap_position, state_update_callbacks):
    tap_position["value"] = tap_position["value"] + tap
    if tap_position["value"] < 0:
        tap_position["value"] = 0
    if tap_position["value"] > 17:
        tap_position["value"] = 17
    
    state_update_callbacks["tap_position"]()