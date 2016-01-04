from mock import patch
from pkg_resources import resource_filename
from serverscripts import cifsfixer
from unittest import TestCase


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
        self.assertEquals((0, 0),
                          cifsfixer.check_if_mounted({}, {}))

    def test_matching_mounts(self):
        mounts = {'/some/folder': 'some//cifs'}
        with patch('serverscripts.cifsfixer._is_folder_accessible') as mocked:
            mocked.return_value = True
            self.assertEquals((0, 0),
                              cifsfixer.check_if_mounted(mounts, mounts))

    def test_mounting_missing_mount(self):
        fstab_mounts = {'/some/folder': 'some//cifs'}
        mtab_mounts = {}
        with patch('serverscripts.cifsfixer._mount') as mocked:
            cifsfixer.check_if_mounted(fstab_mounts, mtab_mounts)
            self.assertTrue(mocked.called)

    def test_not_mounting_if_ok(self):
        fstab_mounts = {'/some/folder': 'some//cifs'}
        mtab_mounts = fstab_mounts
        with patch('serverscripts.cifsfixer._is_folder_accessible') as mocked1:
            mocked1.return_value = True
            with patch('serverscripts.cifsfixer._mount') as mocked2:
                cifsfixer.check_if_mounted(fstab_mounts, mtab_mounts)
                self.assertFalse(mocked2.called)

    def test_re_mounting_if_inaccessible(self):
        fstab_mounts = {'/some/folder': 'some//cifs'}
        mtab_mounts = fstab_mounts
        with patch('serverscripts.cifsfixer._is_folder_accessible') as mocked1:
            mocked1.return_value = False
            with patch('serverscripts.cifsfixer._mount') as mocked2:
                with patch('serverscripts.cifsfixer._unmount') as mocked3:
                    cifsfixer.check_if_mounted(fstab_mounts, mtab_mounts)
                    self.assertTrue(mocked2.called)
                    self.assertTrue(mocked3.called)


class UtilsTestCase(TestCase):

    def test_succesful_mount(self):
        with patch('subprocess.call') as mock_call:
            mock_call.return_value = 0
            cifsfixer._mount('something')

    def test_unsuccesful_mount(self):
        with patch('subprocess.call') as mock_call:
            mock_call.return_value = 1
            cifsfixer._mount('something')
            # The only difference with a succesful mount is a different log
            # message.

    def test_folder_inaccessible(self):
        self.assertFalse(cifsfixer._is_folder_accessible('/does/not/exist'))

    def test_folder_accessible(self):
        self.assertTrue(cifsfixer._is_folder_accessible('/tmp'))

    def test_succesful_unmount(self):
        with patch('subprocess.call') as mock_call:
            mock_call.return_value = 0
            cifsfixer._unmount('something')

    def test_unsuccesful_unmount(self):
        with patch('subprocess.call') as mock_call:
            mock_call.return_value = 1
            cifsfixer._unmount('something')
            # The only difference with a succesful unmount is a different log
            # message.
