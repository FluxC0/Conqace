import time

import requests
import os
from dotenv import load_dotenv
from loguru import logger
from elevate import elevate

load_dotenv()
payload = {
    "app_key": os.getenv("PUSHED_APP_KEY"),
    "app_secret": os.getenv('PUSHED_APP_SECRET'),
    "target_type": "app",
    "content": "Emerge Update Successful."
}


def check_elevation():
    if 'SUDO_USER' in os.environ and os.geteuid() == 0:
        return 0
    else:
        return 1


def start_emerge():
    logger.info("Checking permissions...")
    elevated = check_elevation()
    if elevated == 0:
        logger.success("Elevated, continuing.")
        next_emerge()
    else:
        logger.warning("Not elevated. Please enter sudo password.")
        elevate(graphical=False)




def next_emerge():
    logger.info("Syncing latest packages..")
    os.system("emaint -a sync")
    logger.success("Sync complete")
    logger.info("Updating @world.")
    os.system("emerge -vuDN @world")
    logger.success("Update complete")
    logger.info("Sending push notification...")
    r = requests.post("https://api.pushed.co/1/push", data=payload)
    logger.success("Push notification sent")
    logger.success("Emerge Complete. Exiting Application.")
    exit(0)


start_emerge()
