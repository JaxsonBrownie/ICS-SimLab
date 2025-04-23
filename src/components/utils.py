#!/usr/bin/env python3

# FILE: utils.py
# PURPOSE: Common functions to be used in all components

import json
import time



# FUNCTION: retrieve_configs
# PURPOSE:  Retrieves the JSON configs
def retrieve_configs(filename):
    with open(filename, "r") as config_file:
        content = config_file.read()
        configs = json.loads(content)
    return configs



# FUNCTION: update_register_values
# PURPOSE:  Updates the "register_values" dictionary with the register values of the modbus server,
#           which is in the "values" dictionary.
def update_register_values(register_values, values):
    while True:
        # create a clone dictionary to hold the "to-be-updated" values
        updated_register_values = register_values.copy()

        # update the cloned copy with the real modbus values
        index = 0
        for co in register_values["coil"]:
            modbus_value = values["co"].getValues(co["address"], co["count"])[0]
            updated_register_values["coil"][index]["value"] = modbus_value
            index += 1
        index = 0
        for di in register_values["discrete_input"]:
            modbus_value = values["di"].getValues(di["address"], di["count"])[0]
            updated_register_values["discrete_input"][index]["value"] = modbus_value
            index += 1
        index = 0
        for hr in register_values["holding_register"]:
            modbus_value = values["hr"].getValues(hr["address"], hr["count"])[0]
            updated_register_values["holding_register"][index]["value"] = modbus_value
            index += 1
        index = 0
        for ir in register_values["input_register"]:
            modbus_value = values["ir"].getValues(ir["address"], ir["count"])[0]
            updated_register_values["input_register"][index]["value"] = modbus_value
            index += 1
        
        # update register values from the cloned copy
        register_values["coil"] = updated_register_values["coil"].copy()
        register_values["discrete_input"] = updated_register_values["discrete_input"].copy()
        register_values["holding_register"] = updated_register_values["holding_register"].copy()
        register_values["input_register"] = updated_register_values["input_register"].copy()

        time.sleep(0.2)



# FUNCTION: create_register_values_dict
# PURPOSE:  Returns a dictionary that is used to store all register values in the following format:
# "register_values":
# {
#    "coil": []
#    "discrete_input": []
#    "holding_register": 
#    [
#        {
#            "address": 170
#            "count": 1
#            "value": 3013
#        }
#    ]
#    "input_register: []"
# }
def create_register_values_dict(configs):
    register_values = {}
    register_values["coil"] = []
    register_values["discrete_input"] = []
    register_values["holding_register"] = []
    register_values["input_register"] = []
    for co in configs["values"]["coil"]:
        register = {
            "address": co["address"],
            "count": co["count"],
            "value": False
        }
        if "io" in co:
            register["io"] = co["io"]
        if "id" in co:
            register["id"] = co["id"]
        register_values["coil"].append(register)
    for di in configs["values"]["discrete_input"]:
        register = {
            "address": di["address"],
            "count": di["count"],
            "value": False
        }
        if "io" in di:
            register["io"] = di["io"]
        if "id" in di:
            register["id"] = di["id"]
        register_values["discrete_input"].append(register)
    for hr in configs["values"]["holding_register"]:
        register = {
            "address": hr["address"],
            "count": hr["count"],
            "value": False
        }
        if "io" in hr:
            register["io"] = hr["io"]
        if "id" in hr:
            register["id"] = hr["id"]
        register_values["holding_register"].append(register)
    for ir in configs["values"]["input_register"]:
        register = {
            "address": ir["address"],
            "count": ir["count"],
            "value": False
        }
        if "io" in ir:
            register["io"] = ir["io"]
        if "id" in ir:
            register["id"] = ir["id"]
        register_values["input_register"].append(register)
    return register_values