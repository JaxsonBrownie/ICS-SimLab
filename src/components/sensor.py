#!/usr/bin/env python3

# FILE:     sensor.py
# PURPOSE:  Simulates a sensor. Takes input from a simulated physical process.

import json
import asyncio
import sqlite3
import logging
import time
import utils
from flask import Flask, jsonify
from threading import Thread
from pymodbus.server import ModbusTcpServer, ModbusSerialServer
from pymodbus.datastore import ModbusSequentialDataBlock, ModbusSlaveContext, ModbusServerContext

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logging.getLogger('werkzeug').setLevel(logging.ERROR)

app = Flask(__name__)

# global values (only used for Flask endpoints)
register_values = {}


# FUNCTION: run_tcp_server
# PURPOSE:  An asynchronous function to be used to start a modbus tcp server
async def run_tcp_server(connection, context):
    # bind to all interfaces of the container
    tcp_server = ModbusTcpServer(context=context, address=("0.0.0.0", connection["port"]), ) 
    logging.info("Starting TCP Server")
    await tcp_server.serve_forever()


# FUNCTION: run_rtu_slave
# PURPOSE:  An asynchronous function to use for modbus rtu server
async def run_rtu_slave(connection, context):
    rtu_slave = ModbusSerialServer(context=context, port=connection["comm_port"], baudrate=9600, timeout=1)
    logging.info(f"Starting RTU Slave. Port: {connection['comm_port']}")
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


# FUNCTION: start_sensor
# PURPOSE:  Starts a process to read sensor data from SQLite specific to this sensor.
#           The column is a TEXT datatype to allow for generic inputs. The input "values"
#           is a dictonary with ModbusSequentialDataBlock values, corresponding to co
#           di, hr, and ir as keys.
def start_sensor(configs, values):
    # connect to hardware SQLite database
    conn = sqlite3.connect("physical_interactions.db")
    cursor = conn.cursor()
    table = configs["database"]["table"]

    while True:
        # gets values for all value types from the physical databases
        value = ""
        for co in configs["values"]["coil"]:
            address = co["address"]

            cursor.execute(f"SELECT value FROM {table} WHERE physical_value = ?", (co['physical_value'],))
            value = cursor.fetchone()
            conn.commit()

            if value and value[0] != "":
                values["co"].setValues(address, int(float(value[0])))
        for di in configs["values"]["discrete_input"]:
            address = di["address"]

            cursor.execute(f"SELECT value FROM {table} WHERE physical_value = ?", (di['physical_value'],))
            value = cursor.fetchone()
            conn.commit()

            if value and value[0] != "":
                values["di"].setValues(address, int(float(value[0])))
        for hr in configs["values"]["holding_register"]:
            address = hr["address"]

            cursor.execute(f"SELECT value FROM {table} WHERE physical_value = ?", (hr['physical_value'],))
            value = cursor.fetchone()
            conn.commit()

            if value and value[0] != "":
                values["hr"].setValues(address, int(float(value[0])))
        for ir in configs["values"]["input_register"]:
            address = ir["address"]

            cursor.execute(f"SELECT value FROM {table} WHERE physical_value = ?", (ir['physical_value'],))
            value = cursor.fetchone()
            conn.commit()

            if value and value[0] != "":
                values["ir"].setValues(address, int(float(value[0])))

        time.sleep(0.2)



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
    logging.info(f"Starting Sensor")

    # create slave context (by default will have all address ranges)
    co = ModbusSequentialDataBlock.create()
    di = ModbusSequentialDataBlock.create()
    hr = ModbusSequentialDataBlock.create()
    ir = ModbusSequentialDataBlock.create()
    slave_context = ModbusSlaveContext(co=co, di=di, hr=hr, ir=ir)
    context = ModbusServerContext(slaves=slave_context, single=True)

    # start any configured servers (tcp, rtu or both) with the same context
    values = {"co": co, "di": di, "hr": hr, "ir": ir}
    server_task = start_servers(configs, context)

    # create a dictionary representing all register values
    register_values = utils.create_register_values_dict(configs)

    # start the sensor reading thread
    sensor_thread = Thread(target=start_sensor, args=(configs, values), daemon=True)
    sensor_thread.start()

    # start a thread to continously update the registers dictionary
    sync_registers = Thread(target=utils.update_register_values, args=(register_values, values), daemon=True)
    sync_registers.start()

    # start the flask endpoint
    flask_thread = Thread(target=flask_app, args=(app,), daemon=True)
    flask_thread.start()

    # await tasks
    await server_task
    sync_registers.join()
    flask_thread.join()


if __name__ == "__main__":
    asyncio.run(main())