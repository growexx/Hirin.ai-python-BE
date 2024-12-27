#!/bin/bash

# Define source and destination directories
SOURCE_DIR="/tmp/python/python-deploy/AI-CV-Screening/*"
DEST_DIR="/home/opc/python/Hirin.ai-python-BE-main/AI-CV-Screening/"

# Copy files from source to destination
echo "Copying files from $SOURCE_DIR to $DEST_DIR..."
cp -Rf $SOURCE_DIR $DEST_DIR && ls -ltrah $DEST_DIR

# Check if the copy command was successful
if [ $? -eq 0 ]; then
  echo "Files copied successfully to $DEST_DIR"
else
  echo "Failed to copy files to $DEST_DIR"
fi
