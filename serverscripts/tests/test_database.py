from serverscripts import database
from unittest import TestCase

import mock


class DatabaseTestCase(TestCase):

    def setUp(self):
        self.sizes_output = """
        template1                  |        6000000
        template0                  |        6000000
        postgres                   |        6000000
        lizard_nxt                 |     2207000000
        template_postgis           |       11000000
        efcis_site2                |     1781000000
        uploadserver_site_redesign |       88000000
        bluegold-staging           |       22000000
        lizard5-staging-default    |       22000000
        deltaportaal2              |       49000000
        efcis_site                 |      575000000
        uploadserver_site          |      118000000
        flooding                   |      731000000"""

    def test_available(self):
        database.is_postgres_available()
        self.assertTrue("Smoke test, it just should not crash")

    def test_postgres_version(self):
        with mock.patch('subprocess.Popen.communicate') as mock_communicate:
            mock_communicate.return_value = ("9.3/main (port 5432): online",
                                             "")
            self.assertEquals("9.3", database._postgres_version())

    def test_database_info(self):
        with mock.patch('subprocess.Popen.communicate') as mock_communicate:
            mock_communicate.return_value = (self.sizes_output,
                                             "")
            self.assertEquals(9, len(database._database_infos()))

    def test_database_info(self):
        with mock.patch('subprocess.Popen.communicate') as mock_communicate:
            mock_communicate.return_value = (self.sizes_output,
                                             "")
            self.assertEquals(
                database._database_infos()['lizard_nxt']['size'],
                2207000000)

    def test_all_info(self):
        with mock.patch(
                'serverscripts.database._postgres_version') as mock_version:
            with mock.patch(
                    'serverscripts.database._database_infos') as mock_infos:
                mock_version.return_value = '2.0'
                mock_infos.return_value = {'reinout': {'name': 'reinout',
                                                       'size': 20},
                                           'alexandr': {'name': 'reinout',
                                                        'size': 40}}
                result = database.all_info()
                self.assertEquals(result['version'], '2.0')
                self.assertEquals(result['num_databases'], 2)
                self.assertEquals(result['total_databases_size'], 60)
                self.assertEquals(result['biggest_database_size'], 40)
