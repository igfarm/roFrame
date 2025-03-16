# roFrame - A Picture Frame with Roon Display

![roFrame](assets/pic3.jpg)

A simple digital frame that shows "Now Playing" information from a Roon audio zone. It communicates with Roon as an extension. When music is not playing, it cycles through a user-defined slideshow of images.

## Features

- Connection: Connects to Roon over Wi-Fi as an extension, so only a power cable is needed, and it can be placed where you like to see it.
- Slideshow: Displays images from a local pictures directory when no music is playing.
- Roon Metadata: Shows currently playing track information (artist, track title, album art, etc.) for a chosen Roon zone.
- Kiosk Mode: Automatically launches in a full-screen browser on Raspberry Pi OS (with optional display power management).
- Lightweight: Uses a simple Python app and minimal services to run efficiently on a Raspberry Pi.

## Setup

Assuming you have freshly installed the latest Raspberry Pi OS Lite (bookworm) on an SD card, enabled Wi-Fi and SSH access, and opened a remote terminal to the board.

### Install Application

Update OS and install required packages:

    sudo apt update
    sudo apt install -y git

Install application:

    mkdir ~/work
    cd ~/work
    git clone https://github.com/igfarm/roFrame
    cd roFrame
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt

Make a copy of the configuration and update `NAME` to have a unique name for this device:

    cp .env.example .env
    nano .env

Start the discovery program, and go to Roon extensions to approve it:

    python discovery.py

This will list all available zones. Edit .env file to add update `ROON_ZONE` to one of those values.

Add a few images to the `pictures` folder. In my case, the panel I am using has a resolution of 1024x600, so pictures should be that size. If you don't do this step, you will be rewarded with some modern art on your frame.

Test that things are working as expected by starting the frame application:

    python app.py

and open a browser and open the URL of the machine the app is running on as indicated when running the app.

### Parameters in `.env` file

The application requires the following environment variables to be set.

| Variable Name                  | Description                         | Required | Possible Values                                                                               | Default            |
| ------------------------------ | ----------------------------------- | -------- | --------------------------------------------------------------------------------------------- | ------------------ |
| `DISPLAY_CONTROL`              | Enables or disables display control | ❌ No    | `on`, `off`                                                                                   | `on`               |
| `DISPLAY_OFF_HOUR`             | Hour to turn off the display        | ❌ No    | `0-23` (e.g., `22`)                                                                           | `22`               |
| `DISPLAY_ON_HOUR`              | Hour to turn on the display         | ❌ No    | `0-23` (e.g., `10`)                                                                           | `10`               |
| `IMAGE_SIZE`                   | Image size in pixels                | ❌ No    | Any number (e.g., `600`)                                                                      | `600`              |
| `NAME`                         | Unique device name                  | ✅ Yes   | Any string (e.g., `Display`)                                                                  |                    |
| `PORT`                         | Application port                    | ❌ No    | Any number (e.g., `5006`)                                                                     | `5006`             |
| `ROON_API_KEY_FNAME`           | Filename for Roon API key           | ❌ No    | Any filename                                                                                  | `roon_api_key.txt` |
| `ROON_CORE_ID_FNAME`           | Filename for Roon Core ID           | ❌ No    | Any filename                                                                                  | `roon_core_id.txt` |
| `ROON_ZONE`                    | Roon zone name                      | ✅ Yes   | Any string (e.g., `Livingroom`)                                                               |                    |
| `SLIDESHOW`                    | Enables or disables slideshow       | ❌ No    | `on`, `off`                                                                                   | `on`               |
| `SLIDESHOW_FOLDER`             | Folder path for slideshow images    | ❌ No    | Any folder path (e.g., `./pictures`)                                                          | `./pictures`       |
| `SLIDESHOW_TRANSITION_SECONDS` | Time per slide transition (seconds) | ❌ No    | Any number (e.g., `15`)                                                                       | `15`               |
| `TZ`                           | Timezone setting                    | ❌ No    | Valid timezone, see [Wikipedia](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones) | `America/New_York` |

### Install and configure OS

Install required packages:

    sudo apt update
    sudo apt install -y xserver-xorg xinit chromium-browser unclutter

Create an `.xinit` file that `startx` will execute once it starts running:

    cat << EOF > ~/.xinitrc
    #!/bin/bash

    # A small wait to make sure needed services have started
    sleep 10

    # Disable mouse and power management
    unclutter -idle 0.1 -root &
    xset dpms 0 0 0
    xset -dpms      # Disable power management
    xset s off      # Disable screen saver
    xset s noblank  # Prevent screen blanking

    # Start Chromium in kiosk mode
    exec chromium-browser --noerrdialogs --disable-infobars --hide-scrollbars --kiosk "http://127.0.0.1:5006"
    EOF

    chmod +x ~/.xinitrc

Install the application's service:

    cd ~/work/roFrame

    sudo cp frame.service /lib/systemd/system/
    sudo sed -i "s|PATH|$(pwd)|g" /lib/systemd/system/frame.service
    sudo sed -i "s|USER|$(whoami)|g" /lib/systemd/system/frame.service
    sudo systemctl enable frame.service

Install the kiosk service:

    sudo cp kiosk.service /lib/systemd/system/
    sudo sed -i "s|USER|$(whoami)|g" /lib/systemd/system/kiosk.service
    sudo systemctl enable kiosk.service

Allow `startx` to be started by a service:

    sudo sed -i "s|allowed_users=console|allowed_users=anybody|g" /etc/X11/Xwrapper.config

Reboot the Pi:

    sudo reboot

The frame should come up and you should see some pictures on the screen.

### Debugging

To see the frame service logs:

    journalctl -u frame -e

To see the kiosk service logs:

    journalctl -u kiosk -e

## Hardware

In my case, this is what I used:

- 10.1" display - https://www.amazon.com/dp/B09XDK2FRR
- Raspberry Pi 4 with 2GB RAM - https://www.amazon.com/gp/product/B07TYK4RL8
- 32GB SD Card - https://www.amazon.com/SanDisk-128GB-Extreme-UHS-I-Memory/dp/B09X7FXHVJ

It may run on different hardware, but software configuration might be different than described here.

![roFrame back](assets/pic2.png)

## Acknowledgments

- https://github.com/geerlingguy/pi-kiosk - Inspiration on setting up Kiosk mode
- https://github.com/pavoni/pyroon - Python interface to Roon Core
- https://darko.audio/2025/03/how-to-put-roons-now-playing-screen-on-a-tv-or-monitor/ - Article that gave me the idea of creating this app.

## License

[Apache 2.0](LICENSE)

## Author

This project was created by Jaime Pereira in 2025.
