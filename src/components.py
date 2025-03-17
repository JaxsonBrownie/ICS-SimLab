#!/usr/bin/env python3

# FILE: components.py
# PURPOSE: Classes for all SCADA components

from pathlib import Path

# CLASS: PLC
# PURPOSE: Represents a PLC to be built into a container
class PLC:
    def __init__(self, json_data):
        self.container_name = json_data["container_name"]
        self.connection_type = json_data["connection_type"]
        self.connection_config = json_data["connection_config"]
        self.coils = json_data["values"]["coils"]
        self.discrete_inputs = json_data["values"]["discrete_inputs"]
        self.holding_registers = json_data["values"]["holding_registers"]
        self.input_registers = json_data["values"]["input_registers"]

    # FUNCTION: build_directory
    # PURPOSE:  Builds a container directory using defined fields. Includes a Dockerfile,
    #           python executable, and JSON configuration.
    def build_directory(self):
        Path(f"containers/{self.container_name}").mkdir
        