"""Determine whether pbis runs correctly

"""
import argparse
import json
import logging
import os
import serverscripts
import sys
import subprocess

VAR_DIR = '/var/local/serverscripts'
OUTPUT_DIR = '/var/local/serverinfo-facts'
OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'pbis.fact')
PBIS_EXECUTABLE = '/usr/bin/pbis'
OK = 0
ERROR = 1

logger = logging.getLogger(__name__)


def check_pbis():
    command = "%s status" % PBIS_EXECUTABLE
    logger.debug("Running '%s'...", command)
    sub = subprocess.Popen(command,
                           shell=True,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE,
                           universal_newlines=True)
    output, error = sub.communicate()
    if error:
        logger.warning("Error output from pbis command: %s", error)
    lines = [line.strip().lower() for line in output.split('\n')]
    online = [line for line in lines if 'online' in line]
    nens_local = [line for line in lines if 'nens.local' in line]
    if online and nens_local:
        logger.info("Both 'online' and 'nens.local' found")
        return OK
    else:
        logger.error("Not both of 'online' and 'nens.local' found")
        return ERROR


def main():
    """Installed as bin/rabbitmq-info"""
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

    status = OK
    pbis_exists = os.path.exists(PBIS_EXECUTABLE)
    if pbis_exists:
        status = check_pbis()
    else:
        logger.info("No %s found, skipping the pbis check", PBIS_EXECUTABLE)

    # Write facts for serverinfo.
    if not os.path.exists(OUTPUT_DIR):
        os.mkdir(OUTPUT_DIR)
        logger.info("Created %s", OUTPUT_DIR)
    open(OUTPUT_FILE, 'w').write(json.dumps(
        {'exists': pbis_exists}, sort_keys=True, indent=4))

    zabbix_errors_file = os.path.join(VAR_DIR, 'nens.pbis.errors')
    open(zabbix_errors_file, 'w').write(str(status))
