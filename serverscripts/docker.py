"""Extract info on docker."""
import argparse
import json
import logging
import os
import serverscripts
import subprocess
import sys


VAR_DIR = '/var/local/serverscripts'
OUTPUT_DIR = '/var/local/serverinfo-facts'
OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'dockers.fact')
DOCKER_TEMPLATE = {'active_images': 0,
                   'active_containers': 0,
                   'active_volumes': 0,
}


logger = logging.getLogger(__name__)


def is_docker_available():
    return os.path.exists('/etc/docker')


def all_info():
    """Return the info we want to extract from docker.

    The output looks like this::

      $ docker system df

      TYPE                TOTAL               ACTIVE              SIZE                RECLAIMABLE
      Images              50                  2                   16.66 GB            16.13 GB (96%)
      Containers          2                   2                   70 B                0 B (0%)
      Local Volumes       3                   3                   123 MB              0 B (0%)

    """
    result = DOCKER_TEMPLATE.copy()
    command = "docker system df"
    logger.debug("Running '%s'...", command)
    sub = subprocess.Popen(command,
                           shell=True,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE,
                           universal_newlines=True)
    output, error = sub.communicate()
    if error:
        logger.warn("Error output from docker command: %s", error)
    lines = [line.strip() for line in output.split('\n')]
    lines = [line.lower() for line in lines if line]
    if 'active' not in lines[0]:
        return
    start_column = lines[0].find('active')
    for line in lines[1:]:
        count = line[start_column:start_column + 4].strip()
        try:
            count = int(count)
        except:
            count = 'unknown'
            logger.exception("Couldn't parse int: %r", count)
            continue
        if 'images' in line:
            result['active_images'] = count
        if 'containers' in line:
            result['active_containers'] = count
        if 'volumes' in line:
            result['active_volumes'] = count
    logger.info("Found the following info on docker: %r", result)
    return result


def main():
    """Installed as bin/docker-info"""
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

    if not is_docker_available():
        return

    info_on_docker = all_info()
    docker_is_active = any(info_on_docker.values())
    result_for_serverinfo = {'available': True,
                             'active': docker_is_active}
    open(OUTPUT_FILE, 'w').write(json.dumps(result_for_serverinfo,
                                            sort_keys=True,
                                            indent=4))

    zabbix_file1 = os.path.join(VAR_DIR, 'nens.num_active_docker_images.info')
    open(zabbix_file1, 'w').write(str(info_on_docker['active_images']))
    zabbix_file2 = os.path.join(VAR_DIR, 'nens.num_active_docker_containers.info')
    open(zabbix_file2, 'w').write(str(info_on_docker['active_containers']))
    zabbix_file3 = os.path.join(VAR_DIR, 'nens.num_active_docker_volumes.info')
    open(zabbix_file3, 'w').write(str(info_on_docker['active_volumes']))
