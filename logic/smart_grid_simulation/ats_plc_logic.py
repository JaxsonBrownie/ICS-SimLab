import time

# note that "physical_values" is a dictionary of all the values defined in the JSON
# the keys are defined in the JSON
def logic(input_registers, output_registers, state_update_callbacks):
    state_change = True
    sp_pm_prev = None
    ts_prev = None

    while True:
        # get the solar panel power meter value reference
        sp_pm_value = next((i for i in input_registers["input_register"] if i["address"] == 30), None)

        # get the transfer switch output value reference
        ts_value = next((i for i in output_registers["coil"] if i["address"] == 10), None)
        
        if sp_pm_prev != sp_pm_value["value"]:
            print(f"SOLAR PANEL POWER METER READING: {sp_pm_value['value']}")
            sp_pm_prev = sp_pm_value["value"]
        
        if ts_prev != ts_value["value"]:
            print(f"TRANSFER SWITCH VALUE: {ts_value['value']}")
            ts_prev = ts_value["value"]

        # write to the transfer switch
        # note that we retrieve the value by reference only (["value"])
        if sp_pm_value["value"] > 200 and state_change == True:
            ts_value["value"] = True
            state_change = False
            state_update_callbacks["transfer_switch_state"]()
            print("TRANSFER SWITCH SWITCHED TO SOLAR POWER")
        if sp_pm_value["value"] <= 200 and state_change == False:
            ts_value["value"] = False
            state_change = True
            state_update_callbacks["transfer_switch_state"]()
            print("TRANSFER SWITCH SWITCHED TO MAINS POWER")
        time.sleep(0.05)