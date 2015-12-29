from pkg_resources import resource_filename
from unittest import TestCase
from serverscripts import cifsfixer


class TabfileTestCase(TestCase):

    def setUp(self):
        self.fstab = resource_filename('serverscripts.tests',
                                       'example_fstab')
        self.fstab_with_duplicate_mount_point = resource_filename(
            'serverscripts.tests',
            'example_fstab_with_duplicate_mount_point')
        self.fstab_with_duplicate_mount = resource_filename(
            'serverscripts.tests',
            'example_fstab_with_duplicate_mount')
        self.mtab = resource_filename('serverscripts.tests',
                                      'example_mtab')

    def test_fstab(self):
        expected = {'/some/mount': '//someserver/somewhere'}
        # So: only cifs mounts are returned and commented-out cifs mounts are
        # ignored.
        self.assertEquals(expected, cifsfixer._cifs_lines(self.fstab))

    def test_fstab_with_duplicate_mount_point(self):
        expected = {'/some/mount': '//someserver/something'}
        # In case of duplicates, the second one wins. A warning is logged (but
        # we don't test that here).
        self.assertEquals(
            expected,
            cifsfixer._cifs_lines(self.fstab_with_duplicate_mount_point))

    def test_fstab_with_duplicate_mount(self):
        expected = {'/some/mount1': '//someserver/somewhere',
                    '/some/mount2': '//someserver/somewhere'}
        # In case of a file system that is mounted in two places, both are
        # returned. A warning is logged, but we don't test that here).
        self.assertEquals(
            expected,
            cifsfixer._cifs_lines(self.fstab_with_duplicate_mount))

    def test_mtab(self):
        expected = {'/some/mount': '//someserver/somewhere'}
        # So: only cifs mounts are returned and commented-out cifs mounts are
        # ignored.
        self.assertEquals(expected, cifsfixer._cifs_lines(self.mtab))


class CheckerTestCase(TestCase):

    def test_empty(self):
        self.assertEquals(0, cifsfixer.check_if_mounted([], []))
