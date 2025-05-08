#!/bin/bash

if [ -z "$1" ]; then
    echo "Usage: $0 <config_directory>"
    exit 1
fi

echo "ICS-SimLab SETUP STARTED"

echo "DOWN PREVIOUS CONTAINERS"
docker compose down 

echo "PRUNING DOCKER"
docker system prune -f

echo "CREATING PYTHON ENVIRONMENT"
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

echo "ACTIVATING ENVIRONMENT AND INSTALLING REQUIREMENTS"
source .venv/bin/activate
pip3 install -r requirements.txt

echo "BUILDING SIMULATION FILES"
python3 main.py $1

echo "DOCKER_COMPOSE BUILD"
docker compose build

echo "DOCKER_COMPOSE UP"
docker compose up