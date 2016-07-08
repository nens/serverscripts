"""Extract information from nginx config files.

"""
import argparse
import json
import logging
import os
import re
import serverscripts
import sys
import subprocess


VAR_DIR = '/var/local/serverscripts'

CONFIG_DIR = '/etc/serverscripts'
CONFIG_FILE = os.path.join(CONFIG_DIR, 'rabbitmq_zabbix.json')

OUTPUT_DIR = '/var/local/rabbitmq-facts'
OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'rabbitmq.fact')


logger = logging.getLogger(__name__)


def parse_queues_stdout(queues_stdout):
    """
    Retrieve the amount of messages in queues.
    queues_stdout attribute contains the shell output of 
    rabbitmqctl list_queues command like:
    
    Listing queues ...
    queuename1     0
    queuename1     4
    ...done.

    The second column contains amount of massages in the queue.
    """
    messages = []
    for line in queues_stdout.split('\n'):
        line_attrs = line.split('\t')
        if len(line_attrs) > 1:
            messages.append(int(line_attrs[1]))
    return messages


def retrieve_queues(vhost):
    """Run shell command en return the queues."""
    process = subprocess.Popen(
        ['rabbitmqctl', 'list_queues', '-p', vhost],
        stdout=subprocess.PIPE)
    status, stdout = process.communicate()
    if status:
        return stdout
    else:
        logger.warn("%s vhost is not available or has not any queue.")
        return ''


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
    if not os.path.isfile(CONFIG_FILE)
        return
    
    rabbitmq_config = json.loads(CONFIG_FILE)
    vhosts = rabbitmq_config.keys()
    for vhost in vhosts
    for paramee

    open(OUTPUT_FILE, 'w').write(json.dumps(result, sort_keys=True, indent=4))
    zabbix_file = os.path.join(VAR_DIR, 'nens.nginx_sites.warnings')
    open(zabbix_file, 'w').write(str(num_errors))
