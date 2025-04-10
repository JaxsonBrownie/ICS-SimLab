#!/usr/bin/env python3

# FILE:     ui.py
# PURPOSE:  Creates a streamlit dashboard to view data from all components. Data
#           is fetched from other components using a RESTful API

import requests
import json
import logging
import threading
import time
import asyncio
import streamlit as st
import pandas as pd

# FUNCTION: retrieve_configs
# PURPOSE:  Retrieves the JSON configs
def retrieve_configs(filename):
    with open(filename, "r") as config_file:
        content = config_file.read()
        configs = json.loads(content)
    return configs


# FUNCTION: get_component_info
# PURPOSE:  Returns all names and info for all the components in a dictionary
def get_component_info(configs):
    plc_info = []
    sensor_info = []
    actuator_info = []

    for plc in configs["plcs"]:
        plc_info.append({
            "name": plc["name"], 
            "ip": plc["network"]["ip"]
            })
    for sensor in configs["sensors"]:
        sensor_info.append({
            "name": sensor["name"],
            "ip": sensor["network"]["ip"],
        })
    for actuator in configs["actuators"]:
        actuator_info.append({
            "name": actuator["name"],
            "ip": actuator["network"]["ip"],
        })
    return plc_info, sensor_info, actuator_info


# FUNCTION: create_table_rows
# PURPOSE:  Builds up the table rows for the component registers
def create_table_rows(type, address, count, value, response):
    for co in response["coil"]:
        type.append("coil")
        address.append(co["address"])
        count.append(co["count"])
        value.append(co["value"])
    for di in response["discrete_input"]:
        type.append("discrete_input")
        address.append(di["address"])
        count.append(di["count"])
        value.append(di["value"])
    for ir in response["input_register"]:
        type.append("input_register")
        address.append(ir["address"])
        count.append(ir["count"])
        value.append(ir["value"])
    for hr in response["holding_register"]:
        type.append("holding_register")
        address.append(hr["address"])
        count.append(hr["count"])
        value.append(hr["value"])


# FUNCTION: create_table
# PURPOSE:  Creates a dataframe for the component register table
def create_table(response):
    type = []
    address = []
    count = []
    value = []
    create_table_rows(type, address, count, value, response)
    dataframe = pd.DataFrame({
            "type": type,
            "address": address,
            "count": count,
            "value": value
        })
    return dataframe.astype(str)


# FUNCTION: main
# PURPOSE:  The main execution
async def main():
    time.sleep(1)

    # render the streamlit application
    st.set_page_config(
        page_title="ICS Dashboard",
        layout="wide",
    )

    if 'config_loaded' not in st.session_state:
        # retrieve configurations from the given JSON (will be in the same directory)
        configs = retrieve_configs("config.json")

        # get all component info (name: ip)
        plc_info, sensor_info, actuator_info = get_component_info(configs)
        st.session_state['config_loaded'] = True

    # render everything first  
    st.title("Industrial Control System Dashboard")

    st.header("Overall Statistics")
    st.write(f"Number of PLCs: {len(plc_info)}")
    st.write(f"Number of Sensors: {len(sensor_info)}")
    st.write(f"Number of Actuators: {len(actuator_info)}")

    st.header("Programmable Logic Controllers")
    plcs = {}
    for plc in plc_info:
        plcs[plc["name"]] = st.empty() 

    st.header("Sensors")
    sensors = {}
    for sensor in sensor_info:
        sensors[sensor["name"]] = st.empty()  
    
    st.header("Actuators")  
    actuators = {}
    for actuator in actuator_info:
        actuators[actuator["name"]] = st.empty() 

    # have a single event loop for API polling (streamlit sucks for multi threaded stuff)
    while True:
        for plc in plc_info:
            plc_response = requests.get(f"http://{plc['ip']}:1111/registers").json()
            plc_table = create_table(plc_response)
            plcs[plc["name"]].table(plc_table)

        for sensor in sensor_info:
            sensor_response = requests.get(f"http://{sensor['ip']}:1111/registers").json()
            sensor_table = create_table(sensor_response)
            sensors[sensor["name"]].table(sensor_table)

        for actuator in actuator_info:
            actuator_response = requests.get(f"http://{actuator['ip']}:1111/registers").json()
            actuator_table = create_table(actuator_response)
            actuators[actuator["name"]].table(actuator_table)

        time.sleep(1)


if __name__ == "__main__":
    asyncio.run(main())