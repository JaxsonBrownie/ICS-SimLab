#!/usr/bin/env python3

# FILE: ics_setup.py
# PURPOSE: Parses the configuration JSON file into a Docker Compose YAML file

import yaml
import json

# FUNCTION: parse_json_to_yaml
# PURPOSE: Opens and validates the JSON file and parses it into a
#          Docker Compose YAML file
def parse_json_to_yaml(json_filename, yaml_filename):
    with open(json_filename, "r") as json_file:
        content = json_file.read()
        json_content = {}

        # check if the file is a valid JSON file
        try:
            json_content = json.loads(content)
        except ValueError as e:
            print(f"Invalid JSON: {e}")

        # create PLCs section
        
        
        # create the YAML file



        yaml_content = yaml.dump(json_content, sort_keys=False)
        with open(yaml_filename, "w") as yaml_file:
            yaml_file.write(yaml_content)


def construct_plcs(json_content):
    print(json_content)



# FUNCTION: main
# PURPOSE: Main content
def main():
    parse_json_to_yaml("test_json.json", "test_yaml.yaml")

if __name__ == "__main__":
    main()