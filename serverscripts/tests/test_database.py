from serverscripts import database
from unittest import TestCase

import mock


class DatabaseTestCase(TestCase):

    def setUp(self):
        self.sizes_output = """
        template1                  |        6
        template0                  |        6
        postgres                   |        6
        lizard_nxt                 |     2207
        template_postgis           |       11
        efcis_site2                |     1781
        uploadserver_site_redesign |       88
        bluegold-staging           |       22
        lizard5-staging-default    |       22
        deltaportaal2              |       49
        efcis_site                 |      575
        uploadserver_site          |      118
        flooding                   |      731"""

    def test_available(self):
        database.is_postgres_available()
        self.assertTrue("Smoke test, it just should not crash")

    def test_postgres_version(self):
        with mock.patch('subprocess.Popen.communicate') as mock_communicate:
            mock_communicate.return_value = ("9.3/main (port 5432): online",
                                             "")
            self.assertEquals("9.3", database._postgres_version())

    def test_database_sizes1(self):
        with mock.patch('subprocess.Popen.communicate') as mock_communicate:
            mock_communicate.return_value = (self.sizes_output,
                                             "")
            self.assertEquals(9, len(database._database_sizes()))

    def test_database_sizes2(self):
        with mock.patch('subprocess.Popen.communicate') as mock_communicate:
            mock_communicate.return_value = (self.sizes_output,
                                             "")
            self.assertEquals(database._database_sizes()['lizard_nxt'],
                              2207)

    def test_all_info(self):
        with mock.patch(
                'serverscripts.database._postgres_version') as mock_version:
            with mock.patch(
                    'serverscripts.database._database_sizes') as mock_sizes:
                mock_version.return_value = '2.0'
                mock_sizes.return_value = {'reinout': 20,
                                           'alexandr': 40}
                result = database.all_info()
                self.assertEquals(result['version'], '2.0')
                self.assertEquals(result['num_databases'], 2)
                self.assertEquals(result['total_databases_size'], 60)
                self.assertEquals(result['biggest_database_size'], 40)
