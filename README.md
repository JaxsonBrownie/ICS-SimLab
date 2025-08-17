# Curtin ICS-SimLab

![curtin_logo](docs/img/curtin_logo.png)

![logo](docs/img/logo.png)

**"Curtin ICS-SimLab" is a software suite designed to simulate general Industrial Control Systems through a configurable, containerized environment.**


## Quickstart
Run `sudo ./start.sh <configuration>` to start the simulation, where `<configuration>` is a directory for a configured simulation.

Pre-configured simulations are found in */config/\**.

E.g. to run the water bottle filling facility simulation, run `sudo ./start.sh config/water_bottle_factory`.


## Documentation
- Refer to [init.md](docs/init.md) to start a preconfigured simulation.
- Refer to [architecture.md](docs/architecture.md) to understand the architecture of the simulation.
- Refer to [configure.md](docs/configure.md) to learn to configure a custom SCADA simulation.
