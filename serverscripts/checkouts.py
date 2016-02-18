"""Extract information from a buildout with python/zope/django.

A buildout should be inside ``/srv/``, the id of a buildout is the directory
name. So ``/srv/reinout.vanrees.org/`` has the id ``reinout.vanrees.org``.

Originally copied from ``buildout.py`` in
https://github.com/reinout/serverinfo/

"""
from xml.etree import ElementTree

import copy
import json
import logging
import os
import re
import subprocess
import sys

import pkg_resources

from serverinfo import utils

FILENAME = 'buildout___{id}.json'
SRV_DIR = '/srv/'
GIT_URL = re.compile(r"""
    origin           # We want the origin remote.
    \W*              # Whitespace.
    git@github.com:  # Base github incantation.
    (?P<user>.+)     # User/org string.
    /                # Slash.
    (?P<project>.+)  # Project.
    \.git             # .git
    .*$              # Whatever till the end of line.
    """, re.VERBOSE)


logger = logging.getLogger(__name__)


def id(directory):
    """Return id of buildout based on the directory name."""
    directory = directory.rstrip('/')
    parts = directory.split('/')
    return parts[-1]


def vcs_info(directory):
    data = {}
    dir_contents = os.listdir(directory)
    if not '.git' in dir_contents:
        logger.warn("No .git directory found in %s", directory)
        return

    sub = subprocess.Popen('git remote -v', cwd=directory, shell=True,
                           stdout=subprocess.PIPE)
    for line in sub.communicate():
        if not line:
            continue
        match = GIT_URL.search(line)
        data['url'] = 'https://github.com/{user}/{project}'.format(
            user=match.group('user'),
            project=match.group('project'))
    sub = subprocess.Popen('git status', cwd=directory, shell=True,
                           stdout=subprocess.PIPE)
    first_line = sub.communicate()[0]
    if 'master' in first_line:
        data['release'] = 'master'
    else:
        sub = subprocess.Popen('git describe', cwd=directory, shell=True,
                               stdout=subprocess.PIPE)
        first_line = sub.communicate()[0]
        data['release'] = first_line.strip()
    return data


def eggs_info(directory):
    files_of_interest = ['python', 'django', 'test']
    possible_egg_dirs = set()
    before = copy.copy(sys.path)
    bin_dir = os.path.join(directory, 'bin')
    if not os.path.exists(bin_dir):
        return

    for file_ in os.listdir(bin_dir):
        if file_ not in files_of_interest:
            continue
        new_contents = []
        for line in open(os.path.join(directory, 'bin', file_)):
            # Skipping imports that may be unavailable in the current path.
            if line.strip() != 'import sys':
                # When we see these lines we have past the sys.path:
                if 'import ' in line or 'os.chdir' in line or\
                    '__import__' in line or '_interactive = True' in line:
                    break
            new_contents.append(line)
        # This is very evil, but cool! Because the __name__ != main the
        # remainder of the script is not executed.
        exec ''.join(new_contents)
        possible_egg_dirs.update(sys.path)
    # reset sys.path
    sys.path = before

    eggs = {}
    for dir_ in possible_egg_dirs:
        info = list(pkg_resources.find_distributions(dir_, only=True))
        if len(info) == 0:
            continue
        info = info[0]
        eggs[info.project_name] = info.version
    return eggs


def grab_one(directory):
    """Grab and write info on one buildout."""
    logger.info("Grabbing buildout info from %s", directory)
    result = {}
    result['directory'] = directory
    result['eggs'] = eggs_info(directory)
    result['vcs'] = vcs_info(directory)
    result['id'] = id(directory)
    result['hostname'] = utils.hostname()

    outfile = os.path.join(utils.grabber_dir(),
                           FILENAME.format(id=id(directory)))
    open(outfile, 'w').write(
        json.dumps(result, sort_keys=True, indent=4))
    logger.debug("Wrote info to %s", outfile)


def grab_all():
    """Grab and write info on all the buildouts."""
    buildout_dirs = [os.path.join(SRV_DIR, d)
                     for d in os.listdir(SRV_DIR)]
    buildout_dirs = [d for d in buildout_dirs
                     if os.path.exists(os.path.join(d, 'buildout.cfg'))]
    for buildout_dir in buildout_dirs:
        grab_one(buildout_dir)
