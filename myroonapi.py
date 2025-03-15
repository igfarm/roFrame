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
        self.core_id_fname = os.environ.get("ROON_CORE_ID_FNAME", "roon_core_id.txt")
        self.token_fname = os.environ.get("ROON_TOKEN_FNAME", "roon_token.txt")
        self.clients = set()
        self.notify_clients: Optional[Callable[[Dict[str, Any]], None]] = None
        self.logger = logging.getLogger(__name__)
        self.image_size = os.environ.get("IMAGE_SIZE", 600)
        self.connected = False

        if self.zone_name is None:
            raise Exception(
                "ROON_ZONE environment variable must be set to the name of the zone you want to control"
            )

        self.appinfo = {
            "extension_id": "roFrame",
            "display_name": "Frame for Roon",
            "display_version": "1.0.0",
            "publisher": "igfarm",
            "email": "jaime@igfarm.com",
        }

    def check_auth(self) -> bool:
        if not os.path.exists(self.core_id_fname) or not os.path.exists(
            self.token_fname
        ):
            self.logger.error("auth files not found")
            return False
        return True

    def register(self) -> None:
        discover = RoonDiscovery(None)
        server = discover.first()
        discover.stop()

        self.logger.info("Found the following server")
        self.logger.info(server)

        api = RoonApi(self.appinfo, None, server[0], server[1], True)
        while api.token is None:
            self.logger.info("Waiting for authorisation")
            time.sleep(1)

        self.logger.info("Got authorisation")
        self.logger.info(api.host)
        self.logger.info(api.core_name)
        self.logger.info(api.core_id)

        # This is what we need to reconnect
        self.__save_credentials(api.core_id, api.token)
        api.stop()

    def connect(
        self, notify_clients: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> bool:
        self.roonapi = None

        if not os.path.exists(self.core_id_fname) or not os.path.exists(
            self.token_fname
        ):
            self.logger.error("Please authorise first using discovery.py")
            return False

        try:
            with open(self.core_id_fname) as f:
                core_id = f.read()
            with open(self.token_fname) as f:
                token = f.read()

            self.logger.info(core_id)
            discover = RoonDiscovery(core_id)
            server = discover.first()
            discover.stop()

            if server[0] is None:
                self.logger.error("No server found")
                return False

            self.logger.info(server)
            self.roonapi = RoonApi(self.appinfo, token, server[0], server[1], False)
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

    def get_zone_data(self) -> Optional[str]:
        roonapi = self.__get_roonapi()
        for zone_id, zone_info in roonapi.zones.items():
            if zone_info["display_name"] == self.zone_name:
                zone = roonapi.zones[zone_id]
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
            "image_size": self.image_size,
            "artist": now_playing["three_line"]["line2"],
            "title": now_playing["three_line"]["line3"],
            "track": now_playing["three_line"]["line1"],
            "url": self.roonapi.get_image(
                now_playing["image_key"], width=self.image_size, height=self.image_size
            ),
        }

    def __save_credentials(self, core_id: str, token: str) -> None:
        with open(self.core_id_fname, "w") as f:
            f.write(core_id)
        with open(self.token_fname, "w") as f:
            f.write(token)

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
