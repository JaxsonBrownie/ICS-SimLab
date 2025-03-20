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
    print("Could not import logic for HIL component")

# FUNCTION: retrieve_configs
# PURPOSE:  Retrieves the JSON configs
def retrieve_configs(filename):
    with open(filename, "r") as config_file:
        content = config_file.read()
        configs = json.loads(content)
    return configs


# FUNCTION: database_interaction
# PURPOSE:  Handles writing the physical values into the SQLite database
def database_interaction(configs, physical_values):
    # connect to hardware SQLite database
    conn = sqlite3.connect("physical_interations.db")
    cursor = conn.cursor()
    table = configs["database"]["table"]

    while True:
        for physical_value in configs["database"]["physical_values"]:
            cursor.execute(f"""
                UPDATE {table}
                SET value = ?
                WHERE physical_value = ?
            """, (physical_values[physical_value['name']], physical_value['name']))
            conn.commit()

        #logging.info(physical_values[physical_value['name']])
        #logging.info(physical_value['name'])
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
        physical_values[value["name"]] = "s"

    # begin sensor simulation thread
    sensor_sim_thread = Thread(target=logic.logic, args=(physical_values, 1))
    sensor_sim_thread.daemon = True
    sensor_sim_thread.start()

    # begin the database writing thread
    database_thread = Thread(target=database_interaction, args=(configs, physical_values))
    database_thread.daemon = True
    database_thread.start()

    # wait for threads
    sensor_sim_thread.join()
    database_thread.join()


if __name__ == "__main__":
    asyncio.run(main())