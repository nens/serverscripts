from pprint import pprint
from serverscripts import haproxy
from unittest import TestCase

import os


class HaproxyTestCase(TestCase):
    def setUp(self):
        our_dir = os.path.dirname(__file__)
        self.example = os.path.join(our_dir, "example_haproxy.cfg")

    def test_site_regex1(self):
        line = "acl host_nxt hdr_dom(host) -i alkmaar.lizard.net"
        match = haproxy.SITE.search(line)
        self.assertEqual(match.group("sitename"), "alkmaar.lizard.net")

    def test_site_regex2(self):
        line = "acl host_nxt hdr_dom(host) -i alkmaar.lizard.net"
        match = haproxy.SITE.search(line)
        self.assertEqual(match.group("backend"), "nxt")

    def test_backend_regex(self):
        line = "backend nxt_cluster"
        match = haproxy.BACKEND_START.search(line)
        self.assertEqual(match.group("backend"), "nxt")

    def test_server_regex(self):
        line = (
            "server 110-raster-d1.ourdomain  "
            + "10.100.110.131:80 check observe layer7"
        )
        match = haproxy.SERVER.search(line)
        self.assertEqual(match.group("server"), "110-raster-d1.ourdomain")

    def test_count(self):
        # 3 nxt sites * 3 nxt servers + 1 raster site * 2 raster backends = 11
        result = list(haproxy.extract_sites(self.example))
        pprint(result)
        self.assertEqual(len(result), 11)

    def test_protocol_http(self):
        # We're hardcoded to http as that's our current setup.
        result = list(haproxy.extract_sites(self.example))
        pprint(result)
        self.assertEqual(result[0]["protocol"], "http")

    def test_proxy_remote_count(self):
        result = list(haproxy.extract_sites(self.example))
        pprint(result)
        specific_sites = [
            site for site in result if site["name"] == "alkmaar.lizard.net"
        ]
        # 3 backends, so there should be 3 sites with this name.
        self.assertEqual(len(specific_sites), 3)

    def test_proxy_remote(self):
        result = list(haproxy.extract_sites(self.example))
        pprint(result)
        specific_sites = [
            site for site in result if site["name"] == "alkmaar.lizard.net"
        ]
        # 3 backends, so there should be 3 sites with this name.
        remote_servers = [site["proxy_to_other_server"] for site in specific_sites]
        self.assertTrue("p-web-ws-d2.ourdomain" in remote_servers)
