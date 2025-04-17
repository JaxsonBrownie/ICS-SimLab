#!/usr/bin/env python3

# FILE: ics_setup.py
# PURPOSE: Parses the configuration JSON file into a Docker Compose YAML file

import yaml
import json
import ipaddress
import shutil
import sqlite3
import subprocess
from pathlib import Path


# FUNCTION: parse_json_to_yaml
# PURPOSE: Opens and validates the JSON file and parses it into a
#          Docker Compose YAML file
def parse_json_to_yaml(json_filename, yaml_filename):
    parsed_json_content = ""
    with open(json_filename, "r") as json_file:
        content = json_file.read()
        json_content = {}

        # check if the file is a valid JSON file
        try:
            json_content = json.loads(content)
        except ValueError as e:
            print(f"Invalid JSON: {e}")

        # create all sections for the YAML file
        networks = build_network_yaml(json_content)
        ui = build_ui_yaml(json_content)
        hmis = build_hmi_yaml(json_content)
        plcs = build_plc_yaml(json_content)
        sensors = build_sensor_yaml(json_content)
        actuators = build_actuator_yaml(json_content)
        hils = build_hil_yaml(json_content)

        # create the YAML file
        parsed_json_content = {
            "services": ui | hmis | plcs | sensors | actuators | hils,
            "networks": networks,
        }

        yaml_content = yaml.dump(parsed_json_content, sort_keys=False)
        with open(yaml_filename, "w") as yaml_file:
            yaml_file.write(yaml_content)
    
    return json_content


# FUNCTION: build_network_yaml
# PURPOSE: Builds the section of the YAML docker compose file for the IP networks
def build_network_yaml(json_content):
    json_networks = {}

    for network in json_content["ip_networks"]:
        docker_name = network["docker_name"]
        name = network["name"]
        subnet = network["subnet"]
        
        json_networks[docker_name] = {
            "driver": "bridge",
            "name": name,
            "ipam": {
                "config": [
                    {
                        "subnet": subnet
                    }
                ]
            },
            "driver_opts": {
                "com.docker.network.bridge.name": name
            }
        }
    
    return json_networks


# FUNCTION: build_ui_yaml
# PURPOSE:  Builds the UI yaml
def build_ui_yaml(json_content):
    root_path = Path(__file__).resolve().parent.parent
    json_ui = {}

    # extract basic docker configuration
    build = f"{root_path}/simulation/containers/ui"
    ip = json_content["ui"]["network"]["ip"]
    port = json_content["ui"]["network"]["port"]
    docker_network = json_content["ui"]["network"]["docker_network"]
    privileged = True

    json_ui["ui"] = {
        "build": build,
        "container_name": "ui",
        "privileged": privileged,
        "ports": [port, 1111],
        "command": ["streamlit", "run", "ui.py", f"--server.port={port}", "--server.address=0.0.0.0"],
    }
    json_ui["ui"]["networks"] = {}
    json_ui["ui"]["networks"][docker_network] = {}
    json_ui["ui"]["networks"][docker_network]["ipv4_address"] = ip

    return json_ui

################################################################################

# FUNCTION: build_plc_yaml
# PURPOSE:  Builds the section of the YAML file for the PLCs
def build_plc_yaml(json_content):
    root_path = Path(__file__).resolve().parent.parent
    json_plcs = {}

    for plc in json_content["plcs"]:
        # extract basic docker configuration
        build = f"{root_path}/simulation/containers/{plc['name']}"
        container_name = plc["name"]
        privileged = True

        json_plcs[container_name] = {
            "build": build,
            "container_name": container_name,
            "privileged": privileged,
            "command": ["python3", "-u", "plc.py"]
        }

        # add inbound connection info
        found_ip = False
        json_plcs[container_name]["volumes"] = []
        for connection in plc["inbound_connections"]:
            if connection["type"] == "tcp":
                ip = connection["ip"]

                # find network info that the ip fits into
                network_docker_name = ""
                for network in json_content["ip_networks"]:
                    if ipaddress.ip_address(ip) in ipaddress.ip_network(network["subnet"], strict=False):
                        network_docker_name = network["docker_name"]

                        # check if more than one IP is given
                        if found_ip:
                            raise KeyError("More than one inbound IP specified")
                        break

                # throw exception if no valid network exists
                if network_docker_name == "":
                    raise KeyError(f"No valid network exists for this component: {container_name}")

                json_plcs[container_name]["networks"] = {
                    network_docker_name: {
                        "ipv4_address": ip
                    }
                }
                found_ip = True
            elif connection["type"] == "rtu":
                # add comm port as a volume
                comm_port = connection["comm_port"]
                json_plcs[container_name]["volumes"].append(
                    f"{root_path}/simulation/communications/{comm_port}:/src/{comm_port}"
                )

        # add outbound connection info (only relevant for rtu)
        for connection in plc["outbound_connections"]:
            if connection["type"] == "rtu":
                # add comm port as a volume
                comm_port = connection["comm_port"]
                json_plcs[container_name]["volumes"].append(
                    f"{root_path}/simulation/communications/{comm_port}:/src/{comm_port}"
                )

        # add ip address
        ip = plc["network"]["ip"]
        docker_network = plc["network"]["docker_network"]
        json_plcs[container_name]["networks"] = {}
        json_plcs[container_name]["networks"][docker_network] = {}
        json_plcs[container_name]["networks"][docker_network]["ipv4_address"] = ip

        # export ports (1111 for UI, 5020 for modbus)
        json_plcs[container_name]["ports"] = []
        json_plcs[container_name]["ports"].append(1111)
        json_plcs[container_name]["ports"].append(5020)
    return json_plcs


# FUNCTION: build_hmi_yaml
# PURPOSE:  Builds the section of the YAML file for the HMIs
def build_hmi_yaml(json_content):
    root_path = Path(__file__).resolve().parent.parent
    json_hmis = {}

    for hmi in json_content["hmis"]:
        # extract basic docker configuration
        build = f"{root_path}/simulation/containers/{hmi['name']}"
        container_name = hmi["name"]
        privileged = True

        json_hmis[container_name] = {
            "build": build,
            "container_name": container_name,
            "privileged": privileged,
            "command": ["python3", "-u", "hmi.py"]
        }

        # add inbound connection info
        found_ip = False
        json_hmis[container_name]["volumes"] = []
        for connection in hmi["inbound_connections"]:
            if connection["type"] == "tcp":
                ip = connection["ip"]

                # find network info that the ip fits into
                network_docker_name = ""
                for network in json_content["ip_networks"]:
                    if ipaddress.ip_address(ip) in ipaddress.ip_network(network["subnet"], strict=False):
                        network_docker_name = network["docker_name"]

                        # check if more than one IP is given
                        if found_ip:
                            raise KeyError("More than one inbound IP specified")
                        break

                # throw exception if no valid network exists
                if network_docker_name == "":
                    raise KeyError(f"No valid network exists for this component: {container_name}")

                json_hmis[container_name]["networks"] = {
                    network_docker_name: {
                        "ipv4_address": ip
                    }
                }
                found_ip = True
            elif connection["type"] == "rtu":
                # add comm port as a volume
                comm_port = connection["comm_port"]
                json_hmis[container_name]["volumes"].append(
                    f"{root_path}/simulation/communications/{comm_port}:/src/{comm_port}"
                )

        # add outbound connection info (only relevant for rtu)
        for connection in hmi["outbound_connections"]:
            if connection["type"] == "rtu":
                # add comm port as a volume
                comm_port = connection["comm_port"]
                json_hmis[container_name]["volumes"].append(
                    f"{root_path}/simulation/communications/{comm_port}:/src/{comm_port}"
                )

        # add ip address
        ip = hmi["network"]["ip"]
        docker_network = hmi["network"]["docker_network"]
        json_hmis[container_name]["networks"] = {}
        json_hmis[container_name]["networks"][docker_network] = {}
        json_hmis[container_name]["networks"][docker_network]["ipv4_address"] = ip

        # export ports (1111 for UI, 5020 for modbus)
        json_hmis[container_name]["ports"] = []
        json_hmis[container_name]["ports"].append(1111)
        json_hmis[container_name]["ports"].append(5020)
    return json_hmis

# FUNCTION: build_sensor_yaml
# PURPOSE:  Builds the section of the YAML file for the sensors
def build_sensor_yaml(json_content):
    root_path = Path(__file__).resolve().parent.parent
    json_sensors = {}

    for sensor in json_content["sensors"]:
        build = f"{root_path}/simulation/containers/{sensor['name']}"
        container_name = sensor["name"]
        privileged = True

        # add the SQLite database as a volume in the src/ directory
        volumes = []
        volumes.append(f"{root_path}/simulation/communications/physical_interations.db:/src/physical_interations.db")

        # add any virtual serial port
        for connection in sensor["inbound_connections"]:
            if connection["type"] == "rtu":
                comm_port = connection["comm_port"]
                volumes.append(f"{root_path}/simulation/communications/{comm_port}:/src/{comm_port}")

        json_sensors[container_name] = {
            "build": build,
            "container_name": container_name,
            "privileged": privileged,
            "volumes": volumes,
            "command": ["python3", "-u", "sensor.py"]
        }

        # add ip address
        ip = sensor["network"]["ip"]
        docker_network = sensor["network"]["docker_network"]
        json_sensors[container_name]["networks"] = {}
        json_sensors[container_name]["networks"][docker_network] = {}
        json_sensors[container_name]["networks"][docker_network]["ipv4_address"] = ip

        # export ports (1111 for UI, 5020 for modbus)
        json_sensors[container_name]["ports"] = []
        json_sensors[container_name]["ports"].append(1111)
        json_sensors[container_name]["ports"].append(5020)
    return json_sensors


# FUNCTION: build_actuator_yaml
# PURPOSE:  Builds the YAML section for the actuators
def build_actuator_yaml(json_content):
    root_path = Path(__file__).resolve().parent.parent
    json_actuators = {}

    for actuator in json_content["actuators"]:
        build = f"{root_path}/simulation/containers/{actuator['name']}"
        container_name = actuator["name"]
        privileged = True
        
        # add the SQLite database as a volume in the src/ directory
        volumes = []
        volumes.append(f"{root_path}/simulation/communications/physical_interations.db:/src/physical_interations.db")

        # add any virtual serial port to the volumes
        for connection in actuator["inbound_connections"]:
            if connection["type"] == "rtu":
                comm_port = connection["comm_port"]
                volumes.append(f"{root_path}/simulation/communications/{comm_port}:/src/{comm_port}")
        
        json_actuators[container_name] = {
            "build": build,
            "container_name": container_name,
            "privileged": privileged,
            "volumes": volumes,
            "command": ["python3", "-u", "actuator.py"]
        }

        # add ip address
        ip = actuator["network"]["ip"]
        docker_network = actuator["network"]["docker_network"]
        json_actuators[container_name]["networks"] = {}
        json_actuators[container_name]["networks"][docker_network] = {}
        json_actuators[container_name]["networks"][docker_network]["ipv4_address"] = ip

        # export ports (1111 for UI, 5020 for modbus)
        json_actuators[container_name]["ports"] = []
        json_actuators[container_name]["ports"].append(1111)
        json_actuators[container_name]["ports"].append(5020)
    return json_actuators
        

# FUNCTION: build_hil_yaml
# PURPOSE:  Builds the section of the YAML file for the physical hardware-in-the-loop
def build_hil_yaml(json_content):
    root_path = Path(__file__).resolve().parent.parent
    json_hils = {}

    for hil in json_content["hils"]:
        build = f"{root_path}/simulation/containers/{hil['name']}"
        container_name = hil["name"]
        privileged = True

        # add the SQLite database as a volume in the src/ directory
        volumes = []
        volumes.append(f"{root_path}/simulation/communications/physical_interations.db:/src/physical_interations.db")

        json_hils[container_name] = {
            "build": build,
            "container_name": container_name,
            "privileged": privileged,
            "volumes": volumes,
            "command": ["python3", "-u", "hil.py"]
        }
    return json_hils

################################################################################

# FUNCTION: build_ui_directory
# PURPOSE:  Creates the ui directory
def build_ui_directory(json_content):
    root_path = Path(__file__).resolve().parent.parent
    Path(f"{root_path}/simulation/containers/ui").mkdir()
    Path(f"{root_path}/simulation/containers/ui/src").mkdir()
    shutil.copy(f"{root_path}/src/docker-files/ui/Dockerfile", f"{root_path}/simulation/containers/ui")

    # copy the whole json config into the container
    with open(f"{root_path}/simulation/containers/ui/src/config.json", "w") as conf_file:
        conf_file.write(json.dumps(json_content, indent=4))

    # copy ui code
    shutil.copy(f"{root_path}/src/components/ui.py", f"{root_path}/simulation/containers/ui/src")


# FUNCTION: build_hmi_directory
# PURPOSE:  Creates the hmi directory
def build_hmi_directory(json_content):
    root_path = Path(__file__).resolve().parent.parent

    # create hmi directories
    for hmi in json_content["hmis"]:
        Path(f"{root_path}/simulation/containers/{hmi['name']}").mkdir()
        Path(f"{root_path}/simulation/containers/{hmi['name']}/src").mkdir()
        shutil.copy(f"{root_path}/src/docker-files/component/Dockerfile", f"{root_path}/simulation/containers/{hmi['name']}")
        
        # create JSON configuration and write into directory
        json_config = {
            "inbound_connections": hmi["inbound_connections"],
            "outbound_connections": hmi["outbound_connections"],
            "values": hmi["values"],
            "monitors": hmi["monitors"],
            "controllers": hmi["controllers"]
        }
        with open(f"{root_path}/simulation/containers/{hmi['name']}/src/config.json", "w") as conf_file:
            conf_file.write(json.dumps(json_config, indent=4))

        # copy hmi code
        shutil.copy(f"{root_path}/src/components/hmi.py", f"{root_path}/simulation/containers/{hmi['name']}/src")


# FUNCTION: build_plc_directory
# PURPOSE:  Creates the plc directory
def build_plc_directory(json_content):
    root_path = Path(__file__).resolve().parent.parent

    # create plc directories
    for plc in json_content["plcs"]:
        Path(f"{root_path}/simulation/containers/{plc['name']}").mkdir()
        Path(f"{root_path}/simulation/containers/{plc['name']}/src").mkdir()
        shutil.copy(f"{root_path}/src/docker-files/component/Dockerfile", f"{root_path}/simulation/containers/{plc['name']}")
        
        # create JSON configuration and write into directory
        json_config = {
            "inbound_connections": plc["inbound_connections"],
            "outbound_connections": plc["outbound_connections"],
            "values": plc["values"],
            "monitors": plc["monitors"],
            "controllers": plc["controllers"]
        }
        with open(f"{root_path}/simulation/containers/{plc['name']}/src/config.json", "w") as conf_file:
            conf_file.write(json.dumps(json_config, indent=4))

        # copy PLC code and logic file
        logic_file = plc["logic"]
        shutil.copy(f"{root_path}/logic/{logic_file}", f"{root_path}/simulation/containers/{plc['name']}/src/logic.py")
        shutil.copy(f"{root_path}/src/components/plc.py", f"{root_path}/simulation/containers/{plc['name']}/src")


# FUNCTION: build_sensor_directory
# PURPOSE:  Creates the directories for the sensor componenets
def build_sensor_directory(json_content):
    root_path = Path(__file__).resolve().parent.parent

    # create sensor directories
    for sensor in json_content["sensors"]:
        Path(f"{root_path}/simulation/containers/{sensor['name']}").mkdir()
        Path(f"{root_path}/simulation/containers/{sensor['name']}/src").mkdir()
        shutil.copy(f"{root_path}/src/docker-files/component/Dockerfile", f"{root_path}/simulation/containers/{sensor['name']}")

        # create JSON configuration and write into directory
        json_config = {
            "database": {
                "table": f"{sensor['hil']}",
            },
            "inbound_connections": sensor["inbound_connections"],
            "values": sensor["values"]
        }
        with open(f"{root_path}/simulation/containers/{sensor['name']}/src/config.json", "w") as conf_file:
            conf_file.write(json.dumps(json_config, indent=4))

        # copy sensor code
        shutil.copy(f"{root_path}/src/components/sensor.py", f"{root_path}/simulation/containers/{sensor['name']}/src")


# FUNCTION: build_actuator_directory
# PURPOSE:  Creates the directories for the actuator components
def build_actuator_directory(json_content):
    root_path = Path(__file__).resolve().parent.parent
    
    # create actuator directories
    for actuator in json_content["actuators"]:
        Path(f"{root_path}/simulation/containers/{actuator['name']}").mkdir()
        Path(f"{root_path}/simulation/containers/{actuator['name']}/src").mkdir()
        shutil.copy(f"{root_path}/src/docker-files/component/Dockerfile", f"{root_path}/simulation/containers/{actuator['name']}")

        # create JSON configuration and write into directory
        json_config = {
            "database": {
                "table": f"{actuator['hil']}",
                "physical_values": actuator["physical_values"],
            },
            "inbound_connections": actuator["inbound_connections"],
            "values": actuator["values"]
        }
        with open(f"{root_path}/simulation/containers/{actuator['name']}/src/config.json", "w") as conf_file:
            conf_file.write(json.dumps(json_config, indent=4))

        # copy actuator code and logic
        logic_file = actuator["logic"]
        shutil.copy(f"{root_path}/logic/{logic_file}", f"{root_path}/simulation/containers/{actuator['name']}/src/logic.py")
        shutil.copy(f"{root_path}/src/components/actuator.py", f"{root_path}/simulation/containers/{actuator['name']}/src")


# FUNCTION: build_hil_directory
# PURPOSE:  Creates the hardware-in-the-loop directories
def build_hil_directory(json_content):
    root_path = Path(__file__).resolve().parent.parent

    # create hil directories
    for hil in json_content["hils"]:
        Path(f"{root_path}/simulation/containers/{hil['name']}").mkdir()
        Path(f"{root_path}/simulation/containers/{hil['name']}/src").mkdir()
        shutil.copy(f"{root_path}/src/docker-files/component/Dockerfile", f"{root_path}/simulation/containers/{hil['name']}")

        json_config = {
            "database": {
                "table": f"{hil['name']}",
                "physical_values": hil["physical_values"]
            },
        }
        with open(f"{root_path}/simulation/containers/{hil['name']}/src/config.json", "w") as conf_file:
            conf_file.write(json.dumps(json_config, indent=4))

        # copy logic file and code
        logic_file = hil["logic"]
        shutil.copy(f"{root_path}/logic/{logic_file}", f"{root_path}/simulation/containers/{hil['name']}/src/logic.py")
        shutil.copy(f"{root_path}/src/components/hil.py", f"{root_path}/simulation/containers/{hil['name']}/src")


# FUNCTION: create_containers
# PURPOSE:  Builds the directory containers for the main components of the simulation. These
#           include the PLCs, HMIs, and the sensors and actuators.
def create_containers(json_content):
    root_path = Path(__file__).resolve().parent.parent

    # delete all existing container directories
    shutil.rmtree(f"{root_path}/simulation/containers", ignore_errors=True)
    Path(f"{root_path}/simulation/containers").mkdir()

    # create directories for all component containers
    build_ui_directory(json_content)
    build_hmi_directory(json_content)
    build_plc_directory(json_content)
    build_sensor_directory(json_content)
    build_actuator_directory(json_content)
    build_hil_directory(json_content)
    
    
# FUNCTION: create_communications
# PURPOSE:  Builds the directory used for communications. This directory holds the SQLite database
#           and the virtual serial ports, which are created using socat.
def create_communications(json_content):
    root_path = Path(__file__).resolve().parent.parent

    # delete existing communications directory
    shutil.rmtree(f"{root_path}/simulation/communications", ignore_errors=True)
    Path(f"{root_path}/simulation/communications").mkdir()

    # create hardware SQLite database
    conn = sqlite3.connect(f"{root_path}/simulation/communications/physical_interations.db")
    
    # create tables for the HIL components in the SQLite database
    cursor = conn.cursor()
    for hil in json_content["hils"]:
        cursor.execute(
            f"""CREATE TABLE {hil['name']} (
                physical_value TEXT PRIMARY KEY,
                value TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )"""
            )
        conn.commit()

        # create default values for all the physical values (just the empty string)
        for physical_value in hil["physical_values"]:
            cursor.execute(
                f"""INSERT INTO {hil['name']} (physical_value, value)
                    VALUES (?, ?)
                """, (physical_value['name'], "")
            )
            conn.commit()
    conn.close()

    # create virtual serial ports
    links = []
    for serial_link in json_content["serial_networks"]:
        links.append(subprocess.Popen(["socat", 
                                       "-d", 
                                       f"pty,raw,echo=0,link={root_path}/simulation/communications/{serial_link['src']}", 
                                       f"pty,raw,echo=0,link={root_path}/simulation/communications/{serial_link['dest']}"]))

    # return the links to terminate later
    return links

# FUNCTION: build
# PURPOSE:  Builds the simulation content, which includes the docker compoes YAML,
#           the docker container directories, and the communication files.
def build():
    root_path = Path(__file__).resolve().parent.parent

    # create the docker compose yaml file
    json_filename = "smart_grid_simulation.json"
    #json_filename = "test_json.json"
    json_content = parse_json_to_yaml(f"{root_path}/config/{json_filename}", f"{root_path}/docker-compose.yaml")

    # create container directories
    create_containers(json_content)

    # build communication directory
    links = create_communications(json_content)

if __name__ == "__main__":
    build()