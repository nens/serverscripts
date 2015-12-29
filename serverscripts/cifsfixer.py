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
import argparse
import logging
import logging.handlers
import os
import re
import serverscripts
import subprocess
import sys
import time

FSTAB = '/etc/fstab'
MTAB = '/etc/mtab'
CIFS_PATTERN = re.compile(r"""
^(?P<file_system>[^#]+)  # File system string at start of line
\s+                      # Whitespace
(?P<mount_point>.+)      # Second item is the mount point
\s+                      # Whitespace
cifs                     # We're only interested in cifs mounts
\s+                      # Whitespace
.+$                      # Rest of the line until the end.
""", re.VERBOSE)

logger = logging.getLogger(__name__)


def _cifs_lines(tabfile):
    """Return file system and mount point for cifs mounts in tabfile"""
    result = {}
    for line in open(tabfile):
        line = line.strip()
        match = CIFS_PATTERN.search(line)
        if match:
            mount_point = match.group('mount_point')
            file_system = match.group('file_system')
            logger.debug("Found mount in %s: %s (%s)",
                         tabfile, mount_point, file_system)
            if mount_point in result:
                logger.warning("Mount point %s is a duplicate!", mount_point)
            if file_system in result.values():
                logger.warning("File system %s is already mounted elsewhere",
                               file_system)
            result[mount_point] = file_system
    return result


def check_if_mounted(fstab_mounts, mtab_mounts):
    """Return number of cifs mount related errors

    - Check if all CIFS mounts in fstab are mounted (=listed in mtab).

    - Check if they can be listed and if not, remount them.

    """
    num_errors = 0
    for fstab_mount in fstab_mounts:
        # Check if it is mounted.
        if fstab_mount not in mtab_mounts:
            logger.error("Error: %s is not mounted (%s), mounting it...",
                         fstab_mount,
                         fstab_mounts[fstab_mount])
            exit_code = subprocess.call(['mount', fstab_mount])
            if exit_code == 0:
                logger.info("Mounted %s succesfully", fstab_mount)
            else:
                logger.error("Mounting %s failed", fstab_mount)

            num_errors += 1  # We *did* have an error!
            continue  # This goes to the next one in the 'for' loop.

        # Check if the mount is readable. Listing the contents is OK.
        try:
            subprocess.check_output(['ls', fstab_mount])
        except subprocess.CalledProcessError as e:
            logger.error(e.output)
            logger.error(
                "Listing the contents of %s went wrong, unmounting it...",
                fstab_mount)
            exit_code = subprocess.call(['umount', fstab_mount])
            if exit_code:
                logger.error("Regular unmounting failed, re-trying it lazy..")
                exit_code = subprocess.call(['umount', '-l', fstab_mount])

            time.sleep(3)
            logger.info("Mounting %s...", fstab_mount)
            exit_code = subprocess.call(['mount', fstab_mount])
            if exit_code == 0:
                logger.info("Re-mounted %s succesfully", fstab_mount)
            else:
                logger.error("Re-mounting %s failed", fstab_mount)

            num_errors += 1
            continue

    return num_errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        dest="verbose",
        default=False,
        help="Verbose output")
    parser.add_argument(
        "-V",
        "--version",
        action="store_true",
        dest="print_version",
        default=False,
        help="Print version")
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        dest="force",
        default=False,
        help="Force processing even when %s has been edited recently" % FSTAB)
    options = parser.parse_args()
    if options.print_version:
        print(serverscripts.__version__)
        sys.exit()
    if options.verbose:
        loglevel = logging.DEBUG
    else:
        loglevel = logging.WARN
    logging.basicConfig(level=loglevel,
                        format="%(levelname)s: %(message)s")

    file_handler = logging.handlers.RotatingFileHandler(
        '/var/log/cifsfixer.log', mode='a', maxBytes=1000000, backupCount=3)
    long_formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)s: %(message)s")
    file_handler.setFormatter(long_formatter)
    logger.addHandler(file_handler)

    # Check fstab modification time. Don't run if edited recently.
    seconds_since_last_edit = time.time() - os.path.getmtime(FSTAB)
    logger.debug("%s last edited %s seconds ago",
                 FSTAB,
                 seconds_since_last_edit)
    if (seconds_since_last_edit < 60 * 5) and not options.force:
        logger.warn("%s edited less than 5 minutes ago, skipping for now.",
                    FSTAB)
        sys.exit()

    fstab_mounts = _cifs_lines(FSTAB)
    mtab_mounts = _cifs_lines(MTAB)
    num_errors = check_if_mounted(fstab_mounts, mtab_mounts)
    if num_errors == 0:
        logger.info("Everything OK with the mounts: %s",
                    ', '.join(fstab_mounts.keys()))
    else:
        sys.exit(1)

    # TODO: write exit code to file for zabbix.
