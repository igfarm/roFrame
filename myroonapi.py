import os
import time
import asyncio

from roonapi import RoonApi, RoonDiscovery

class MyRoonApi():

    def __init__(self) -> None:
        self.zone_name = os.environ.get("ROON_ZONE", None)
        self.core_id_fname = os.environ.get("ROON_CORE_ID_FNAME", "roon_core_id.txt")
        self.token_fname = os.environ.get("ROON_TOKEN_FNAME", "roon_token.txt")
        self.clients = set()
        self.notify_clients = None

        if self.zone_name is None:
            raise Exception("ROON_ZONE environment variable must be set to the name of the zone you want to control")

        self.appinfo = {
            "extension_id": "roFrame",
            "display_name": "Frame for Roon",
            "display_version": "1.0.0",
            "publisher": "igfarm",
            "email": "jaime@igfarm.com",
        }

    def register(self):
        discover = RoonDiscovery(None)
        server = discover.first()
        discover.stop()

        print("Found the following server")
        print(server)

        api = RoonApi(self.appinfo, None, server[0], server[1], False)
        while api.token is None:
            print("Waiting for authorisation")
            time.sleep(1)

        print("Got authorisation")
        print(api.host)
        print(api.core_name)
        print(api.core_id)

        # This is what we need to reconnect
        self._save_credentials(api.core_id, api.token)
        api.stop()

    def _save_credentials(self, core_id, token):
        with open(self.core_id_fname, "w") as f:
            f.write(core_id)
        with open(self.token_fname, "w") as f:
            f.write(token)

    def queue_callback(self, data):
        print("queue_callback")
        album = self._extract_album(data)
        if album and self.notify_clients:
            img = self.roonapi.get_image(album["image_key"], width=600, height=600)
            evdata = { 
                "album_artist": album["three_line"]["line2"], 
                "album_title": album["three_line"]["line3"], 
                "album_track": album["three_line"]["line1"],
                "album_cover_url": img,
                "state": self.get_zone_state(),
            }
            asyncio.run(self.notify_clients(evdata))  # Use the notify_clients function

    def _extract_album(self, data):
        if 'items' in data and len(data['items']) > 0:
            return data['items'][0]
        elif 'changes' in data and len(data['changes']) > 0:
            for change in data['changes']:
                if change['operation'] == 'insert':
                    return change['items'][0]
        return None

    def state_callback(self, event, changed_items):
        if event == "zones_changed":
            state = self.get_zone_state()
            copy = self.get_copy()
            url = self.get_image_url()
            evdata = {
                "album_artist": copy["artist"], 
                "album_title": copy["title"], 
                "album_track": copy["track"],
                "album_cover_url": url,
                "state": state,
            }
            asyncio.run(self.notify_clients(evdata))  # Use the notify_clients function

    def connect(self, notify_clients=None):
        self.roonapi = None

        if not os.path.exists(self.core_id_fname) or not os.path.exists(self.token_fname):
            print("Please authorise first using discovery.py")
            exit()

        # Can be None if you don't yet have a token
        try:
            core_id = open(self.core_id_fname).read()
            token = open(self.token_fname).read()

            print(core_id)
            discover = RoonDiscovery(core_id)
            server = discover.first()
            discover.stop()

            print(server)
            self.roonapi = RoonApi(self.appinfo, token, server[0], server[1], True)

            self.notify_clients = notify_clients
            self.roonapi.register_queue_callback(self.queue_callback, self.get_zone_id())
            self.roonapi.register_state_callback(self.state_callback)
        except OSError:
            print("Please authorise first using discovery.py")
            exit()

    def __get_roonapi(self):
        if self.roonapi is None:
            raise Exception("RoonApi not initialized")
        return self.roonapi

    def set_zone_name(self, zone_name):
        self.zone_name = zone_name

    def get_zones(self):
        roonapi = self.__get_roonapi()
        return roonapi.zones
    
    def get_zone_id(self):
        roonapi = self.__get_roonapi()
        for zone_id, zone_info in roonapi.zones.items():
            if zone_info["display_name"] == self.zone_name:
                return zone_id
        return None
    
    def get_zone_state(self):
        roonapi = self.__get_roonapi()
        zone_id = self.get_zone_id()
        if zone_id:
            return roonapi.zones[zone_id]["state"]
        return None
    
    def get_image_url(self, image_size=600):
        # start with a single pixel gif
        image_url = "data:image/gif;base64,R0lGODdhAQABAIABAAAAAAAAACwAAAAAAQABAAACAkwBADs="
        if self.get_zone_state() == "playing" or self.get_zone_state() == "paused":  
            roonapi = self.__get_roonapi()
            zone_id = self.get_zone_id()
            if zone_id:
                zone = roonapi.zones[zone_id]
                if "now_playing" in zone:
                    image_key = zone["now_playing"]["image_key"]
                    image_url = roonapi.get_image(image_key, width=image_size, height=image_size)
        return image_url
    
    def get_copy(self):
        if self.get_zone_state() == "playing":
            roonapi = self.__get_roonapi()
            zone_id = self.get_zone_id()
            if zone_id:
                zone = roonapi.zones[zone_id]
                if "now_playing" in zone:
                    lines = zone["now_playing"]["three_line"]
                    return { "artist": lines["line2"], "title": lines["line3"], "track": lines["line1"] }
        return { "artist": '', "title": '', "track": '' }
