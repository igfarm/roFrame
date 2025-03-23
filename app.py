import os
import subprocess
from datetime import datetime
import zoneinfo
import time
from threading import Event
import asyncio
import logging
import sdnotify  # Add this import
import threading  # Add this import

from flask import (
    redirect,
    url_for,
    request,
    Flask,
    render_template,
    jsonify,
    send_from_directory,
)
from flask_socketio import SocketIO, emit
from dotenv import load_dotenv
from myroonapi import MyRoonApi
from art_generator import generate_mondrian

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True  # Enable auto-reloading of templates
socketio = SocketIO(app, cors_allowed_origins="*")
thread = None
thread_stop_event = Event()


def load_config():
    """Load configuration from environment variables into global scope."""
    global name, display_on_hour, display_off_hour, display_control, slideshow_enabled
    global slideshow_folder, slideshow_transition_seconds, slideshow_clock_ratio
    global clock_size, clock_offset, index_file, host, port, my_tz

    # Load environment variables from .env file
    load_dotenv()

    my_tz = zoneinfo.ZoneInfo(os.getenv("TZ", "America/New_York"))
    name = os.getenv("NAME", "")
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
    index_file = os.getenv("INDEX_FILE", "index.html")
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 5006))


load_config()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

display_state = False

myRoonApi = None
if name:
    print("name")
    myRoonApi = MyRoonApi()


def getRoonApi():
    global myRoonApi

    # if not myRoonApi.is_connected():
    #    logger.info("Connecting to Roon API")
    #    myRoonApi.connect(notify_clients=notify_clients)

    return myRoonApi


def display(turn_on):
    global display_state
    display_state = turn_on

    """Function to control the display"""
    state = "on" if turn_on else "off"
    if display_control == "on":
        try:
            subprocess.check_output(["xset", "dpms", "force", state])
        except subprocess.CalledProcessError as e:
            logger.warning("problem with xset")
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


def resave_env():
    # Load existing .env variables into a dictionary
    existing_env_vars = {}
    with open(".env", "r") as env_file:
        for line in env_file:
            if "=" in line:
                key, value = line.strip().split("=", 1)
                existing_env_vars[key] = os.getenv(key, value)

    # Sort the dictionary by keys
    sorted_env_vars = dict(sorted(existing_env_vars.items()))

    # Write the updated dictionary back to the .env file
    logger.info("saving setup data")
    with open(".env", "w") as env_file:
        for key, value in sorted_env_vars.items():
            env_file.write(f"{key}={value}\n")


@app.route("/ping")
def ping():
    return jsonify({"message": "pong"})


@app.route("/")
def index():

    if not os.path.exists(".env"):
        return redirect(url_for("init"))

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
        index_file,
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


@app.route("/settings", methods=["GET", "POST"])
def settings():

    if not os.path.exists(".env"):
        return redirect(url_for("init"))

    if request.method == "POST":

        # Load existing .env variables into a dictionary
        existing_env_vars = {}
        if os.path.exists(".env"):
            with open(".env", "r") as env_file:
                for line in env_file:
                    if "=" in line:
                        key, value = line.strip().split("=", 1)
                        existing_env_vars[key] = value

        # Get form data and validate inputs
        try:
            display_on_hour = int(request.form.get("DISPLAY_ON_HOUR", "9"))
            display_off_hour = int(request.form.get("DISPLAY_OFF_HOUR", "23"))
            if not (0 <= display_on_hour <= 23 and 0 <= display_off_hour <= 23):
                raise ValueError("Display hours must be between 0 and 23.")

            slideshow_transition_seconds = int(
                request.form.get("SLIDESHOW_TRANSITION_SECONDS", "15")
            )
            if slideshow_transition_seconds <= 0:
                raise ValueError(
                    "Slideshow transition seconds must be a positive integer."
                )

            slideshow_clock_ratio = int(request.form.get("SLIDESHOW_CLOCK_RATIO", "0"))
            if not (0 <= slideshow_clock_ratio <= 100):
                raise ValueError("Slideshow clock ratio must be between 0 and 100.")

            clock_size = int(request.form.get("CLOCK_SIZE", "0"))
            if clock_size < 0:
                raise ValueError("Clock size must be a non-negative integer.")

            clock_offset = int(request.form.get("CLOCK_OFFSET", "0"))
            if clock_offset < 0:
                raise ValueError("Clock offset must be a non-negative integer.")
        except ValueError as e:
            logger.error(f"Invalid input: {e}")
            return jsonify({"error": str(e)}), 400

        # Prepare form data for updating the .env file
        form_env_vars = {
            "ROON_ZONE": request.form.get("ROON_ZONE", os.getenv("ROON_ZONE", "")),
            "DISPLAY_ON_HOUR": str(display_on_hour),
            "DISPLAY_OFF_HOUR": str(display_off_hour),
            "DISPLAY_CONTROL": request.form.get("DISPLAY_CONTROL", "off"),
            "SLIDESHOW": request.form.get("SLIDESHOW", "on"),
            "SLIDESHOW_TRANSITION_SECONDS": str(slideshow_transition_seconds),
            "SLIDESHOW_CLOCK_RATIO": str(slideshow_clock_ratio),
            "CLOCK_SIZE": str(clock_size),
            "CLOCK_OFFSET": str(clock_offset),
        }

        # Update existing_env_vars with form_env_vars
        existing_env_vars.update(form_env_vars)

        # Sort the dictionary by keys
        sorted_env_vars = dict(sorted(existing_env_vars.items()))

        # Write the updated dictionary back to the .env file
        logger.info("saving setup data")
        with open(".env", "w") as env_file:
            for key, value in sorted_env_vars.items():
                env_file.write(f"{key}={value}\n")                

        # Restart the server to apply the new settings
        if os.uname().machine.startswith("aarch64"):
            logger.info("restarting...")
            subprocess.Popen(
                ["/bin/bash", "./etc/restart.sh", "5"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        else:
            threading.Thread(target=lambda: (time.sleep(2), os._exit(0))).start()

        return redirect(url_for("settings"))

    # Load current .env variables
    current_env = {
        "NAME": os.getenv("NAME", "roFrame"),
        "DISPLAY_ON_HOUR": os.getenv("DISPLAY_ON_HOUR", "9"),
        "DISPLAY_OFF_HOUR": os.getenv("DISPLAY_OFF_HOUR", "23"),
        "DISPLAY_CONTROL": os.getenv("DISPLAY_CONTROL", "off"),
        "SLIDESHOW": os.getenv("SLIDESHOW", "on"),
        "SLIDESHOW_FOLDER": os.getenv("SLIDESHOW_FOLDER", "./pictures"),
        "SLIDESHOW_TRANSITION_SECONDS": os.getenv("SLIDESHOW_TRANSITION_SECONDS", "15"),
        "SLIDESHOW_CLOCK_RATIO": os.getenv("SLIDESHOW_CLOCK_RATIO", "0"),
        "CLOCK_SIZE": os.getenv("CLOCK_SIZE", "0"),
        "CLOCK_OFFSET": os.getenv("CLOCK_OFFSET", "0"),
        "PORT": os.getenv("PORT", "5006"),
        "HOST": os.getenv("HOST", "127.0.0.1"),
    }

    # Pass along the current selected zone and a list of available zones
    available_zones = myRoonApi.get_zone_list()
    current_env["ROON_ZONE"] = os.getenv("ROON_ZONE", "")

    current_env["AVAILABLE_ZONES"] = available_zones

    return render_template("settings.html", env=current_env)


@app.route("/init", methods=["GET", "POST"])
def init():

    logger.info("init")
    if os.path.exists(".env"):
        return redirect(url_for("settings"))

    if request.method == "GET":
        print("init")
        return render_template("init.html")

    elif request.method == "POST":
        logger.info("init POST")
        logger.info(request.form)

        name = request.form.get("NAME", "").strip()
        if not name:
            return jsonify({"error": "Name cannot be empty"}), 400

        # Run the register process
        try:
            os.environ["NAME"] = name
            api = MyRoonApi()
            available_zones = api.register()
            os.environ["ROON_ZONE"] = available_zones[0] if available_zones else ""
            subprocess.run(["cp", ".env.example", ".env"], check=True)
            resave_env()

            # Schedule os._exit(0) two seconds after returning
            threading.Thread(target=lambda: (time.sleep(2), os._exit(0))).start()

            return jsonify({"message": "Registration successful"}), 200

        except Exception as e:
            logger.error(f"Error during registration: {e}")
            return jsonify({"error": str(e)}), 400

            for file in [".env", "roon_token.txt", "roon_core_id.txt"]:
                if os.path.exists(file):
                    os.remove(file)
            return redirect(url_for("init"))

    return redirect(url_for("index"))


@app.route("/shutdown", methods=["POST", "GET"])
def shutdown():
    """Gracefully shut down the application."""
    logger.info("Shutting down the application...")
    thread_stop_event.set()  # Stop the background thread
    func = request.environ.get("werkzeug.server.shutdown")
    if func is None:
        logger.warning(
            "Not running with the Werkzeug Server. Using os._exit(0) as fallback."
        )
        os._exit(0)  # Forcefully exit the application
    func()  # Call the Werkzeug server shutdown function

    return jsonify({"message": "Application shutting down..."}), 200


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
    global display_state

    logger.info("trigger_album_update")
    myRoonApi = getRoonApi()
    album = myRoonApi.get_zone_data()

    album["display_state"] = display_state

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
    # Check if the Roon token file exists
    if not os.path.exists("roon_token.txt"):
        logger.info("Roon token file not found. Redirecting to /init.")
        app.run(debug=False, port=port, host=host)
        os._exit(0)  # Forcefully exit the application

    # start the Roon
    if not myRoonApi.check_auth():
        logger.error("Please authorise first using discovery.py")
        os._exit(0)  # Forcefully exit the application
    if not myRoonApi.connect(notify_clients=notify_clients):
        logger.error("Unable to connect to Roon")
        os._exit(0)  # Forcefully exit the application

    # Notify systemd that the service is ready
    n = sdnotify.SystemdNotifier()
    n.notify("READY=1")

    # Start the Flask web server
    socketio.run(
        app,
        debug=False,
        port=port,
        host=host,
        allow_unsafe_werkzeug=True,
    )
