#!/usr/bin/env python3

# -----------------------------------------------------------------------------
# Project: Curtin ICS-SimLab
# File: ui.py
#
# Copyright (c) 2025 Jaxson Brown, Curtin University
#
# Licensed under the MIT License. You may obtain a copy of the License at:
#     https://opensource.org/licenses/MIT
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
# This work is supported by a Cross-Campus Cyber Security Research Project
# funded by **Curtin University**
#
# Author: Jaxson Brown
# Organisation: Curtin University
# Last Modified: 2025-08-17
# -----------------------------------------------------------------------------

# FILE PURPOSE: Creates a streamlit dashboard to view data from all components. Data
#               is fetched from other components using a RESTful API

import requests
import json
import time
import sqlite3
import streamlit as st
import pandas as pd
import altair as alt
                  
# FUNCTION: retrieve_configs
# PURPOSE:  Retrieves the JSON configs
def retrieve_configs(filename):
    with open(filename, "r") as config_file:
        content = config_file.read()
        configs = json.loads(content)
    return configs



# FUNCTION: get_component_info
# PURPOSE:  Returns all names and info for all the components in lists
def get_component_info(configs):
    hmi_info = {}
    plc_info = {}
    sensor_info = {}
    actuator_info = {}
    hil_info = {}

    if "hmis" in configs:
        for hmi in configs["hmis"]:
            hmi_info[hmi["name"]] = {
                "ip": hmi["network"]["ip"]
            }
            
    if "plcs" in configs:
        for plc in configs["plcs"]:
            plc_info[plc["name"]] = {
                "ip": plc["network"]["ip"]
            }

    if "sensors" in configs:
        for sensor in configs["sensors"]:
            sensor_info[sensor["name"]] = {
                "ip": sensor["network"]["ip"],
            }

    if "actuators" in configs:
        for actuator in configs["actuators"]:
            actuator_info[actuator["name"]] = {
                "ip": actuator["network"]["ip"],
            }

    if "hils" in configs:
        for hil in configs["hils"]:
            physical_values = []
            for physical_value in hil["physical_values"]:
                physical_values.append(physical_value["name"])
            hil_info[hil["name"]] = {
                "values": physical_values
            }

    return hmi_info, plc_info, sensor_info, actuator_info, hil_info



# FUNCTION: create_register_table_rows
# PURPOSE:  Builds up the table rows for the component registers
def create_register_table_rows(type, address, count, value, response):
    for register in response.values():
        type.append(register["type"])
        address.append(register["address"])
        count.append(register["count"])
        value.append(register["value"])



# FUNCTION: create_register_table
# PURPOSE:  Creates a dataframe for the component register table
def create_register_table(response):
    type = []
    address = []
    count = []
    value = []
    create_register_table_rows(type, address, count, value, response)
    dataframe = pd.DataFrame({
            "type": type,
            "address": address,
            "count": count,
            "value": value
        })
    return dataframe.astype(str)



# FUNCTION: main
# PURPOSE:  The main execution. Here we render everything to show on the web user interface.
def main():
    time.sleep(1)

    # render the streamlit application
    st.set_page_config(
        page_title="ICS Dashboard",
        layout="wide",
    )

    if 'config_loaded' not in st.session_state:
        # retrieve configurations from the given JSON (will be in the same directory)
        configs = retrieve_configs("config.json")

        # get all component info. for Modbus (name, ip), for physical (column_name)
        hmi_info, plc_info, sensor_info, actuator_info, hil_info = get_component_info(configs)
        st.session_state['config_loaded'] = True

    # render everything first  
    st.title("Industrial Control System Dashboard")

    # show system information
    col1, _, _, _ = st.columns(4)
    with col1:
        with st.container(border=True):
            st.subheader("Devices", divider="orange")
            st.write(f"Human Machine Interfaces (HMIs): {len(hmi_info)}")
            st.write(f"Programmable Logic Controllers (PLCs): {len(plc_info)}")
            st.write(f"Sensors: {len(sensor_info)}")
            st.write(f"Actuators: {len(actuator_info)}")
    st.divider()

    # show register devices
    st.header("Human Machine Interfaces", divider="orange")
    col1, col2, col3, col4 = st.columns(4)
    columns = {1: col1, 2: col2, 3: col3, 4: col4}
    column_switcher = 1
    st_hmis = {}
    for hmi in hmi_info:
        with columns[column_switcher].container():
            st.markdown(f"##### {hmi}")
            st_hmis[hmi] = st.empty()
            column_switcher = (column_switcher % len(columns)) + 1
            
    st.header("Programmable Logic Controllers", divider="orange")
    col1, col2, col3, col4 = st.columns(4)
    columns = {1: col1, 2: col2, 3: col3, 4: col4}
    column_switcher = 1
    st_plcs = {}
    for plc in plc_info:
        with columns[column_switcher].container():
            st.markdown(f"##### {plc}")
            st_plcs[plc] = st.empty()
            column_switcher = (column_switcher % len(columns)) + 1

    st.header("Sensors", divider="orange")
    col1, col2, col3, col4 = st.columns(4)
    columns = {1: col1, 2: col2, 3: col3, 4: col4}
    column_switcher = 1
    st_sensors = {}
    for sensor in sensor_info:
        with columns[column_switcher].container():
            st.markdown(f"##### {sensor}")
            st_sensors[sensor] = st.empty()
            column_switcher = (column_switcher % len(columns)) + 1
    
    st.header("Actuators", divider="orange")
    col1, col2, col3, col4 = st.columns(4)
    columns = {1: col1, 2: col2, 3: col3, 4: col4}
    column_switcher = 1
    st_actuators = {}
    for actuator in actuator_info:
        with columns[column_switcher].container():
            st.markdown(f"##### {actuator}")
            st_actuators[actuator] = st.empty()
            column_switcher = (column_switcher % len(columns)) + 1
    
    # create hardware in the loop graphs
    st.divider()
    st.header("Hardware-in-the-Loops") 
    st.subheader("Physical Values") 
    hils = {}
    graphs = {}

    col1, col2, col3 = st.columns(3)
    columns = {1: col1, 2: col2, 3: col3}
    column_switcher = 1

    for hil in hil_info.values():
        for physical_value in hil["values"]:
            with columns[column_switcher].container(border=True):
                hils[physical_value] = st.empty()
                graphs[physical_value] = st.empty()
            column_switcher = (column_switcher % len(columns)) + 1

    # have a single event loop for API polling (streamlit sucks for multi threaded stuff)
    while True:
        try:
            # poll hmi
            for hmi, info in hmi_info.items():
                hmi_response = requests.get(f"http://{info['ip']}:1111/registers").json()
                hmi_table = create_register_table(hmi_response)
                st_hmis[hmi].dataframe(hmi_table)
            
            # poll plc
            for plc, info in plc_info.items():
                plc_response = requests.get(f"http://{info['ip']}:1111/registers").json()
                plc_table = create_register_table(plc_response)
                st_plcs[plc].dataframe(plc_table)

            # poll sensor
            for sensor, info in sensor_info.items():
                sensor_response = requests.get(f"http://{info['ip']}:1111/registers").json()
                sensor_table = create_register_table(sensor_response)
                st_sensors[sensor].dataframe(sensor_table)

            # poll actuator
            for actuator, info in actuator_info.items():
                actuator_response = requests.get(f"http://{info['ip']}:1111/registers").json()
                actuator_table = create_register_table(actuator_response)
                st_actuators[actuator].dataframe(actuator_table)
        except Exception:
            # if an api endpoint cannot be reached, just wait until it can
            time.sleep(1)

        # poll the physical hil (through the SQLite3 database)
        conn = sqlite3.connect("physical_interactions.db")
        for hil in hil_info.values():
            for physical_value in hil["values"]:
                table = physical_value
                df = pd.read_sql_query(f"SELECT value FROM {table} ORDER BY timestamp DESC LIMIT 1", conn)
                df["physical_value"] = table
                hils[physical_value].dataframe(df, column_order=["physical_value", "value"])

                df = pd.read_sql_query(f"SELECT timestamp, value FROM {table} ORDER BY timestamp DESC LIMIT 100", conn)
                df["timestamp"] = pd.to_datetime(df["timestamp"])
                df["value"] = pd.to_numeric(df["value"])
                df_grouped = df.groupby('timestamp')[["value"]].mean()
                
                chart = alt.Chart(df_grouped.reset_index(), height=325).mark_line().encode(
                    x=alt.X("timestamp:T", title="Time", axis=alt.Axis(format="%M:%S")),
                    y=alt.Y("value:Q", title="Value"),
                )

                graphs[physical_value].altair_chart(chart)
        conn.close()

        time.sleep(1)


if __name__ == "__main__":
    main()