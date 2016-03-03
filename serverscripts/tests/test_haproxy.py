from pprint import pprint
from serverscripts import haproxy
from unittest import TestCase

import os


class HaproxyTestCase(TestCase):

    def setUp(self):
        our_dir = os.path.dirname(__file__)
        self.example = os.path.join(
            our_dir, 'example_haproxy.cfg')

    def test_count(self):
        result = list(haproxy.extract_sites(self.example))
        pprint(result)
        self.assertEquals(len(result), 4)

    def test_protocol_http(self):
        # We're hardcoded to http as that's our current setup.
        result = list(haproxy.extract_sites(self.example))
        pprint(result)
        self.assertEquals(result[0]['protocol'], 'http')

    def test_proxy_remote_count(self):
        result = list(haproxy.extract_sites(self.example))
        pprint(result)
        specific_sites = [site for site in result
                          if site['name'] == 'alkmaar.lizard.net']
        # 3 backends, so there should be 3 sites with this name.
        self.assertEquals(len(specific_sites), 3)

    def test_proxy_remote(self):
        result = list(haproxy.extract_sites(self.example))
        pprint(result)
        specific_sites = [site for site in result
                          if site['name'] == 'alkmaar.lizard.net']
        # 3 backends, so there should be 3 sites with this name.
        remote_servers = [site['proxy_to_other_server']
                          for site in specific_sites]
        self.assertTrue('p-web-ws-d2.external-nens.local' in remote_servers)

    def test_proxy_remote_protocol(self):
        # We're hardcoded to http as that's our current setup.
        result = list(haproxy.extract_sites(self.example))
        pprint(result)
        specific_sites = [site for site in result
                          if site['name'] == 'alkmaar.lizard.net']
        # 3 backends, so there should be 3 sites with this name.
        remote_protocols = [site['redirect_to_protocol']
                            for site in specific_sites]
        self.assertEquals(remote_protocols[0], 'http')
