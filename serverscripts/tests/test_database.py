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
        with mock.patch("serverscripts.database.get_output") as mock_get_output:
            mock_get_output.return_value = (
                "14160 bla bla /usr/lib/postgresql/9.3/bin/postgres bla bla",
                "",
            )
            self.assertEqual("9.3", database._postgres_version())

    def test_database_info1(self):
        with mock.patch("serverscripts.database.get_output") as mock_get_output:
            mock_get_output.return_value = (self.sizes_output, "")
            self.assertEqual(9, len(database._database_infos()))

    def test_database_info2(self):
        with mock.patch("serverscripts.database.get_output") as mock_get_output:
            mock_get_output.return_value = (self.sizes_output, "")
            self.assertEqual(
                database._database_infos()["lizard_nxt"]["size"], 2207000000
            )

    def test_database_usage(self):
        with mock.patch("serverscripts.database.get_output") as mock_get_output:
            mock_get_output.return_value = ("""
                9 ror_export database=ror_export
               73 waterlabel_site database=waterlabel_site
            23054 efcis_site database=efcis_site
            26591 schademodule database=schademodule2018
            """, "")
            result = database._usage()
            print(result)
            self.assertEqual(result["waterlabel_site"], 73)

    def test_all_info(self):
        with mock.patch("serverscripts.database._postgres_version") as mock_version:
            with mock.patch("serverscripts.database._database_infos") as mock_infos:
                with mock.patch("serverscripts.database._usage") as mock_usage:
                    with mock.patch("serverscripts.database.get_output") as mock_get_output:
                        mock_get_output.return_value = ("", "")
                        mock_version.return_value = "2.0"
                        mock_infos.return_value = {
                            "reinout": {"name": "reinout", "size": 20},
                            "alexandr": {"name": "reinout", "size": 40},
                        }
                        mock_usage.return_value = {"reinout": 1972}
                        result = database.all_info()
                        self.assertEqual(result["version"], "2.0")
                        self.assertEqual(result["num_databases"], 2)
                        self.assertEqual(result["total_databases_size"], 60)
                        self.assertEqual(result["biggest_database_size"], 40)
                        self.assertEqual(result["databases"]["reinout"]["num_logins"], 1972)
                        self.assertEqual(result["databases"]["alexandr"]["num_logins"], 0)
