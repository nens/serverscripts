"""Extract information from geoserver

"""
import argparse
import json
import logging
import os
import serverscripts

# import subprocess
import sys


OUTPUT_DIR = "/var/local/serverinfo-facts"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "geoserver.fact")
CONFIG_DIR = "/etc/serverscripts"
CONFIG_FILE = os.path.join(CONFIG_DIR, "geoserver.json")

logger = logging.getLogger(__name__)


def load_config(config_file_path):
    """Return configuration"""
    content = {}
    if not os.path.exists(config_file_path):
        return
    with open(config_file_path, "r") as config_file:
        try:
            content = json.loads(config_file.read())
        except:  # Yes, a bare except
            logger.exception("Faulty config file %s", config_file_path)
            return

    required_keys = ["logfile", "data_dir"]
    for info_per_server in content.values():
        for required_key in required_keys:
            if required_key not in info_per_server:
                logger.error("Required key %s missing in config file", required_key)
                return

    return content


def main():
    """Installed as bin/geoserver-info"""
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

    options = parser.parse_args()
    if options.print_version:
        print(serverscripts.__version__)
        sys.exit()
    if options.verbose:
        loglevel = logging.DEBUG
    else:
        loglevel = logging.WARN
    logging.basicConfig(level=loglevel, format="%(levelname)s: %(message)s")

    if not os.path.exists(CONFIG_DIR):
        os.mkdir(CONFIG_DIR)
        logger.info("Created %s", CONFIG_DIR)

    configuration = load_config(CONFIG_FILE)
    if not configuration:
        return

    result_for_serverinfo = {}
    if not result_for_serverinfo:
        return

    open(OUTPUT_FILE, "w").write(
        json.dumps(result_for_serverinfo, sort_keys=True, indent=4)
    )
