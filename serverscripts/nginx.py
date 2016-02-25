"""Extract information from nginx config files.

"""
import argparse
import copy
import json
import logging
import os
import re
import serverscripts
import subprocess
import sys

import pkg_resources

NGINX_DIR = '/etc/nginx/sites-enabled'
GIT_URL = re.compile(r"""
    origin           # We want the origin remote.
    \W*              # Whitespace.
    .*               # git@ or https://
    github.com       # Base github incantation.
    [:/]             # : (git@) or / (https)
    (?P<user>.+)     # User/org string.
    /                # Slash.
    (?P<project>.+)  # Project.
    \.git             # .git
    .*$              # Whatever till the end of line.
    """, re.VERBOSE)
SERVER_START = re.compile(r"""
    ^server          # 'server' at the start of the line.
    \W*              # Optional whitespace.
    \{               # Starting curly brace
    .*$              # Whatever till the end of line.
    """, re.VERBOSE)
OUTPUT_DIR = '/var/local/serverinfo-facts'
OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'nginxs.fact')
SITE_TEMPLATE = {'name': '',
                 'protocol': 'http',
}


logger = logging.getLogger(__name__)


def extract_sites(filename):
    """Yield info per site found in the nginx config file"""
    lines = open(filename).readlines()
    lines = [line.strip() for line in lines]
    lines = [line.rstrip(';') for line in lines]
    lines = [line for line in lines
             if line and not line.startswith('#')]
    site = None
    site_names = []
    for line in lines:
        if SERVER_START.match(line):
            if site:
                # Note: keep in sync with last lines in this function!
                for site_name in site_names:
                    site['name'] = site_name
                    yield site
            site = copy.deepcopy(SITE_TEMPLATE)
            site_names = []
            continue
        if not site:
            # Not ready to start yet.
            continue
        if line.startswith('server_name'):
            line = line.replace(',', ' ')
            line = line[len('server_name'):]
            parts = line.split()
            site_names = [part for part in parts if part]
        elif line.startswith('listen'):
            if '80' in line:
                site['protocol'] = 'http'
            elif '443' in line:
                site['protocol'] = 'https'
            else:
                logger.error("Listen line without proper port: %s", line)

    if site:
        for site_name in site_names:
            site['name'] = site_name
            yield site


def main():
    """Installed as bin/checkout-info"""
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

    result = {}
    if not os.path.exists(OUTPUT_DIR):
        os.mkdir(OUTPUT_DIR)
        logger.info("Created %s", OUTPUT_DIR)
    if not os.path.exists(NGINX_DIR):
        return
    for conf_filename in os.listdir(NGINX_DIR):
        if conf_filename.startswith('.'):
            continue
        for site_info in extract_sites(os.path.join(NGINX_DIR,
                                                    conf_filename)):
            name = site_info['name']
            protocol = site_info['protocol']  # http or https
            key = '_'.join([name, protocol])
            if key in result:
                logger.error("Nginx %s site %s from %s is already known",
                             protocol, name, conf_filename)
                continue

            result[key] = site_info
    open(OUTPUT_FILE, 'w').write(json.dumps(result))
