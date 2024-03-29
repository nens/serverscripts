"""Extract information from nginx config files.

"""
from urllib.parse import urlparse

import argparse
import copy
import json
import logging
import os
import re
import serverscripts
import sys


VAR_DIR = "/var/local/serverscripts"
NGINX_DIR = "/etc/nginx/sites-enabled"
GIT_URL = re.compile(
    r"""
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
    """,
    re.VERBOSE,
)
SERVER_START = re.compile(
    r"""
    ^server          # 'server' at the start of the line.
    \W*              # Optional whitespace.
    \{               # Starting curly brace
    .*$              # Whatever till the end of line.
    """,
    re.VERBOSE,
)
OUTPUT_DIR = "/var/local/serverinfo-facts"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "nginxs.fact")
SITE_TEMPLATE = {"name": "", "protocol": "http"}


logger = logging.getLogger(__name__)


def extract_sites(filename):
    """Yield info per site found in the nginx config file"""
    logger.debug("Looking at %s", filename)
    lines = open(filename).readlines()
    lines = [line.strip() for line in lines]
    lines = [line.rstrip(";") for line in lines]
    lines = [line for line in lines if line and not line.startswith("#")]
    site = None
    site_names = []
    for line in lines:
        if SERVER_START.match(line):
            if site:
                # Note: keep in sync with last lines in this function!
                for site_name in site_names:
                    # Yield one complete site object per name.
                    site["name"] = site_name
                    logger.debug("Returning site %s", site_name)
                    yield site
            logger.debug("Starting new site...")
            site = copy.deepcopy(SITE_TEMPLATE)
            site_names = []
            continue
        if not site:
            # Not ready to start yet.
            continue
        if line.startswith("server_name"):
            line = line.replace(",", " ")
            if ")$" in line:
                # lizard 5 regex magic
                line = line.replace("~(", " ")
                line = line.replace(")$", " ")
                line = line.replace(r"\.", ".")
                line = line.replace("|", " ")
            line = line[len("server_name") :]
            parts = line.split()
            site_names = [part for part in parts if part]

        elif line.startswith("listen"):
            if "80" in line:
                site["protocol"] = "http"
            elif "443" in line:
                site["protocol"] = "https"
            else:
                logger.error("Listen line without proper port: %s", line)
        elif re.compile(r"access_log\s+off").match(line):
            # Logging may be disabled (favicon.ico, robots.txt, etc.).
            # http://nginx.org/en/docs/http/ngx_http_log_module.html
            continue
        elif line.startswith("access_log"):
            # Assumption: access log is in the buildout directory where our
            # site is, so something like /srv/DIRNAME/var/log/access.log.
            line = line[len("access_log") :]
            line = line.strip()
            logfilename = line.split()[0]
            parts = logfilename.split("/")
            if parts[1] != "srv":
                logger.warning("access_log line without a dir inside /srv: %s", line)
                continue
            buildout_directory = parts[2]
            logger.debug(
                "Found access_log pointing to a /srv dir: /srv/%s", buildout_directory
            )
            site["related_checkout"] = buildout_directory

        elif line.startswith("proxy_pass"):
            line = line[len("proxy_pass") :]
            line = line.strip()
            proxied_to = line.split()[0]
            parsed = urlparse(proxied_to)
            if parsed.hostname == "localhost":
                logger.debug("Proxy to localhost port %s", parsed.port)
                site["proxy_to_local_port"] = str(parsed.port)
            else:
                logger.debug("Proxy to other server: %s", parsed.hostname)
                site["proxy_to_other_server"] = parsed.hostname

        elif line.startswith("return"):
            if not ("301" in line) and not ("302" in line):
                logger.info("Return line without 301/302 code: %s", line)
                continue
            parts = line.split()
            something_with_http = [part for part in parts if part.startswith("http")]
            if something_with_http:
                # https://uploadservice.lizard.net$request_uri
                redirect_to = something_with_http[0]
                redirect_to = redirect_to.split("$")[0]
                site["redirect_to"] = urlparse(redirect_to).hostname
                site["redirect_to_protocol"] = urlparse(redirect_to).scheme

    if site:
        for site_name in site_names:
            # Yield one complete site object per name.
            site["name"] = site_name
            logger.debug("Returning site %s", site_name)
            yield copy.deepcopy(site)


def main():
    """Installed as bin/checkout-info"""
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

    result = {}
    if not os.path.exists(OUTPUT_DIR):
        os.mkdir(OUTPUT_DIR)
        logger.info("Created %s", OUTPUT_DIR)
    if not os.path.exists(NGINX_DIR):
        return
    num_errors = 0
    for conf_filename in os.listdir(NGINX_DIR):
        if conf_filename.startswith("."):
            continue
        try:
            fullpath = os.path.join(NGINX_DIR, conf_filename)
            for site_info in extract_sites(fullpath):
                name = site_info["name"]
                protocol = site_info["protocol"]  # http or https
                key = "_".join([name, protocol])
                if key in result:
                    logger.error(
                        "Nginx %s site %s from %s is already known",
                        protocol,
                        name,
                        conf_filename,
                    )
                    num_errors += 1
                    continue

                result[key] = site_info
        except:  # Bare except
            num_errors += 1
            logger.exception("Something went wrong when reading %s", fullpath)

    open(OUTPUT_FILE, "w").write(json.dumps(result, sort_keys=True, indent=4))
    zabbix_file = os.path.join(VAR_DIR, "nens.nginx_sites.warnings")
    open(zabbix_file, "w").write(str(num_errors))
