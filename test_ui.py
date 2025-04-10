#!/usr/bin/env python3

# FILE:     ui.py
# PURPOSE:  Creates a streamlit dashboard to view data from all components. Data
#           is fetched from other components using a RESTful API

import requests
import json
import logging
import threading
import time
import streamlit as st


# global variables for UI displaying
plc_data = {}


# FUNCTION: retrieve_configs
# PURPOSE:  Retrieves the JSON configs
def retrieve_configs(filename):
    with open(filename, "r") as config_file:
        content = config_file.read()
        configs = json.loads(content)
    return configs


# FUNCTION: get_ips
# PURPOSE:  Returns all ips for all the components
def get_ips(configs):
    plc_ips = []
    sensor_ips = []
    actuator_ips = []

    for plc in configs["plcs"]:
        plc_ips.append({
            "name": plc["name"], 
            "ip": plc["network"]["ip"]
            })
    for sensor in configs["sensors"]:
        sensor_ips.append(sensor["network"]["ip"])
    for actuator in configs["actuators"]:
        actuator_ips.append(actuator["network"]["ip"])
        
    return plc_ips, sensor_ips, actuator_ips


# FUNCTION: poll_url
# PURPOSE:  Polls the given URL every interval
def poll_url(url, data_dict, key, interval=1):
    response = ""
    while True:
        try:
            response = requests.get(url)
        except Exception as e:
            response = f"Error: {e}"
        data_dict[key] = response

        print(response)
        time.sleep(interval)


# FUNCTION: main
# PURPOSE:  The main execution
def main():
    # retrieve configurations from the given JSON (will be in the same directory)
    configs = retrieve_configs("config/smart_grid_simulation.json")
    logging.info(f"Booting the User Interface container")

    # get all ips
    plc_ips, sensor_ips, actuator_ips = get_ips(configs)

    # ensure that the threads are created only once
    if "polling_started" not in st.session_state:
        # create a thread to poll all the PLCs
        for plc_ip in plc_ips:
            plc_thread = threading.Thread(target=poll_url, args=(f"{plc_ip['ip']}:1111", plc_data, plc_ip["name"]))
            plc_thread.start()


    # render the streamlit application
    st.set_page_config(
        page_title="ICS Dashboard",
        layout="wide",
    )
    
    st.title("Industrial Control System Dashboard")

    st.header("Overall Statistics")
    st.write(f"Number of PLCs: {len(plc_ips)}")
    st.write(f"Number of Sensors: {len(sensor_ips)}")
    st.write(f"Number of Actuators: {len(actuator_ips)}")

    st.header("Programmable Logic Controllers")
    


    
if __name__ == "__main__":
    main()