<div style="background-color: rgb(20, 16, 20); padding: 15px 30px; border-radius: 2px; text-align: center;">

# Architecture

</div>
<br>

**An overview of ICS architecture and how ICS-SimLab virtualises an ICS**

---
## Overview

ICS-SimLab can simulate the following components:
- Human Machine Interfaces (HMIs)
- Programmable Logic Controllers (PLCs)
- Sensors
- Actuators
- Hardware-in-the-Loop (HIL) Modules

**Human Machine Interfaces (HMI)** - These consist of a visual interface that engineers use to interact with the main control system. They typically send commands to PLCs or RTUs and also read values.

 **Programmable Logic Controllers (PLC)** - These control logic and automate certain sections of an ICS. They are usually programmed with Ladder Logic, but in this simulation Python is used. They connnect to field devices (Sensors + Actuators), HMIs, and other PLCs.

**Sensors** - Devices that record (read) physical processes. E.g. temperature sensor, light sensor, power meters.

**Actuators** - Devices that interact or change (write) physical processes. E.g. valves, pistons, conveyors.

**Hardware-in-the-Loop**\* - HILs are modules that simulate physical interactions. Real ICSs don't use them, as real ICSs simply interact with a real physical environment. This simulation uses Python to implement HIL components for physical environment interaction simulation.


---
## Containers
Docker containers are used to virtualise the different ICS components.

*Docker Compose* is used to run multiple containers simultaneously. Compose uses a YAML file, called `docker-compose.yaml`, to define all containers and IP networks.

ICS-SimLab builds up this YAML file through a Python script that reads a `configuration.json` file. ICS-SimLab then starts up Docker Compose, which then reads the built YAML file to start all the containers.


---
## Networking (Serial + IP/TCP)

ICSs use serial communication and IP/TCP communication amongst components. ICS-SimLab uses Modbus-TCP for IP/TCP communication and Modbus-RTU for serial communication.

*Docker Compose* can define IP networks in the YAML file, which is what ICS-SimLab uses for Modbus-TCP.

`Socat` is used for Modbus-RTU. `Socat` is a Unix command line utility that creates two bidirectional byte streams for creating virtual serial ports. It is used by ICS-SimLab to create serial ports for Modbus-RTU. `Socat` essentially creates two files that act as the entry points for the serial ports. ICS-SimLab mounts these files as **volumes** within the containers that need serial communciation, which are then used for Modbus-RTU communication.

---
## Physical Interactions
To virtual the physical interactions of a ICS (sensors reading environment values and actuators moving physical parts), ICS-SimLab uses an SQLite3 database.

Sensors continuously read from the database, and actuators continuously write to the database. Sensors read values and store them in registers (which other devices can then read from). Actuators write values based on values in their own registers.

HIL modules can read and write the database. They have the ability to change physical values in the database depending on some predefined logic (again, refer to [configure.md](configure.md) on how you can create your own predefined logic). 

> For example, if an output water valve from a tank is on, the HIL module would read that the output valve is on, then would write (decrement) the water level value to simulate the water draining. This would be defined in a Python file.

---
## Python Scripts
ICS-SimLab uses Python script as entry points for the containers. They essentially build all the functionality for the HMIs, PLCs, sensors, actuators and HIL modules. These scripts can be found in `/src/components/*`. 

Below are descriptions of what each script does, noting that the specific configurations are defined in a JSON configuration file. Refer to [configure.md](configure.md) for information on the configuration system.

- `hmi.py` - Starts configured Modbus RTU/TCP masters/clients. Continuously polls for values from PLCs and visually displays it.

- `plc.py` - Starts any configured Modbus RTU/TCP masters/clients and any slaves/servers. Executes any controllers (to write to other devices) and monitors (to monitors data from other devices). Runs a predefined Python script that handles any internal logic, which involves reading internal registers and writing to other internal registers.

- `actuator.py` - Starts configured Modbus RTU/TCP slaves/servers. Continuously writes Modbus register values from the slave/server to the SQLite3 database.

- `sensor.py` - Starts configured Modbus RTU/TCP slaves/servers. Continuously reads values from the SQLite3 database and writes them to Modbus register values in the slave/server.

- `hil.py` - Connects to the SQLite3 database and begins altering values from the database based on some predefined python file.