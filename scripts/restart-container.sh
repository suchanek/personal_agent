#!/bin/bash

# restart-container.sh

CONTAINER_NAME=$1

if [ -z "$CONTAINER_NAME" ]; then
  echo "Usage: $0 <container_name>"
  exit 1
fi

echo "Attempting to restart container: $CONTAINER_NAME"

# Check if the container exists (either running or stopped)
if [ -z "$(docker ps -aq -f name=$CONTAINER_NAME)" ]; then
  echo "Error: Container '$CONTAINER_NAME' not found."
  exit 1
fi

echo "Restarting container..."
if docker restart $CONTAINER_NAME > /dev/null; then
  echo "Container '$CONTAINER_NAME' has been successfully restarted."
else
  echo "Error: Failed to restart container '$CONTAINER_NAME'."
  exit 1
fi
