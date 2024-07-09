import argparse
import os
import subprocess
import time
import keyring

import distro
import requests

from elevate import elevate
from loguru import logger

distro_name = distro.id()
parser = argparse.ArgumentParser()

parser.add_argument("--verbose", "-v", help="runs command verbosely. helpful for debugging!", action="store_true")
parser.add_argument("--flatpak", "-f", help="updates flatpak packages as well.", action="store_true")
parser.add_argument("--snap", "-s", help="updates snaps as well.", action="store_true")
parser.add_argument("--no-notify", "-N", help="skips the phone notification.", action="store_true")
parser.add_argument("--version", "-V", help="displays the version.", action="store_true")
parser.add_argument("--pretend", "-p", help="simulates the process without making any changes to your computer.",
                    action="store_true")
args = parser.parse_args()

__version__ = "1.0.0"


def first_run():
    if args.version:
        print("Conqace v" + __version__)
        exit(0)
    if keyring.get_password('pushed_api', '<appkey>') is None or keyring.get_password('pushed_api',
                                                                                      '<appsecret>') is None:
        import getpass
        appkey = getpass.getpass(
            "Enter your pushed app key (not secret). this will be safely stored in your system's keyring: ")
        appsecret = input(
            "Enter your pushed app secret (not key). this will be safely stored in your system's keyring.")
        keyring.set_password('pushed_api', '<appkey>', appkey)
        keyring.set_password('pushed_api', '<appsecret>', appsecret)
        temppl = {
            "app_key": keyring.get_password('pushed_api', '<appkey>'),
            "app_secret": keyring.get_password('pushed_api', '<appsecret>'),
            "target_type": "app",
            "content": "Update Successful."
        }

    else:

        temppl = {
            "app_key": keyring.get_password('pushed_api', '<appkey>'),
            "app_secret": keyring.get_password('pushed_api', '<appsecret>'),
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
        logger.warning("Not elevated.")
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
    if args.pretend:
        logger.info("Running in pretend mode. skipping the rest of the script.")
        logger.info("Sending notification")
        notification()
    else:
        if distro_name in ("ubuntu", "debian", "linuxmint", "raspbian"):
            logger.info("Distro identified as Debian/Debian based. Using apt. ")
            ubuntu_apt()
        elif distro.id() in "gentoo":
            logger.info("Distro identified as Gentoo. Using emerge/portage. ")
            gentoo_emerge()
        elif distro.id() in ("arch", "endeavouros", "manjaro"):
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


if __name__ == "__main__":
    payload = first_run()
    start_update()
