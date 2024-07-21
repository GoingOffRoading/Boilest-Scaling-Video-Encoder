#!/bin/bash

# Navigate to the project root directory
cd "$(dirname "$0")/.."

# Build the Docker images
docker build -t manager -f 01_Manager/Dockerfile .
docker build -t worker -f 02_Worker/Dockerfile .

# Run the Docker containers
docker run -p 5000:5000 -p 5555:5555 -d manager:latest
docker run --volume=/c/cwest/YOU/Videos:/tv -d worker:latest