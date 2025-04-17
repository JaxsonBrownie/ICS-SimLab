#!/usr/bin/env python3

# FILE: hil.py
# PURPOSE: Simulates the physical layer. Data is written to the SQLite database to represent physical data collection

import json
import asyncio
import sqlite3
import logging
import time
from threading import Thread

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

# here we import the defined logic
# the logic will always be in a python file called logic.py, which gets copied to the container
try:
    import logic # type: ignore
except ModuleNotFoundError:
    logging.error("Could not import logic for HIL component")

# FUNCTION: retrieve_configs
# PURPOSE:  Retrieves the JSON configs
def retrieve_configs(filename):
    with open(filename, "r") as config_file:
        content = config_file.read()
        configs = json.loads(content)
    return configs


# FUNCTION: database_interaction
# PURPOSE:  Handles writing the physical values into the SQLite database. Only used with output
#           interactions.
def database_interaction(configs, physical_values):
    # connect to hardware SQLite database
    conn = sqlite3.connect("physical_interations.db")
    cursor = conn.cursor()
    table = configs["database"]["table"]

    while True:
        for physical_value in configs["database"]["physical_values"]:
            if physical_value["io"] == "output":
                cursor.execute(f"""
                    UPDATE {table}
                    SET value = ?
                    WHERE physical_value = ?
                """, (physical_values[physical_value['name']], physical_value['name']))
                conn.commit()
        time.sleep(0.1)


# FUNCTION: monitor_physical_inputs
# PURPOSE:  Monitors physical database interactions for input interactions.
def monitor_physical_inputs(configs, physical_values):
    # connect to hardware SQLite database
    conn = sqlite3.connect("physical_interations.db")
    cursor = conn.cursor()
    table = configs["database"]["table"]

    while True:
        for physical_value in configs["database"]["physical_values"]:
            if physical_value["io"] == "input":
                cursor.execute(f"""
                    SELECT value
                    FROM {table}
                    WHERE physical_value = ?
                """, (physical_value['name'],))
                value = cursor.fetchone()
                conn.commit()

                if value and value[0] != "":
                    physical_values[physical_value['name']] = int(float(value[0]))
        time.sleep(0.1)


# FUNCTION: main
# PURPOSE:  The main execution
async def main():
    configs = retrieve_configs("config.json")
    logging.info(f"Starting HIL")

    # create a dictionary to represent the different physical values
    physical_values = {}
    for value in configs["database"]["physical_values"]:
        # initialise all physical values to just be an empty string (the key matters more)
        physical_values[value["name"]] = ""

    # begin physical logic simulation thread
    logic_thread = Thread(target=logic.logic, args=(physical_values, 0.2))
    logic_thread.daemon = True
    logic_thread.start()

    # begin the database output writing thread
    db_in_thread = Thread(target=database_interaction, args=(configs, physical_values))
    db_in_thread.daemon = True
    db_in_thread.start()

    # begin database input reading thread
    db_out_thread = Thread(target=monitor_physical_inputs, args=(configs, physical_values))
    db_out_thread.daemon = True
    db_out_thread.start()

    # wait for threads
    logic_thread.join()
    db_in_thread.join()
    db_out_thread.join()
    

if __name__ == "__main__":
    asyncio.run(main())