#!/usr/bin/env python3

# FILE:     actuator.py
# PURPOSE:  Simulates an actuators. Can read and write to a HIL physical environment.

import logging
import asyncio
import time
import sqlite3
import utils
from flask import Flask, jsonify
from threading import Thread
from pymodbus.datastore import ModbusSequentialDataBlock, ModbusSlaveContext, ModbusServerContext

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logging.getLogger('werkzeug').setLevel(logging.ERROR)

app = Flask(__name__)

# global variables (only used for endpoints)
register_values = {}



# FUNCTION: start_servers
# PURPOSE:  Starts any tcp/rtu servers configured in the config file
async def start_servers(configs, context):
    tasks = []
    for connection in configs["inbound_connections"]:
        if connection["type"] == "tcp":            
            # start tcp server thread
            tasks.append(asyncio.create_task(utils.run_tcp_server(connection, context)))
        elif connection["type"] == "rtu":
            # start rtu slave thread
            tasks.append(asyncio.create_task(utils.run_rtu_slave(connection, context)))        
    for task in tasks:
        await task



# FUNCTION: start_actuator
# PURPOSE:  Starts a process to write data to an SQLite column specific to this actuator.
def start_actuator(configs, values):
    # connect to hardware SQLite database
    conn = sqlite3.connect("physical_interactions.db")
    cursor = conn.cursor()

    while True:
        # gets values for all value types from the physical databases
        value = ""
        for co in configs["registers"]["coil"]:
            address = co["address"]
            count = co["count"]
            table = co["physical_value"]
            value = values["co"].getValues(address, count)[0]

            cursor.execute(f"INSERT INTO {table}(value) VALUES(?)", (value,))
            value = cursor.fetchone()
            conn.commit()
        for di in configs["registers"]["discrete_input"]:
            address = di["address"]
            count = di["count"]
            table = di["physical_value"]
            value = values["di"].getValues(address, count)[0]

            cursor.execute(f"INSERT INTO {table}(value) VALUES(?)", (value,))
            value = cursor.fetchone()
            conn.commit()
        for hr in configs["registers"]["holding_register"]:
            address = hr["address"]
            count = hr["count"]
            table = hr["physical_value"]
            value = values["hr"].getValues(address, count)[0]

            cursor.execute(f"INSERT INTO {table}(value) VALUES(?)", (value,))
            value = cursor.fetchone()
            conn.commit()
        for ir in configs["registers"]["input_register"]:
            address = ir["address"]
            count = ir["count"]
            table = ir["physical_value"]
            value = values["ir"].getValues(address, count)[0]

            cursor.execute(f"INSERT INTO {table}(value) VALUES(?)", (value,))
            value = cursor.fetchone()
            conn.commit()

        time.sleep(0.1)



# define the flask endpoint
@app.route("/registers", methods=['GET'])
def get_registers_route():
    global register_values
    return jsonify(register_values)

# define function to run flask in another thread
def flask_app(flask_app):
    flask_app.run(host="0.0.0.0", port=1111)

# FUNCTION: main
# PURPOSE:  Main execution
async def main():
    global register_values
    
    # retrieve configurations from the given JSON (will be in the same directory)
    configs = utils.retrieve_configs("config.json")
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
    
    # create a dictionary to represent the different register values
    register_values = utils.create_register_values_dict(configs)

    # start the actuator writing thread
    actuator_thread = Thread(target=start_actuator, args=(configs, values), daemon=True)
    actuator_thread.start()

    # start a thread to constantly update the "register_values" dictionary with the actual modbus register values
    sync_registers = Thread(target=utils.update_register_values, args=(register_values, values), daemon=True)
    sync_registers.start()

    # start the flask endpoint
    flask_thread = Thread(target=flask_app, args=(app,), daemon=True)
    flask_thread.start()

    # await tasks and threads
    await server_task
    actuator_thread.join()
    sync_registers.join()
    #logic_thread.join()
    flask_thread.join()


if __name__ == "__main__":
    asyncio.run(main())