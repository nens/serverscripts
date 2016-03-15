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
        self.credentials = resource_filename(
            'serverscripts.tests', 'example_cifs_credentials')

    def test_fstab(self):
        expected = {'/some/mount': {
            'cifs_share': '//someserver/somewhere',
            'options': {'credentials': '/etc/blabla.txt',
                        'iocharset': 'utf8'}}}
        # So: only cifs mounts are returned and commented-out cifs mounts are
        # ignored.
        self.assertEquals(expected, cifsfixer._cifs_lines(self.fstab)[0])

    def test_fstab_with_duplicate_mount_point(self):
        result = cifsfixer._cifs_lines(
            self.fstab_with_duplicate_mount_point)[0]
        # In case of duplicates, the second one wins. A warning is logged (but
        # we don't test that here).
        self.assertEquals(result['/some/mount']['cifs_share'],
                          '//someserver/something')

    def test_fstab_with_duplicate_mount(self):
        expected_keys = ['/some/mount1', '/some/mount2']
        # In case of a file system that is mounted in two places, both are
        # returned. A warning is logged, but we don't test that here).
        self.assertEquals(
            expected_keys,
            sorted(
                cifsfixer._cifs_lines(
                    self.fstab_with_duplicate_mount)[0].keys()))

    def test_mtab(self):
        expected = {'/some/mount': {'cifs_share': '//someserver/somewhere'}}
        # So: only cifs mounts are returned and commented-out cifs mounts are
        # ignored.
        self.assertEquals(expected, cifsfixer._cifs_lines(self.mtab)[0])

    def test_username_extraction(self):
        self.assertEquals('some_user',
                          cifsfixer._extract_username(self.credentials))


class CheckerTestCase(TestCase):
    # Test check_if_mounted()

    def test_empty(self):
        self.assertEquals(0, cifsfixer.check_if_mounted({}, {}))

    def test_matching_mounts(self):
        mounts = {'/some/folder': 'some//cifs'}
        with patch('serverscripts.cifsfixer._is_folder_accessible') as mocked:
            mocked.return_value = True
            self.assertEquals(0, cifsfixer.check_if_mounted(mounts, mounts))

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

    def test_check_unkown_mounts1(self):
        fstab_mounts = {'/some/folder': 'some//cifs'}
        mtab_mounts = {}
        # Additional fstab mounts are not *our* problem.
        self.assertEquals(0, cifsfixer.check_unknown_mounts(
            fstab_mounts, mtab_mounts))

    def test_check_unkown_mounts2(self):
        fstab_mounts = {}
        mtab_mounts = {'/some/folder': 'some//cifs'}
        self.assertEquals(1, cifsfixer.check_unknown_mounts(
            fstab_mounts, mtab_mounts))
