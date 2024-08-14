#!/bin/bash

# Build the Docker image
docker build -f docker/Dockerfile --no-cache -t linkedinauto-jupyterlab .

CONTAINER_NAME="linkedinauto"

# Remove the existing container if it exists
docker rm -f "$CONTAINER_NAME"

# Get the current working directory (for Git Bash on Windows use $(pwd -W))
CURRENT_DIR=$(pwd -W)
# For Git Bash on Windows, you might need: CURRENT_DIR=$(pwd -W)

# Run the Docker container
docker run -p 8888:8888 -v "$CURRENT_DIR/module:/app" --name "$CONTAINER_NAME" -d linkedinauto-jupyterlab:latest
