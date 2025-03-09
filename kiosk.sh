#!/bin/bash

#. /home/jaime/work/frame/venv/bin/activate
#python app.py > /dev/null 2>&1 &

export DISPLAY=:0

# TODO: Set this to a default, but allow easy override by passing a parameter or
# using the environment variable KIOSK_URL.
KIOSK_URL="http://127.0.0.1:5006/"

# Wait for services to come online.
# TODO: It would be nice to get rid of this, but right now on Bookworm, if we
# don't wait, there are errors at boot and you have to start kiosk manually.
sleep 10

echo 'Hiding the mouse cursor...'
unclutter -idle 0.1 -root &

echo 'Disable screen saver...'
xset dpms 0 0 0
xset s off         # Disable screen saver / screen-blanking
xset -dpms         # Disable DPMS (Display Power Management Signaling)
xset s noblank     # Prevent the screen from blanking

echo 'Starting Chromium...'
/usr/bin/chromium-browser --incognito --noerrdialogs --disable-infobars --kiosk --app=$KIOSK_URL