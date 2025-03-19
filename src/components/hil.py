#!/usr/bin/env python3

# FILE: hil.py
# PURPOSE: Simulates the physical layer. Data is written to the SQLite database to represent physical data collection

import json
import asyncio
import sqlite3

# FUNCTION: retrieve_configs
# PURPOSE:  Retrieves the JSON configs
def retrieve_configs(filename):
    with open(filename, "r") as config_file:
        content = config_file.read()
        configs = json.loads(content)
    return configs


# FUNCTION: main
# PURPOSE:  The main execution
async def main():
    # connect to hardware SQLite database
    conn = sqlite3.connect("hardware_interactions.db")
    cursor = conn.cursor()

    # create a dictionary to represent the different physical values
    physical_values = {}

    # begin sensor simulation thread
    

    

if __name__ == "__main__":
    asyncio.run(main())