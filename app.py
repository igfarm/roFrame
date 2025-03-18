import os
import subprocess
from datetime import datetime
import zoneinfo
import time
from threading import Event
import asyncio
import logging
import sdnotify  # Add this import

from flask import Flask, render_template, jsonify, send_from_directory
from flask_socketio import SocketIO, emit
from dotenv import load_dotenv
from myroonapi import MyRoonApi
from art_generator import generate_mondrian

# Load environment variables from .env file
load_dotenv()

my_tz = zoneinfo.ZoneInfo(os.getenv("TZ", "America/New_York"))

myRoonApi = MyRoonApi()

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")
thread = None
thread_stop_event = Event()

name = os.getenv("NAME", "roFrame")
port = int(os.getenv("PORT", 5006))
display_on_hour = int(os.getenv("DISPLAY_ON_HOUR", 9))
display_off_hour = int(os.getenv("DISPLAY_OFF_HOUR", 23))
display_control = os.getenv("DISPLAY_CONTROL", "off")
slideshow_enabled = os.getenv("SLIDESHOW", "on") == "on"
slideshow_folder = os.getenv(
    "SLIDESHOW_FOLDER", os.path.join(app.root_path, "./pictures")
)
slideshow_transition_seconds = int(os.getenv("SLIDESHOW_TRANSITION_SECONDS", 15))
slideshow_clock_ratio = int(os.getenv("SLIDESHOW_CLOCK_RATIO", 0)) / 100

clock_size = int(os.getenv("CLOCK_SIZE", 0))
clock_offset = int(os.getenv("CLOCK_OFFSET", 0))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def getRoonApi():
    global myRoonApi

    # if not myRoonApi.is_connected():
    #    logger.info("Connecting to Roon API")
    #    myRoonApi.connect(notify_clients=notify_clients)

    return myRoonApi


def display(turn_on):
    """Function to control the display"""
    state = "on" if turn_on else "off"
    if display_control == "on":
        subprocess.check_output(["xset", "dpms", "force", state])
    logger.info(f"display: {state}")


def is_screen_on(current_hour, on_hour, off_hour):
    if on_hour == off_hour:
        return False  # Device should be off if on and off hours are the same
    if on_hour < off_hour:
        return on_hour <= current_hour < off_hour  # Normal range
    else:
        return not (off_hour <= current_hour < on_hour)  # Overnight case


def background_thread():
    """
    A background thread that emits a message every 10 minutes.
    """
    while not thread_stop_event.is_set():
        myRoonApi = getRoonApi()
        album = myRoonApi.get_zone_data()
        state = album.get("state")
        current_hour = datetime.now().astimezone(my_tz).hour

        # Turn off screen during certain hours
        if state in ["playing", "loading"] or is_screen_on(
            current_hour, display_on_hour, display_off_hour
        ):
            display(True)
        else:
            display(False)

        time.sleep(600)


@app.route("/")
def index():
    images = []
    art_images = []
    if slideshow_enabled:
        images = os.listdir(slideshow_folder)
        image_extensions = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff"}
        images = [
            img
            for img in images
            if os.path.splitext(img)[1].lower() in image_extensions
        ]
        if not images:
            art_images = [generate_mondrian() for _ in range(10)]

    return render_template(
        "index.html",
        name=name,
        images=images,
        art_images=art_images,
        transition_seconds=slideshow_transition_seconds,
        slideshow_clock_ratio=slideshow_clock_ratio,
        clock_size=clock_size,
        clock_offset=clock_offset,
    )


@app.route("/slideshow/<filename>")
def slideshow_pic(filename):
    if filename not in os.listdir(slideshow_folder):
        return jsonify({"error": "File not found"}), 404
    return send_from_directory(slideshow_folder, filename)


@app.route("/static/<path:filename>")
def static_files(filename):
    """Serve static files from the static directory."""
    return send_from_directory(os.path.join(app.root_path, "static"), filename)


@socketio.on("connect")
def handle_connect():
    logger.info("Socket client connected")
    emit("response", {"data": "Connected"})

    # Start the background thread if it’s not running yet
    global thread
    if thread is None or not thread.is_alive():
        thread = socketio.start_background_task(background_thread)


@socketio.on("disconnect")
def handle_disconnect():
    logger.info("Client disconnected")


@socketio.on("trigger_album_update")
def trigger_album_update():
    logger.info("trigger_album_update")
    myRoonApi = getRoonApi()
    album = myRoonApi.get_zone_data()
    asyncio.run(notify_clients(album))  # Use asyncio.run to await the coroutine

    if album["state"] in ["playing", "loading"]:
        display(True)


async def notify_clients(message):
    logger.info("notify_clients")
    logger.info(message)
    socketio.emit("album_update", message)
    if message.get("state") in ["playing", "loading"]:
        display(True)


if __name__ == "__main__":
    # start the Roon
    if not myRoonApi.check_auth():
        logger.error("Please authorise first using discovery.py")
        exit()
    if not myRoonApi.connect(notify_clients=notify_clients):
        logger.error("Unable to connect to Roon")
        exit()

    # Notify systemd that the service is ready
    n = sdnotify.SystemdNotifier()
    n.notify("READY=1")

    # Start the Flask web server
    socketio.run(
        app, debug=False, port=port, host="0.0.0.0", allow_unsafe_werkzeug=True
    )
