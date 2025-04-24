import time

def logic(input_registers, output_registers, state_update_callbacks):
    state = "ready"

    # get value references
    bottle_level_ref = next((i for i in input_registers["input_register"] if i["address"] == 1), None)
    bottle_distance_to_filler_ref = next((i for i in input_registers["input_register"] if i["address"] == 2), None)
    conveyor_engine_state_ref = next((i for i in output_registers["coil"] if i["address"] == 3), None)
    plc1_tank_output_state_ref = next((i for i in output_registers["coil"] if i["address"] == 11), None)

    # initial writing
    conveyor_engine_state_ref["value"] = False
    state_update_callbacks["conveyor_engine_state"]()   
    plc1_tank_output_state_ref["value"] = True
    state_update_callbacks["plc1_tank_output_state"]()

    # wait for the first sync to happen
    time.sleep(2)

    # create mapping logic
    while True:
        # stop conveyor and start tank
        if state == "ready":
            plc1_tank_output_state_ref["value"] = True
            state_update_callbacks["plc1_tank_output_state"]()
            conveyor_engine_state_ref["value"] = False
            state_update_callbacks["conveyor_engine_state"]()
            #print("PLC2: FILLING THE BOTTLE")
            state = "filling"

        # stop filling and start conveyor
        if bottle_level_ref["value"] >= 180 and state == "filling":
            # turn off the tank and start conveyoer
            plc1_tank_output_state_ref["value"] = False
            state_update_callbacks["plc1_tank_output_state"]()
            conveyor_engine_state_ref["value"] = True
            state_update_callbacks["conveyor_engine_state"]()
            #print("PLC2: BOTTLE IS FULL")
            state = "moving"

        # wait for conveyor to move the bottle
        if state == "moving":
            if bottle_distance_to_filler_ref["value"] >= 0 and bottle_distance_to_filler_ref["value"] <= 30:
                # wait for a new bottle to enter
                if bottle_level_ref["value"] == 0:
                    state = "ready"

        time.sleep(0.1)
