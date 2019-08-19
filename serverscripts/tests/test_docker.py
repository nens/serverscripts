from serverscripts import docker
from unittest import TestCase

import mock


REGULAR_OUTPUT = """
TYPE                TOTAL               ACTIVE              SIZE                RECLAIMABLE
Images              50                  2                   16.66 GB            16.13 GB (96%)
Containers          2                   2                   70 B                0 B (0%)
Local Volumes       3                   3                   123 MB              0 B (0%)
"""


class DockerTestCase(TestCase):

    def test_all_info(self):
        with mock.patch('subprocess.Popen.communicate') as mock_communicate:
            mock_communicate.return_value = (REGULAR_OUTPUT, "")
            result = docker.all_info()
            self.assertEqual(3, result['active_volumes'])
