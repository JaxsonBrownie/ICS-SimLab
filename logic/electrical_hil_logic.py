import time
import numpy as np

# note that "physical_values" is a dictionary of all the values defined in the JSON
# the keys are defined in the JSON
def logic(physical_values, interval):
    # initial values
    physical_values["solar_power"] = 0

    mean = 0
    std_dev = 1
    height = 2000

    x_values = np.linspace(mean - 4*std_dev, mean + 4*std_dev, 100)
    y_values = height * np.exp(-0.5 * ((x_values - mean) / std_dev) ** 2)

    while True:
        # implement solar power simulation
        for i in range(100):
            solar_power = y_values[i]
            physical_values["solar_power"] = solar_power
            time.sleep(interval)
        
if __name__ == "__main__":
    logic({}, 0.2)