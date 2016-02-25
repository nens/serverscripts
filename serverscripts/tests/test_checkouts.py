from mock import patch
from serverscripts import checkouts
from unittest import TestCase

import os


class GitAndEggInfoTestCase(TestCase):

    def setUp(self):
        self.our_dir = os.path.dirname(__file__)
        self.dir_with_git = os.path.join(self.our_dir, '..', '..')

    def test_no_git_dir(self):
        self.assertEquals(checkouts.git_info(self.our_dir), None)

    def test_correct_git_dir(self):
        output = checkouts.git_info(self.dir_with_git)
        self.assertIn('github.com/nens/serverscripts', output['url'])

    def test_no_eggs_info(self):
        self.assertEquals(checkouts.eggs_info(self.our_dir), None)

    def test_correct_eggs_info(self):
        output = checkouts.eggs_info(self.dir_with_git)
        self.assertIn('mock', output)

    def test_git_regex(self):
        line = "origin git@github.com:nens/delfland.git (fetch)"
        match = checkouts.GIT_URL.search(line)
        self.assertEquals(match.group('user'), 'nens')

    def test_git_regex2(self):
        line = "origin git@github.com:nens/delfland.git (fetch)"
        match = checkouts.GIT_URL.search(line)
        self.assertEquals(match.group('project'), 'delfland')

    def test_https_regex(self):
        line = "origin https://github.com/ddsc/webclient.git (fetch)"
        match = checkouts.GIT_URL.search(line)
        self.assertEquals(match.group('user'), 'ddsc')

    def test_git_regex_without_dot_git(self):
        line = "origin	git@github.com:nens/ror-export (fetch)"
        match = checkouts.GIT_URL.search(line)
        self.assertEquals(match.group('user'), 'nens')
