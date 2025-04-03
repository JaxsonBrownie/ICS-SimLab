import time
import numpy as np
from threading import Thread

# note that "physical_values" is a dictionary of all the values defined in the JSON
# the keys are defined in the JSON
def logic(physical_values, interval):
    # initial values
    physical_values["solar_power"] = 0
    print(physical_values)

    mean = 0
    std_dev = 1
    height = 2000

    x_values = np.linspace(mean - 4*std_dev, mean + 4*std_dev, 100)
    y_values = height * np.exp(-0.5 * ((x_values - mean) / std_dev) ** 2)

    solar_power_thread = Thread(target=solar_power_sim, args=(y_values, physical_values))
    solar_power_thread.daemon = True
    solar_power_thread.start()

    transfer_switch_thread = Thread(target=transfer_switch_sim, args=(physical_values,))
    transfer_switch_thread.daemon = True
    transfer_switch_thread.start()


def transfer_switch_sim(physical_values):
    while True:
        print(physical_values["transfer_switch_state"])
        print(physical_values["solar_power"])
        print(physical_values["input_power"])
        if physical_values["transfer_switch_state"] == True:
            physical_values["input_power"] = physical_values["solar_power"]
        else:
            physical_values["input_power"] = 180
        time.sleep(0.1)


def solar_power_sim(y_values, physical_values):
    while True:
        # implement solar power simulation
        for i in range(100):
            solar_power = y_values[i]
            physical_values["solar_power"] = solar_power
            time.sleep(1)


        
if __name__ == "__main__":
    logic({}, 0.2)