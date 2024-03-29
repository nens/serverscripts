"""Extract info on docker."""
from serverscripts.checkouts import parse_freeze
from serverscripts.checkouts import parse_python_version
from serverscripts.utils import get_output

import argparse
import json
import logging
import os
import serverscripts
import sys


VAR_DIR = "/var/local/serverscripts"
OUTPUT_DIR = "/var/local/serverinfo-facts"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "docker.fact")
DOCKER_TEMPLATE = {
    "active_images": 0,
    "active_containers": 0,
    "active_volumes": 0,
    "containers": [],
}
DOCKER_PS_FIELDS = (
    "ID",
    "Image",
    "Command",
    "CreatedAt",
    "RunningFor",
    "Ports",
    # "State",  errors on older docker
    "Status",
    "Size",
    "Names",
    # "Labels",  very long field
    "Mounts",
    "Networks",
)
# create a string like: {"id": {{.ID}}, "image": "{{.Image}}"}
DOCKER_PS_FORMAT = "\t".join(["{{." + x + "}}" for x in DOCKER_PS_FIELDS])
# recognize a python interpreter by the presence of one of these in the docker command:
PYTHON_EXEC_OPTIONS = (
    "python",
    "python3",
    "bin/python",
    ".venv/bin/python",
    "/usr/bin/python",
    "/usr/bin/python3",
)
DOCKER_EXEC_ERROR = "OCI runtime exec failed:"

logger = logging.getLogger(__name__)


def is_docker_available():
    return os.path.exists("/etc/docker")


def python_details(container):
    """Run pip freeze in containers that are python-based

    A container is python based if it has "python" in its command.
    """
    # identify the python interpreter inside the docker
    split_command = container["command"].strip('"').split(" ")
    for python_exec in PYTHON_EXEC_OPTIONS:
        if python_exec in split_command:
            break
    else:
        # it is some other command (gunicorn; bin/gunicorn)
        dirname = os.path.dirname(split_command[0])
        if dirname == "":
            python_exec = "python3"  # global default
        else:
            python_exec = os.path.join(dirname, "python")
    python_in_docker = "docker exec " + container["id"] + " " + python_exec + " "

    # identify the python version
    command = "--version"
    logger.debug(
        "Running %s %s in container '%s'..", python_exec, command, container["names"]
    )
    output, _ = get_output(python_in_docker + command, fail_on_exit_code=False)
    if output.startswith(DOCKER_EXEC_ERROR) or output.startswith("Traceback"):
        logger.info("Did not find Python in docker %s", container["names"])
        return {}
    python_version = parse_python_version(output, "")
    logger.info(
        "Found Python %s ('%s') in container '%s'..",
        python_version,
        python_exec,
        container["names"],
    )

    # identify the python packages (eggs)
    command = "-m pip freeze --all"
    logger.debug(
        "Running %s %s in container '%s'..", python_exec, command, container["names"]
    )
    output, _ = get_output(python_in_docker + command, fail_on_exit_code=False)
    if output.startswith(DOCKER_EXEC_ERROR):
        logger.warning("Error output from pip freeze in docker: %s", output)
    eggs = parse_freeze(output)
    eggs["python"] = python_version

    return {"eggs": eggs}


def container_details():
    """Return a list of details of running containers

    The fields are all fields that docker ps can return. See:
    See https://docs.docker.com/engine/reference/commandline/ps/.
    """
    command = "docker ps --no-trunc --format '{}'".format(DOCKER_PS_FORMAT)
    logger.debug("Running 'docker ps'...")
    output, error = get_output(command, fail_on_exit_code=False)
    if error:
        logger.warning("Error output from docker command: %s", error)
        return []
    keys = [x.lower() for x in DOCKER_PS_FIELDS]
    return [dict(zip(keys, line.split("\t"))) for line in output.split("\n") if line]


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
    output, error = get_output(command, fail_on_exit_code=False)
    if error:
        logger.warning("Error output from docker command: %s", error)
    lines = [line.strip() for line in output.split("\n")]
    lines = [line.lower() for line in lines if line]
    if not lines or "active" not in lines[0]:
        return {}
    start_column = lines[0].find("active")
    for line in lines[1:]:
        count = line[start_column : start_column + 4].strip()
        try:
            count = int(count)
        except:
            count = "unknown"
            logger.exception("Couldn't parse int: %r", count)
            continue
        if "images" in line:
            result["active_images"] = count
        if "containers" in line:
            result["active_containers"] = count
        if "volumes" in line:
            result["active_volumes"] = count
    result["containers"] = container_details()
    for container in result["containers"]:
        container["python"] = python_details(container)
    logger.info("Found %d active docker containers", result["active_containers"])
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

    if not is_docker_available():
        return

    info_on_docker = all_info()
    docker_is_active = any(info_on_docker.values())
    result_for_serverinfo = {
        "available": True,
        "active": docker_is_active,
        "containers": info_on_docker["containers"],
    }
    open(OUTPUT_FILE, "w").write(
        json.dumps(result_for_serverinfo, sort_keys=True, indent=4)
    )

    if "active_images" in info_on_docker:
        zabbix_file1 = os.path.join(VAR_DIR, "nens.num_active_docker_images.info")
        open(zabbix_file1, "w").write(str(info_on_docker["active_images"]))
        zabbix_file2 = os.path.join(VAR_DIR, "nens.num_active_docker_containers.info")
        open(zabbix_file2, "w").write(str(info_on_docker["active_containers"]))
        zabbix_file3 = os.path.join(VAR_DIR, "nens.num_active_docker_volumes.info")
        open(zabbix_file3, "w").write(str(info_on_docker["active_volumes"]))
