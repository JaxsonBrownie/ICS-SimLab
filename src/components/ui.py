#!/usr/bin/env python3

# FILE:     ui.py
# PURPOSE:  Creates a streamlit dashboard to view data from all components. Data
#           is fetched from other components using a RESTful API

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
    hmi_info = []
    plc_info = []
    sensor_info = []
    actuator_info = []
    hil_info = []

    if "hmis" in configs:
        for hmi in configs["hmis"]:
            hmi_info.append({
                "name": hmi["name"], 
                "ip": hmi["network"]["ip"]
                })
            
    if "plcs" in configs:
        for plc in configs["plcs"]:
            plc_info.append({
                "name": plc["name"], 
                "ip": plc["network"]["ip"]
                })
    if "sensors" in configs:
        for sensor in configs["sensors"]:
            sensor_info.append({
                "name": sensor["name"],
                "ip": sensor["network"]["ip"],
            })
    if "actuators" in configs:
        for actuator in configs["actuators"]:
            actuator_info.append({
                "name": actuator["name"],
                "ip": actuator["network"]["ip"],
            })
    if "hils" in configs:
        for hil in configs["hils"]:
            physical_values = []
            for physical_value in hil["physical_values"]:
                physical_values.append(physical_value["name"])
            hil_info.append({
                "name": hil["name"],
                "values": physical_values
            })

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

    st.header("Overall Statistics")
    st.write(f"Number of Human Machine Interfaces (HMIs): {len(hmi_info)}")
    st.write(f"Number of Programmable Logic Controllers (PLCs): {len(plc_info)}")
    st.write(f"Number of Sensors: {len(sensor_info)}")
    st.write(f"Number of Actuators: {len(actuator_info)}")

    st.divider()
    st.header("Human Machine Interfaces")
    st.subheader("Input + Output Registers")
    hmis = {}
    for hmi in hmi_info:
        hmis[hmi["name"]] = st.empty() 

    st.divider()
    st.header("Programmable Logic Controllers")
    st.subheader("Input + Output Registers")
    plcs = {}
    for plc in plc_info:
        plcs[plc["name"]] = st.empty() 

    st.divider()
    st.header("Sensors")
    st.subheader("Input Registers")
    sensors = {}
    for sensor in sensor_info:
        sensors[sensor["name"]] = st.empty()  
    
    st.divider()
    st.header("Actuators") 
    st.subheader("Output Registers") 
    actuators = {}
    for actuator in actuator_info:
        actuators[actuator["name"]] = st.empty()
    
    st.divider()
    st.header("Hardware-in-the-Loops") 
    st.subheader("Physical Values") 
    hils = {}
    graphs = {}

    col1, col2 = st.columns(2, border=True)
    column_switcher = "col1"

    for hil in hil_info:
        for physical_value in hil["values"]:

            if column_switcher == "col1":
                hils[physical_value] = col1.empty()
                graphs[physical_value] = col1.empty() 
                col1.divider()
                column_switcher = "col2"
            elif column_switcher == "col2":
                hils[physical_value] = col2.empty()
                graphs[physical_value] = col2.empty()
                col2.divider()
                column_switcher = "col1"

    # have a single event loop for API polling (streamlit sucks for multi threaded stuff)
    while True:
        # poll hmi
        for hmi in hmi_info:
            hmi_response = requests.get(f"http://{hmi['ip']}:1111/registers").json()
            hmi_table = create_register_table(hmi_response)
            hmis[hmi["name"]].dataframe(
                hmi_table,
                column_config={
                    "type": st.column_config.TextColumn("Type", width="medium"),
                    "value": st.column_config.Column("Value", width="medium"),
                    "address": st.column_config.NumberColumn("Address", width="medium"),
                    "count": st.column_config.NumberColumn("Count", width="medium"),
                },
                use_container_width=False
            )
        
        # poll plc
        for plc in plc_info:
            plc_response = requests.get(f"http://{plc['ip']}:1111/registers").json()
            plc_table = create_register_table(plc_response)
            plcs[plc["name"]].dataframe(
                plc_table,
                column_config={
                    "type": st.column_config.TextColumn("Type", width="medium"),
                    "value": st.column_config.Column("Value", width="medium"),
                    "address": st.column_config.NumberColumn("Address", width="medium"),
                    "count": st.column_config.NumberColumn("Count", width="medium"),
                },
                use_container_width=False
            )

        # poll sensor
        for sensor in sensor_info:
            sensor_response = requests.get(f"http://{sensor['ip']}:1111/registers").json()
            sensor_table = create_register_table(sensor_response)
            sensors[sensor["name"]].dataframe(
                sensor_table,
                column_config={
                    "type": st.column_config.TextColumn("Type", width="medium"),
                    "value": st.column_config.Column("Value", width="medium"),
                    "address": st.column_config.NumberColumn("Address", width="medium"),
                    "count": st.column_config.NumberColumn("Count", width="medium"),
                },
                use_container_width=False
            )

        # poll actuator
        for actuator in actuator_info:
            actuator_response = requests.get(f"http://{actuator['ip']}:1111/registers").json()
            actuator_table = create_register_table(actuator_response)
            actuators[actuator["name"]].dataframe(
                actuator_table,
                column_config={
                    "type": st.column_config.TextColumn("Type", width="medium"),
                    "value": st.column_config.Column("Value", width="medium"),
                    "address": st.column_config.NumberColumn("Address", width="medium"),
                    "count": st.column_config.NumberColumn("Count", width="medium"),
                },
                use_container_width=False
            )

        # poll the physical hil (through the SQLite3 database)
        conn = sqlite3.connect("physical_interactions.db")
        for hil in hil_info:
            for physical_value in hil["values"]:
                table = physical_value
                df = pd.read_sql_query(f"SELECT value FROM {table} ORDER BY timestamp DESC LIMIT 1", conn)
                df["physical_value"] = table
                hils[physical_value].dataframe(df, column_order=["physical_value", "value"])


                df = pd.read_sql_query(f"SELECT timestamp, value FROM {table} ORDER BY timestamp DESC LIMIT 100", conn)
                df["timestamp"] = pd.to_datetime(df["timestamp"])
                df["value"] = pd.to_numeric(df["value"])
                df_grouped = df.groupby('timestamp')[["value"]].mean()
                
                chart = alt.Chart(df_grouped.reset_index()).mark_line().encode(
                    x=alt.X("timestamp:T", title="Time", axis=alt.Axis(format="%M:%S")),
                    y=alt.Y("value:Q", title="Value")
                )

                graphs[physical_value].altair_chart(chart)
        conn.close()

        time.sleep(1)


if __name__ == "__main__":
    main()