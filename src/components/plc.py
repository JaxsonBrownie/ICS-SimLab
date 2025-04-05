#!/usr/bin/env python3

# FILE:     plc.py
# PURPOSE:  Implements the functionality of a PLC. The configurations are taken from
#           a JSON file called config.json.

import json
import asyncio
import time
import logging
from threading import Thread
from pymodbus.client import ModbusTcpClient, ModbusSerialClient
from pymodbus.server import ModbusTcpServer, ModbusSerialServer, StartSerialServer, StartTcpServer
from pymodbus.datastore import ModbusSequentialDataBlock, ModbusSlaveContext, ModbusServerContext
from pymodbus.exceptions import ModbusIOException

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

# here we import the defined logic
# the logic will always be in a python file called logic.py, which gets copied to the container
try:
    import logic # type: ignore
except ModuleNotFoundError:
    print("Could not import logic for PLC component")

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
def monitor(value_config, monitor_configs, modbus_con, values):
    print(f"Starting monitor: {monitor_configs['id']}")
    interval = monitor_configs["interval"]
    value_type = monitor_configs["value_type"]
    out_address = monitor_configs["address"]
    count = monitor_configs["count"]

    while True:
        try:
            # select the correct function
            if value_type == "coil":
                response_values = modbus_con.read_coils(out_address, count).bits
                values["co"].setValues(value_config["address"], response_values)
            elif value_type == "discrete_input":
                response_values = modbus_con.read_discrete_inputs(out_address, count).bits
                values["di"].setValues(value_config["address"], response_values)
            elif value_type == "holding_register":
                response_values = modbus_con.read_holding_registers(out_address, count).registers
                values["hr"].setValues(value_config["address"], response_values)
            elif value_type == "input_register":
                response_values = modbus_con.read_input_registers(out_address, count).registers
                values["ir"].setValues(value_config["address"], response_values)
        except:
            print("Error: couldn't read values")

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

# FUNCTION: get_controller_callbacks
# PURPOSE:  Returns a dictionary of callbacks to be used to write to 
#           write to their specific register.
# TODO: may get broken stuff because "reference vs values"
def get_controller_callbacks(configs, outbound_cons, output_reg_values):
    controller_callbacks = {}
    for controller_config in configs["controllers"]:
        # get outbound connection for the controller
        outbound_con_id = controller_config["outbound_connection_id"]
        modbus_con = outbound_cons[outbound_con_id]

        # create the callback writing function (remember modbus_con is the modbus connection object)
        if controller_config["value_type"] == "coil":
            # define a first class function that gets the correct out_reg_value and modbus writes it
            def write_value():
                print("CALLBACK PING")
                # find the output register to write from
                for output_reg in output_reg_values["coil"]:
                    if output_reg["id"] == controller_config["id"]:
                        # write to the modbus object
                        modbus_con.write_coil(address=controller_config["address"],
                                                #slave=controller_config["slave_id"], #TODO
                                                value=output_reg["value"])
            
            callback = write_value
            
        elif controller_config["value_type"] == "holding_register":
            def write_value():
                print("CALLBACK PING")
                # find the output register to write from
                for output_reg in output_reg_values["holding_register"]:
                    if output_reg["id"] == controller_config["id"]:
                        # write to the modbus object
                        modbus_con.write_register(address=controller_config["address"],
                                                #slave=controller_config["slave_id"],
                                                value=output_reg["value"])
            callback = write_value
        else:
            raise Exception("Trying to write to non-writable register")
        # put the writing callback function into the controller_callbacks dictionary (key is the controller id)
        controller_callbacks[controller_config["id"]] = callback
    return controller_callbacks


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
        register_values["coil"].append(
            {
                "address": co["address"],
                "count": co["count"],
                "io": co["io"],
                "id": co["id"],
                "value": False
            }
        )
    for di in configs["values"]["discrete_input"]:
        register_values["discrete_input"].append(
            {
                "address": di["address"],
                "count": di["count"],
                "io": di["io"],
                "id": di["id"],
                "value": False
            }
        )
    for hr in configs["values"]["holding_register"]:
        register_values["holding_register"].append(
            {
                "address": hr["address"],
                "count": hr["count"],
                "io": hr["io"],
                "id": hr["id"],
                "value": 0
            }
        )
    for ir in configs["values"]["input_register"]:
        register_values["input_register"].append(
            {
                "address": ir["address"],
                "count": ir["count"],
                "io": ir["io"],
                "id": ir["id"],
                "value": 0
            }
        )
    return register_values


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


# FUNCTION: main
# PURPOSE:  The main execution
async def main():
    # retrieve configurations from the given JSON (will be in the same directory)
    configs = retrieve_configs("config.json")
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

    # start any outbound connections, waiting 2 seconds to ensure connections are up
    outbound_cons = init_outbound_cons(configs)
    time.sleep(2)

    # start any configured monitors using the started outbound connections
    monitor_threads = start_monitors(configs, outbound_cons, values)

    # create a dictionary representing all register values
    register_values = create_register_values_dict(configs)

    # separate the register values into input and output registers
    input_reg_values, output_reg_values = separate_io_registers(register_values)

    # create a dictionary to store the controller callback functions (key is the controller id)
    controller_callbacks = get_controller_callbacks(configs, outbound_cons, output_reg_values)

    # start a thread to continously update the input registers dictionary
    sync_in_registers = Thread(target=update_register_values, args=(input_reg_values, values))
    sync_in_registers.daemon = True
    sync_in_registers.start()

    # start the logic thread, passing in the input registers, output registers, and modbus controlling callback functions
    logic_thread = Thread(target=logic.logic, args=(input_reg_values, output_reg_values, controller_callbacks))
    logic_thread.daemon = True
    logic_thread.start()

    # block on the inbound connection servers and outbound monitors
    await inbound_cons
    for monitor_thread in monitor_threads:
        monitor_thread.join()
    logic_thread.join()
    sync_in_registers.join()

    # close all outbound client connections
    for outbound_con in outbound_cons.values():
        outbound_con.close()
    
    # block (useful if no servers or monitors are made)
    while True:
        time.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())