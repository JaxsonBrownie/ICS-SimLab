<div style="background-color: rgb(20, 16, 20); padding: 15px 30px; border-radius: 2px; text-align: center;">

# Configuration

</div>

## Configuration Directory
ICS-Sim uses a directory containing configuration information to build a custom ICS simulation. The directory needs to contain the following:

1. `configuration.json` - This is a JSON file containing the configuration for all components and networks (both serial ports and IP/TCP networks), as well as details on how the components talk to each other. For full details on how to create your own configuration, refer to the [configuration documentation](configure.md).

2. `logic/` - This is a directory that holds Python files to implement the logic for components that require custom logic (PLCs and HILs). For information on how these work again refer to the [configuration documentation](configure.md).

The name of the configuration file must be `configuration.json` and the name of the logic directory must be `logic`, but the Python files within the logic directory can be named whatever (the Python file names are referenced in the JSON config file).

## JSON Format
The `configuration.json` file follows a set format. We will implement an example to describe each component of this file.

1. To create HMI components, use the "hmis" JSON key. Below are all the "hmis" keys:
    - *name* - the name of the device
    - *network* - what Docker network it belongs too (all components must belong to a Docker network)
        - *ip* - its IP within this network
        - *docker_network* - the name of the Docker network
    - "inbound_connections"
        - *inbound_connections* - configures Modbus RTU/TCP slaves/servers for inbound devices to connect to
            - *type* - can be "rtu" or "tcp"
            - *slave_id* - Modbus slave id **(only for "rtu")**
            - *comm_port* - name of the virtual port to connect to **(only for "rtu")**
            - *ip* - IP adddress **(only for "tcp")**
            - *docker_network* - the name of the Docker network  **(only for "tcp")**


## Logic
Certain devices need to have logic implemented into them. For exampel, PLCs need to be able to map input to output. Below are all the ways devices need logic.
1. To map input registers to output registers. This is relevant for PLCs.
2. To write to other devices. This 

