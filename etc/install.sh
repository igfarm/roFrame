#!/bin/bash

# make sure we are on a raspberry pi
set -euo pipefail

is_latest_rpi4_64bit() {
    # --- 1. OS check: Debian 12 (Bookworm) ---
    grep -q 'VERSION_CODENAME=bookworm' /etc/os-release || return 1

    # --- 2. Architecture check: 64-bit (arm64) ---
    [[ $(uname -m) == "aarch64" ]] || return 1

    # --- 3. Hardware check: Raspberry Pi 4 / CM4 ---
    if grep -q 'Raspberry Pi 4' /proc/device-tree/model 2>/dev/null; then
        return 0
    else
        local rev
        rev=$(awk '/^Revision/ {print $3}' /proc/cpuinfo 2>/dev/null)
        [[ $rev == d0* ]] || return 1
    fi

    return 0
}

if is_latest_rpi4_64bit; then
    echo "✅ Verified: Raspberry Pi 4, 64-bit, Debian 12 (Bookworm)"
else
    echo "⚠️ This system is NOT a Raspberry Pi 4 running 64-bit Debian 12 (Bookworm)."
    read -rp "Do you want to continue anyway? [y/N] " response
    case "$response" in
        [yY][eE][sS]|[yY])
            echo "🔄 Continuing anyway..."
            ;;
        *)
            echo "❌ Exiting script."
            exit 1
            ;;
    esac
fi

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
rm ~/.xinint
ln -s $(pwd)/etc/xinitrc  ~/.xinitrc

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
