#!/bin/bash

# Stop the running containers
docker stop $(docker ps -q --filter ancestor=manager:latest)
docker stop $(docker ps -q --filter ancestor=worker:latest)

# Remove the containers
docker rm $(docker ps -a -q --filter ancestor=manager:latest)
docker rm $(docker ps -a -q --filter ancestor=worker:latest)

# Remove the Docker images
docker rmi manager:latest
docker rmi worker:latest
