"""Extract information from a buildout with python/zope/django.

A buildout should be inside ``/srv/``, the id of a buildout is the directory
name. So ``/srv/reinout.vanrees.org/`` has the id ``reinout.vanrees.org``.

Originally copied from ``buildout.py`` in
https://github.com/reinout/serverinfo/

"""
import copy
import json
import logging
import os
import re
import subprocess
import sys

import pkg_resources

SRV_DIR = '/srv/'
GIT_URL = re.compile(r"""
    origin           # We want the origin remote.
    \W*              # Whitespace.
    .*               # git@ or https://
    github.com       # Base github incantation.
    [:/]             # : (git@) or / (https)
    (?P<user>.+)     # User/org string.
    /                # Slash.
    (?P<project>.+)  # Project.
    \.git             # .git
    .*$              # Whatever till the end of line.
    """, re.VERBOSE)
OUTPUT_DIR = '/var/local/serverinfo-facts'
OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'checkouts.fact')


logger = logging.getLogger(__name__)


def git_info(directory):
    data = {}
    dir_contents = os.listdir(directory)
    if not '.git' in dir_contents:
        logger.warn("No .git directory found in %s", directory)
        return

    sub = subprocess.Popen('git remote -v', cwd=directory, shell=True,
                           stdout=subprocess.PIPE,
                           universal_newlines=True)
    for line in sub.communicate():
        if not line:
            continue
        match = GIT_URL.search(line)
        if not match:
            continue
        data['url'] = 'https://github.com/{user}/{project}'.format(
            user=match.group('user'),
            project=match.group('project'))
    sub = subprocess.Popen('git status', cwd=directory, shell=True,
                           stdout=subprocess.PIPE,
                           universal_newlines=True)
    output, errors = sub.communicate()
    output = output.lower()
    if 'master' in output:
        data['release'] = 'master'
    else:
        sub = subprocess.Popen('git describe', cwd=directory, shell=True,
                               stdout=subprocess.PIPE,
                               universal_newlines=True)
        first_line = sub.communicate()[0]
        data['release'] = first_line.strip()
    data['has_local_modifications'] = ('changes not staged' in output)
    data['has_untracked_files'] = ('untracked' in output)
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
        exec(''.join(new_contents))
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


def main():
    """Installed as bin/checkout-info"""
    result = {}
    if not os.path.exists(OUTPUT_DIR):
        os.mkdir(OUTPUT_DIR)
        logger.info("Created %s", OUTPUT_DIR)
    for name in os.listdir(SRV_DIR):
        directory = os.path.join(SRV_DIR, name)
        if not os.path.exists(os.path.join(directory, 'buildout.cfg')):
            logger.warn("/srv directory without buildout.cfg: %s", directory)
            continue
        checkout = {}
        checkout['name'] = name
        checkout['directory'] = directory
        checkout['eggs'] = eggs_info(directory)
        checkout['git'] = git_info(directory)

        # TODO: diffsettings
        # TODO: git status
        # ^^^ Perhaps in separate checker?

        result[name] = checkout
    open(OUTPUT_FILE, 'w').write(json.dumps(result))
