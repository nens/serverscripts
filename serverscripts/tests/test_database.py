from pprint import pprint
from serverscripts import database
from unittest import TestCase

import mock
import os


class DatabaseTestCase(TestCase):

    def setUp(self):
        # our_dir = os.path.dirname(__file__)
        # self.example = os.path.join(
        #     our_dir, 'example_haproxy.cfg')
        pass

    def test_available(self):
        database.is_postgres_available()
        self.assertTrue("Smoke test, it just should not crash")

    def test_postgres_version(self):
        with mock.patch('subprocess.Popen.communicate') as mock_communicate:
            mock_communicate.return_value = ("9.3/main (port 5432): online",
                                             "")
            self.assertEquals("9.3", database._postgres_version())
