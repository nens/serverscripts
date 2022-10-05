"""Extract information from postgres databases.

"""
from serverscripts.utils import get_output

import argparse
import copy
import json
import logging
import os
import re
import serverscripts
import sys


VAR_DIR = "/var/local/serverscripts"
POSTGRES_DIR = "/etc/postgres/sites-enabled"
OUTPUT_DIR = "/var/local/serverinfo-facts"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "databases.fact")
DATABASE_TEMPLATE = {"name": "", "size": 0}
POSTGRES_VERSION = re.compile(
    r"""
    .*
    /usr/lib/postgresql/     # Start of path to binary
    (?P<version>[0-9\.]+)    # dotted version
    /bin/postgres            # end of path to binary
    .*
    """,
    re.VERBOSE,
)
USAGE_LINE = re.compile(
    r"""
    ^\s*                     # Start of line plus whitespace
    (?P<num_logins>\d+)      # Number of logins
    .+database=              # Whitespace, username, etc.
    (?P<database>[\w\-]+)    # Database name
    """,
    re.VERBOSE,
)
CONNECTION_LINE = re.compile(
    r"""
    ^\s*                     # Start of line plus whitespace
    (?P<num_connections>\d+) # Number of logins
    \s+                      # Whitespace
    (?P<ip_address>[\d\.]+)  # IP address
    """,
    re.VERBOSE,
)


logger = logging.getLogger(__name__)


def is_postgres_available():
    return os.path.exists("/etc/postgresql")


def _postgres_version():
    output, error = get_output("ps ax")
    lines = output.split("\n")
    for line in lines:
        if POSTGRES_VERSION.match(line):
            match = POSTGRES_VERSION.search(line)
            version = match.group("version")
            return version
    return ""


def _database_infos():
    """Return dict with info about the databases {database name: info}"""
    query = "select datname, pg_database_size(datname) from pg_database;"
    command = "sudo -u postgres psql -c '%s' --tuples-only" % query
    output, error = get_output(command)
    if error:
        logger.warning("Error output from psql command: %s", error)
    result = {}
    for line in output.split("\n"):
        if "|" not in line:
            continue
        parts = line.split("|")
        name = parts[0].strip()
        size = parts[1].strip()  # in MB
        if name.startswith("template") or name == "postgres":
            logger.debug("Omitting database %s", name)
            continue
        size = int(size)
        database_info = copy.deepcopy(DATABASE_TEMPLATE)
        database_info["name"] = name
        database_info["size"] = size
        result[name] = database_info
        logger.info(
            "Found database %s with size %s (%s MB)", name, size, size / 1024 / 1024
        )
    return result


def _usage():
    command = (
        'zgrep "connection authorized" /var/log/postgresql/postgres*main.log*'
        r'|grep -v "user=postgres"|cut -d= -f2,3|cut -d\  -f1,2|sort|uniq -c | sort -n'
    )
    output, error = get_output(command)
    if error:
        logger.warning("Error output from usage zgrep command: %s", error)
    # Output looks like this:
    #     9 ror_export database=ror_export
    #    73 waterlabel_site database=waterlabel_site
    # 23054 efcis_site database=efcis_site
    # 26591 schademodule database=schademodule2018
    result = {}
    for line in output.split("\n"):
        if USAGE_LINE.match(line):
            match = USAGE_LINE.search(line)
            num_logins = int(match.group("num_logins"))
            database = match.group("database")
            result[database] = num_logins
    return result


def _connections():
    command = (
        'zgrep "connection received: host=" /var/log/postgresql/postgres*main.log*'
        r'|grep -v "local"|cut -d= -f2|cut -d\  -f1|sort|uniq -c | sort -n'
    )
    output, error = get_output(command)
    if error:
        logger.warning("Error output from usage zgrep command: %s", error)
    # Output looks like this:
    #   1629 10.100.160.171
    #   2495 10.100.57.17
    #   9805 10.100.57.16
    result = {}
    for line in output.split("\n"):
        if CONNECTION_LINE.match(line):
            match = CONNECTION_LINE.search(line)
            num_connections = int(match.group("num_connections"))
            ip_address = match.group("ip_address")
            result[ip_address] = num_connections
    return result


def all_info():
    """Return the info we want to extract from postgres + its databases"""
    result = {}
    result["version"] = _postgres_version()
    if not result["version"]:
        return result
    result["databases"] = _database_infos()

    # database_names = result["databases"].keys()
    result["bloated_tables"] = []  # Left for BBB

    used_databases = _usage()
    for database in result["databases"]:
        result["databases"][database]["num_logins"] = used_databases.get(database, 0)

    result["connections"] = _connections()
    if result["databases"]:
        # Info for zabbix.
        result["num_databases"] = len(result["databases"])
        sizes = [info["size"] for info in result["databases"].values()]
        result["total_databases_size"] = sum(sizes)
        result["biggest_database_size"] = max(sizes)

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

    if not os.path.exists(OUTPUT_DIR):
        os.mkdir(OUTPUT_DIR)
        logger.info("Created %s", OUTPUT_DIR)

    if not is_postgres_available():
        return

    result = all_info()
    open(OUTPUT_FILE, "w").write(json.dumps(result, sort_keys=True, indent=4))

    zabbix_file = os.path.join(VAR_DIR, "nens.num_databases.info")
    open(zabbix_file, "w").write(str(result["num_databases"]))
    zabbix_file = os.path.join(VAR_DIR, "nens.total_databases_size.info")
    open(zabbix_file, "w").write(str(result["total_databases_size"]))
    zabbix_file = os.path.join(VAR_DIR, "nens.biggest_database_size.info")
    open(zabbix_file, "w").write(str(result["biggest_database_size"]))
