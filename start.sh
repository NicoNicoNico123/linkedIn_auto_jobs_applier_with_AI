#!/usr/bin/env bash

# Set variables
CONTAINER_NAME="linkedinauto"
IMAGE_NAME="linkedinauto-dynamic"
DOCKER_DIR="$(pwd -W)/docker"
DOCKERFILE_PATH="$DOCKER_DIR/Dockerfile"

# Get current directory using pwd -W
CURRENT_DIR=$(pwd -W)

# Ensure config.toml and start_jupyter.sh exist in the docker folder
if [ ! -f "$DOCKER_DIR/config.toml" ] || [ ! -f "$DOCKER_DIR/start_jupyter.sh" ]; then
    echo "Error: config.toml and start_jupyter.sh must be in the docker directory."
    exit 1
fi

# Build the Docker image
echo "Building Docker image..."
if ! docker build -f "$DOCKERFILE_PATH" -t $IMAGE_NAME "$DOCKER_DIR"; then
    echo "Docker build failed. Please check your Dockerfile and try again."
    exit 1
fi

# Remove existing container if it exists
echo "Removing existing container if it exists..."
docker rm -f $CONTAINER_NAME 2>/dev/null

# Run the Docker container
echo "Starting the container..."
if ! docker run -d \
  -p 4444:4444 \
  -p 8888:8888 \
  -v "${CURRENT_DIR}/module":/app \
  -v "${CURRENT_DIR}/assets":/opt/selenium/assets \
  -v //var/run/docker.sock:/var/run/docker.sock \
  --name $CONTAINER_NAME \
  $IMAGE_NAME
then
    echo "Failed to start the container. Please check the Docker logs."
    exit 1
fi

# Check if the container is running
if [ "$(docker ps -q -f name=$CONTAINER_NAME)" ]; then
    echo "Container $CONTAINER_NAME is running."
    echo "Selenium Grid is available at http://localhost:4444"
    echo "JupyterLab is available at http://localhost:8888"
    echo "Please wait a moment for the services to fully start."
else
    echo "Failed to start the container. Showing logs:"
    docker logs $CONTAINER_NAME
    exit 1
fi