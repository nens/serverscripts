from pprint import pprint
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
        self.redirect_example = os.path.join(
            our_dir, 'example_redirect_nginx.conf')

    def test_single_count(self):
        result = list(nginx.extract_sites(self.single_example))
        pprint(result)
        self.assertEquals(len(result), 1)

    def test_multiple_count(self):
        # Two server parts, one with a double name.
        result = list(nginx.extract_sites(self.multiple_example))
        pprint(result)
        self.assertEquals(len(result), 3)

    def test_regex_count(self):
        # Weird lizard5-only regex magic.
        result = list(nginx.extract_sites(self.regex_example))
        pprint(result)
        self.assertEquals(len(result), 3)

    def test_protocol_http(self):
        result = list(nginx.extract_sites(self.single_example))
        pprint(result)
        self.assertEquals(result[0]['protocol'], 'http')

    def test_protocol_https(self):
        result = list(nginx.extract_sites(self.multiple_example))
        pprint(result)
        self.assertEquals(result[0]['protocol'], 'https')

    def test_proxy_local(self):
        result = list(nginx.extract_sites(self.single_example))
        pprint(result)
        self.assertEquals(result[0]['proxy_to_local_port'], '9070')

    def test_proxy_remote(self):
        result = list(nginx.extract_sites(self.multiple_example))
        pprint(result)
        specific_site = [site for site in result
                         if site['name'] == 'api.ddsc.nl'][0]
        self.assertEquals(specific_site['proxy_to_other_server'],
                          '110-haprox-d2.external-nens.local')

    def test_redirect_count(self):
        result = list(nginx.extract_sites(self.redirect_example))
        pprint(result)
        self.assertEquals(len(result), 1)

    def test_redirect_target(self):
        result = list(nginx.extract_sites(self.redirect_example))
        pprint(result)
        self.assertEquals(result[0]['redirect_to'],
                          'https://uploadservice.lizard.net')
