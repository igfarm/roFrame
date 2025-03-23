import logging

logger = logging.getLogger(__name__)


def is_screen_on(current_hour, on_hour, off_hour):
    if on_hour == off_hour:
        return False  # Device should be off if on and off hours are the same
    if on_hour < off_hour:
        return on_hour <= current_hour < off_hour  # Normal range
    else:
        return not (off_hour <= current_hour < on_hour)  # Overnight case


# Form data validation
def validate_settings_form_data(form):
    """Validate and parse form data."""
    try:
        display_on_hour = int(form.get("DISPLAY_ON_HOUR", "9"))
        display_off_hour = int(form.get("DISPLAY_OFF_HOUR", "23"))
        if not (0 <= display_on_hour <= 23 and 0 <= display_off_hour <= 23):
            raise ValueError("Display hours must be between 0 and 23.")

        slideshow_transition_seconds = int(
            form.get("SLIDESHOW_TRANSITION_SECONDS", "15")
        )
        if slideshow_transition_seconds <= 0:
            raise ValueError("Slideshow transition seconds must be a positive integer.")

        slideshow_clock_ratio = int(form.get("SLIDESHOW_CLOCK_RATIO", "0"))
        if not (0 <= slideshow_clock_ratio <= 100):
            raise ValueError("Slideshow clock ratio must be between 0 and 100.")

        clock_size = int(form.get("CLOCK_SIZE", "0"))
        if clock_size < 0:
            raise ValueError("Clock size must be a non-negative integer.")

        clock_offset = int(form.get("CLOCK_OFFSET", "0"))
        if clock_offset < 0:
            raise ValueError("Clock offset must be a non-negative integer.")
        
        lock_settings = form.get("LOCK_SETTINGS", "off")
        if lock_settings not in ["on", "off"]:
            lock_settings = "off"

        return {
            "DISPLAY_ON_HOUR": str(display_on_hour),
            "DISPLAY_OFF_HOUR": str(display_off_hour),
            "SLIDESHOW_TRANSITION_SECONDS": str(slideshow_transition_seconds),
            "SLIDESHOW_CLOCK_RATIO": str(slideshow_clock_ratio),
            "CLOCK_SIZE": str(clock_size),
            "CLOCK_OFFSET": str(clock_offset),
            "LOCK_SETTINGS": lock_settings
        }
    except ValueError as e:
        logger.error(f"Invalid input: {e}")
        raise
