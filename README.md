# Curtin ICS-SimLab: a Containerized Approach for Simulating Industrial Control Systems for Cyber Security Research

![curtin_logo](docs/img/curtin_logo.png)

![logo](docs/img/logo.png)

> This work is supported by a Cross-Campus Cyber Security Research Project
funded by **Curtin University**.

**"Curtin ICS-SimLab" is a software suite designed to simulate general Industrial Control Systems through a configurable, containerized environment.**

---


## Citiation

This repository contains the implementation of the following paper:

> J. Brown, D. S. Pham, S. Soh, F. Motalebi, S. Eswaran, M. Almsahor, "ICS-SimLab: a Containerized Approach for Simulating Industrial Control Systems for Cyber Security Research" in Proceedings of the First International Workshop on Secure Industrial Control Systems and Industrial IoT, France, 2025. (Forthcoming)

**Abstract:**

Industrial Control Systems (ICSs) manage processes in environments such as chemical plants and water treatment facilities. As these systems increasingly connect to the Internet, they face higher risks of cyberattacks, making ICS-specific Intrusion Detection Systems (IDS) essential. Since testing on live systems is impractical and unsafe, researchers rely on simulated testbeds. Existing testbeds are often limited, lacking flexibility to model diverse ICS architectures.

This repository presents **ICS-SimLab**, a Docker-based framework for building configurable ICS simulations aligned with the Purdue Enterprise Reference Architecture. ICS-SimLab supports multiple environments. This repository has 3 predefined simulations built with ICS-SimLab: a solar panel smart grid, a water bottle filling facility, and a network of intelligent electronic devices. 

```
If you find this work useful, then please consider for citing the paper:

@unpublished{brown2025ics-simlab,
  title        = {ICS-SimLab: a Containerized Approach for Simulating Industrial Control Systems for Cyber Security Research},
  author       = {Brown, Jaxson and Pham, Duc-Son and Soh, Sieteng and Motalebi, Foad and Eswaran, Sivaraman and Almashor, Mahathir},
  year         = {2025},
  note         = {Accepted for publication in Proceedings of the First International Workshop on Secure Industrial Control Systems and Industrial IoT},
  institution  = {Curtin University, Curtin University Malaysia, CSIRO}
}

```

## Quickstart
Run `sudo ./start.sh <configuration>` to start the simulation, where `<configuration>` is a directory for a configured simulation.

Pre-configured simulations are found in */config/\**.

E.g. to run the water bottle filling facility simulation, run `sudo ./start.sh config/water_bottle_factory`.


## Documentation
- Refer to [init.md](docs/init.md) to start a preconfigured simulation.
- Refer to [architecture.md](docs/architecture.md) to understand the architecture of the simulation.
- Refer to [configure.md](docs/configure.md) to learn to configure a custom SCADA simulation.
