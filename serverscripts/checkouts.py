"""Extract information from a buildout with python/zope/django.

A buildout should be inside ``/srv/``, the id of a buildout is the directory
name. So ``/srv/reinout.vanrees.org/`` has the id ``reinout.vanrees.org``.

Originally copied from ``buildout.py`` in
https://github.com/reinout/serverinfo/

"""
import argparse
import copy
import json
import logging
import os
import pkg_resources
import re
import serverscripts
import subprocess
import sys
import tempfile


SRV_DIR = '/srv/'
GIT_URL = re.compile(r"""
    origin            # We want the origin remote.
    \W*               # Whitespace.
    .*                # git@ or https://
    github.com        # Base github incantation.
    [:/]              # : (git@) or / (https)
    (?P<user>.+)      # User/org string.
    /                 # Slash.
    (?P<project>\S+?) # Project.
    (\.git)?          # Optional '.git'.
    \W*               # Whitespace.
    \(                # Opening parentheses.
    .*$               # Whatever till the end of line.
    """, re.VERBOSE)
VAR_DIR = '/var/local/serverscripts'
OUTPUT_DIR = '/var/local/serverinfo-facts'
OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'checkouts.fact')


logger = logging.getLogger(__name__)


def git_info(directory):
    """Return git information (like remote repo) for the directory"""
    logger.debug("Looking in %s...", directory)
    data = {}
    dir_contents = os.listdir(directory)
    if not '.git' in dir_contents:
        logger.warn("No .git directory found in %s", directory)
        return

    sub = subprocess.Popen('git remote -v', cwd=directory, shell=True,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE,
                           universal_newlines=True)
    for line in sub.communicate():
        if not line:
            continue
        match = GIT_URL.search(line)
        if not match:
            logger.warn("Non-recognized 'git remote -v' line: %s", line)
            continue

        data['url'] = 'https://github.com/{user}/{project}'.format(
            user=match.group('user'),
            project=match.group('project'))
        logger.debug("Git repo found: %s", data['url'])
    sub = subprocess.Popen('git status', cwd=directory, shell=True,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE,
                           universal_newlines=True)
    output, errors = sub.communicate()
    output = output.lower()
    if 'master' in output:
        data['release'] = 'master'
        logger.debug("It is a master checkout")
    else:
        sub = subprocess.Popen('git describe', cwd=directory, shell=True,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               universal_newlines=True)
        first_line = sub.communicate()[0]
        data['release'] = first_line.strip()
        logger.debug("We're on a tag or branch: %s", data['release'])
    data['has_local_modifications'] = ('changes not staged' in output)
    data['has_untracked_files'] = ('untracked' in output)
    return data


def eggs_info(directory):
    files_of_interest = ['django', 'test', 'python']
    possible_egg_dirs = set()
    python_version = None
    before = copy.copy(sys.path)
    bin_dir = os.path.join(directory, 'bin')
    if not os.path.exists(bin_dir):
        return

    bin_dir_contents = os.listdir(bin_dir)
    for file_ in files_of_interest:
        if file_ not in bin_dir_contents:
            continue
        if possible_egg_dirs:
            logger.debug("Omitting bin/%s, we already have our info", file_)
            continue
        logger.debug("Looking in bin/%s for eggs+versions", file_)
        new_contents = []
        lines = open(os.path.join(directory, 'bin', file_)).readlines()
        for line in lines:
            # Skipping imports that may be unavailable in the current path.
            if line.strip() != 'import sys':
                # When we see these lines we have moved past the sys.path:
                if 'import ' in line or 'os.chdir' in line or\
                    '__import__' in line or '_interactive = True' in line:
                    break
            new_contents.append(line)
        # This is very evil, but cool! Because of the __name__ != main the
        # remainder of the script is not executed.
        exec(''.join(new_contents))
        possible_egg_dirs.update(sys.path)
        # Detect python executable
        first_line = lines[0].strip()
        python_executable = first_line.lstrip('#!')
        sub = subprocess.Popen('%s --version' % python_executable,
                               cwd=directory,
                               shell=True,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               universal_newlines=True)
        output, error = sub.communicate()
        output = output + error
        try:
            python_version = output.strip().split()[1]
            # ^^^ stdout (3) / stderr (2) outputs "Python 2.7.10"
        except IndexError:
            python_version = 'UNKNOWN'
        logger.debug("Python version used: %s", python_version)

    # reset sys.path
    sys.path = before

    eggs = {}
    for dir_ in possible_egg_dirs:
        info = list(pkg_resources.find_distributions(dir_, only=True))
        if len(info) == 0:
            continue
        info = info[0]
        eggs[info.project_name] = info.version
    if 'Python' in eggs:
        del eggs['Python']  # This is the version we run with, it seems.
    eggs['python'] = python_version
    return eggs


def django_info(bin_django):
    result = {'databases': []}
    command = "sudo -u buildout %s diffsettings" % bin_django
    logger.debug("Running %s diffsettings...", bin_django)
    sub = subprocess.Popen(command,
                           shell=True,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE,
                           universal_newlines=True)
    output, error = sub.communicate()
    if error:
        logger.warn("Error output from diffsettings command: %s", error)
    dont_care, tempfile_name = tempfile.mkstemp()
    output = '\n'.join([line for line in output.split('\n')
                        if 'object at' not in line
                        and 'function <lambda>' not in line])
    # ^^^ This filters out ancient lizard-ui layout.Action objects...
    open(tempfile_name, 'w').write(output)
    global_env = {}
    settings = {}
    try:
        execfile(tempfile_name, global_env, settings)
    except Exception:
        logger.exception("'%s diffsettings' output could not be parsed:\n%s",
                         bin_django, output)
        return
    for database in settings.get('DATABASES', {}).values():
        engine = database.get('ENGINE')
        if 'spatialite' in engine or 'sqlite' in engine:
            result['databases'].append(
                {'name': 'local sqlite/spatialite file',
                 'host': 'localhost'})
        elif 'post' in engine:
            result['databases'].append(
                {'name': database.get('NAME'),
                 'host': database.get('HOST', 'localhost'),
                 'user': database.get('USER')})
        else:
            logger.warn("Unkown db engine %s", engine)
    result['debug_mode'] = ('DEBUG' in settings)
    result['settings_module'] = settings['SETTINGS_MODULE']
    os.remove(tempfile_name)
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

    result = {}
    num_bin_django_failures = 0
    if not os.path.exists(OUTPUT_DIR):
        os.mkdir(OUTPUT_DIR)
        logger.info("Created %s", OUTPUT_DIR)
    for name in os.listdir(SRV_DIR):
        directory = os.path.join(SRV_DIR, name)
        checkout = {}
        checkout['name'] = name
        checkout['directory'] = directory
        checkout['git'] = git_info(directory)
        if os.path.exists(os.path.join(directory, 'buildout.cfg')):
            checkout['eggs'] = eggs_info(directory)
        else:
            logger.warn("/srv directory without buildout.cfg: %s", directory)

        bin_django = os.path.join(directory, 'bin', 'django')
        if os.path.exists(bin_django):
            checkout['django'] = django_info(bin_django)
            if not checkout['django']:
                num_bin_django_failures += 1
        else:
            logger.debug("No django script found: %s", bin_django)

        result[name] = checkout
    open(OUTPUT_FILE, 'w').write(json.dumps(result, sort_keys=True, indent=4))
    zabbix_file = os.path.join(VAR_DIR, 'nens.bin_django_failures.errors')
    open(zabbix_file, 'w').write(str(num_bin_django_failures))
