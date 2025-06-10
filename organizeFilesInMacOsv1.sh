#!/bin/bash

# Navigate to Downloads folder
cd ~/Downloads

# Create Images folder if it doesn't exist
mkdir -p Images

# Move all common image file types to Images folder
find . -maxdepth 1 \( -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png" -o -iname "*.gif" -o -iname "*.bmp" -o -iname "*.tiff" -o -iname "*.tif" -o -iname "*.webp" -o -iname "*.svg" -o -iname "*.ico" \) -exec mv {} Images/ \;

echo "All image files have been moved to the Images folder!"