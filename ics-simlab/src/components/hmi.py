#!/usr/bin/env python3

# -----------------------------------------------------------------------------
# Project: Curtin ICS-SimLab
# File: hmi.py
#
# Copyright (c) 2025 Jaxson Brown, Curtin University
#
# Licensed under the MIT License. You may obtain a copy of the License at:
#     https://opensource.org/licenses/MIT
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
# Author: Jaxson Brown
# Organisation: Curtin University
# Last Modified: 2025-08-17
# -----------------------------------------------------------------------------

# FILE PURPOSE: Implements the functionality of a Human Machine Interface device (HMI)

import asyncio
import time
import logging
import utils
from flask import Flask, jsonify
from threading import Thread
from pymodbus.client import ModbusTcpClient, ModbusSerialClient
from pymodbus.server import ModbusTcpServer, ModbusSerialServer
from pymodbus.datastore import ModbusSequentialDataBlock, ModbusSlaveContext, ModbusServerContext

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logging.getLogger('werkzeug').setLevel(logging.ERROR)

app = Flask(__name__)

# global variables (only used for endpoints)
register_values = {}



# FUNCTION: init_inbound_cons
# PURPOSE:  Starts any tcp/rtu servers configured in the config file for inbound connections
async def init_inbound_cons(configs, context):
    server_tasks = []
    for connection in configs["inbound_connections"]:
        if connection["type"] == "tcp":            
            # start tcp server thread
            server_tasks.append(asyncio.create_task(utils.run_tcp_server(connection, context)))
        elif connection["type"] == "rtu":
            # start rtu slave thread
            server_tasks.append(asyncio.create_task(utils.run_rtu_slave(connection, context))) 
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
        time.sleep(0.75)
        if connection["type"] == "tcp":
            client = utils.run_tcp_client(connection)
            connections[connection["id"]] = client
        elif connection["type"] == "rtu":
            client = utils.run_rtu_master(connection)
            connections[connection["id"]] = client
    return connections



# FUNCTION: monitor
# PURPOSE:  A monitor thread to continuously read data from a defined and intialised connection
def monitor(value_config, monitor_configs, modbus_con, values):
    logging.info(f"Starting Monitor: {monitor_configs['id']}")
    interval = monitor_configs["interval"]
    value_type = monitor_configs["value_type"]
    out_address = monitor_configs["address"]
    count = monitor_configs["count"]

    while True:
        try:
            # select the correct function
            if value_type == "coil":
                response_values = modbus_con.read_coils(out_address-1, count).bits
                values["co"].setValues(value_config["address"], response_values)
            elif value_type == "discrete_input":
                response_values = modbus_con.read_discrete_inputs(out_address-1, count).bits
                values["di"].setValues(value_config["address"], response_values)
            elif value_type == "holding_register":
                response_values = modbus_con.read_holding_registers(out_address-1, count).registers
                values["hr"].setValues(value_config["address"], response_values)
            elif value_type == "input_register":
                response_values = modbus_con.read_input_registers(out_address-1, count).registers
                values["ir"].setValues(value_config["address"], response_values)
        except:
            logging.error("Error: couldn't read values")


        time.sleep(interval)



# FUNCTION: start_monitors
# PURPOSE:  Started all of the monitor threads. Note that more than one monitor can
#           utilise a single connection (but there must be a connection!).
def start_monitors(configs, outbound_cons, values):
    monitor_threads = []
    for monitor_config in configs["monitors"]:
        # get the outbound connection (Modbus object) for the monitor
        outbound_con_id = monitor_config["outbound_connection_id"]
        modbus_con = outbound_cons[outbound_con_id]

        # get the address of the internal register to write to
        value_config = {}
        if monitor_config["value_type"] == "coil":
            for co in configs["registers"]["coil"]:
                if co["id"] == monitor_config["id"]:
                    value_config = co
        elif monitor_config["value_type"] == "discrete_input":
            for di in configs["registers"]["discrete_input"]:
                if di["id"] == monitor_config["id"]:
                    value_config = di
        elif monitor_config["value_type"] == "holding_register":
            for hr in configs["registers"]["holding_register"]:
                if hr["id"] == monitor_config["id"]:
                    value_config = hr
        elif monitor_config["value_type"] == "input_register":
            for ir in configs["registers"]["input_register"]:
                if ir["id"] == monitor_config["id"]:
                    value_config = ir

        # start the monitor threads
        monitor_thread = Thread(target=monitor, args=(value_config, monitor_config, modbus_con, values), daemon=True)
        monitor_thread.start()

        monitor_threads.append(monitor_thread)
    return monitor_threads



# define the flask endpoint
@app.route("/registers", methods=['GET'])
def get_registers_route():
    global register_values
    return jsonify(register_values)


# define function to run flask in another thread
def flask_app(flask_app):
    flask_app.run(host="0.0.0.0", port=1111)


# FUNCTION: main
# PURPOSE:  The main execution
async def main():
    global register_values
    
    # retrieve configurations from the given JSON (will be in the same directory)
    configs = utils.retrieve_configs("config.json")
    logging.info(f"Starting HMI")

    # create slave context (by default will have all address ranges)
    co = ModbusSequentialDataBlock.create()
    di = ModbusSequentialDataBlock.create()
    hr = ModbusSequentialDataBlock.create()
    ir = ModbusSequentialDataBlock.create()
    slave_context = ModbusSlaveContext(co=co, di=di, hr=hr, ir=ir)
    context = ModbusServerContext(slaves=slave_context, single=True)

    # start any inbound connection servers (tcp, rtu or both) with the same context
    values = {"co": co, "di": di, "hr": hr, "ir": ir}
    inbound_cons = asyncio.create_task(init_inbound_cons(configs, context))

    # start any outbound connections
    outbound_cons = init_outbound_cons(configs)

    # start any configured monitors using the started outbound connections
    monitor_threads = start_monitors(configs, outbound_cons, values)

    # create a dictionary representing all register values
    register_values = utils.create_register_values_dict(configs)

    # start a thread to continously update the registers dictionary
    sync_registers = Thread(target=utils.update_register_values, args=(register_values, values), daemon=True)
    sync_registers.start()
    
    # start the flask endpoint
    flask_thread = Thread(target=flask_app, args=(app,), daemon=True)
    flask_thread.start()

    # block on all asyncio and threads
    await inbound_cons
    for monitor_thread in monitor_threads:
        monitor_thread.join()
    for outbound_con in outbound_cons.values():
        outbound_con.close()
    sync_registers.join()
    flask_thread.join()

    # block (useful if no threads are running for some reason)
    while True:
        time.sleep(1)


if __name__ == "__main__":
    asyncio.run(main())