from mock import patch
from serverscripts import nginx
from unittest import TestCase

import os


class GitAndEggInfoTestCase(TestCase):

    def setUp(self):
        our_dir = os.path.dirname(__file__)
        self.single_example = os.path.join(
            our_dir, 'example_single_nginx.conf')
        self.multiple_example = os.path.join(
            our_dir, 'example_multiple_nginx_proxy.conf')
        self.regex_example = os.path.join(
            our_dir, 'example_regex_nginx.conf')

    def test_single_count(self):
        result = list(nginx.extract_sites(self.single_example))
        print(result)
        self.assertEquals(len(result), 1)

    def test_multiple_count(self):
        # Two server parts, one with a double name.
        result = list(nginx.extract_sites(self.multiple_example))
        print(result)
        self.assertEquals(len(result), 3)

    def test_regex_count(self):
        # Weird lizard5-only regex magic.
        result = list(nginx.extract_sites(self.regex_example))
        print(result)
        self.assertEquals(len(result), 3)

    def test_protocol_http(self):
        result = list(nginx.extract_sites(self.single_example))
        print(result)
        self.assertEquals(result[0]['protocol'], 'http')

    def test_protocol_https(self):
        result = list(nginx.extract_sites(self.multiple_example))
        print(result)
        self.assertEquals(result[0]['protocol'], 'https')
