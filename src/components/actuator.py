#!/usr/bin/env python3

# FILE:     actuator.py
# PURPOSE:  Simulates an actuators. Can read and write to a HIL physical environment.

import logging
import json
import asyncio
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
def update_register_values(configs, register_values, values):
    pass


# FUNCTION: main
# PURPOSE:  Main execution
async def main():
    # retrieve configurations from the given JSON (will be in the same directory)
    configs = retrieve_configs("config.json")
    logging.info("Starting Actuator")

    # create a dictionary to represent the different physical values (for this actuator to write to)
    physical_values = {}
    for value in configs["database"]["physical_values"]:
        # initialise all physical values to just be an empty string (the key matters more)
        physical_values[value["name"]] = ""

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

    # TODO: make a dictionary "register_values", keys being defined in JSON, values being ints 

    # TODO: create a thread that constantly updates "register_values" with the actuator modbus value


    # start the actuator logic thread
    # the logic will read "register_values" and write to "physical_values"
    actuator_thread = Thread(target=logic.logic, args=(values, physical_values))
    actuator_thread.daemon = True
    actuator_thread.start()
    

    # TODO: start actuator database writing thread
    # this thread writes the values of physical_values to the database (so we don't need database queries in the logic)



    # await tasks
    actuator_thread.join()
    await server_task

if __name__ == "__main__":
    asyncio.run(main())