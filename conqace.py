import time

import requests
import os
from dotenv import load_dotenv
from loguru import logger
from elevate import elevate
import argparse
import distro
import subprocess

distro_name = distro.id()
parser = argparse.ArgumentParser()

parser.add_argument("--verbose", "-v", help="runs command verbosely. helpful for debugging!", action="store_true")
args = parser.parse_args()

load_dotenv()
payload = {
    "app_key": os.getenv("PUSHED_APP_KEY"),
    "app_secret": os.getenv('PUSHED_APP_SECRET'),
    "target_type": "app",
    "content": "Update Successful."
}


def check_elevation():
    if 'SUDO_USER' in os.environ and os.geteuid() == 0:
        return 0
    else:
        return 1


def start_update():
    logger.info("Checking permissions...")
    elevated = check_elevation()
    if elevated == 0:
        logger.success("Elevated, continuing.")
        version_checking()

    else:
        logger.warning("Not elevated. Please enter sudo password.")
        elevate(graphical=False)


def notification():
    r = requests.post("https://api.pushed.co/1/push", data=payload)
    if "error" in r.json():
        logger.error(r.text)
        logger.error("Failed to send push notification")
        logger.warning("Update Complete, but notification failed. Exiting Application.")
        exit(1)
    else:
        logger.success("Push notification sent")
        logger.success("Emerge Complete. Exiting Application.")
        exit(0)


def version_checking():
    if distro_name in ("ubuntu", "debian", "linuxmint", "raspbian"):
        logger.info("Distro identified as Debian/Debian based. Using apt. ")
        ubuntu_apt()
    elif distro.id() in "gentoo":
        logger.info("Distro identified as Gentoo. Using emerge/portage. ")
        gentoo_emerge()
    else:
        logger.error("Your distribution is unsupported.  ")
        exit(0)


def gentoo_emerge():
    logger.info("Syncing with emaint.")
    time.sleep(2)
    # Artificial delay in place to allow user to read the message before emaint syncs.


    logger.info("Syncing with emaint.")
    time.sleep(2)
    subprocess.run(["emaint", "-a", "sync"], check=True)
    logger.info("Updating @world. this may take a while...")
    if args.verbose:
        os.system("emerge -vuDN @world")
    else:
        os.system("emerge -quDN @world")
    logger.success("Update complete. ")
    logger.info("Sending push notification...")
    notification()


def ubuntu_apt():
    logger.info("Updating and Upgrading. this may take a while...")
    if args.verbose:
        os.system("apt-get -y update")
        logger.info("Updates fetched. Applying now.")
        os.system("apt-get -y upgrade")
    else:
        os.system("apt-get -y update > /dev/null")
        logger.info("Updates fetched. Applying now.")
        os.system("apt-get -y upgrade > /dev/null")

    logger.info("Sending Notification")
    notification()


start_update()
