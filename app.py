import os
import subprocess
from datetime import datetime
import zoneinfo
import time
from threading import Thread, Event
import asyncio  # Add asyncio import

from flask import Flask, render_template, jsonify, send_from_directory
from flask_socketio import SocketIO, emit
from dotenv import load_dotenv
from myroonapi import MyRoonApi
from art_generator import generate_mondrian

# Load environment variables from .env file
load_dotenv()

my_tz = zoneinfo.ZoneInfo(os.getenv("TZ", "America/New_York"))

myRoonApi = None

app = Flask(__name__)
socketio = SocketIO(
    app, cors_allowed_origins="*"
)
thread = None
thread_stop_event = Event()

name = os.getenv("NAME", "roFrame")
port = int(os.getenv("PORT", 5006))
image_size = int(os.getenv("IMAGE_SIZE", 600))
slideshow_transition_seconds = int(os.getenv("SLIDESHOW_TRANSITION_SECONDS", 15))
display_on_hour = int(os.getenv("DISPLAY_ON_HOUR", 9))
display_off_hour = int(os.getenv("DISPLAY_OFF_HOUR", 23))
display_control = os.getenv("DISPLAY_CONTROL", "off")
pictures_folder = os.getenv("PICTURE_FOLDER", os.path.join(app.root_path, "pictures"))


def getRoonApi():
    global myRoonApi
    if myRoonApi is None:
        myRoonApi = MyRoonApi()
        myRoonApi.connect(notify_clients=notify_clients)
    return myRoonApi


def display(turn_on):
    """Function to control the display"""
    state = "on" if turn_on else "off"
    if display_control == "on":
        subprocess.check_output(["xset", "dpms", "force", state])
    print(f"display: {state}")


def background_thread():
    """
    A background thread that emits a message every 10 minutes.
    """
    while not thread_stop_event.is_set():
        myRoonApi = getRoonApi()
        state = myRoonApi.get_zone_state()
        if state == "playing":
            display(True)
        else:
            # add code to turn off screen after 12AM and turn it back on at 6AM
            current_hour = datetime.now().astimezone(my_tz).hour
            if display_off_hour <= current_hour or current_hour < display_on_hour:
                display(False)
            else:
                display(True)
        time.sleep(600)


@app.route("/")
def index():
    # Get the list of images in the pictures folder
    art_images = []
    images = os.listdir(pictures_folder)
    image_extensions = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff"}
    images = [
        img for img in images if os.path.splitext(img)[1].lower() in image_extensions
    ]
    if not images:
        art_images = [generate_mondrian() for _ in range(10)]
    return render_template(
        "index.html",
        images=images,
        art_images=art_images,
        transition_seconds=slideshow_transition_seconds,
    )


@app.route("/slideshow/<filename>")
def slideshow_pic(filename):
    if filename not in os.listdir(pictures_folder):
        return jsonify({"error": "File not found"}), 404
    return send_from_directory(pictures_folder, filename)


@app.route("/static/<path:filename>")
def static_files(filename):
    """Serve static files from the static directory."""
    return send_from_directory(os.path.join(app.root_path, "static"), filename)


@socketio.on("connect")
def handle_connect():
    print("Client connected")
    emit("response", {"data": "Connected"})

    # Start the background thread if it’s not running yet
    global thread
    if thread is None or not thread.is_alive():
        thread = Thread(target=background_thread)
        thread.daemon = True
        thread.start()


@socketio.on("disconnect")
def handle_disconnect():
    print("Client disconnected")


@socketio.on("trigger_album_update")
def trigger_album_update():
    print("trigger_album_update")
    myRoonApi = getRoonApi()
    copy = myRoonApi.get_copy()
    state = myRoonApi.get_zone_state()
    message = {
        "name": name,
        "album_cover_url": myRoonApi.get_image_url(image_size=image_size),
        "state": state,
        "image_size": image_size,
        "album_title": copy["title"],
        "album_artist": copy["artist"],
        "album_track": copy["track"],
    }
    asyncio.run(notify_clients(message))  # Use asyncio.run to await the coroutine

    if state == "playing":
        display(True)


async def notify_clients(message):
    print("notify_clients")
    print(message)
    socketio.emit("album_update", message)
    if "state" in message and message["state"] == "playing":
        display(True)


def check_time():
    while True:
        current_hour = datetime.now().astimezone(my_tz).hour
        print(f"Current hour: {current_hour}")
        if 5 <= current_hour < 10:
            print("The hour is between 5 and 10")
        time.sleep(5)  # Sleep for 15 minutes


if __name__ == "__main__":
    # socketio.start_background_task(check_time())
    socketio.run(app, debug=True, port=port, host="0.0.0.0", allow_unsafe_werkzeug=True)
