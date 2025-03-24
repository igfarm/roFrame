#!/bin/bash

# Update package lists and install Git
sudo apt update
sudo apt install -y git xserver-xorg xinit chromium-browser unclutter x11-utils

# Clone the application repository
git clone https://github.com/igfarm/roFrame
cd roFrame

# Set up Python virtual environment and install dependencies
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure X11 startup script
cp etc/xinitrc  ~/.xinitrc
chmod +x ~/.xinitrc

# Create and enable the frame service
sudo cp etc/frame.service /lib/systemd/system/
sudo sed -i "s|PATH|$(pwd)|g" /lib/systemd/system/frame.service
sudo sed -i "s|USER|$(whoami)|g" /lib/systemd/system/frame.service
sudo systemctl enable frame.service

# Create and enable the kiosk service
sudo cp etc/kiosk.service /lib/systemd/system/
sudo sed -i "s|USER|$(whoami)|g" /lib/systemd/system/kiosk.service
sudo systemctl enable kiosk.service

# Fix X11 startup
sudo sed -i "s|allowed_users=console|allowed_users=anybody|g" /etc/X11/Xwrapper.config

