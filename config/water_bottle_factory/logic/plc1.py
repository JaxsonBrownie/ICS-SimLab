import time

def logic(input_registers, output_registers, state_update_callbacks):
    state_change = True

    # get value references
    tank_level_ref = next((i for i in input_registers["input_register"] if i["address"] == 1), None)
    tank_input_valve_ref = next((i for i in output_registers["coil"] if i["address"] == 2), None)
    tank_output_valve_ref = next((i for i in output_registers["coil"] if i["address"] == 3), None)
    #plc1_tank_output_state_ref = next((i for i in output_registers["coil"] if i["address"] == 11), None)

    # initial writing
    tank_input_valve_ref["value"] = False
    state_update_callbacks["tank_input_valve_state"]()
    tank_output_valve_ref["value"] = True
    state_update_callbacks["tank_output_valve_state"]()

    # wait for the first sync to happen
    time.sleep(2)

    # create mapping logic
    prev_tank_output_valve = tank_output_valve_ref["value"]
    while True:
        # turn input on if the tank is almost empty
        if tank_level_ref["value"] < 40 and state_change:
            print("Water level below 40")
            tank_input_valve_ref["value"] = True
            state_update_callbacks["tank_input_valve_state"]()
            state_change = False

        # turn input off if tank gets full
        elif tank_level_ref["value"] > 70 and not state_change:
            print("Water level above 70")
            tank_input_valve_ref["value"] = False
            state_update_callbacks["tank_input_valve_state"]()
            state_change = True
        
        # write to actuator if the tank output state changes
        if tank_output_valve_ref["value"] != prev_tank_output_valve:
            state_update_callbacks["tank_output_valve_state"]()
            prev_tank_output_valve = tank_output_valve_ref["value"]

        time.sleep(0.2)

