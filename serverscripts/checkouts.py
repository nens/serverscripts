"""Extract information from a buildout with python/zope/django.

A buildout should be inside ``/srv/``, the id of a buildout is the directory
name. So ``/srv/reinout.vanrees.org/`` has the id ``reinout.vanrees.org``.

Originally copied from ``buildout.py`` in
https://github.com/reinout/serverinfo/

"""
from serverscripts.utils import get_output

import argparse
import copy
import json
import logging
import os
import pkg_resources
import re
import serverscripts
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
EDITABLE_PKG = re.compile(r"""
    -e                # editable
    \W*               # Whitespace.
    .*                # git@ or https://
    github.com        # Base github incantation.
    [:/]              # : (git@) or / (https)
    (?P<user>.+)      # User/org string.
    /                 # Slash.
    (?P<project>\S+?) # Project.
    (\.git)?          # Optional '.git'.
    @(?P<ref>.+)      # Branch or revision
    \#egg=            # Opening parentheses.
    (?P<module>.+)$   # Module name
    """, re.VERBOSE)
PYTHON_VERSION = re.compile(r"""
    .*                # anything
    Python            # what we are looking for
    \W*               # Whitespace.
    (?P<version>.[0-9.]+)  # version
    .*$               # anything until the end
    """, re.VERBOSE)
VAR_DIR = '/var/local/serverscripts'
OUTPUT_DIR = '/var/local/serverinfo-facts'
OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'checkouts.fact')
SUPERVISOR_CRONJOB_EXCEPTIONS = [
    'cron',
    # p-3di-model-d1
    'process_uploaded_model_files',
    # p-web-ws-00-d6
    'calculate_province_statistics_script',
    'check_result_zip_files',
    'create_province_excel_script',
]


logger = logging.getLogger(__name__)


def git_info(directory):
    """Return git information (like remote repo) for the directory"""
    logger.debug("Looking in %s...", directory)
    data = {}
    dir_contents = os.listdir(directory)
    if '.git' not in dir_contents:
        logger.warn("No .git directory found in %s", directory)
        return

    output, error = get_output('git remote -v', cwd=directory)
    for line in output.split('\n'):
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
    output, error = get_output('git status', cwd=directory)
    output = output.lower()
    if 'master' in output:
        data['release'] = 'master'
        logger.debug("It is a master checkout")
    else:
        output, error = get_output('git describe',
                                   cwd=directory)
        first_line = output.split('\n')[0]
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
                if (
                    'import ' in line or 'os.chdir' in line or
                    '__import__' in line or '_interactive = True' in line
                ):
                    break
            new_contents.append(line)
        # This is very evil, but cool! Because of the __name__ != main the
        # remainder of the script is not executed.
        exec(''.join(new_contents))
        possible_egg_dirs.update(sys.path)
        # Detect python executable
        first_line = lines[0].strip()
        python_executable = first_line.lstrip('#!')
        output, error = get_output('%s --version' % python_executable,
                                   cwd=directory)
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


def whereis(name):
    """ Find the first available path to an executable script. """
    paths = os.environ.get("PATH").split(":")
    for path in paths:
        executable = os.path.join(path, name)
        if os.access(executable, os.X_OK):
            return executable


def pipenv_info(directory):
    directory = os.path.abspath(directory)
    output, error = get_output("pipenv --where", cwd=directory)

    if output.strip() != directory:
        logger.error("No pipenv found in %s", directory)
        return

    output, error = get_output("pipenv run python --version", cwd=directory)
    match = PYTHON_VERSION.match((output + error).replace('\n', ''))
    if match is None:
        python_version = 'UNKNOWN'
    else:
        python_version = match.group('version')
    logger.debug("Python version used: %s", python_version)

    output, error = get_output("pipenv run pip freeze", cwd=directory)

    pkgs = dict()
    for pkg in output.split('\n'):
        if len(pkg) == 0:
            continue
        if pkg.startswith('-e'):
            match = EDITABLE_PKG.match(pkg)
            pkgs[match.group('project')] = match.group('ref')
        pkg = pkg.split('==')  # name==version
        if len(pkg) != 2:
            # invalid spec
            continue
        pkgs[pkg[0]] = pkg[1]

    pkgs['python'] = python_version
    return pkgs


def django_info_buildout(bin_django):
    matplotlibenv = 'MPLCONFIGDIR=/tmp'
    # Corner case when something needs matplotlib in django's settings.
    command = "sudo -u buildout %s %s diffsettings" % (matplotlibenv,
                                                       bin_django)
    logger.debug("Running %s diffsettings...", bin_django)
    output, error = get_output(command)
    if error:
        logger.warn("Error output from diffsettings command: %s", error)
        if not output:
            return
    return parse_django_info(output)


def django_info_pipenv(directory):
    django_script = 'pipenv run python manage.py'

    matplotlibenv = 'MPLCONFIGDIR=/tmp'
    # Corner case when something needs matplotlib in django's settings.
    command = "sudo -u buildout %s %s diffsettings" % (matplotlibenv,
                                                       django_script)
    output, error = get_output(command, cwd=directory)
    if error:
        logger.warn("Error output from diffsettings command: %s", error)
        if not output:
            return
    return parse_django_info(output)


def parse_django_info(output):
    result = {'databases': []}
    dont_care, tempfile_name = tempfile.mkstemp()
    interesting = ['DEBUG',
                   'DATABASES',
                   'SETTINGS_MODULE', ]
    lines = [line for line in output.split('\n')
             if '<' not in line
             and 'datetime' not in line
             and line]
    lines = [line for line in lines
             if line.split()[0] in interesting]
    output = '\n'.join(lines)

    open(tempfile_name, 'w').write(output)
    global_env = {}
    settings = {}
    try:
        execfile(tempfile_name, global_env, settings)
    except Exception:
        logger.exception("'diffsettings' output could not be parsed:\n%s",
                         output)
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


def supervisorctl_warnings(supervisorctl_command):
    """Return number of not-running processes inside supervisorctl"""
    command = "%s status" % supervisorctl_command
    logger.debug("Running '%s'...", command)
    output, error = get_output(command)
    if error:
        logger.warn("Error output from supervisorctl command: %s", error)

    lines = [line.strip() for line in output.split('\n')]
    lines = [line for line in lines if line]
    for exception in SUPERVISOR_CRONJOB_EXCEPTIONS:
        lines = [line for line in lines if exception not in line]
    not_running = [line for line in lines if 'running' not in line.lower()]
    num_not_running = len(not_running)
    if num_not_running:
        logger.warn(
            "Some processes in %s aren't running:", supervisorctl_command)
        for line in not_running:
            logger.warn("    %s", line)
    return num_not_running


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
    num_not_running = 0
    if not os.path.exists(OUTPUT_DIR):
        os.mkdir(OUTPUT_DIR)
        logger.info("Created %s", OUTPUT_DIR)
    for name in os.listdir(SRV_DIR):
        directory = os.path.join(SRV_DIR, name)
        if os.path.islink(directory):
            logger.info("Ignoring %s, it is a symlink", directory)
            continue
        if os.path.isfile(directory):
            logger.info("Ignoring %s, it is a file (*.tgz, for instance)",
                        directory)
            continue
        if name == 'lost+found':
            logger.info("Ignoring /srv/lost+found dir")
            continue
        checkout = {}
        checkout['name'] = name
        checkout['directory'] = directory
        checkout['git'] = git_info(directory)

        # determine the type of installation (buildout or pipenv)
        if os.path.exists(os.path.join(directory, 'Pipfile')) and \
                whereis('pipenv'):
            mode = 'pipenv'
        elif os.path.exists(os.path.join(directory, 'buildout.cfg')):
            mode = 'buildout'
        else:
            mode = None
            logger.warn("/srv directory without buildout.cfg or "
                        "Pipfile: %s", directory)

        # determine the installed packages
        if mode == 'buildout':
            checkout['eggs'] = eggs_info(directory)
        elif mode == 'pipenv':
            checkout['eggs'] = pipenv_info(directory)
        else:
            checkout['eggs'] = None

        # determine django info settings
        if mode == 'buildout':
            bin_django = os.path.join(directory, 'bin', 'django')
            if os.path.exists(bin_django):
                checkout['django'] = django_info_buildout(bin_django)
                if not checkout['django']:
                    num_bin_django_failures += 1
            else:
                logger.debug("bin/django not found in %s", directory)
        elif mode == 'pipenv':
            django_manage = os.path.join(directory, 'manage.py')
            if os.path.exists(django_manage):
                checkout['django'] = django_info_pipenv(directory)
                if not checkout['django']:
                    num_bin_django_failures += 1
            else:
                logger.debug("manage.py not found in %s", directory)

        # determine supervisorctl status
        if mode == 'buildout':
            bin_supervisor = os.path.join(directory, 'bin', 'supervisorctl')
            if os.path.exists(bin_supervisor):
                try:
                    num_not_running += supervisorctl_warnings(bin_supervisor)
                except Exception:  # Bare except.
                    logger.exception("Error calling %s", bin_supervisor)
            else:
                logger.debug("bin/supervisorctl not found in %s", directory)
        elif mode == 'pipenv' and whereis('supervisorctl'):
            # expect the supervisor conf file in the etc directory
            etc_directory = os.path.join(directory, 'etc')
            if os.path.exists(etc_directory):
                confs = [fn for fn in os.listdir(etc_directory)
                         if 'supervisor' in fn and fn.endswith('.conf')]
                if len(confs) == 1:
                    svc_command = "supervisorctl -c '{0}'".format(
                        os.path.join(etc_directory, confs[0]),
                    )
                    try:
                        num_not_running += supervisorctl_warnings(svc_command)
                    except Exception:  # Bare except.
                        logger.exception("Error calling %s", svc_command)
                elif len(confs) == 0:
                    logger.exception("No supervisorctl configuration found in %s",
                                     etc_directory)
                else:
                    logger.exception("Multiple supervisorctl configurations "
                                     "found in %s", etc_directory)
        result[name] = checkout

    open(OUTPUT_FILE, 'w').write(json.dumps(result, sort_keys=True, indent=4))
    zabbix_file = os.path.join(VAR_DIR, 'nens.bin_django_failures.errors')
    open(zabbix_file, 'w').write(str(num_bin_django_failures))
    zabbix_file2 = os.path.join(VAR_DIR, 'nens.num_not_running.warnings')
    open(zabbix_file2, 'w').write(str(num_not_running))
