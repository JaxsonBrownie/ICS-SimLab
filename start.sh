#!/bin/bash

if [ -z "$1" ]; then
    echo "Usage: $0 <config_directory>"
    exit 1
fi

echo "ICS-SimLab STARTED"

echo "ACTIVATING ENVIRONMENT"
source .venv/bin/activate

echo "BUILDING SIMULATION FILES"
python3 main.py $1

echo "DOCKER_COMPOSE BUILD"
docker compose build

echo "DOCKER_COMPOSE UP"
docker compose up