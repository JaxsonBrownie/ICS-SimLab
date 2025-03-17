#!/usr/bin/env python3

# FILE: ics_setup.py
# PURPOSE: Parses the configuration JSON file into a Docker Compose YAML file

import yaml
import json
import ipaddress
import shutil
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

        # create networks
        networks = build_network_yaml(json_content)

        # create PLCs section
        plcs = build_plc_yaml(json_content)

        # create the YAML file
        parsed_json_content = {
            "services": plcs,
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

    for network in json_content["networks"]:
        docker_name = network["docker_name"]
        name = network["name"]
        subnet = network["subnet"]
        
        json_networks["networks"] = {
            docker_name: {
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
        }
    
    return json_networks

# FUNCTION: build_plc_yaml
# PURPOSE:  Builds the section of the YAML file for the PLCs
def build_plc_yaml(json_content):
    json_plcs = {}

    for plc in json_content["plcs"]:

        # extract basic docker configuration
        build = f"containers/{plc['name']}"
        container_name = plc["name"]
        privileged = True

        # TODO: volumes
        # TODO: command

        json_plcs[container_name] = {
            "build": build,
            "container_name": container_name,
            "privileged": privileged,
        }

        # add network info if needed
        found_ip = False
        for connection in plc["connection_endpoints"]:

            if connection["type"] == "tcp":
                ip = connection["ip"]

                # find network info that the ip fits into
                network_docker_name = ""
                for network in json_content["networks"]:
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

    return json_plcs

# FUNCTION: create_containers
# PURPOSE:  Builds the directory containers for the main components of the simulation. These
#           include the PLCs, HMIs, and the sensors and actuators.
def create_containers(json_content):
    path = Path(__file__).resolve().parent

    # delete all existing container directories
    shutil.rmtree(f"{path}/containers", ignore_errors=True)
    Path(f"{path}/containers").mkdir()

    # create PLC directories
    for plc in json_content["plcs"]:
        Path(f"{path}/containers/{plc['name']}").mkdir()
        Path(f"{path}/containers/{plc['name']}/src").mkdir()

        shutil.copy(f"{path}/docker-files/component/Dockerfile", f"{path}/containers/{plc['name']}")
        
        # create JSON configuration
        json_config = {
            "connection_endpoints": plc["connection_endpoints"],
            "values": plc["values"]
        }

        # write confiugration into the containers source code as a JSON file
        with open(f"{path}/containers/{plc['name']}/src/config.json", "w") as conf_file:
            conf_file.write(json.dumps(json_config, indent=4))

# FUNCTION: build
# PURPOSE:  Builds the simulation content, which includes the docker compoes YAML file
#           and the required container directories.
def build():
    # create the docker compose yaml file
    json_content = parse_json_to_yaml("test_json.json", "test_yaml.yaml")

    # create container directories
    create_containers(json_content)

if __name__ == "__main__":
    build()