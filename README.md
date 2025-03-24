# roFrame - A Picture Frame with Roon Display

![roFrame](assets/pic3.jpg)

A simple digital frame that shows "Now Playing" information from a Roon audio zone. It communicates with Roon as an extension. When music is not playing, it cycles through a user-defined slideshow of images.

## Features

- Connection: Connects to Roon over Wi-Fi as an extension, so only a power cable is needed, and it can be placed where you like to see it.
- Slideshow: Displays images from a local pictures directory when no music is playing in Roon.
- Analog Clock: Option to enable clock display to intermingle or replace slideshow.
- Roon Metadata: Shows currently playing track information (artist, track title, album art, etc.) for a chosen Roon zone.
- Kiosk Mode: Automatically launches in a full-screen browser on Raspberry Pi OS (with optional display power management).
- Lightweight: Uses a simple Python app and minimal services to run efficiently on a Raspberry Pi.
- Orientation: Landscape mode, portait mode optional.

## Setup

Assuming you have Raspberry Pi 4 with the display connected to it, freshly installed the latest Raspberry Pi OS Lite (64 bit - bookworm) on an SD card, enabled Wi-Fi and SSH access, and opened a remote terminal to the board.

When logged into the Raspberry pi page the following command:

    wget https://raw.githubusercontent.com/igfarm/roFrame/main/etc/install.sh
   
Inspect the script:

    less install.sh

Run the script to do the installation:

    bash ./install.sh


When installation finishes, do the initial discovery to register the device with Roon:

    ./venv/bin/python discovery.py


Optionally add a few images into the pictures directory:

    ./venv/bin/python etc/get_images.py landscape


After that completes, reboot the system:

    sudo reboot

Once system reboots, you can visit the following URL to update the settings:

    http://<ipaddr>/settings



### Parameters in `.env` file

The application requires the following environment variables to be set.

| Variable Name                  | Description                                | Required | Possible Values                                                                               | Default            |
| ------------------------------ | ------------------------------------------ | -------- | --------------------------------------------------------------------------------------------- | ------------------ |
| `CLOCK_SIZE`                   | Diameter of clock in pixels                | No       | `0` means autosize.                                                                           | `0`                |
| `CLOCK_OFFSET`                 | Clock offset pixels from top of the screen | No       | `0` means autosize.                                                                           | `0`                |
| `DISPLAY_CONTROL`              | Enables or disables display control        | No       | `on`, `off`                                                                                   | `on`               |
| `DISPLAY_OFF_HOUR`             | Hour to turn off the display               | No       | `0-23` (e.g., `22`)                                                                           | `22`               |
| `DISPLAY_ON_HOUR`              | Hour to turn on the display                | No       | `0-23` (e.g., `10`)                                                                           | `10`               |
| `IMAGE_SIZE`                   | Album image size in pixels                 | No       | Any number (e.g., `600`)                                                                      | `600`              |
| `NAME`                         | Unique device name                         | Yes      | Any string (e.g., `Display`)                                                                  |                    |
| `PORT`                         | Application port                           | No       | Any number (e.g., `5006`)                                                                     | `5006`             |
| `ROON_API_KEY_FNAME`           | Filename for Roon API key                  | No       | Any filename                                                                                  | `roon_api_key.txt` |
| `ROON_CORE_ID_FNAME`           | Filename for Roon Core ID                  | No       | Any filename                                                                                  | `roon_core_id.txt` |
| `ROON_ZONE`                    | Roon zone name                             | Yes      | Any string (e.g., `Livingroom`)                                                               |                    |
| `SLIDESHOW`                    | Enables or disables slideshow              | No       | `on`, `off`                                                                                   | `on`               |
| `SLIDESHOW_FOLDER`             | Folder path for slideshow images           | No       | Any folder path (e.g., `./pictures`)                                                          | `./pictures`       |
| `SLIDESHOW_TRANSITION_SECONDS` | Time per slide transition (seconds)        | No       | Any number (e.g., `15`)                                                                       | `0`                |
| `SLIDESHOW_CLOCK_RATIO`        | How often to show the clock                | No       | `0-100` (`0` is never, `100` is always)                                                       | `0`                |
| `TZ`                           | Timezone setting                           | No       | Valid timezone, see [Wikipedia](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones) | `America/New_York` |

### Sample Configuations

Display is only on when Roon is playing

    DISPLAY_ON_HOUR=0
    DISPLAY_OFF_HOUR=0

Display is on from 9AM to 10PM and shows clock when Roon is not playing

    DISPLAY_ON_HOUR=9
    DISPLAY_OFF_HOUR=22
    SLIDESHOW_CLOCK_RATIO=100

Display is on from 1AM to 1PM and shows slide show (or art show) when Roon is not playing.

    DISPLAY_ON_HOUR=1
    DISPLAY_OFF_HOUR=13
    SLIDESHOW_CLOCK_RATIO=0

Display is on from 11PM to 6AM and alternates between slide slide show (or art show) and clock 50% of the time when Roon is not playing.

    DISPLAY_ON_HOUR=22
    DISPLAY_OFF_HOUR=6
    SLIDESHOW_CLOCK_RATIO=50

### Portrait Mode

The systems comes out of the box in Landscape mode. You can also configure it to run in Portrait mode by adding the following line at the top of the `~/.xinitrc` file.

    xrandr --output HDMI-1 --rotate right

### Getting Public Domain Art

You can get free art to display in your frame, complements of the [Art Institute of Chicago](https://api.artic.edu/docs/#introduction) API, by using the following command:
show in your frame:

    ./venv/bin/python etc/get_art.py landscape

## Debugging

To see the frame service logs:

    journalctl -u frame -e

To see the kiosk service logs:

    journalctl -u kiosk -e

Restart processes after `.env` change:

    ./etc/restart.sh

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
