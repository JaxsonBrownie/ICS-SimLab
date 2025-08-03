<div style="background-color: rgb(20, 16, 20); padding: 15px 30px; border-radius: 2px; text-align: center;">

# Architecture

</div>

## Overview

ICS/SCADA systems use certain components to control and monitor physical processes. The components that this software simulates are:

- **Human Machine Interfaces (HMI)** - These consist of a visual interface that engineers use to interact with the main control system. They typically send commands to PLCs or RTUs.

- **Programmable Logic Controllers (PLC)** - These control logic and automate certain sections of an ICS. They are usually programmed with Ladder Logic, but in this simulation Python is used. They connnect to field devices (Sensors + Actuators), HMIs, and other PLCs.

- **Sensors** - Devices that record (read) physical processes. E.g. temperature sensor, light sensor, power meters.

- **Actuators** - Devices that interact or change (write) physical processes. E.g. valves, pistons, conveyors.

- **Hardware-in-the-Loop**\* - HILs are modules that simulate physical interactions. Real ICSs don't use them, as real ICSs simply interact with a real physical environment. This simulation uses Python to implement HIL components for physical environment interaction simulation.

## Containers
Docker containers are used to virtualise the different ICS components. Containers are more efficient that virtual machines and are far more quicker to deploy.

*Docker Compose* is used to run multiple containers simultaneously. Compose uses a YAML file, called `docker-compose.yaml`, to define all containers, as well as IP networks.

This software builds up this YAML file through a Python script that reads a `configuration.json` file.

## Networking (Serial + IP/TCP)

ICSs use serial communication and IP/TCP communication through wireless or wired mediums such as Cat32 cables.

This simulation uses Docker Compose networks to

## Modbus (RTU + TCP)

## 