"""Extract info on docker."""
import argparse
import copy
import json
import logging
import os
import serverscripts
import subprocess
import sys


VAR_DIR = '/var/local/serverscripts'
OUTPUT_DIR = '/var/local/serverinfo-facts'
OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'docker.fact')
DOCKER_TEMPLATE = {'images': 0,
                   'active_images': 0,
                   'images_size': 0,
                   'containers': 0,
                   'active_containers': 0,
                   'containers_size': 0,
                   'volumes': 0,
                   'active_volumes': 0,
                   'volumes_size': 0,
}


logger = logging.getLogger(__name__)


def is_docker_available():
    return os.path.exists('/etc/docker')


def all_info():
    """Return the info we want to extract from docker.

    $ docker system df

    TYPE                TOTAL               ACTIVE              SIZE                RECLAIMABLE
    Images              50                  2                   16.66 GB            16.13 GB (96%)
    Containers          2                   2                   70 B                0 B (0%)
    Local Volumes       3                   3                   123 MB              0 B (0%)

    """
    result = {}
    # TODO
    return result


def main():
    """Installed as bin/docker-info"""
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

    if not os.path.exists(OUTPUT_DIR):
        os.mkdir(OUTPUT_DIR)
        logger.info("Created %s", OUTPUT_DIR)

    if not is_docker_available():
        return

    result = all_info()
    open(OUTPUT_FILE, 'w').write(json.dumps(result, sort_keys=True, indent=4))
