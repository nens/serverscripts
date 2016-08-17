"""Extract information from rabbitmq.

"""
import argparse
import json
import logging
import os
import serverscripts
import sys
import subprocess
import operator


VAR_DIR = '/var/local/serverscripts'

CONFIG_DIR = '/etc/serverscripts'
CONFIG_FILE = os.path.join(CONFIG_DIR, 'rabbitmq_zabbix.json')

ALLOWED_NUM_QUEUES = 100
ALLOWED_NUM_MESSAGES = 200

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


def parse_vhosts_stdout(vhosts_stdout):
    """
    Retrieve vhosts from stdout,
    vhosts_stdout attribute contains the shell output of
    'rabbitmqctl list_vhosts' command like:

    Listing vhosts ...
    /
    efcis
    nrr
    lizard-nxt
    ...done.

    """
    vhosts = []
    for line in vhosts_stdout.split('\n'):
        if line.find("done") > 0:
            # end of stdout is reached
            break
        line_attrs = line.split()
        if len(line_attrs) == 1:
            vhosts.append(line_attrs[0])
    return vhosts


def retrieve_vhosts():
    """Run shell command 'rabbitmqctl list_vhosts', parse stdout, return vhosts."""
    stdout = ''
    try:
        stdout = subprocess.check_output(
            ['rabbitmqctl', 'list_vhosts'])
    except OSError:
        logger.info("rabbitmqctl is not available.")
        return
    except subprocess.CalledProcessError:
        logger.info("'rabbitmqctl list_vhosts' returns non-zero exit status.")
        return

    return parse_vhosts_stdout(stdout)


def retrieve_queues(vhost):
    """Run shell command, parse stdout, returtn queues."""
    stdout = ''
    try:
        stdout = subprocess.check_output(
            ['rabbitmqctl', 'list_queues', '-p', str(vhost)])
    except OSError:
        logger.warn("rabbitmqctl is not available.")
        return
    except subprocess.CalledProcessError:
        logger.warn("'rabbitmqctl list_queues -p %s' returns non-zero exit status." % vhost)
        return

    return parse_queues_stdout(stdout)


def get_max_queue(queues):
    """Retrieve a queue with max messages as tuple."""
    queue, value = max(queues.iteritems(), key=operator.itemgetter(1))
    return (queue, value)


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
        try:
            int(queues_limit_value)
            int(messages_limit_value)
        except:
            logger.error("%s: '%s' one of the values is not an integer.",
                         error_type, vhost)
            return False
    return True


def load_config(config_file_path):
    """Retrieve conriguration, return a {} when
    the content is invalid"""
    content = {}
    with open(config_file_path, 'r') as config_file:
        try:
            content = json.loads(config_file.read())
        except:
            logger.error('Can not load a rabbitmq-zabbix configuration.')
    # end with
    if validate_configuration(content):
        return content
    return {}


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

    vhosts = retrieve_vhosts()
    if not vhosts:
        return
    if not os.path.exists(CONFIG_DIR):
        os.mkdir(CONFIG_DIR)
        logger.info("Created %s", CONFIG_DIR)

    configuration = load_config(CONFIG_FILE)
    num_too_big = 0
    wrong_vhosts = []

    for vhost in vhosts:
        vhost_num_queues = ALLOWED_NUM_QUEUES
        queue_num_messages = ALLOWED_NUM_MESSAGES
        queues = retrieve_queues(vhost)
        # check or the vhost has a queue
        if not queues:
            continue
        # check the allowed amount of queues per vhost
        vhost_configuration = configuration.get(vhost)
        if vhost_configuration:
            vhost_num_queues = vhost_configuration.get(QUEUES_LIMIT)
            queue_num_messages = vhost_configuration.get(MESSAGES_LIMIT)
        if len(queues) >= vhost_num_queues:
            wrong_vhosts.append(vhost)
            num_too_big = num_too_big + 1
            continue
        # check the allowed amount of messages in the largest queue 
        queue_name, queue_value = get_max_queue(queues)
        if queue_value >= queue_num_messages:
            wrong_vhosts.append(vhost)
            num_too_big = num_too_big + 1

    logger.info("Write check results to files: %d." % num_too_big)
    zabbix_message_file = os.path.join(VAR_DIR, 'nens.rabbitmq.message')
    if num_too_big:
        open(zabbix_message_file, 'w').write(
            "Number queues/messages too big by: %s" % ", ".join(wrong_vhosts))
    else:
        open(zabbix_message_file, 'w').write("")
    zabbix_rmq_count_file = os.path.join(VAR_DIR, 'nens.num_rabbitmq_too_big.warnings')
    open(zabbix_rmq_count_file, 'w').write('%d' % num_too_big)
