import time

# note that "physical_values" is a dictionary of all the values defined in the JSON
# the keys are defined in the JSON
def logic(input_registers, output_registers, state_update_callbacks):
    state_change = True

    while True:
        # get the solar panel power meter value reference
        sp_pm_value = next((i for i in input_registers["input_register"] if i["address"] == 100), None)

        # get the transfer switch output value reference
        ts_value = next((i for i in output_registers["coil"] if i["address"] == 200), None)

        # write to the transfer switch
        if sp_pm_value["value"] > 200 and state_change == True:
            ts_value["value"] = True
            state_change = False
            state_update_callbacks["transfer_switch_state"]()
        if sp_pm_value["value"] <= 200 and state_change == False:
            ts_value["value"] = False
            state_change = True
            state_update_callbacks["transfer_switch_state"]()
        time.sleep(0.05)