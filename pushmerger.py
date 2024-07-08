import time

import requests
import os
from dotenv import load_dotenv
from loguru import logger
from elevate import elevate
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--skip-sync", "-s", help="Skips the emaint sync.", action="store_true")
parser.add_argument("--verbose", "-v", help="runs command verbosely. helpful for debugging!", action="store_true")
args = parser.parse_args()

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
    if args.skip_sync:
        logger.warning("Skipping emerge sync due to --skip-sync flag.")
        time.sleep(2)
    else:
        logger.info("Syncing with emaint.")
        time.sleep(2)
        os.system("emaint -a sync")

    logger.info("Updating @world. this may take a while...")
    if args.verbose:
        os.system("emerge -vuDN @world")
    else:
        os.system("emerge -quDN @world")
    logger.success("Update complete. ")
    logger.info("Sending push notification...")
    r = requests.post("https://api.pushed.co/1/push", data=payload)
    if "error" in r.json():
        logger.error(r.text)
        logger.error("Failed to send push notification")
        logger.warning("Emerge Complete, but notification failed. Exiting Application.")
        exit(1)
    else:
        logger.success("Push notification sent")
        logger.success("Emerge Complete. Exiting Application.")
        exit(0)


start_emerge()
