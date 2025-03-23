# Organized imports
import os
import subprocess
import time
import asyncio
import logging
import threading
import base64
from datetime import datetime
from threading import Event
from io import BytesIO

import sdnotify
import qrcode
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
from utils import is_screen_on, validate_settings_form_data
from myroonapi import MyRoonApi
from art_generator import generate_mondrian
from config import Config  # Import the Config class

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask app and SocketIO setup
app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
socketio = SocketIO(app, cors_allowed_origins="*")
thread = None
thread_stop_event = Event()

# Global variables
display_state = False
myRoonApi = None

# Create a single instance of the configuration object
config = Config()
if config.dot_env_exists():
    config.load()

# Initialize Roon API
myRoonApi = MyRoonApi() if config.name else None


def getRoonApi():
    """Ensure Roon API is connected and return the instance."""
    global myRoonApi

    if not myRoonApi.is_connected():
        logger.info("Connecting to Roon API")
        myRoonApi.connect(notify_clients=notify_clients)

    return myRoonApi


# Display control
def display(turn_on):
    """Control the display state."""
    global display_state
    display_state = turn_on

    state = "on" if turn_on else "off"
    if config.display_control == "on":
        try:
            subprocess.check_output(["xset", "dpms", "force", state])
        except subprocess.CalledProcessError:
            logger.warning("problem with xset")
    logger.info(f"display: {state}")


# Background thread for periodic tasks
def background_thread():
    """A background thread that emits a message every 10 minutes."""
    while not thread_stop_event.is_set():
        try:
            myRoonApi = getRoonApi()
            album = myRoonApi.get_zone_data()
            state = album.get("state")
            current_hour = datetime.now().astimezone(config.my_tz).hour

            # Turn off screen during certain hours
            if state in ["playing", "loading"] or is_screen_on(
                current_hour, config.display_on_hour, config.display_off_hour
            ):
                display(True)
            else:
                display(False)

            # Wait for 600 seconds or until the thread_stop_event is set
            thread_stop_event.wait(600)
        except Exception as e:
            logger.error(f"Error in background thread: {e}")


# Flask routes
@app.route("/ping")
def ping():
    return jsonify({"message": "pong"})


@app.route("/")
def index():
    """Render the main index page."""
    if not config.dot_env_exists():
        return redirect(url_for("init"))

    images = []
    art_images = []
    if config.slideshow_enabled:
        images = os.listdir(config.slideshow_folder)
        image_extensions = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff"}
        images = [
            img
            for img in images
            if os.path.splitext(img)[1].lower() in image_extensions
        ]
        if not images:
            art_images = [generate_mondrian() for _ in range(10)]

    return render_template(
        config.index_file,
        name=config.name,
        images=images,
        art_images=art_images,
        transition_seconds=config.slideshow_transition_seconds,
        slideshow_clock_ratio=config.slideshow_clock_ratio,
        clock_size=config.clock_size,
        clock_offset=config.clock_offset,
    )


@app.route("/slideshow/<filename>")
def slideshow_pic(filename):
    """Serve slideshow images."""
    if filename not in os.listdir(config.slideshow_folder):
        return jsonify({"error": "File not found"}), 404
    return send_from_directory(config.slideshow_folder, filename)


@app.route("/static/<path:filename>")
def static_files(filename):
    """Serve static files."""
    return send_from_directory(os.path.join(app.root_path, "static"), filename)


@app.route("/settings", methods=["GET", "POST"])
def settings():
    """Handle settings page."""
    if not config.dot_env_exists():
        return redirect(url_for("init"))

    if config.is_locked():
        return redirect(url_for("index"))

    if request.method == "POST":
        # Get form data and validate inputs
        try:
            validated_data = validate_settings_form_data(request.form)
        except ValueError as e:
            return jsonify({"error": str(e)}), 400

        # Prepare form data for updating the .env file
        form_env_vars = {
            "ROON_ZONE": request.form.get("ROON_ZONE", os.getenv("ROON_ZONE", "")),
            **validated_data,
        }

        # Update the .env file using the Config class
        config.save(form_env_vars)

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
        "NAME": config.name,
        "DISPLAY_ON_HOUR": str(config.display_on_hour),
        "DISPLAY_OFF_HOUR": str(config.display_off_hour),
        "DISPLAY_CONTROL": config.display_control,
        "SLIDESHOW": "on" if config.slideshow_enabled else "off",
        "SLIDESHOW_FOLDER": config.slideshow_folder,
        "SLIDESHOW_TRANSITION_SECONDS": str(config.slideshow_transition_seconds),
        "SLIDESHOW_CLOCK_RATIO": str(int(config.slideshow_clock_ratio * 100)),
        "CLOCK_SIZE": str(config.clock_size),
        "CLOCK_OFFSET": str(config.clock_offset),
        "PORT": str(config.port),
        "HOST": config.host,
    }

    # Pass along the current selected zone and a list of available zones
    available_zones = myRoonApi.get_zone_list()
    current_env["ROON_ZONE"] = os.getenv("ROON_ZONE", "")
    current_env["AVAILABLE_ZONES"] = available_zones

    return render_template("settings.html", env=current_env)


@app.route("/init", methods=["GET", "POST"])
def init():
    """Handle initialization."""
    logger.info("init")
    if config.dot_env_exists():
        return redirect(url_for("settings"))

    if request.method == "GET":
        external_ip = None
        qr_code_base64 = None
        try:
            if True or os.uname().machine.startswith(
                "aarch64"
            ):  # Check if running on Raspberry Pi
                # external_ip = subprocess.check_output( ["hostname", "-I"], text=True).strip().split()[0]  # Get the first IP address

                external_ip = "192.168.86.42"
                if external_ip:
                    url = f"http://{external_ip}/init"
                    qr = qrcode.QRCode()
                    qr.add_data(url)
                    qr.make(fit=True)
                    img = qr.make_image(fill="black", back_color="white")
                    buffered = BytesIO()
                    img.save(buffered, format="PNG")
                    qr_code_base64 = base64.b64encode(buffered.getvalue()).decode(
                        "utf-8"
                    )
        except Exception as e:
            logger.error(f"Error retrieving external IP or generating QR code: {e}")

        return render_template(
            "init.html", external_ip=external_ip, qr_code=qr_code_base64
        )

    else:
        name = request.form.get("NAME", "").strip()
        if not name:
            return jsonify({"error": "Name cannot be empty"}), 400

        # Run the register process
        try:
            config.reset()
            config.save({"NAME": name})

            api = MyRoonApi()
            available_zones = api.register()

            if not available_zones:
                return jsonify({"error": "No Roon zones found"}), 400
            
            # Save the Roon core ID and token to the .env file
            config.save(
                {
                    "ROON_CORE_ID": os.environ["ROON_CORE_ID"],
                    "ROON_API_TOKEN": os.environ["ROON_API_TOKEN"],
                    "ROON_ZONE": available_zones[0] if available_zones else ""
                }
            )
            # Schedule os._exit(0) two seconds after returning
            threading.Thread(target=lambda: (time.sleep(2), os._exit(0))).start()

            return jsonify({"message": "Registration successful"}), 200

        except Exception as e:
            logger.error(f"Error during registration: {e}")
            return jsonify({"error": str(e)}), 400


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


# SocketIO events
@socketio.on("connect")
def handle_connect():
    """Handle client connection."""
    logger.info("Socket client connected")
    emit("response", {"data": "Connected"})

    # Start the background thread if it’s not running yet
    global thread
    if thread is None or not thread.is_alive():
        thread = socketio.start_background_task(background_thread)


@socketio.on("disconnect")
def handle_disconnect():
    """Handle client disconnection."""
    logger.info("Client disconnected")


@socketio.on("trigger_album_update")
def trigger_album_update():
    """Trigger album update."""
    global display_state

    logger.info("trigger_album_update")
    myRoonApi = getRoonApi()
    album = myRoonApi.get_zone_data()

    album["display_state"] = display_state

    asyncio.run(notify_clients(album))  # Use asyncio.run to await the coroutine

    if album["state"] in ["playing", "loading"]:
        display(True)


# Notify clients of album updates
async def notify_clients(message):
    """Notify connected clients of album updates."""
    logger.info("notify_clients")
    logger.info(message)
    socketio.emit("album_update", message)
    if message.get("state") in ["playing", "loading"]:
        display(True)


# Main entry point
if __name__ == "__main__":
    logger.info("Starting roFrame")

    # Fix any old configuration issues
    config.migrage_legacy()

    # Check if the Roon token file exists
    if not myRoonApi.check_auth():
        logger.info("Roon token file not found. Redirecting to /init.")
        app.run(debug=False, port=config.port, host=config.host)
        os._exit(0)  # Forcefully exit the application

    # start the Roon
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
        port=config.port,
        host=config.host,
        allow_unsafe_werkzeug=True,
    )
