
<div style="background-color: rgb(20, 16, 20); padding: 15px 30px; border-radius: 2px; text-align: center;">

# ICS-SimLab

![logo](docs/logo.png)

**Second development of the ICS simulation program. Designed to simulate general ICS and SCADA systems through a configurable and flexible system.**

</div>

<br>

<div style="background-color: rgb(28, 27, 28); padding: 6px 30px; border-radius: 15px">

## Quickstart
Run `sudo ./start.sh <configuration>` to start the simulation, where `<configuration>` is a directory for a configured simulation.

Pre-configured simulations are found in */config/\**.

E.g. to run a water bottle filling facility simulation, run `sudo ./start.sh config/water_bottle_factory`.

</div>

<br>

<div style="background-color: rgb(28, 27, 28); padding: 6px 30px; border-radius: 15px">

## Documentation
- Refer to [init.md](docs/init.md) to start a preconfigured simulation.
- Refer to [architecture.md](docs/architecture.md) to understand the architecture of the simulation.
- Refer to [configure.md](docs/configure.md) to learn to configure a custom SCADA simulation.