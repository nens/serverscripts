from serverscripts import checkouts
from unittest import TestCase

import mock
import os
import shutil
import sys
import tempfile


OUR_PYTHON_VERSION = "%s.%s.%s" % (
    sys.version_info.major,
    sys.version_info.minor,
    sys.version_info.micro,
)


def test_parse_pip_freeze_with_error():
    to_parse = "ERROR: foo\nWARNING: bar\nappdirs==1.4.4\n-e sso==2.18.dev0"
    to_parse += "\n-e git+git@github.com:nens/repo.git@master#egg=repo"
    actual = checkouts.parse_freeze(to_parse)
    assert actual == {
        "appdirs": "1.4.4",
        "-e sso": "2.18.dev0",
        "-e repo": "master",
    }


class VenvPipenvTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.our_dir = os.path.dirname(__file__)
        cls.dir_outside_proj = tempfile.mkdtemp()
        cls.dir_with_pipenv = tempfile.mkdtemp()
        cls.dir_with_venv = tempfile.mkdtemp()
        os.chdir(cls.dir_with_pipenv)
        os.system(sys.executable + " -m pipenv install --python=" + sys.executable)
        os.chdir(cls.dir_with_venv)
        os.system(sys.executable + " -m virtualenv .")
        os.chdir(cls.our_dir)
        cls.example_diffsettings_output = open(
            os.path.join(cls.our_dir, "example_diffsettings.txt")
        ).read()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.dir_outside_proj)
        shutil.rmtree(cls.dir_with_pipenv)
        shutil.rmtree(cls.dir_with_venv)

    def test_no_pipenv(self):
        # a subdirectory of the project
        self.assertIsNone(checkouts.pipenv_info(self.our_dir))
        # an empty directory in /tmp
        self.assertIsNone(checkouts.pipenv_info(self.dir_outside_proj))

    def test_correct_pipenv_info(self):
        output = checkouts.pipenv_info(self.dir_with_pipenv)
        self.assertIn("pip", output)
        self.assertEqual(output["python"], OUR_PYTHON_VERSION)

    def test_correct_venv_info(self):
        """Pipenv is just a special virtualenv"""
        bin_dir = self.dir_with_venv + "/bin"
        output = checkouts.venv_info(bin_dir)
        self.assertIn("pip", output)
        self.assertEqual(output["python"], OUR_PYTHON_VERSION)

    def test_django_info_no_pipenv(self):
        with mock.patch("serverscripts.checkouts.get_output") as mock_get_output:
            with mock.patch("serverscripts.checkouts.os.stat") as mock_stat:
                mock_get_output.return_value = ("", "bloody murder")
                mock_stat.return_value = mock.Mock(st_uid=1234)
                result = checkouts.django_info_pipenv(self.dir_outside_proj)
                self.assertIsNone(result)

    def test_django_info(self):
        with mock.patch("serverscripts.checkouts.get_output") as mock_get_output:
            with mock.patch("serverscripts.checkouts.os.stat") as mock_stat:
                mock_get_output.return_value = (self.example_diffsettings_output, "")
                mock_stat.return_value = mock.Mock(st_uid=1234)
                result = checkouts.django_info_pipenv(self.dir_outside_proj)
                self.assertEqual(len(result["databases"]), 2)


class GitAndEggInfoTestCase(TestCase):
    def setUp(self):
        self.our_dir = os.path.dirname(__file__)
        self.dir_with_git = os.path.join(self.our_dir, "..", "..")
        self.dir_with_buildout = os.path.join(self.our_dir, "example_buildout_project")
        self.example_diffsettings_output = open(
            os.path.join(self.our_dir, "example_diffsettings.txt")
        ).read()

    def test_no_git_dir(self):
        self.assertEqual(checkouts.git_info(self.our_dir), None)

    def test_correct_git_dir(self):
        output = checkouts.git_info(self.dir_with_git)
        self.assertIn("github.com/nens/serverscripts", output["url"])

    def test_no_eggs_info(self):
        self.assertEqual(checkouts.eggs_info(self.our_dir), None)

    def test_correct_eggs_info(self):
        output = checkouts.eggs_info(self.dir_with_buildout)
        self.assertIn("serverscripts", output)

    def test_python_version_in_eggs_info(self):
        with mock.patch("serverscripts.checkouts.get_output") as mock_get_output:
            mock_get_output.return_value = ("Python 2.9.42", "")
            output = checkouts.eggs_info(self.dir_with_buildout)
            self.assertEqual(output["python"], "2.9.42")
            mock_get_output.assert_called_with(
                "python3 --version", cwd=self.dir_with_buildout
            )

    def test_git_regex(self):
        line = "origin git@github.com:nens/delfland.git (fetch)"
        match = checkouts.GIT_URL.search(line)
        self.assertEqual(match.group("user"), "nens")

    def test_git_regex2(self):
        line = "origin git@github.com:nens/delfland.git (fetch)"
        match = checkouts.GIT_URL.search(line)
        self.assertEqual(match.group("project"), "delfland")

    def test_https_regex(self):
        line = "origin https://github.com/ddsc/webclient.git (fetch)"
        match = checkouts.GIT_URL.search(line)
        self.assertEqual(match.group("user"), "ddsc")

    def test_git_regex_without_dot_git(self):
        line = "origin	git@github.com:nens/ror-export (fetch)"
        match = checkouts.GIT_URL.search(line)
        self.assertEqual(match.group("user"), "nens")

    def test_django_info(self):
        with mock.patch("serverscripts.checkouts.get_output") as mock_get_output:
            with mock.patch("serverscripts.checkouts.os.stat") as mock_stat:
                mock_get_output.return_value = (self.example_diffsettings_output, "")
                mock_stat.return_value = mock.Mock(st_uid=1234)
                result = checkouts.django_info_buildout("some/bin/django")
                self.assertEqual(len(result["databases"]), 2)

    def test_supervisorctl_warnings(self):
        with mock.patch("serverscripts.checkouts.get_output") as mock_get_output:
            mock_get_output.return_value = (
                """
gunicorn                         RUNNING   pid 1418, uptime 0:39:04
something                        STOPPED

            """,
                "",
            )
            result = checkouts.supervisorctl_warnings("some/bin/supervisorctl")
            self.assertEqual(result, 1)
