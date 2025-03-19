#!/usr/bin/env python3

# FILE:     main.py
# PURPOSE:  Convenient entry point to start the ICS simulation

import subprocess
from src import ics_setup
from pathlib import Path

if __name__ == "__main__":
    # get absolute parent path
    root_path = Path(__file__).resolve().parent

    # build everything
    print("BUILDING SIMULATION FILES")
    ics_setup.build()

    # build images
    print("BUILDING IMAGES")
    dc_build = subprocess.Popen(["docker", "compose", "-f", f"{root_path}/docker-compose.yaml", "build"])

    dc_build.wait()
    print("DONE! Now run \"docker compose run\" in your terminal.")