#!/usr/bin/env python3

# FILE:     sensor.py
# PURPOSE:  Simulates a sensor. Takes input from a simulated physical process.

import json
import asyncio
import sqlite3
import logging
import time
from threading import Thread
from pymodbus.server import ModbusTcpServer, ModbusSerialServer
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


# FUNCTION: start_sensor
# PURPOSE:  Starts a process to read sensor data from SQLite specific to this sensor.
#           The column is a TEXT datatype to allow for generic inputs. The input "values"
#           is a dictonary with ModbusSequentialDataBlock values, corresponding to co
#           di, hr, and ir as keys.
def start_sensor(configs, values):
    # connect to hardware SQLite database
    conn = sqlite3.connect("physical_interations.db")
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
                values["co"].setValues(address+1, int(value[0]))
        for di in configs["values"]["discrete_input"]:
            address = di["address"]

            cursor.execute(f"SELECT value FROM {table} WHERE physical_value = ?", (di['physical_value'],))
            value = cursor.fetchone()
            conn.commit()

            if value and value[0] != "":
                values["di"].setValues(address+1, int(value[0]))
        for hr in configs["values"]["holding_register"]:
            address = hr["address"]

            cursor.execute(f"SELECT value FROM {table} WHERE physical_value = ?", (hr['physical_value'],))
            value = cursor.fetchone()
            conn.commit()

            if value and value[0] != "":
                values["hr"].setValues(address+1, int(value[0]))
        for ir in configs["values"]["input_register"]:
            address = ir["address"]

            cursor.execute(f"SELECT value FROM {table} WHERE physical_value = ?", (ir['physical_value'],))
            value = cursor.fetchone()
            conn.commit()

            if value and value[0] != "":
                values["ir"].setValues(address+1, int(value[0]))

        time.sleep(0.2)


# FUNCTION: main
# PURPOSE:  The main execution
async def main():
    # retrieve configurations from the given JSON (will be in the same directory)
    configs = retrieve_configs("config.json")
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
    
    # start the sensor reading thread
    sensor_thread = Thread(target=start_sensor, args=(configs, values))
    sensor_thread.daemon = True
    sensor_thread.start()

    # await tasks
    await server_task


if __name__ == "__main__":
    asyncio.run(main())