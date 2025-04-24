#!/usr/bin/env python3

# FILE:     plc.py
# PURPOSE:  Implements the functionality of a PLC. The configurations are taken from
#           a JSON file called config.json.

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

# here we import the defined logic
# the logic will always be in a python file called logic.py, which gets copied to the container
try:
    import logic # type: ignore
except ModuleNotFoundError:
    logging.error("Could not import logic for PLC component")



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
        # pause for each connections to wait for corresponding input server to start
        # TODO: optimise somehow (make a system that waits for all containers to boot up)
        time.sleep(0.5)
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
    logging.debug(f"Starting Monitor: {monitor_configs['id']}")
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
            for co in configs["values"]["coil"]:
                if co["id"] == monitor_config["id"]:
                    value_config = co
        elif monitor_config["value_type"] == "discrete_input":
            for di in configs["values"]["discrete_input"]:
                if di["id"] == monitor_config["id"]:
                    value_config = di
        elif monitor_config["value_type"] == "holding_register":
            for hr in configs["values"]["holding_register"]:
                if hr["id"] == monitor_config["id"]:
                    value_config = hr
        elif monitor_config["value_type"] == "input_register":
            for ir in configs["values"]["input_register"]:
                if ir["id"] == monitor_config["id"]:
                    value_config = ir

        # start the monitor threads
        monitor_thread = Thread(target=monitor, args=(value_config, monitor_config, modbus_con, values))
        monitor_thread.daemon = True
        monitor_thread.start()

        monitor_threads.append(monitor_thread)
    return monitor_threads



# FUNCTION: make_writing_callback
# PURPOSE:  Function that creates a first class function callback (outside of scope) to be
#           called when a value needs to be written
def make_writing_callback(configs, controller_config, output_reg_values, modbus_con, values):
    def write_value():
        outbound_con_id = controller_config["outbound_connection_id"]

        if controller_config["value_type"] == "coil":
            # get the PLC value to write to
            for coil in configs["values"]["coil"]:
                if coil["id"] == controller_config["id"]:
                    plc_coil = coil

            # find the output register to write from
            for output_reg in output_reg_values["coil"]:
                if output_reg["id"] == controller_config["id"]:
                    # write to the modbus object
                    modbus_con.write_coil(address=controller_config["address"]-1,
                                            #slave=controller_config["slave_id"], #TODO
                                            value=output_reg["value"])
                    logging.debug(f"Writing to controller {outbound_con_id}, to address {controller_config['address']} value {output_reg['value']}")
                    # write to the PLCs memory as well 
                    values["co"].setValues(plc_coil["address"], output_reg["value"])

        elif controller_config["value_type"] == "holding_register":
            # get the PLC value to write to
            for hr in configs["values"]["holding_register"]:
                if hr["id"] == controller_config["id"]:
                    plc_hr = hr 

                # find the output register to write from
                for output_reg in output_reg_values["holding_register"]:
                    if output_reg["id"] == controller_config["id"]:
                        # write to the modbus object
                        modbus_con.write_register(address=controller_config["address"]-1,
                                                #slave=controller_config["slave_id"],
                                                value=output_reg["value"])
                        logging.debug(f"Writing to controller {outbound_con_id}, to address {controller_config['address']} value {output_reg['value']}")
                        # write to the PLCs memory as well 
                        values["hr"].setValues(plc_hr["address"], output_reg["value"])
        else:
            raise Exception("Trying to write to non-writable register")
    return write_value


# FUNCTION: get_controller_callbacks
# PURPOSE:  Returns a dictionary of callbacks to be used to write to 
#           their specific register.
def get_controller_callbacks(configs, outbound_cons, output_reg_values, values):
    controller_callbacks = {}
    for controller_config in configs["controllers"]:
        # get outbound connection for the controller
        outbound_con_id = controller_config["outbound_connection_id"]
        modbus_con = outbound_cons[outbound_con_id]

        # define a first class function that gets the correct out_reg_value and modbus writes it
        callback = make_writing_callback(configs, controller_config, output_reg_values, modbus_con, values)
    
        # put the writing callback function into the controller_callbacks dictionary (key is the controller id)
        controller_callbacks[controller_config["id"]] = callback
    return controller_callbacks



# FUNCTION: separate_io_registers
# PURPOSE:  Takes in a register_values dictionary and separates the registers based
#           on whether they are input or output registers. Returns two new
#           dictionaries
def separate_io_registers(register_values):
    input_registers = {}
    input_registers["coil"] = []
    input_registers["discrete_input"] = []
    input_registers["holding_register"] = []
    input_registers["input_register"] = []

    output_registers = {}
    output_registers["coil"] = []
    output_registers["discrete_input"] = []
    output_registers["holding_register"] = []
    output_registers["input_register"] = []
    
    for co in register_values["coil"]:
        if co["io"] == "input":
            input_registers["coil"].append(co)
        elif co["io"] == "output":
            output_registers["coil"].append(co)
    for di in register_values["discrete_input"]:
        if di["io"] == "input":
            input_registers["discrete_input"].append(di)
        elif di["io"] == "output":
            output_registers["discrete_input"].append(di)
    for hr in register_values["holding_register"]:
        if hr["io"] == "input":
            input_registers["holding_register"].append(hr)
        elif hr["io"] == "output":
            output_registers["holding_register"].append(hr)
    for ir in register_values["input_register"]:
        if ir["io"] == "input":
            input_registers["input_register"].append(ir)
        elif ir["io"] == "output":
            output_registers["input_register"].append(ir)
    
    return input_registers, output_registers


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
    logging.info(f"Starting PLC")

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

    # separate the register values into input and output registers
    input_reg_values, output_reg_values = separate_io_registers(register_values)

    # create a dictionary to store the controller callback functions (key is the controller id)
    controller_callbacks = get_controller_callbacks(configs, outbound_cons, output_reg_values, values)

    # start a thread to continously update the input and output registers dictionaries
    sync_in_registers = Thread(target=utils.update_register_values, args=(input_reg_values, values), daemon=True)
    sync_in_registers.start()
    sync_out_registers = Thread(target=utils.update_register_values, args=(output_reg_values, values), daemon=True)
    sync_out_registers.start()

    # start the logic thread, passing in the input registers, output registers, and modbus controlling callback functions
    logic_thread = Thread(target=logic.logic, args=(input_reg_values, output_reg_values, controller_callbacks), daemon=True)
    logic_thread.start()
    
    # start the flask endpoint
    flask_thread = Thread(target=flask_app, args=(app,), daemon=True)
    flask_thread.start()

    # block on the asyncio and threads
    await inbound_cons
    for monitor_thread in monitor_threads:
        monitor_thread.join()
    for outbound_con in outbound_cons.values():
        outbound_con.close()
    logic_thread.join()
    sync_in_registers.join()
    sync_out_registers.join()
    flask_thread.join()
    
    # block (useful if no servers or monitors are made)
    while True:
        time.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())