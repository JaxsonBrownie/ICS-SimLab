<div style="background-color: rgb(20, 16, 20); padding: 15px 30px; border-radius: 2px; text-align: center;">

# Configuration

</div>

> Refer to 

## Components

ICS-SimLab can simulate the following components:
- Human Machine Interfaces (HMIs)
- Programmable Logic Controllers (PLCs)
- Sensors
- Actuators
- Hardware-in-the-Loop (HIL) Modules

**HMIs:**
These read from sensors and can write to actuators. They boot up a GUI.

**PLCs:**
These control logic. They can read from sensors and write to actuators. They require a Python file to define logic.

**Sensors:**
These read from physical values defined in HIL modules.

**Actuators:**
These write to physical values defined in HIL modules.

**HILs**
These define physical values that sensors and actuators can interact with. They require a Python file to define how the physical values affect each other, and how they change over time.

> All of these components are defined in a JSON file, along with some extra definitions for the simulation to run properly.

## JSON Format


## Logic
Certain devices need to have logic implemented into them. For exampel, PLCs need to be able to map input to output. Below are all the ways devices need logic.
1. To map input registers to output registers. This is relevant for PLCs.
2. To write to other devices. This 

