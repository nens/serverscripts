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

SUCCEEDED = 'SUCCEEDED'
FAILED = 'FAILED'

QUEUES_LIMIT = 'queues_limit'
MESSAGES_LIMIT = 'messages_limit'

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
        if len(line_attrs) == 2:
            queues[line_attrs[0]] = int(line_attrs[1])
    return queues


def retrieve_queues(vhost):
    """Run shell command en return a tuple with status and stdout."""
    status = SUCCEEDED
    stdout = ''
    try:
        stdout = subprocess.check_output(
            ['rabbitmqctl', 'list_queues', '-p', str(vhost)])
    except OSError:
        status = FAILED
        stdout = "rabbitmqctl is not available."
    except subprocess.CalledProcessError:
        status = FAILED
        stdout = "'rabbitmqctl list_queues -p %s' returns non-zero exit status." % vhost 
    
    return (status, stdout)


def get_max_queue(queues):
    """Retrieve a queue with max messages as tuple."""
    queue, value = max(queues.iteritems(), key=operator.itemgetter(1))
    return (queue, value)


def load_config(config_file_path):
    with open(config_file_path, 'r') as config_file:
        try:
            content = json.loads(config_file.read())
            status = SUCCEEDED
        except:
            content = 'Can not load a rabbitmq-zabbix configuration.'
            logger.exception(content)
            status = FAILED
        return (status, content)            


def cast_to_int(value):
    try:
        return int(value)
    except:
        return None


def validate_configuration(configuration):
    """Validate loaded content of rabbitmq-zabbix.json."""
    error_type = "Rabbitmq-Zabbix configuration error:"
    if not configuration:
        logger.error("%s: no vhost.", error_type)
        return False

    for vhost in configuration:
        queues_limit_value = configuration[vhost].get(QUEUES_LIMIT)
        messages_limit_value = configuration[vhost].get(MESSAGES_LIMIT)
        queues_limit_key = configuration[vhost].has_key(QUEUES_LIMIT)
        messages_limit_key = configuration[vhost].has_key(MESSAGES_LIMIT)

        if not queues_limit_key:
            logger.error("%s: vhost '%s' has not '%s' item.",
                         error_type, vhost, QUEUES_LIMIT)
            return False
        if not messages_limit_key:
            logger.error("%s: vhost '%s' has not '%s' item.",
                         error_type, vhost, MESSAGES_LIMIT)
            return False
        if cast_to_int(queues_limit_value) is None:
            logger.error("%s: '%s'.'%s' is not an integer.",
                         error_type, vhost, QUEUES_LIMIT)
            return False
        if cast_to_int(messages_limit_value) is None:
            logger.error("%s: '%s'.'%s' is not an integer.",
                         error_type, vhost, MESSAGES_LIMIT)            
            return False
    return True


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

    status, configuration = load_config(CONFIG_FILE)
    if status == FAILED:
        logger.error("Exit due configuration error %s" % configuration)
        return

    is_valid_configuration = validate_configuration(configuration)
    if not is_valid_configuration:
        logger.error("Exit due invalid configuration")
        return

    results = {}
    for vhost in configuration:
        status, stdout = retrieve_queues(vhost)
        logger.debug("Result of rabbitmqctl for vhost %s: status %s, stdout %s" % (
            vhost, status, stdout))
        if status == FAILED:
            results[vhost] = {'messsage': stdout}
            continue
        queues = parse_queues_stdout(stdout)
        # check or the vhost has a queue
        if len(queues) <= 0:
            results[vhost] = {'messsage': 'The vhost has any queue or not exists'}
            continue
        # check the allowed amount of queues per vhost
        if len(queue) >= configuration[vhost][QUEUES_LIMIT]:
            results[vhost] = {'messsage': 'The limit of queues is reached'}
            continue
        # check the allowed amount of messages in the largest queue 
        queue_name, queue_value = get_max_queue(queues)
        if queue_value >= configuration[vhost][MESSAGES_LIMIT]:
            results[vhost] = {
                'message': 'The limit of messages in queue "%s" is reached' % max_queue[0]}

    logger.info("Write check results to files: %d." % len(results))
    open(OUTPUT_FILE, 'w').write(json.dumps(results, sort_keys=True, indent=4))
    zabbix_file = os.path.join(VAR_DIR, 'nens.rabbitmq.warnings')
    open(zabbix_file, 'w').write('%d' % len(results))
