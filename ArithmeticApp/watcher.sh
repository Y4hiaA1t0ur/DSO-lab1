#!/bin/bash

# ===============================
# Auto Docker Rebuild Watcher
# (Monitors local file changes AND remote Git commits)
# ===============================

# --- Configuration ---
IMAGE_NAME="flask-arithmetic-api"
CONTAINER_NAME="flask_api_container"
WATCH_DIR="./"
BRANCH="main"
CHECK_INTERVAL=10       # seconds between Git checks

# --- Initial build and run ---
echo "Starting initial build..."
docker build -t $IMAGE_NAME .
docker rm -f $CONTAINER_NAME 2>/dev/null
docker run -d -p 5000:5000 --name $CONTAINER_NAME $IMAGE_NAME
echo "Container started at http://localhost:5000"

# --- Record initial file hash and git commit ---
LAST_HASH=$(find $WATCH_DIR -type f \( -name "*.py" -o -name "Dockerfile" \) -exec md5sum {} \; | md5sum)
git fetch origin $BRANCH >/dev/null 2>&1
LAST_COMMIT=$(git rev-parse origin/$BRANCH 2>/dev/null)

echo "Watching local changes in $WATCH_DIR and remote branch '$BRANCH'..."
echo "Initial commit hash: $LAST_COMMIT"

# --- Helper: rebuild and redeploy container ---
rebuild_container() {
    echo "🧱 Rebuilding Docker image and redeploying container..."
    docker rm -f $CONTAINER_NAME >/dev/null 2>&1
    docker build -t $IMAGE_NAME .
    docker run -d -p 5000:5000 --name $CONTAINER_NAME $IMAGE_NAME
    echo "✅ Redeployment complete! Running latest version at http://localhost:5000"
}

# --- Main loop ---
while true; do
    # Check for local file changes
    NEW_HASH=$(find $WATCH_DIR -type f \( -name "*.py" -o -name "Dockerfile" \) -exec md5sum {} \; | md5sum)
    if [ "$NEW_HASH" != "$LAST_HASH" ]; then
        echo "📝 Local change detected! Rebuilding..."
        LAST_HASH=$NEW_HASH
        rebuild_container
    fi

    # Check for new Git commits
    git fetch origin $BRANCH >/dev/null 2>&1
    NEW_COMMIT=$(git rev-parse origin/$BRANCH 2>/dev/null)
    if [ "$NEW_COMMIT" != "$LAST_COMMIT" ]; then
        echo "🔄 New remote commit detected!"
        echo "Old commit: $LAST_COMMIT"
        echo "New commit: $NEW_COMMIT"
        LAST_COMMIT=$NEW_COMMIT

        git pull origin $BRANCH
        rebuild_container
    fi

    sleep $CHECK_INTERVAL
done
