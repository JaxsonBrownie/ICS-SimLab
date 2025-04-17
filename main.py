#!/usr/bin/env python3

# FILE:     main.py
# PURPOSE:  Convenient entry point to start the ICS simulation

import subprocess
import argparse
from src import ics_setup
from pathlib import Path

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
                    prog='ICS-SimLab',
                    description='Industrial Control System Simulator',
                    epilog='Refer to full documentation on how to properly configure an ICS simulation')
    
    parser.add_argument("directory")
    args = parser.parse_args()

    # get absolute parent path
    root_path = Path(__file__).resolve().parent

    # build everything
    print("BUILDING SIMULATION FILES")
    ics_setup.build(args.directory)

    # build images
    print("BUILDING IMAGES")
    dc_build = subprocess.Popen(["docker", "compose", "-f", f"{root_path}/docker-compose.yaml", "build"])

    dc_build.wait()
    print("DONE! Now run \"docker compose up\" in your terminal.")