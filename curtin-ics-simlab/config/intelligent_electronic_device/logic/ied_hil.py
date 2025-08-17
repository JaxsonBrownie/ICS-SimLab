import time
import numpy as np
from threading import Thread

# note that "physical_values" is a dictionary of all the values defined in the JSON
# the keys are defined in the JSON
def logic(physical_values):
    # initial values (output only)
    physical_values["transformer_voltage"] = 120
    physical_values["output_voltage"] = 120
    physical_values["tap_position"] = 7

    # transformer variables
    tap_change_perc = 1.5
    tap_change_center = 7
    voltage_normal = 120

    while True:
        # get the difference in tap position
        real_tap_pos_dif = max(0, min(int(physical_values["tap_position"]), 17))
        tap_pos_dif = real_tap_pos_dif - tap_change_center

        # get voltage change
        volt_change = tap_pos_dif * (tap_change_perc / 100) * voltage_normal
        physical_values["transformer_voltage"] = voltage_normal + volt_change

        # implement breaker
        if physical_values["breaker_state"] == 1:
            physical_values["output_voltage"] = 0
            pass
        else:
            physical_values["output_voltage"] = physical_values["transformer_voltage"]


        time.sleep(0.1)

    # TODO: implement voltage change
    # TODO: theres no way to make a t-flipflop in a PLC (can't change an input register) - maybe some way to send one-way modbus command