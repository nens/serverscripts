"""Extract information from rabbitmq.

"""
import argparse
import json
import logging
import os
import re
import serverscripts
import sys
import subprocess
import operator


VAR_DIR = '/var/local/serverscripts'

CONFIG_DIR = '/etc/serverscripts'
CONFIG_FILE = os.path.join(CONFIG_DIR, 'rabbitmq_zabbix.json')

OUTPUT_DIR = '/var/local/serverinfo-facts'
OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'rabbitmq.fact')


logger = logging.getLogger(__name__)


def parse_queues_stdout(queues_stdout):
    """
    Retrieve the amount of messages per queues.
    queues_stdout attribute contains the shell output of
    'rabbitmqctl list_queues' command like:

    Listing queues ...
    queuename1     0
    queuename1     4
    ...done.

    The second column contains amount of massages in the queue.
    """
    queues = {}
    for line in queues_stdout.split('\n'):
        line_attrs = line.split()
        print(line_attrs)
        if len(line_attrs) == 2:
            queues[line_attrs[0]] = int(line_attrs[1])
    return queues


def retrieve_queues(vhost):
    """Run shell command en return the queues."""
    result = subprocess.check_output(
        ['rabbitmqctl', 'list_queues', '-p', str(vhost)])
    if result:
        return result
    else:
        logger.warn("%s vhost is not available or has not any queue.")
        return ''


def get_max_queue(queues):
    """Retrieve a queue with max messages as tulp."""
    return max(queues.iteritems(), key=operator.itemgetter(1))


def load_config(config_file_path):
    with open(config_file_path, 'r') as config_file:
        return json.loads(config_file.read())


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

    result = {}
    if not os.path.exists(OUTPUT_DIR):
        os.mkdir(OUTPUT_DIR)
        logger.info("Created %s", OUTPUT_DIR)
    if not os.path.exists(CONFIG_DIR):
        os.mkdir(CONFIG_DIR)
        logger.info("Created %s", CONFIG_DIR)
    if not os.path.isfile(CONFIG_FILE):
        return

    rabbitmq_config = load_config(CONFIG_FILE)
    logger.info("VHOST to check %d" % len(rabbitmq_config))
    vhosts = rabbitmq_config.keys()
    result = {}
    for vhost in vhosts:
        queues_stdout = retrieve_queues(vhost)
        logger.debug("Queues stdout: %s" % queues_stdout)
        queues = parse_queues_stdout(queues_stdout)
        max_queue = get_max_queue(queues)
        if max_queue[1] >= rabbitmq_config[vhost]['messages']:
            result[vhost] = {max_queue[0]: max_queue[1]}
        else:
            continue

    logger.info("Check results to dump: %d." % len(result))
    open(OUTPUT_FILE, 'w').write(json.dumps(result, sort_keys=True, indent=4))
    zabbix_file = os.path.join(VAR_DIR, 'nens.rabbitmq.warnings')
    open(zabbix_file, 'w').write(len(results))
