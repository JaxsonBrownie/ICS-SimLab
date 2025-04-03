#!/usr/bin/env python3

# FILE:     actuator.py
# PURPOSE:  Simulates an actuators. Can read and write to a HIL physical environment.

import logging
import json
import asyncio
import time
import sqlite3
from threading import Thread
from pymodbus.server import ModbusTcpServer, ModbusSerialServer
from pymodbus.datastore import ModbusSequentialDataBlock, ModbusSlaveContext, ModbusServerContext

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

# here we import the defined logic
# the logic will always be in a python file called logic.py, which gets copied to the container
try:
    import logic # type: ignore
except ModuleNotFoundError:
    print("Could not import logic for Actuator component")

# FUNCTION: retrieve_configs
# PURPOSE:  Retrieves the JSON configs
def retrieve_configs(filename):
    with open(filename, "r") as config_file:
        content = config_file.read()
        configs = json.loads(content)
    return configs


# FUNCTION: run_tcp_server
# PURPOSE:  An asynchronous function to be used to start a modbus tcp server
async def run_tcp_server(connection, context):
    # bind to all interfaces of the container
    tcp_server = ModbusTcpServer(context=context, address=("0.0.0.0", connection["port"]), ) 
    print("Starting tcp")
    await tcp_server.serve_forever()


# FUNCTION: run_rtu_slave
# PURPOSE:  An asynchronous function to use for modbus rtu server
async def run_rtu_slave(connection, context):
    rtu_slave = ModbusSerialServer(context=context, port=connection["comm_port"], baudrate=9600, timeout=1)
    print(f"Starting rtu slave on port {connection['comm_port']}")
    await rtu_slave.serve_forever()


# FUNCTION: start_servers
# PURPOSE:  Starts any tcp/rtu servers configured in the config file
async def start_servers(configs, context):
    tasks = []
    for connection in configs["inbound_connections"]:
        if connection["type"] == "tcp":            
            # start tcp server thread
            tasks.append(asyncio.create_task(run_tcp_server(connection, context)))
        elif connection["type"] == "rtu":
            # start rtu slave thread
            tasks.append(asyncio.create_task(run_rtu_slave(connection, context)))        
    for task in tasks:
        await task


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
            modbus_value = values["co"].getValues(co["address"]+1, co["count"])[0]
            updated_register_values["coil"][index]["value"] = modbus_value
            index += 1
        index = 0
        for di in register_values["discrete_input"]:
            modbus_value = values["di"].getValues(di["address"]+1, di["count"])[0]
            updated_register_values["discrete_input"][index]["value"] = modbus_value
            index += 1
        index = 0
        for hr in register_values["holding_register"]:
            modbus_value = values["hr"].getValues(hr["address"]+1, hr["count"])[0]
            updated_register_values["holding_register"][index]["value"] = modbus_value
            index += 1
        index = 0
        for ir in register_values["input_register"]:
            modbus_value = values["ir"].getValues(ir["address"]+1, ir["count"])[0]
            updated_register_values["input_register"][index]["value"] = modbus_value
            index += 1
        
        # update register values from the cloned copy
        register_values["coil"] = updated_register_values["coil"].copy()
        register_values["discrete_input"] = updated_register_values["discrete_input"].copy()
        register_values["holding_register"] = updated_register_values["holding_register"].copy()
        register_values["input_register"] = updated_register_values["input_register"].copy()


        time.sleep(0.2)


# FUNCTION: database_interaction
# PURPOSE:  Starts a process that writes to the SQLite table specific to this actuator.
#           The values from the dictionary "physical_values" will get written to the
#           database to simulate the actuator affecting the physical environment.
def database_interaction(configs, physical_values):
    # connect to hardware SQLite database
    conn = sqlite3.connect("physical_interations.db")
    cursor = conn.cursor()
    table = configs["database"]["table"]

    while True:
        # write the actuators physical values to the SQLite database
        for physical_value in configs["database"]["physical_values"]:
            cursor.execute(f"""
                UPDATE {table}
                SET value = ?
                WHERE physical_value = ?
            """, (physical_values[physical_value['name']], physical_value['name']))
            conn.commit()
        time.sleep(0.1)


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
        register_values["coil"].append(
            {
                "address": co["address"],
                "count": co["count"],
                "value": False
            }
        )
    for di in configs["values"]["discrete_input"]:
        register_values["discrete_input"].append(
            {
                "address": di["address"],
                "count": di["count"],
                "value": False
            }
        )
    for hr in configs["values"]["holding_register"]:
        register_values["holding_register"].append(
            {
                "address": hr["address"],
                "count": hr["count"],
                "value": 0
            }
        )
    for ir in configs["values"]["input_register"]:
        register_values["input_register"].append(
            {
                "address": ir["address"],
                "count": ir["count"],
                "value": 0
            }
        )
    return register_values


# FUNCTION: main
# PURPOSE:  Main execution
async def main():
    # retrieve configurations from the given JSON (will be in the same directory)
    configs = retrieve_configs("config.json")
    logging.info("Starting Actuator")

    # create slave context
    co = ModbusSequentialDataBlock.create()
    di = ModbusSequentialDataBlock.create()
    hr = ModbusSequentialDataBlock.create()
    ir = ModbusSequentialDataBlock.create()
    slave_context = ModbusSlaveContext(co=co, di=di, hr=hr, ir=ir)
    context = ModbusServerContext(slaves=slave_context, single=True)

    # start any configured servers with the same context
    values = {"co": co, "di": di, "hr": hr, "ir": ir}
    server_task = start_servers(configs, context)

    # create a dictionary to represent the different physical values
    physical_values = {}
    for value in configs["database"]["physical_values"]:
        # initialise all physical values to just be an empty string (the key matters more)
        physical_values[value["name"]] = ""
    
    # create a dictionary to represent the different register values
    # we do this as we want to abstract the actual modbus registers
    # a sample of register_values could look like:
    register_values = create_register_values_dict(configs)

    # start a thread to constantly update the "register_values" dictionary with the actual modbus register values
    sync_register_values = Thread(target=update_register_values, args=(register_values, values))
    sync_register_values.daemon = True
    sync_register_values.start()

    # TODO: investigate if the actuator even needs logic
    # start the actuator logic thread
    # the logic will read "register_values" and write to "physical_values"
    actuator_thread = Thread(target=logic.logic, args=(register_values, physical_values, 1))
    actuator_thread.daemon = True
    actuator_thread.start()
    
    # this thread writes the values of physical_values to the database (so we don't need database queries in the logic)
    database_thread = Thread(target=database_interaction, args=(configs, physical_values))
    database_thread.daemon = True
    database_thread.start()

    # await tasks and threads
    await server_task
    sync_register_values.join()
    actuator_thread.join()


if __name__ == "__main__":
    asyncio.run(main())