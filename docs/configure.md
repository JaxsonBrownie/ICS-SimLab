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

---
### DEVICES

The JSON file starts of with defining all the devices used in the ICS. It may start like this:

```
{
    "hmis": [],
    "plcs": [],
    "sensors": [],
    "actuators": [],
    "hils": [],
}
```

Under each array is where the different devices get defined. There are certain JSON configurations that are used in several components. These configurations are desribed below, along with each device it is used in.

---

- *name* ***(hmis, plcs, sensors, actuators, hils)*** - the name of the device
- *network* ***(hmis, plcs, sensors, actuators)*** - what Docker network it belongs too (all components apart from HILs must belong to a Docker network)
    - *ip* - its IP within this network
    - *docker_network* - the name of the Docker network
- *inbound_connections* ***(hmis, plcs, sensors, actuators)*** [Array] - configures Modbus RTU/TCP slaves/servers for other devices to connect to
    - *type* - can be "rtu" or "tcp"
    - *slave_id* - Modbus slave id **(only for "rtu")**
    - *comm_port* - name of the virtual port to connect to **(only for "rtu")**
    - *ip* - IP address for server **(only for "tcp")**
    - *port* - port address for server **(only for "tcp")**
    - *docker_network* - the name of the Docker network  **(only for "tcp")**
- *outbound_connections* ***(hmis, plcs)*** [Array] - configures Modbus RTU/TCP masters/clients for this device to connect to other devices
    - *type* - can be "rtu" or "tcp"
    - *comm_port* - name of the virtual port to connect to **(only for "rtu")**
    - *ip* - IP address of client to connect to **(only for "tcp")**
    - *port* - port of client to connect to (default 502) **(only for "tcp")**
    - *id* - an id for this connection - is used for monitors and controllers that use this connection line
- *registers* ***(hmis, plcs, sensors, actuators)*** - defines all Modbus registers that this device can use
    - *coil* [Array] - configurations for coils
        - *address* - coil address
        - *count* - number of relays (usually just 1)
        - *id* - an id for this coil - used by monitors and controllers
    - *discrete_input* [Array] - configurations for discrete inputs
        - *address* - discrete input address
        - *count* - number of relays used (usually 1)
        - *id* - an id for this discrete input - used by monitors and controllers
    - *holding_register* [Array] - configurations for holding registers
        - *address* - holding register address
        - *count* - number of registers used by this value (usually 1 for regular integers)
        - *id* - an id for this holding register value - used by monitors and controllers
    - *input_register* [Array] - configurations for input registers
        - *address* - input register address
        - *count* - number of registers used by this value (usually 1)
        - *id* - an id for this input register - used by monitors and controllers
- *monitors* ***(hmis, plcs)*** [Array] - these are custom ICS-SimLab configurations that handle continuous polling operations. They connect to an outside device, read a specific address + count at a continuous interval, then write what they have read to a given register on this device.
    - *outbound_connection_id* - this must match an id of one of the *outbound_connections* from before - it determines what device this monitor will be reading from
    - *value_type* - the value type that is being read - can be "coil", "discrete_input", "holding_register" or "input_register"
    - *id* - this must match an id of a register from *registers* configurations for this device - it determines which register will have the externally read value written to
    - *address* - address of the register to read on the external device
    - *count* - number of registers to read (usually 1)
    - *interval* - how often to poll this device (seconds)
- *controllers* ***(hmis, plcs)*** [Array] - these are custom ICS-SimLab configurations that handle writing operations. They connect to an outside device, then write to a specific address on that outside device. The value they write is determined by another register on this device. Essentially, it reads a register value on this device, then writes it to an outside device.
    - *outbound_connection_id* - this must match an id of one of the *outbound_connections* from before - it determines what device this controller will to writing to
    - *value_type* - the value type that of the register being written to - can be "coil" or "holding_register"
    - *id* - this must match an id of a register from *registers* configurations for this device - the value of the register is what gets written to on the external device
    - *address* - address of the register to write to
    - *count* - number of registers being written to (usually 1)
- *logic* ***(plcs, hils)*** - a Python file name that implements the logic for this device (explained later)
- *physical_values* ***(sensors, actuators)***  [Array] - a list of physical value names, which defines what physical values the sensor/actuator affects
    - *name* - name of the physical value (e.g. "water_temperature")
- *physical_values* ***(hils)*** [Array] - a list of all phyiscal values - is used by ***hil*** components to define how physical interactions occur
    - *name* - name of the physical value
    - *io* - whether the physical value represents input (can only be written to - **used for actuator values***) or output (can only be read - **used for sensor values**)


| JSON configuration    | Device |
| ------------------    | ------ |
| *name*                | ***hmis, plcs, sensors, actuators, hils*** |
| *network*             | ***hmis, plcs, sensors, actuators*** |
| *inbound_connections* | ***hmis, plcs, sensors, actuators*** |
| *outbound_connections*| ***hmis, plcs*** |
| *registers*           | ***hmis, plcs, sensors, actuators*** |
| *monitors*            | ***hmis, plcs*** |
| *controllers*         | ***hmis, plcs*** |
| *logic*               | ***plcs, hils*** |
| *physical_values*     | ***sensors, actuators, hils - note that sensors/actuators have a slightly different value definition than hils***

---

A sample configuration with a single ***hmi*** device may look like the following (note that it does nothing). Refer to the table above to understand what JSON properties each device expects.

```
{
    "hmis":
    [
        {
            "name": "test_hmi",
            "network":
            {
                "ip": "192.168.1.1",
                "docker_network": "vlan1"
            },
            "inbound_connections": [],
            "outbound_connections": [],
            "registers":
            {
                "coil": [],
                "discrete_input": [],
                "input_register": [],
                "holding_register": []
            },
            "monitors": [],
            "controllers": []
        }
    ],

    "plcs": [],
    "sensors": [],
    "actuators": [],
    "hils": []
}
```

---
### NETWORKS
Before we go further, devices depend on serial or IP networks for inter-device communication. This is missing in the above example. These get defined separately in the same JSON file as the following:

- *serial_networks* [Array] - defines many virtual serial ports to be used by other devices
    - *src* - source communication port - these are used in other device configurations where a *comm_port* is required
    - *dest* - destination communication port
- *ip_networks* [Array] - defines IP networks
    - *docker_name* - the name of the network that Docker Compose uses
    - *name* - a convenient name for the network interface
    - *subnet* - network definition in CIDR notation

> Note that there must always exists one IP network, and every device must have an IP in it, which is defined under the *network* property (even for serial-only devices).

With correct network definitions, the example would now look like this (open up <code>configurations.json</code> to view):

<details>
    <summary><code>configuration.json</code></summary>

    {
        "hmis":
        [
            {
                "name": "test_hmi",
                "network":
                {
                    "ip": "192.168.1.1",
                    "docker_network": "vlan1"
                },
                "inbound_connections": [],
                "outbound_connections": [],
                "registers":
                {
                    "coil": [],
                    "discrete_input": [],
                    "input_register": [],
                    "holding_register": []
                },
                "monitors": [],
                "controllers": []
            }
        ],

        "plcs": [],
        "sensors": [],
        "actuators": [],
        "hils": [],

        "serial_networks": [],
        "ip_networks":
        [
            {
                "docker_name": "vlan1",
                "name": "example_network",
                "subnet": "192.168.0.0/24"
            }
        ]
    }

</details>

### MONITORS 
Continuing with this example, we will add a holding register to the ***hmi*** and add a ***plc***. The ***hmi*** will constantly poll a value from the ***plc***, which will be recorded in the holding register in the ***hmi***. First we will define the ***plc*** and the registers for both devices.

<details>
    <summary><code>configuration.json</code></summary>

    {
        "hmis":
        [
            {
                "name": "test_hmi",
                "network":
                {
                    "ip": "192.168.1.1",
                    "docker_network": "vlan1"
                },
                "inbound_connections": [],
                "outbound_connections": [],
                "registers":
                {
                    "coil": [],
                    "discrete_input": [],
                    "input_register": [],
                    "holding_register": 
                    [
                        {
                            "address": 200,
                            "count": 1,
                            "id": "example_hmi_register"
                        }
                    ]
                },
                "monitors": [],
                "controllers": []
            }
        ],

        "plcs": 
        [
            {
                "name": "test_plc",
                "network":
                {
                    "ip": "192.168.1.2",
                    "docker_network": "vlan1"
                },
                "inbound_connections": [],
                "outbound_connections": [],
                "registers":
                {
                    "coil": [],
                    "discrete_input": [],
                    "input_register": [],
                    "holding_register": 
                    [
                        {
                            "address": 100,
                            "count": 1,
                            "id": "example_plc_register"
                        }
                    ]
                },
                "monitors": [],
                "controllers": []
            }
        ],


        "sensors": [],
        "actuators": [],
        "hils": [],

        "serial_networks": [],
        "ip_networks":
        [
            {
                "docker_name": "vlan1",
                "name": "example_network",
                "subnet": "192.168.0.0/24"
            }
        ]
    }

</details>

Note 2 things. 1, we have created a ***plc*** device. 2, we have given both devices a holding register. The address in the ***hmi*** is 200, and the address in the ***plc*** is 100. We will now configure the ***hmi*** to poll the register in the ***plc***, and make it write this polled value in its own holding register.

The ***hmi*** will need an outbound connection, and the ***plc*** will need a inbound connection to be configured. We will use Modbus TCP here. 


<details>
    <summary><code>configuration.json</code></summary>

    {
        "hmis":
        [
            {
                "name": "test_hmi",
                "network":
                {
                    "ip": "192.168.1.1",
                    "docker_network": "vlan1"
                },
                "inbound_connections": [],
                "outbound_connections": 
                [
                    {
                        "type": "tcp",
                        "ip":"192.168.1.2",
                        "port": 502,
                        "id": "connection_to_plc"
                    }
                ],
                "registers":
                {
                    "coil": [],
                    "discrete_input": [],
                    "input_register": [],
                    "holding_register": 
                    [
                        {
                            "address": 200,
                            "count": 1,
                            "id": "example_hmi_register"
                        }
                    ]
                },
                "monitors": [],
                "controllers": []
            }
        ],

        "plcs": 
        [
            {
                "name": "test_plc",
                "network":
                {
                    "ip": "192.168.1.2",
                    "docker_network": "vlan1"
                },
                "inbound_connections": 
                [
                    {
                        "type": "tcp",
                        "ip": "192.168.1.2",
                        "port": 502,
                        "id": "connection_from_hmi"
                    }

                ],
                "outbound_connections": [],
                "registers":
                {
                    "coil": [],
                    "discrete_input": [],
                    "input_register": [],
                    "holding_register": 
                    [
                        {
                            "address": 100,
                            "count": 1,
                            "id": "example_plc_register"
                        }
                    ]
                },
                "monitors": [],
                "controllers": []
            }
        ],


        "sensors": [],
        "actuators": [],
        "hils": [],

        "serial_networks": [],
        "ip_networks":
        [
            {
                "docker_name": "vlan1",
                "name": "example_network",
                "subnet": "192.168.0.0/24"
            }
        ]
    }

</details>

A *monitor* will then be configured on the ***hmi*** to implement to polling functionality. Note how the *outbound_connection_id* for the monitor uses the previously defined outbound connection, and that the address value in the monitor refers to the ***plcs*** register address. The *id* for the monitor refers to the register within the ***hmi*** where this read value will be written to.

<details>
    <summary><code>configuration.json</code></summary>

    {
        "hmis":
        [
            {
                "name": "test_hmi",
                "network":
                {
                    "ip": "192.168.1.1",
                    "docker_network": "vlan1"
                },
                "inbound_connections": [],
                "outbound_connections": 
                [
                    {
                        "type": "tcp",
                        "ip":"192.168.1.2",
                        "port": 502,
                        "id": "connection_to_plc"
                    }
                ],
                "registers":
                {
                    "coil": [],
                    "discrete_input": [],
                    "input_register": [],
                    "holding_register": 
                    [
                        {
                            "address": 200,
                            "count": 1,
                            "id": "example_hmi_register"
                        }
                    ]
                },
                "monitors": 
                [
                    {
                        "outbound_connection_id": "connection_to_plc",
                        "id": "example_hmi_register",
                        "value_type": "holding_register",
                        "address": 100,
                        "count": 1,
                        "interval": 1.5
                    }
                ],
                "controllers": []
            }
        ],

        "plcs": 
        [
            {
                "name": "test_plc",
                "network":
                {
                    "ip": "192.168.1.2",
                    "docker_network": "vlan1"
                },
                "inbound_connections": 
                [
                    {
                        "type": "tcp",
                        "ip": "192.168.1.2",
                        "port": 502,
                        "id": "connection_from_hmi"
                    }

                ],
                "outbound_connections": [],
                "registers":
                {
                    "coil": [],
                    "discrete_input": [],
                    "input_register": [],
                    "holding_register": 
                    [
                        {
                            "address": 100,
                            "count": 1,
                            "id": "example_plc_register"
                        }
                    ]
                },
                "monitors": [],
                "controllers": []
            }
        ],


        "sensors": [],
        "actuators": [],
        "hils": [],

        "serial_networks": [],
        "ip_networks":
        [
            {
                "docker_name": "vlan1",
                "name": "example_network",
                "subnet": "192.168.0.0/24"
            }
        ]
    }
</details>


We now have a ***hmi*** device that constantly polls a ***plc***. Currently though, no actual values are being exchanged. We can add a ***sensor*** that the ***plc*** can consistently poll from.

TODO: finish off documentation
- sensor
- hil
- actuator
- controller
- logic file
- ui

## Logic
Certain devices need to have logic implemented into them. For exampel, PLCs need to be able to map input to output. Below are all the ways devices need logic.
1. To map input registers to output registers. This is relevant for PLCs.
2. To write to other devices. This 

