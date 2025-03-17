#!/usr/bin/env python3

# FILE: ics_setup.py
# PURPOSE: Parses the configuration JSON file into a Docker Compose YAML file

import yaml
import json
import ipaddress

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
        networks = construct_networks(json_content)

        # create PLCs section
        plcs = construct_plcs(json_content)

        # create the YAML file
        parsed_json_content = {
            "services": plcs,
            "networks": networks,
        }

        print(json.dumps(parsed_json_content, indent=4))


        yaml_content = yaml.dump(parsed_json_content, sort_keys=False)
        with open(yaml_filename, "w") as yaml_file:
            yaml_file.write(yaml_content)
    
    return json_content, parsed_json_content

# FUNCTION: construct_networks
# PURPOSE: Builds the section of the YAML docker compose file for the IP networks
def construct_networks(json_content):
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


# FUNCTION: contruct_plcs
# PURPOSE:  Builds the section of the YAML file for the PLCs
def construct_plcs(json_content):
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
        if plc["connection_type"] == "tcp":
            ip = plc["connection_config"]["ip"]

            # find network info that the ip fits into
            network_docker_name = ""
            for network in json_content["networks"]:
                if ipaddress.ip_address(ip) in ipaddress.ip_network(network["subnet"], strict=False):
                    network_docker_name = network["docker_name"]
                    break

            # throw exception if no valid network exists
            if network_docker_name == "":
                raise KeyError(f"No valid network exists for this component: {container_name}")

            json_plcs[container_name]["networks"] = {
                network_docker_name: {
                    "ipv4_address": ip
                }
            }

    return json_plcs


# FUNCTION: build
# PURPOSE:  Builds the simulation content, which includes the docker compoes YAML file
#           and the required container directories.
def main():
    # create the docker compose yaml file
    json_content = parse_json_to_yaml("test_json.json", "test_yaml.yaml")

    # create all container directories


if __name__ == "__main__":
    main()