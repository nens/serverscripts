"""Extract information from apache config files.

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

VAR_DIR = '/var/local/serverscripts'
APACHE_DIR = '/etc/apache2/sites-enabled'
SERVER_START = re.compile(r"""
    ^<virtualhost    # '<virtualhost' at the start of the line.
    .*$              # Whatever till the end of line.
    """, re.VERBOSE)
OUTPUT_DIR = '/var/local/serverinfo-facts'
OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'apaches.fact')
SITE_TEMPLATE = {'name': '',
                 'protocol': 'http',
}


logger = logging.getLogger(__name__)


def extract_sites(filename):
    """Yield info per site found in the apache config file"""
    logger.debug("Looking at %s", filename)
    lines = open(filename).readlines()
    lines = [line.strip().lower() for line in lines]
    lines = [line for line in lines
             if line and not line.startswith('#')]
    site = None
    site_names = []
    for line in lines:
        if SERVER_START.match(line):
            if site:
                # Note: keep in sync with last lines in this function!
                for site_name in site_names:
                    # Yield one complete site object per name.
                    site['name'] = site_name
                    logger.debug("Returning site %s", site_name)
                    yield site
            logger.debug("Starting new site...")
            site = copy.deepcopy(SITE_TEMPLATE)
            site_names = []
            # Extract xxxxxxxx
            if '80' in line:
                site['protocol'] = 'http'
            elif '443' in line:
                site['protocol'] = 'https'
            else:
                logger.error("<Virtualhost> line without proper port: %s", line)
            continue

        if not site:
            # Not ready to start yet.
            continue
        if line.startswith('servername') or line.startswith('serveralias'):
            line = line.replace(',', ' ')
            parts = line.split()
            site_names += [part for part in parts[1:] if part]
            site_names = [site_name.replace(':443', '').replace(':80', '')
                          for site_name in site_names]

        elif line.startswith('documentroot') or line.startswith('customlog'):
            # Assumption: doc root or custom log is in the buildout directory
            # where our site is, so something like
            # /srv/DIRNAME/var/log/access.log.
            #
            # Format is like this:
            # CustomLog /srv/somewhere/var/log/access.log combined
            #
            # DocumentRoot /srv/serverinfo.lizard.net/var/info
            line_parts = [part for part in line.split() if part]
            where = line_parts[1]
            path_parts = where.split('/')
            if path_parts[1] != 'srv':
                logger.warn(
                    "logfile or doc root line without a dir inside /srv: %s",
                    line)
                continue
            buildout_directory = path_parts[2]
            logger.debug(
                "Found log or doc root pointing to a /srv dir: /srv/%s",
                buildout_directory)
            site['related_checkout'] = buildout_directory

        elif line.startswith('proxypass'):
            parts = line.split()
            something_with_http = [part for part in parts
                                   if part.startswith('http')]
            if something_with_http:
                proxied_to = something_with_http[0]
                proxied_to = proxied_to.replace('$1', '')
                parsed = urlparse(proxied_to)
                if parsed.hostname == 'localhost':
                    logger.warn(
                        "Proxy to localhost port %s, we'd expect mod_wsgi...",
                        parsed.port)
                    site['proxy_to_local_port'] = str(parsed.port)
                else:
                    logger.debug("Proxy to other server: %s", parsed.hostname)
                    site['proxy_to_other_server'] = parsed.hostname

        elif line.startswith('redirect'):
            parts = line.split()
            parts = [part for part in parts if part]
            if len(parts) < 3:
                logger.warn("Redirect line with fewer than 3 parts: %s", line)
                continue
            if ('410'  in parts[1]) or ('gone' in parts[1]):
                site['redirect_to'] = 'GONE'
                continue
            if parts[2] != '/':
                logger.info("Redirect doesn't redirect the root: %s", line)
                continue
            something_with_http = [part for part in parts
                                   if part.startswith('http')]
            if something_with_http:
                redirect_to = something_with_http[0]
                site['redirect_to'] = urlparse(redirect_to).hostname
                site['redirect_to_protocol'] = urlparse(redirect_to).scheme
            else:
                logger.warn(
                    "Redirect without recognizable http(s) target: %s",
                    line)
        elif line.startswith('rewriterule'):
            parts = line.split()
            parts = [part for part in parts if part]
            parts = [part.replace('"', '').replace("'", '') for part in parts]
            if len(parts) < 3:
                logger.warn("Rewriterule line with fewer than 3 parts: %s",
                            line)
                continue
            if parts[1] != '^(.*)':
                logger.info("Rewriterule doesn't redirect the root: %s", line)
                continue
            something_with_http = [part for part in parts
                                   if part.startswith('http')]
            if something_with_http:
                redirect_to = something_with_http[0]
                redirect_to = redirect_to.rstrip('$1')
                site['redirect_to'] = urlparse(redirect_to).hostname
                site['redirect_to_protocol'] = urlparse(redirect_to).scheme
            else:
                logger.warn(
                    "Redirect without recognizable http(s) target: %s",
                    line)

    if site:
        for site_name in site_names:
            # Yield one complete site object per name.
            site['name'] = site_name
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
    if not os.path.exists(APACHE_DIR):
        return
    num_errors = 0
    for conf_filename in os.listdir(APACHE_DIR):
        if conf_filename.startswith('.'):
            continue
        for site_info in extract_sites(os.path.join(APACHE_DIR,
                                                    conf_filename)):
            name = site_info['name']
            protocol = site_info['protocol']  # http or https
            key = '_'.join([name, protocol])
            if key in result:
                logger.error("Apache %s site %s from %s is already known",
                             protocol, name, conf_filename)
                num_errors += 1
                continue

            result[key] = site_info
    open(OUTPUT_FILE, 'w').write(json.dumps(result, sort_keys=True, indent=4))
    zabbix_file = os.path.join(VAR_DIR, 'nens.duplicate_apache_sites.warnings')
    open(zabbix_file, 'w').write(str(num_errors))
