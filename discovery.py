import os
from myroonapi import MyRoonApi
from config import Config  # Import the Config class

config = Config()

# Ensure .env file exists
if not config.dot_env_exists():
    raise FileNotFoundError(
        ".env file not found. Please create it before running the program."
    )

config.load()
# check if config.name exists
if not config.name:
    name = input("Enter the name device: ")
    config.save({"NAME": name})

print("Name: ", config.name)
print("Go to Roon settings -> Extensions -> Enable the extension")

myRoonApi = MyRoonApi()
available_zones = myRoonApi.register()

print("Setting zone to: ", available_zones[0])
print("Available zones:")
for zone in available_zones:
    print("- " + zone)

print("Update .env file with one of the available zones")

# Save the Roon core ID and token to the .env file
config.save(
    {
        "ROON_CORE_ID": os.environ["ROON_CORE_ID"],
        "ROON_API_TOKEN": os.environ["ROON_API_TOKEN"],
        "ROON_ZONE": available_zones[0],
    }
)
