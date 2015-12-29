from pkg_resources import resource_filename
from unittest import TestCase
from serverscripts import cifsfixer


class TabfileTestCase(TestCase):

    def setUp(self):
        self.fstab = resource_filename('serverscripts.tests',
                                       'example_fstab')
        self.mtab = resource_filename('serverscripts.tests',
                                      'example_mtab')

    def test_fstab(self):
        expected = {'/some/mount': '//someserver/somewhere'}
        # So: only cifs mounts are returned and commented-out cifs mounts are
        # ignored.
        self.assertEquals(expected, cifsfixer._cifs_lines(self.fstab))
