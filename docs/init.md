<div style="background-color: rgb(20, 16, 20); padding: 15px 30px; border-radius: 2px; text-align: center;">

# Initialisation

</div>

<br>

<div style="background-color: rgb(28, 27, 28); padding: 6px 30px; border-radius: 15px">

## Configuration Directory
ICS-Sim uses a directory containing configuration information to build a custom ICS simulation. The directory needs to contain the following:

1. `configuration.json` - This is a JSON file containing the configuration for all components and networks (both serial ports and IP/TCP networks), as well as details on how the components talk to each other. For full details on how to create your own configuration, refer to the [configuration documentation](configure.md).

2. `logic/` - This is a directory that holds Python files to implement the logic for Programmable Logic Controllers (PLCs) components. For information on how these work again refer to the [configuration documentation](configure.md).


The name of the configuration file must be `configuration.json` and the name of the logic directory must be `logic`, but the Python files within the logic directory can be named whatever.

</div>

<br>

<div style="background-color: rgb(28, 27, 28); padding: 6px 30px; border-radius: 15px">

## Predefined Simulations
This repository has a few pre-defined simulation configurations. They are located within `/config/` at the root of this repository. They are:

1. `smart_grid` - This setup simulates a solar panel system with a PLC acting as an Automatic Transfer Switch between solar panel power input and mains power input.

2. `water_bottle_factory` - This setup simulates a water bottle filling facility. Water bottles are moved from a conveyor belt to underneath an output value, where they are filled up. An tank is also simulated which holds water used to fill the bottles.

</div>