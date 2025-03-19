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
        plcs = build_plc_yaml(json_content)
        sensors = build_sensor_yaml(json_content)

        # create the YAML file
        parsed_json_content = {
            "services": plcs | sensors,
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

        # add network info if needed
        found_ip = False
        for connection in plc["connection_endpoints"]:
            if connection["type"] == "tcp":
                ip = connection["ip"]

                # find network info that the ip fits into
                network_docker_name = ""
                for network in json_content["ip_networks"]:
                    if ipaddress.ip_address(ip) in ipaddress.ip_network(network["subnet"], strict=False):
                        network_docker_name = network["docker_name"]

                        # check if more than one IP is given
                        if found_ip:
                            raise KeyError("More than one IP specified")
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
                comm_port = connection["comm_port"]
                json_plcs[container_name]["volumes"] = [
                    f"{root_path}/simulation/communications/{comm_port}:/src/{comm_port}"
                ]

        # add monitor info
        for monitor in plc["monitors"]:
            connection = monitor["connection"]
            if connection["type"] == "rtu":
                comm_port = connection["comm_port"]
                json_plcs[container_name]["volumes"] = [
                    f"{root_path}/simulation/communications/{comm_port}:/src/{comm_port}"
                ]

    return json_plcs


# FUNCTION: build_sensor_yaml
# PURPOSE: Builds the section of the YAML file for the sensors
def build_sensor_yaml(json_content):
    root_path = Path(__file__).resolve().parent.parent
    json_sensors = {}

    for sensor in json_content["sensors"]:
        build = f"{root_path}/simulation/containers/{sensor['name']}"
        container_name = sensor["name"]
        privileged = True

        # add the SQLite database as a volume in the src/ directory
        volumes = []
        volumes.append(f"{root_path}/simulation/communications/hardware_interactions.db:/src/hardware_interactions.db")

        # add any virtual serial port
        for connection in sensor["connection_endpoints"]:
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
    return json_sensors


# FUNCTION: create_containers
# PURPOSE:  Builds the directory containers for the main components of the simulation. These
#           include the PLCs, HMIs, and the sensors and actuators.
def create_containers(json_content):
    root_path = Path(__file__).resolve().parent.parent

    # delete all existing container directories
    shutil.rmtree(f"{root_path}/simulation/containers", ignore_errors=True)
    Path(f"{root_path}/simulation/containers").mkdir()

    # create PLC directories
    for plc in json_content["plcs"]:
        Path(f"{root_path}/simulation/containers/{plc['name']}").mkdir()
        Path(f"{root_path}/simulation/containers/{plc['name']}/src").mkdir()
        shutil.copy(f"{root_path}/src/docker-files/component/Dockerfile", f"{root_path}/simulation/containers/{plc['name']}")
        
        # create JSON configuration and write into directory
        json_config = {
            "connection_endpoints": plc["connection_endpoints"],
            "values": plc["values"],
            "monitors": plc["monitors"]
        }
        with open(f"{root_path}/simulation/containers/{plc['name']}/src/config.json", "w") as conf_file:
            conf_file.write(json.dumps(json_config, indent=4))

        # copy PLC code
        shutil.copy(f"{root_path}/src/components/plc.py", f"{root_path}/simulation/containers/{plc['name']}/src")


    # create sensor directories
    for sensor in json_content["sensors"]:
        Path(f"{root_path}/simulation/containers/{sensor['name']}").mkdir()
        Path(f"{root_path}/simulation/containers/{sensor['name']}/src").mkdir()
        shutil.copy(f"{root_path}/src/docker-files/component/Dockerfile", f"{root_path}/simulation/containers/{sensor['name']}")

        # create JSON configuration and write into directory
        json_config = {
            "database": {
                "table": f"{sensor['name']}_values"
            },
            "connection_endpoints": sensor["connection_endpoints"],
            "values": plc["values"]
        }
        with open(f"{root_path}/simulation/containers/{sensor['name']}/src/config.json", "w") as conf_file:
            conf_file.write(json.dumps(json_config, indent=4))

        # copy sensor code
        shutil.copy(f"{root_path}/src/components/sensor.py", f"{root_path}/simulation/containers/{sensor['name']}/src")


# FUNCTION: create_communications
# PURPOSE:  Builds the directory used for communications. This directory holds the SQLite database
#           and the virtual serial ports, which are created using socat.
def create_communications(json_content):
    root_path = Path(__file__).resolve().parent.parent

    # delete existing communications directory
    shutil.rmtree(f"{root_path}/simulation/communications", ignore_errors=True)
    Path(f"{root_path}/simulation/communications").mkdir()

    # create hardware SQLite database
    conn = sqlite3.connect(f"{root_path}/simulation/communications/hardware_interactions.db")
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
    # create the docker compose yaml file
    json_content = parse_json_to_yaml("test_json.json", "docker-compose.yaml")

    # create container directories
    create_containers(json_content)

    # build communication directory
    links = create_communications(json_content)

if __name__ == "__main__":
    build()