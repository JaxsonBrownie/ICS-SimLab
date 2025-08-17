import time

# note that "physical_values" is a dictionary of all the values defined in the JSON
# the keys are defined in the JSON
def logic(input_registers, output_registers, state_update_callbacks):
    state_change = True
    sp_pm_prev = None
    ts_prev = None

    # get register references
    sp_pm_value = input_registers["solar_panel_reading"]
    ts_value = output_registers["transfer_switch_state"]

    while True:        
        if sp_pm_prev != sp_pm_value["value"]:
            sp_pm_prev = sp_pm_value["value"]
        
        if ts_prev != ts_value["value"]:
            ts_prev = ts_value["value"]

        # write to the transfer switch
        # note that we retrieve the value by reference only (["value"])
        if sp_pm_value["value"] > 200 and state_change == True:
            ts_value["value"] = True
            state_change = False
            state_update_callbacks["transfer_switch_state"]()
        if sp_pm_value["value"] <= 200 and state_change == False:
            ts_value["value"] = False
            state_change = True
            state_update_callbacks["transfer_switch_state"]()
        time.sleep(0.05)