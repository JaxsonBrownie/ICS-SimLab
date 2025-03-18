#!/usr/bin/env python3

# FILE:     sensor.py
# PURPOSE:  Simulates a sensor. Takes input from a simulated physical process.

import json
import asyncio
import sqlite3
from pymodbus.server import ModbusTcpServer, ModbusSerialServer, StartSerialServer, StartTcpServer
from pymodbus.datastore import ModbusSequentialDataBlock, ModbusSlaveContext, ModbusServerContext

# FUNCTION: retrieve_configs
# PURPOSE: Retrieves the JSON configs
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
    print("Starting rtu")
    await rtu_slave.serve_forever()


# FUNCTION: start_servers
# PURPOSE:  Starts any tcp/rtu servers configured in the config file
async def start_servers(configs, context):
    tasks = []
    for connection in configs["connection_endpoints"]:
        if connection["type"] == "tcp":            
            # start tcp server thread
            tasks.append(asyncio.create_task(run_tcp_server(connection, context)))
        elif connection["type"] == "rtu":
            # start rtu slave thread
            tasks.append(asyncio.create_task(run_rtu_slave(connection, context)))        
    for task in tasks:
        await task


# FUNCTION: start_sensor
# PURPOSE:  Starts a process to read sensor data from SQLite specific to this sensor.
#           The column is a TEXT datatype to allow for generic inputs.
async def start_sensor(configs, context):
    pass


# FUNCTION: main
# PURPOSE:  The main execution
async def main():
    # retrieve configurations from the given JSON (will be in the same directory)
    configs = retrieve_configs("config.json")

    # create slave context (by default will have all address ranges)
    slave_context = ModbusSlaveContext()
    context = ModbusServerContext(slaves=slave_context, single=True)

    # start any configured servers (tcp, rtu or both) with the same context
    await start_servers(configs, context)

    # connect to hardware SQLite database
    conn = sqlite3.connect("hardware_interactions.db")
    cursor = conn.cursor()

    # start the sensor reading


if __name__ == "__main__":
    asyncio.run(main())