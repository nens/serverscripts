from pprint import pprint
from serverscripts import apache
from unittest import TestCase

import os


class ApacheTestCase(TestCase):
    def setUp(self):
        our_dir = os.path.dirname(__file__)
        self.single_example = os.path.join(our_dir, "example_single_apache.conf")
        self.customlog_example = os.path.join(our_dir, "example_apache_customlog.conf")
        self.multiple_example = os.path.join(
            our_dir, "example_multiple_apache_proxy.conf"
        )
        self.redirect_example = os.path.join(our_dir, "example_apache_redirect.conf")

    def test_single_count(self):
        result = list(apache.extract_sites(self.single_example))
        pprint(result)
        self.assertEqual(len(result), 1)

    def test_multiple_count(self):
        # Four virtualhosts
        result = list(apache.extract_sites(self.multiple_example))
        pprint(result)
        self.assertEqual(len(result), 4)

    def test_count_with_alias(self):
        result = list(apache.extract_sites(self.customlog_example))
        pprint(result)
        self.assertEqual(len(result), 2)

    def test_srv_extraction_customlog(self):
        result = list(apache.extract_sites(self.customlog_example))
        pprint(result)
        self.assertEqual("somewhere", result[0]["related_checkout"])

    def test_srv_extraction_docroot(self):
        result = list(apache.extract_sites(self.single_example))
        pprint(result)
        self.assertEqual("serverinfo.lizard.net", result[0]["related_checkout"])

    def test_protocol_http(self):
        result = list(apache.extract_sites(self.single_example))
        pprint(result)
        self.assertEqual(result[0]["protocol"], "http")

    def test_protocol_https(self):
        result = list(apache.extract_sites(self.multiple_example))
        pprint(result)
        self.assertEqual(2, len([i for i in result if i["protocol"] == "https"]))

    def test_protocol_https_without_portnumber(self):
        # A servername can be 'portal.ddsc.nl:443', the port number must be
        # stripped from the servername in this case.
        result = list(apache.extract_sites(self.multiple_example))
        pprint(result)
        https_sites = [i for i in result if i["protocol"] == "https"]
        site_names = [i["name"] for i in https_sites]
        self.assertTrue("portal.ddsc.nl" in site_names)

    def test_proxy_remote(self):
        result = list(apache.extract_sites(self.multiple_example))
        pprint(result)
        specific_site = [
            site for site in result if site["name"] == "fewsvecht.controlnext.org"
        ][0]
        self.assertEqual(
            specific_site["proxy_to_other_server"],
            "p-fews-mc-v2-d1.external-nens.local",
        )

    def test_redirect_count1(self):
        result = list(apache.extract_sites(self.redirect_example))
        pprint(result)
        self.assertEqual(len(result), 4)

    def test_redirect_count2(self):
        result = list(apache.extract_sites(self.redirect_example))
        pprint(result)
        redirects = [i["redirect_to"] for i in result]
        self.assertEqual(len(redirects), 4)

    def test_redirects1(self):
        result = list(apache.extract_sites(self.redirect_example))
        pprint(result)
        redirects = [i["redirect_to"] for i in result]
        self.assertTrue("portal.ddsc.nl" in redirects)

    def test_redirects2(self):
        result = list(apache.extract_sites(self.redirect_example))
        pprint(result)
        redirects = [i["redirect_to"] for i in result]
        self.assertTrue("GONE" in redirects)

    def test_redirects3(self):
        result = list(apache.extract_sites(self.redirect_example))
        pprint(result)
        redirects = [i["redirect_to"] for i in result]
        self.assertTrue("waterschappenlimburg.lizard.net" in redirects)

    def test_redirect_protocol(self):
        result = [
            site
            for site in apache.extract_sites(self.redirect_example)
            if site["name"] == "www.portal.ddsc.nl"
        ][0]
        pprint(result)
        self.assertEqual(result["redirect_to_protocol"], "https")
