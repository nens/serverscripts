#!/usr/bin/python
"""
Goal copy/pasted from trac (https://office.lizard.net/trac/ticket/4272)::

    (1) Bekijkt of alle in de fstab genoemde koppelingen gemount zijn
    (2) Kijkt of de extern gemounte folders gelist kunnen worden

    Als het antwoord op vraag 1 of 2 nee is moet:

    (a) Zabbix rood worden
    (b) de folder wordt geremount. In geval 2 moet er eerst een
        unmount plaatsvinden en daarna weer een mount.

"""
from logging.handlers import RotatingFileHandler

import argparse
import json
import logging
import os
import re
import serverscripts
import subprocess
import sys
import time


LOGFILE = "/var/log/cifsfixer.log"
VAR_DIR = "/var/local/serverscripts"
OUTPUT_DIR = "/var/local/serverinfo-facts"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "cifss.fact")
FSTAB = "/etc/fstab"
MTAB = "/etc/mtab"
CIFS_PATTERN = re.compile(
    r"""
^(?P<cifs_share>[^#\s]+)   # cifs share string at start of line
                           # (not a # and not whitespace)
\s+                        # Whitespace
(?P<local_folder>\S+)      # Second item is the local folder
\s+                        # Whitespace
cifs                       # We're only interested in cifs mounts
\s+                        # Whitespace
(?P<rest>.+)$              # Rest of the line until the end.
""",
    re.VERBOSE,
)

logger = logging.getLogger(__name__)


def _cifs_lines(tabfile):
    """Return cifs share and local folder for cifs mounts in tabfile

    Also return number of warnings.

    """
    result = {}
    num_warnings = 0
    for line in open(tabfile):
        line = line.strip()
        match = CIFS_PATTERN.search(line)
        if match:
            share = {}
            local_folder = match.group("local_folder")
            cifs_share = match.group("cifs_share")
            share["cifs_share"] = cifs_share
            rest = match.group("rest")
            options_part = rest.split()[0]
            options = _extract_options(options_part)
            if options:
                share["options"] = options
            if "credentials" in options:
                username = _extract_username(options["credentials"])
                if username:
                    share["username"] = username
            logger.debug(
                "Found mount in %s: %s (%s)", tabfile, local_folder, cifs_share
            )
            if local_folder in result:
                num_warnings += 1
                logger.warning("local folder %s is a duplicate!", local_folder)
            if cifs_share in result.values():
                num_warnings += 1
                logger.warning("cifs share %s is already mounted elsewhere", cifs_share)
            result[local_folder] = share
    return result, num_warnings


def _extract_options(line_part):
    """Return k/v options found in the part of the line

    The part of the line looks like k=v,k=v,k=2 ."""
    result = {}
    pairs = line_part.split(",")
    for pair in pairs:
        if "=" not in pair:
            continue
        parts = pair.split("=")
        key = parts[0].strip()
        value = parts[1].strip()
        result[key] = value
    return result


def _extract_username(filename):
    """Return username (if found) from the credentials"""
    if not os.path.exists(filename):
        logger.warning("Cifs credentials file %s does not exist", filename)
        return
    for line in open(filename):
        if ("username" in line) and ("=" in line):
            username = line.split("=")[1]
            return username.strip()


def _mount(local_folder):
    """Mount cifs_share. No need to raise errors if unsuccessful."""
    logger.info("Mounting %s...", local_folder)
    exit_code = subprocess.call(["mount", local_folder])
    if exit_code == 0:
        logger.info("Mounted %s succesfully", local_folder)
    else:
        logger.error("Mounting %s failed", local_folder)


def _is_folder_accessible(local_folder):
    """Return if the local folder is readable.

    Listing just the directory itself (so: not the contents) is enough.

    """
    exit_code = subprocess.call(["ls", "-d", local_folder])
    if exit_code == 0:
        logger.debug("Contents of %s can be listed just fine", local_folder)
        return True
    else:
        logger.error("Contents of %s cannot be listed", local_folder)
        return False


def _unmount(local_folder):
    """Unmount cifs_share. No need to raise errors if unsuccessful.

    First try a regular unmount. If it fails, do a lazy unmount. We'll try
    mounting afterwards, which might fail, but that's not our concern. It'll
    fail and the whole script will re-try 5 minutes later, so it is fine.

    """
    logger.info("Unmounting %s...", local_folder)
    exit_code = subprocess.call(["umount", local_folder])
    if exit_code == 0:
        logger.debug("Succesfully unmounted %s", local_folder)
    else:
        logger.error("Regular unmounting failed, re-trying it lazy...")
        subprocess.call(["umount", "-l", local_folder])


def check_if_mounted(fstab_mounts, mtab_mounts):
    """Return number of cifs mount related errors

    - Check if all CIFS mounts in fstab are mounted (=listed in mtab).

    - Check if they can be listed and if not, remount them.

    """
    num_errors = 0
    for local_folder, share_info in fstab_mounts.items():
        cifs_share = share_info["cifs_share"]
        # Check if it is mounted.
        if local_folder not in mtab_mounts:
            logger.error(
                "Error: %s is not mounted (%s), mounting it...",
                local_folder,
                cifs_share,
            )
            _mount(local_folder)
            num_errors += 1  # We *did* originally have an error!
            continue  # This goes to the next one in the 'for' loop.

        if _is_folder_accessible(local_folder):
            logger.debug("Contents of %s can be listed just fine", local_folder)
            continue

        # The folder could not be read... Remount it.
        num_errors += 1
        _unmount(local_folder)
        time.sleep(3)
        _mount(local_folder)

    return num_errors


def check_unknown_mounts(fstab_mounts, mtab_mounts):
    """Return number of unknown cifs mounts"""
    num_warnings = 0
    for local_folder, share_info in mtab_mounts.items():
        cifs_share = share_info["cifs_share"]
        # Check if it is mounted.
        if local_folder not in fstab_mounts:
            logger.warning(
                "Error: %s is mounted (%s), but not known in /etc/fstab",
                local_folder,
                cifs_share,
            )
            num_warnings += 1

    return num_warnings


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        dest="verbose",
        default=False,
        help="Verbose output",
    )
    parser.add_argument(
        "-V",
        "--version",
        action="store_true",
        dest="print_version",
        default=False,
        help="Print version",
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        dest="force",
        default=False,
        help="Force processing even when %s has been edited recently" % FSTAB,
    )
    options = parser.parse_args()
    if options.print_version:
        print(serverscripts.__version__)
        sys.exit()
    if options.verbose:
        loglevel = logging.DEBUG
    else:
        loglevel = logging.WARN
    logging.basicConfig(level=loglevel, format="%(levelname)s: %(message)s")

    file_handler = RotatingFileHandler(
        LOGFILE, mode="a", maxBytes=1000000, backupCount=3
    )
    long_formatter = logging.Formatter(fmt="%(asctime)s %(levelname)s: %(message)s")
    file_handler.setFormatter(long_formatter)
    logger.addHandler(file_handler)

    if not os.path.exists(VAR_DIR):
        os.mkdir(VAR_DIR)
        logger.info("Created %s", VAR_DIR)

    # Check fstab modification time. Don't run if edited recently.
    seconds_since_last_edit = time.time() - os.path.getmtime(FSTAB)
    logger.debug("%s last edited %s seconds ago", FSTAB, seconds_since_last_edit)
    if (seconds_since_last_edit < 60 * 5) and not options.force:
        logger.warning("%s edited less than 5 minutes ago, skipping for now.", FSTAB)
        sys.exit()

    fstab_mounts, num_warnings1 = _cifs_lines(FSTAB)
    mtab_mounts, num_warnings2 = _cifs_lines(MTAB)
    num_warnings3 = check_unknown_mounts(fstab_mounts, mtab_mounts)
    num_warnings = num_warnings1 + num_warnings2 + num_warnings3
    num_errors = check_if_mounted(fstab_mounts, mtab_mounts)

    # Write to files that will be read by zabbix.
    warningsfile = os.path.join(VAR_DIR, "nens.cifschecker.warnings")
    open(warningsfile, "w").write(str(num_warnings))
    errorsfile = os.path.join(VAR_DIR, "nens.cifschecker.errors")
    open(errorsfile, "w").write(str(num_errors))

    # Write facts for serverinfo.
    if not os.path.exists(OUTPUT_DIR):
        os.mkdir(OUTPUT_DIR)
        logger.info("Created %s", OUTPUT_DIR)
    open(OUTPUT_FILE, "w").write(json.dumps(fstab_mounts, sort_keys=True, indent=4))

    if num_errors == 0:
        logger.info("Everything OK with the mounts: %s", ", ".join(fstab_mounts.keys()))
    else:
        sys.exit(1)
