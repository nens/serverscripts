from serverscripts import docker
from unittest import TestCase

import mock


REGULAR_OUTPUT = """
TYPE                TOTAL               ACTIVE              SIZE                RECLAIMABLE
Images              50                  2                   16.66 GB            16.13 GB (96%)
Containers          2                   2                   70 B                0 B (0%)
Local Volumes       3                   3                   123 MB              0 B (0%)
"""

DOCKER_PS_OUTPUT = """
cca6ed94102fa749cd32cb289cde07d38323380697a87f6c6334de9715caac76	harbor.lizard.net/threedi/threedi_api	"python manage.py runserver 0.0.0.0:8000"	2021-04-29 12:17:30 +0200 CEST	5 days ago0.0.0.0:8000->8000/tcp, :::8000->8000/tcp	Up 51 minutes	430kB (virtual 866MB)	threedi-api_api_1	/home/casper/code/threedi-api/threedi-api,/home/casper/code/threedi-api/docker-compose.yml	threedi_backend
9d6dda1ad3054870b157252c3ceb752a67d5382430b8d37a9d40b72db83f2777	minio/minio:RELEASE.2020-10-03T02-19-42Z	"/usr/bin/docker-entrypoint.sh server /export"	2021-04-15 13:42:06 +0200 CEST	2 weeks ago	0.0.0.0:9000->9000/tcp, :::9000->9000/tcp	Up 51 minutes	0B (virtual 62.4MB)	threedi-api_minio_1	1c18c1163d44b55769f5090b8ae12fff8c3f970f63007d98b5130b1fdaaebab5,threedi-api_miniodata	threedi_backend
"""

class DockerTestCase(TestCase):
    @mock.patch("serverscripts.docker.get_output")
    @mock.patch("serverscripts.docker.container_details")
    @mock.patch("serverscripts.docker.python_details")
    def test_all_info(self, mock_python, mock_details, mock_output):
        mock_output.return_value = (REGULAR_OUTPUT, "")
        mock_details.return_value = [{"id": "123", "command": "run"}]
        result = docker.all_info()
        self.assertEqual(3, result["active_volumes"])
        self.assertIs(mock_details.return_value, result["containers"])

    @mock.patch("serverscripts.docker.get_output")
    def test_container_details(self, mock_output):
        mock_output.return_value = (DOCKER_PS_OUTPUT, "")
        result = docker.container_details()
        self.assertEqual(2, len(result))
        self.assertEqual(result[0]["command"], "\"python manage.py runserver 0.0.0.0:8000\"")
        self.assertEqual(result[1]["size"], "0B (virtual 62.4MB)")
