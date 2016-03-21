"""Extract information from postgres databases.

"""
import argparse
import json
import logging
import os
import serverscripts
import subprocess
import sys

VAR_DIR = '/var/local/serverscripts'
POSTGRES_DIR = '/etc/postgres/sites-enabled'
OUTPUT_DIR = '/var/local/serverinfo-facts'
OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'databases.fact')


logger = logging.getLogger(__name__)


def is_postgres_available():
    return os.path.exists('/etc/postgresql')


def _postgres_version():
    sub = subprocess.Popen('service postgresql status',
                           shell=True,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE,
                           universal_newlines=True)
    output, error = sub.communicate()
    # Output is something like "9.3/main (port 5432): online"
    parts = output.split('/')
    return parts[0]


def _database_sizes():
    """Return dict with {database name: database size}"""
    query = ("select datname, pg_database_size(datname)/1024/1024 "
             "from pg_database;")
    command = "sudo -u postgres psql -c '%s' --tuples_only" % query
    sub = subprocess.Popen(command,
                           shell=True,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE,
                           universal_newlines=True)
    output, error = sub.communicate()
    result = {}
    for line in (output + error).split('\n'):
        if not '|' in line:
            continue
        parts = line.split('|')
        name = parts[0].strip()
        size = parts[1].strip()  # in MB
        if name.startswith('template') or name == 'postgres':
            logger.debug("Omitting database %s", name)
            continue
        size = int(size)
        result[name] = size
        logger.info("Found database %s with size %s MB", name, size)
    return result


def all_info():
    """Return the info we want to extract from postgres + its databases"""
    result = {}
    result['version'] = _postgres_version()
    result['databases'] = _database_sizes()

    if result['databases']:
        # Info for zabbix.
        result['num_databases'] = len(result['databases'])
        result['total_databases_size'] = sum(result['databases'].values())
        result['biggest_database_size'] = max(result['databases'].values())

    return result


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

    if not os.path.exists(OUTPUT_DIR):
        os.mkdir(OUTPUT_DIR)
        logger.info("Created %s", OUTPUT_DIR)

    if not is_postgres_available():
        return

    result = all_info()
    open(OUTPUT_FILE, 'w').write(json.dumps(result, sort_keys=True, indent=4))

    zabbix_file = os.path.join(VAR_DIR, 'nens.num_databases.info')
    open(zabbix_file, 'w').write(str(result['num_databases']))
    zabbix_file = os.path.join(VAR_DIR, 'nens.total_databases_size.info')
    open(zabbix_file, 'w').write(str(result['total_databases_size']))
    zabbix_file = os.path.join(VAR_DIR, 'nens.biggest_database_size.info')
    open(zabbix_file, 'w').write(str(result['biggest_database_size']))
