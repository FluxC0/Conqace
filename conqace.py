import time

import requests
import os
from dotenv import load_dotenv
from loguru import logger
from elevate import elevate
import argparse
import distro

distro_name = distro.id()
parser = argparse.ArgumentParser()

parser.add_argument("--verbose", "-v", help="runs command verbosely. helpful for debugging!", action="store_true")
parser.add_argument("--flatpak", "-f", help="updates flatpak packages as well.", action="store_true")
parser.add_argument("--snap", "-s", help="updates snaps as well.", action="store_true")
parser.add_argument("--no-notify", "-N", help="skips the phone notification.", action="store_true")
args = parser.parse_args()


def first_run():
    if os.path.exists(".env"):
        load_dotenv()
        temppl = {
            "app_key": os.getenv("PUSHED_APP_KEY"),
            "app_secret": os.getenv('PUSHED_APP_SECRET'),
            "target_type": "app",
            "content": "Update Successful."
        }
        return temppl
    else:

        with open(r".env", "w+") as environfile:
            logger.info("No .env file found. Creating new one.")
            logger.info("Please enter in your Pushed App Key (not the secret)")
        logger.info("No .env file found. Creating new one.")
        logger.info("Please enter in your Pushed App Key (not the secret)")
        appkey = input()
        logger.info("Please enter in your App Secret (not the key)")
        appsecret = input()
        logger.info("writing to .env file...")
        environfile.write(f"PUSHED_APP_KEY={appkey}\nPUSHED_APP_SECRET={appsecret}")
        logger.info("done.")
        environfile.close()
        load_dotenv()
        temppl = {
            "app_key": os.getenv("PUSHED_APP_KEY"),
            "app_secret": os.getenv('PUSHED_APP_SECRET'),
            "target_type": "app",
            "content": "Update Successful."
        }
        return temppl


def snappak():
    if args.flatpak:
        logger.info("--flatpak argument selected. updating flatpak packages in addition to system packages.")
        time.sleep(2)
        os.system("flatpak update")
    if args.snap:
        logger.info("--snap argument selected. updating snaps in addition to system packages.")
        time.sleep(2)
        os.system("snap refresh")
    else:
        logger.info("just updating system packages.")


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
        snappak()
        version_checking()

    else:
        logger.warning("Not elevated. Please enter sudo password.")
        elevate(graphical=False)


def notification():
    if not args.no_notify:
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
    else:
        logger.info("Skipped notification due to --no-notify. Closing Application.")
        exit(0)


def version_checking():
    if distro_name in ("ubuntu", "debian", "linuxmint", "raspbian"):
        logger.info("Distro identified as Debian/Debian based. Using apt. ")
        ubuntu_apt()
    elif distro.id() in "gentoo":
        logger.info("Distro identified as Gentoo. Using emerge/portage. ")
        gentoo_emerge()
    elif distro.id() in "arch":
        logger.info("Distro identified as Arch. using pacman.  ")
        arch_pacman()
    else:
        logger.error("Your distribution is unsupported.  ")
        exit(0)


def arch_pacman():
    logger.info("Running pacman.")
    time.sleep(2)
    os.system("yes | pacman -Syu > /dev/null")
    logger.info("complete.")
    logger.info("sending notification.")
    notification()


def gentoo_emerge():
    logger.info("Syncing with emaint.")
    time.sleep(2)
    # Artificial delay in place to allow user to read the message before emaint syncs.
    os.system("emaint -a sync")

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


payload = first_run()
start_update()
