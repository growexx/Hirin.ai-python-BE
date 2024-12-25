#!/bin/bash

# Define variables
PROJECT_DIR="/home/opc/python/Hirin.ai-python-BE-main/AI-CV-Screening/"
LOG_FILE="/tmp/python/log"
PORT=7000
REQUIREMENTS_FILE="$PROJECT_DIR/requirements.txt"
PIP_PATH="/home/opc/.local/bin/pip"

# Step 1: Navigate to the project directory
echo "Navigating to the project directory: $PROJECT_DIR"
sudo -u ocarun bash -c "cd \"$PROJECT_DIR\" || { echo 'Failed to navigate to project directory: $PROJECT_DIR'; exit 1; }"

# Step 2: Ensure pip is available (explicitly use pip from the local directory if needed)
if [ ! -f "$PIP_PATH" ]; then
    echo "pip not found at $PIP_PATH. Installing pip..."
    sudo -u ocarun python3 -m ensurepip --upgrade || { echo "Failed to install pip."; exit 1; }
fi

# Step 3: Install dependencies
if [ -f "$REQUIREMENTS_FILE" ]; then
    echo "Installing application dependencies from $REQUIREMENTS_FILE..."
    sudo -u ocarun "$PIP_PATH" install -r "$REQUIREMENTS_FILE" || { echo "Failed to install dependencies."; exit 1; }
    echo "Dependencies installed successfully."
else
    echo "Requirements file not found at $REQUIREMENTS_FILE. Skipping dependency installation."
fi

# Step 4: Check for any running process on the specified port and terminate it
echo "Checking for any running process on port $PORT..."
if sudo -u ocarun lsof -i:"$PORT" > /dev/null; then
    echo "Process found on port $PORT. Terminating it..."
    sudo kill $(sudo -u ocarun lsof -ti:"$PORT") || { echo "Failed to terminate process on port $PORT."; exit 1; }
    echo "Process on port $PORT terminated successfully."
else
    echo "No process running on port $PORT."
fi

# Step 5: Start the Python application
echo "Starting the Python application..."
sudo -u ocarun bash -c "cd \"$PROJECT_DIR\" && nohup python3 run.py > \"$LOG_FILE\" 2>&1 &"

if [ $? -eq 0 ]; then
    echo "Application started successfully. Logs available at $LOG_FILE."
else
    echo "Failed to start the application."
    exit 1
fi
