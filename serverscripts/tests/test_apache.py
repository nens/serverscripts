from mock import patch
from serverscripts import apache
from unittest import TestCase

import os


class ApacheTestCase(TestCase):

    def setUp(self):
        our_dir = os.path.dirname(__file__)
        self.single_example = os.path.join(
            our_dir, 'example_single_apache.conf')
        self.customlog_example = os.path.join(
            our_dir, 'example_apache_customlog.conf')
        self.multiple_example = os.path.join(
            our_dir, 'example_multiple_apache_proxy.conf')

    def test_single_count(self):
        result = list(apache.extract_sites(self.single_example))
        print(result)
        self.assertEquals(len(result), 1)

    def test_multiple_count(self):
        # Four virtualhosts
        result = list(apache.extract_sites(self.multiple_example))
        print(result)
        self.assertEquals(len(result), 4)

    def test_count_with_alias(self):
        result = list(apache.extract_sites(self.customlog_example))
        print(result)
        self.assertEquals(len(result), 2)

    def test_srv_extraction_customlog(self):
        result = list(apache.extract_sites(self.customlog_example))
        print(result)
        self.assertEquals('somewhere', result[0]['related_checkout'])

    def test_srv_extraction_docroot(self):
        result = list(apache.extract_sites(self.single_example))
        print(result)
        self.assertEquals('serverinfo.lizard.net',
                          result[0]['related_checkout'])

    def test_protocol_http(self):
        result = list(apache.extract_sites(self.single_example))
        print(result)
        self.assertEquals(result[0]['protocol'], 'http')

    def test_protocol_https(self):
        result = list(apache.extract_sites(self.multiple_example))
        print(result)
        self.assertEquals(2, len([i for i in result
                                  if i['protocol'] == 'https']))

    def test_protocol_https_without_portnumber(self):
        # A servername can be 'portal.ddsc.nl:443', the port number must be
        # stripped from the servername in this case.
        result = list(apache.extract_sites(self.multiple_example))
        print(result)
        https_sites = [i for i in result if i['protocol'] == 'https']
        site_names = [i['name'] for i in https_sites]
        self.assertTrue('portal.ddsc.nl' in site_names)

    def test_proxy_remote(self):
        result = list(apache.extract_sites(self.multiple_example))
        print(result)
        specific_site = [site for site in result
                         if site['name'] == 'fewsvecht.controlnext.org'][0]
        self.assertEquals(specific_site['proxy_to_other_server'],
                          'p-fews-mc-v2-d1.external-nens.local')
