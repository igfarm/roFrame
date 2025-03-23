import os
import time
import asyncio
import logging
from typing import Optional, Callable, Dict, Any

from roonapi import RoonApi, RoonDiscovery


class MyRoonApi:

    BLACK_PIXEL = (
        "data:image/gif;base64,R0lGODdhAQABAIABAAAAAAAAACwAAAAAAQABAAACAkwBADs="
    )

    def __init__(self) -> None:
        self.zone_name = os.environ.get("ROON_ZONE", None)
        self.core_id = os.environ.get("ROON_CORE_ID", "")
        self.token = os.environ.get("ROON_API_TOKEN", "")
        self.clients = set()
        self.notify_clients: Optional[Callable[[Dict[str, Any]], None]] = None
        self.logger = logging.getLogger(__name__)
        self.image_size = int(os.environ.get("IMAGE_SIZE", 600))
        self.connected = False
        self.last_state = "unknown"
        self.roonapi = None

        if not bool(os.environ.get("NAME", "")):
            raise Exception(
                "NAME environment variable must be set and have unique name for this device"
            )

        self.appinfo = {
            "extension_id": "com.igfarm.roFrame",
            "display_name": "roFrame - " + os.environ.get("NAME", "not assigned"),
            "display_version": "1.0.1",
            "publisher": "igfarm",
            "email": "jaime@igfarm.com",
            "website": "https://github.com/igfarm/roFrame",
        }

    def check_auth(self) -> bool:
        token = os.getenv("ROON_API_TOKEN")
        return bool(token and token.strip())

    def register(self) -> list:
        discover = RoonDiscovery(None)
        server = discover.first()
        discover.stop()

        self.logger.info("Found the following server")
        self.logger.info(server)

        self.roonapi = RoonApi(self.appinfo, None, server[0], server[1], True)
        while self.roonapi.token is None:
            self.logger.info("Waiting for authorisation")
            time.sleep(1)

        album = self.get_zone_data(show_zones=True)
        if album is None:
            self.logger.warning("Please set ROON_ZONE to one of the values above")

        available_zones = self.get_zone_list()

        self.logger.info("Got authorisation")
        self.logger.info(self.roonapi.host)
        self.logger.info(self.roonapi.core_name)
        self.logger.info(self.roonapi.core_id)

        # This is what we need to reconnect
        os.environ["ROON_CORE_ID"] = self.roonapi.core_id
        os.environ["ROON_API_TOKEN"] = self.roonapi.token
        self.roonapi.stop()

        return available_zones

    def connect(
        self, notify_clients: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> bool:
        self.roonapi = None

        if not self.check_auth():
            self.logger.error("ROON_API_TOKEN not found or blank")
            return False

        if not bool(self.zone_name):
            self.logger.error("ROON_ZONE not found or blank")
            return False

        try:
            discover = RoonDiscovery(self.core_id)
            server = discover.first()
            discover.stop()

            if server[0] is None:
                self.logger.error("No server found")
                return False

            self.logger.info(server)
            self.roonapi = RoonApi(
                self.appinfo, self.token, server[0], server[1], False
            )
            self.notify_clients = notify_clients

            album = self.get_zone_data()

            self.roonapi.register_queue_callback(
                self.__queue_callback, album["zone_id"]
            )
            self.roonapi.register_state_callback(self.__state_callback)
            self.connected = True
            return True
        except OSError:
            self.logger.error("Exception connecting to Roon")
            return False

    def is_connected(self) -> bool:
        return self.connected

    def get_zone_list(self) -> list:
        list = []
        roonapi = self.__get_roonapi()
        for zone_id, zone_info in roonapi.zones.items():
            list.append(zone_info["display_name"])
            print("- " + zone_info["display_name"])
        return list

    def get_zone_data(self, show_zones=False) -> Optional[str]:
        roonapi = self.__get_roonapi()
        for zone_id, zone_info in roonapi.zones.items():
            print("- " + zone_info["display_name"])
            if zone_info["display_name"] == self.zone_name:
                zone = roonapi.zones[zone_id]
                self.last_state = zone["state"]
                # pprint(zone )
                data = {
                    "state": zone["state"],
                    "zone_id": zone_id,
                    "url": self.BLACK_PIXEL,
                    "artist": "",
                    "title": "",
                    "track": "",
                }
                if "now_playing" in zone:
                    data.update(self.__get_album_data(zone["now_playing"]))
                return data
        return None

    def __get_album_data(self, now_playing) -> Dict[str, Any]:
        return {
            "state": self.last_state,
            "image_size": self.image_size,
            "artist": now_playing["three_line"]["line2"],
            "title": now_playing["three_line"]["line3"],
            "track": now_playing["three_line"]["line1"],
            "url": self.roonapi.get_image(
                now_playing["image_key"], width=self.image_size, height=self.image_size
            ),
        }

    def __state_callback(self, event: str, changed_items: Any) -> None:
        if event == "zones_changed":
            data = self.get_zone_data()
            if self.notify_clients:
                asyncio.run(self.notify_clients(data))

    def __get_roonapi(self) -> RoonApi:
        if self.roonapi is None:
            raise Exception("RoonApi not initialized")
        return self.roonapi

    def __extract_album(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if "items" in data and len(data["items"]) > 0:
            return data["items"][0]
        elif "changes" in data and len(data["changes"]) > 0:
            for change in data["changes"]:
                if change["operation"] == "insert":
                    return change["items"][0]
        return None

    def __queue_callback(self, data: Dict[str, Any]) -> None:
        self.logger.info("queue_callback")
        album = self.__extract_album(data)
        if album and self.notify_clients:
            evdata = self.__get_album_data(album)
            asyncio.run(self.notify_clients(evdata))
