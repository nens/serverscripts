from serverscripts import checkouts
from unittest import TestCase

import mock
import os
import shutil
import sys
import tempfile


class PipenvTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.our_dir = os.path.dirname(__file__)
        cls.dir_outside_proj = tempfile.mkdtemp()
        cls.dir_with_pipenv = tempfile.mkdtemp()
        os.chdir(cls.dir_with_pipenv)
        os.system("pipenv install")
        os.chdir(cls.our_dir)
        cls.example_diffsettings_output = open(os.path.join(
            cls.our_dir, 'example_diffsettings.txt')).read()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.dir_outside_proj)
        shutil.rmtree(cls.dir_with_pipenv)

    def test_no_pipenv(self):
        # a subdirectory of the project
        self.assertIsNone(checkouts.pipenv_info(self.our_dir))
        # an empty directory in /tmp
        self.assertIsNone(checkouts.pipenv_info(self.dir_outside_proj))

    def test_correct_pipenv_info(self):
        output = checkouts.pipenv_info(self.dir_with_pipenv)
        self.assertIn('serverscripts', output)
        self.assertEquals(output['mock'], mock.__version__)
        our_python_version = '%s.%s.%s' % (sys.version_info.major,
                                           sys.version_info.minor,
                                           sys.version_info.micro)
        self.assertEquals(output['python'], our_python_version)

    def test_django_info_no_pipenv(self):
        with mock.patch('serverscripts.checkouts.get_output') as mock_get_output:
            mock_get_output.return_value = ('', 'bloody murder')
            result = checkouts.django_info_pipenv(self.dir_outside_proj)
            self.assertIsNone(result)

    def test_django_info_pipenv(self):
        result = checkouts.django_info_pipenv(self.dir_with_pipenv)
        self.assertIsNone(result)

    def test_django_info(self):
        with mock.patch('serverscripts.checkouts.get_output') as mock_get_output:
            mock_get_output.return_value = (self.example_diffsettings_output, '')
            result = checkouts.django_info_pipenv(self.dir_outside_proj)
            self.assertEquals(len(result['databases']), 2)


class GitAndEggInfoTestCase(TestCase):

    def setUp(self):
        self.our_dir = os.path.dirname(__file__)
        self.dir_with_git = os.path.join(self.our_dir, '..', '..')
        self.dir_with_buildout = os.path.join(self.our_dir,
                                              'example_buildout_project')
        self.example_diffsettings_output = open(os.path.join(
            self.our_dir, 'example_diffsettings.txt')).read()

    def test_no_git_dir(self):
        self.assertEquals(checkouts.git_info(self.our_dir), None)

    def test_correct_git_dir(self):
        output = checkouts.git_info(self.dir_with_git)
        self.assertIn('github.com/nens/serverscripts', output['url'])

    def test_no_eggs_info(self):
        self.assertEquals(checkouts.eggs_info(self.our_dir), None)

    def test_correct_eggs_info(self):
        output = checkouts.eggs_info(self.dir_with_buildout)
        self.assertIn('serverscripts', output)

    def test_python_version_in_eggs_info(self):
        output = checkouts.eggs_info(self.dir_with_buildout)
        our_python_version = '%s.%s.%s' % (sys.version_info.major,
                                           sys.version_info.minor,
                                           sys.version_info.micro)
        self.assertEquals(output['python'], our_python_version)

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

    def test_django_info(self):
        with mock.patch('serverscripts.checkouts.get_output') as mock_get_output:
            mock_get_output.return_value = (self.example_diffsettings_output,
                                             "")
            result = checkouts.django_info_buildout('some/bin/django')
            self.assertEquals(len(result['databases']), 2)

    def test_supervisorctl_warnings(self):
        with mock.patch('serverscripts.checkouts.get_output') as mock_get_output:
            mock_get_output.return_value = ("""
gunicorn                         RUNNING   pid 1418, uptime 0:39:04
something                        STOPPED

            """, "")
            result = checkouts.supervisorctl_warnings(
                'some/bin/supervisorctl')
            self.assertEquals(result, 1)
