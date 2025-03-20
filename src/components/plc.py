#!/usr/bin/env python3

# FILE:     plc.py
# PURPOSE:  Implements the functionality of a PLC. The configurations are taken from
#           a JSON file called config.json.

import json
import asyncio
import time
import logging
from pymodbus.client import ModbusTcpClient, ModbusSerialClient
from pymodbus.server import ModbusTcpServer, ModbusSerialServer, StartSerialServer, StartTcpServer
from pymodbus.datastore import ModbusSequentialDataBlock, ModbusSlaveContext, ModbusServerContext

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

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
    print("Starting tcp server")
    await tcp_server.serve_forever()


# FUNCTION: run_rtu_slave
# PURPOSE:  An asynchronous function to use for modbus rtu server
async def run_rtu_slave(connection, context):
    rtu_slave = ModbusSerialServer(context=context, port=connection["comm_port"], baudrate=9600, timeout=1)
    print("Starting rtu slave")
    await rtu_slave.serve_forever()


# FUNCTION: run_tcp_client
# PURPOSE:  Creates a tcp client
def run_tcp_client(connection):
    tcp_client = ModbusTcpClient(host=connection["ip"], port=connection["port"])
    print("Starting tcp client")
    tcp_client.connect()
    return tcp_client


# FUNCTION: run_rtu_master
# PURPOSE:  Create an rtu master connection
def run_rtu_master(connection):
    rtu_master = ModbusSerialClient(port=connection["comm_port"], baudrate=9600, timeout=1)
    print("Starting rtu master")
    rtu_master.connect()
    return rtu_master


# FUNCTION: init_inbound_cons
# PURPOSE:  Starts any tcp/rtu servers configured in the config file for inbound connections
async def init_inbound_cons(configs, context):
    server_tasks = []
    for connection in configs["inbound_connections"]:
        if connection["type"] == "tcp":            
            # start tcp server thread
            server_tasks.append(asyncio.create_task(run_tcp_server(connection, context)))
        elif connection["type"] == "rtu":
            # start rtu slave thread
            server_tasks.append(asyncio.create_task(run_rtu_slave(connection, context))) 
    # wait for all servers  
    for task in server_tasks:
        await task


# FUNCTION: init_outbound_cons
# PURPOSE:  Initialised all outbound connections. These connections can be shared amongst
#           monitors. Returns a map of connection ids as keys, and the connection object
#           itself as the values.
def init_outbound_cons(configs):
    connections = {}
    for connection in configs["outbound_connections"]:
        if connection["type"] == "tcp":
            client = run_tcp_client(connection)
            connections[connection["id"]] = client
        elif connection["type"] == "rtu":
            client = run_rtu_master(connection)
            connections[connection["id"]] = client
    return connections

# FUNCTION: monitor
# PURPOSE:  A monitor thread to continuously read data from a defined and intialised connection
async def monitor(monitor_configs, modbus_con):
    print(f"Starting monitor: {monitor_configs['id']}")
    interval = monitor_configs["interval"]
    value_type = monitor_configs["value_type"]
    address = monitor_configs["address"]
    count = monitor_configs["count"]

    while True:
        # select the correct function
        if value_type == "coil":
            values = modbus_con.read_coils(address, count).bits
        elif value_type == "discrete_input":
            values = modbus_con.read_discrete_inputs(address, count).bits
        elif value_type == "holding_register":
            values = modbus_con.read_holding_registers(address, count).registers
        elif value_type == "input_register":
            values = modbus_con.read_input_registers(address, count).registers

        print(values)
        time.sleep(interval)
        

# FUNCTION: start_monitors
# PURPOSE:  Started all of the monitor threads. Note that more than one monitor can
#           utilise a single connection (but there must be a connection!).
async def start_monitors(configs, outbound_cons):
    monitors = []
    for monitor_config in configs["monitors"]:
        # get the outbound connection (Modbus object) for the monitor
        outbound_con_id = monitor_config["outbound_connection_id"]
        modbus_con = outbound_cons[outbound_con_id]

        # start the monitor thread
        monitors.append(asyncio.create_task(monitor(monitor_config, modbus_con)))
    return monitors

        
# FUNCTION: main
# PURPOSE:  The main execution
async def main():
    # retrieve configurations from the given JSON (will be in the same directory)
    configs = retrieve_configs("config.json")
    logging.info(f"Starting PLC")

    # create slave context (by default will have all address ranges)
    slave_context = ModbusSlaveContext()
    context = ModbusServerContext(slaves=slave_context, single=True)

    # start any inbound connection servers (tcp, rtu or both) with the same context
    inbound_cons = asyncio.create_task(init_inbound_cons(configs, context))

    # start any outbound connections, waiting 2 seconds to ensure connections are up
    outbound_cons = init_outbound_cons(configs)
    time.sleep(2)

    # start any configured monitors
    monitors = asyncio.create_task(start_monitors(configs, outbound_cons))

    # block on the inbound connection servers and monitors
    await inbound_cons
    await monitors

    # close all outbound client connections
    for outbound_con in outbound_cons.values():
        outbound_con.close()
    
    # block
    while True:
        time.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())