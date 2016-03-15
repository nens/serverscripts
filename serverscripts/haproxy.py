"""Extract information from haproxy config files.

"""
import argparse
import copy
import json
import logging
import os
import re
import serverscripts
import sys

from serverscripts.six.moves.urllib.parse import urlparse

HAPROXY_CFG = '/etc/haproxy/haproxy.cfg'
SITE = re.compile(r"""
    ^acl                   # 'acl' at the start of the line.
    \s+                    # Whitespace.
    host_(?P<backend>\S+)  # 'host_nxt' returns 'nxt' as backend.
    \s+                    # Whitespace.
    .*                     # Whatever.
    \s+                    # Whitespace.
    (?P<sitename>\S+)$     # Sitename at the end of the line.
    """, re.VERBOSE)
BACKEND_START = re.compile(r"""
    ^backend                  # 'backend' at the start of the line.
    \s+                       # Whitespace.
    (?P<backend>\S+)_cluster$ # 'nxt_cluster' returns 'nxt' as backend.
    """, re.VERBOSE)
SERVER = re.compile(r"""
    ^server                # 'server' at the start of the line.
    \s+                    # Whitespace.
    (?P<server>\S+)        # Server name.
    \s+                    # Whitespace.
    .*$                    # Whatever till the end of the line.
    """, re.VERBOSE)

OUTPUT_DIR = '/var/local/serverinfo-facts'
OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'haproxys.fact')


logger = logging.getLogger(__name__)


def extract_sites(filename):
    """Yield info per site found in the haproxy config file"""
    logger.debug("Looking at %s", filename)
    lines = open(filename).readlines()
    lines = [line.strip().lower() for line in lines]
    lines = [line for line in lines
             if line and not line.startswith('#')]

    # First grab the {sitename: backend} info
    sitenames_with_backend = {}
    for line in lines:
        if SITE.match(line):
            match = SITE.search(line)
            sitename = match.group('sitename')
            backend_name = match.group('backend')
            logger.debug("Found site %s with backend %s",
                         sitename, backend_name)
            sitenames_with_backend[sitename] = backend_name

    # Then collect {backend: [servers]} info
    backends_with_servers = {}
    backend = None
    servers = []
    for line in lines:
        match = BACKEND_START.search(line)
        if match:
            if backend:
                # First store existing one.
                # Note: keep in sync with last lines in this function!
                backends_with_servers[backend] = servers
                logger.debug("Adding servers %s to backend %s",
                             servers, backend)

            backend = match.group('backend')
            servers = []
            logger.debug("Starting new backend' %s'", backend)
            continue

        if not backend:
            # Not ready to start yet.
            continue

        match = SERVER.search(line)
        if match:
            servers.append(match.group('server'))

        if line.startswith('listen'):
            # We're done!
            backends_with_servers[backend] = servers
            logger.debug("Adding servers %s to backend %s",
                         servers, backend)
            break

    # Now we're ready to return sites. One site per backend.
    for sitename, backend in sitenames_with_backend.items():
        for server in backends_with_servers[backend]:
            yield {'name': sitename,
                   'protocol': 'http',  # Hardcoded
                   'proxy_to_other_server': server}


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
    if not os.path.exists(HAPROXY_CFG):
        return
    for site_info in extract_sites(HAPROXY_CFG):
        name = site_info['name']
        protocol = site_info['protocol']  # http or https
        key = '_'.join([name, protocol])
        if key in result:
            logger.error("Haproxy %s site %s from %s is already known",
                         protocol, name, HAPROXY_CFG)
            # TODO: record this as an error for zabbix
            continue

        result[key] = site_info
    open(OUTPUT_FILE, 'w').write(json.dumps(result, sort_keys=True, indent=4))
