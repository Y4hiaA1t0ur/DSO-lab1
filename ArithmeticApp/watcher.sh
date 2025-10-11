#!/bin/bash

# Configuration
IMAGE_NAME="flask-arithmetic-api"
CONTAINER_NAME="flask_api_container"
WATCH_DIR="./"
HASH_TARGETS='*.py Dockerfile'

# Initial build and run
echo "Starting initial build..."
docker build -t $IMAGE_NAME .
docker rm -f $CONTAINER_NAME 2>/dev/null
docker run -d -p 5000:5000 --name $CONTAINER_NAME $IMAGE_NAME
echo "Container started at http://localhost:5000"

# Record initial file hash state (so no double rebuild)
LAST_HASH=$(find $WATCH_DIR -type f \( -name "*.py" -o -name "Dockerfile" \) -exec md5sum {} \; | md5sum)

# Watch for changes (polling mode)
echo "Watching $WATCH_DIR for changes..."
while true; do
    NEW_HASH=$(find $WATCH_DIR -type f \( -name "*.py" -o -name "Dockerfile" \) -exec md5sum {} \; | md5sum)
    if [ "$NEW_HASH" != "$LAST_HASH" ]; then
        echo "Change detected! Rebuilding and redeploying container..."
        LAST_HASH=$NEW_HASH

        docker rm -f $CONTAINER_NAME 2>/dev/null
        docker build -t $IMAGE_NAME .
        docker run -d -p 5000:5000 --name $CONTAINER_NAME $IMAGE_NAME

        echo "✅ Rebuild complete! Running latest version at http://localhost:5000"
    fi
    sleep 3
done
