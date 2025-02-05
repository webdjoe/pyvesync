"""General VeSync tests."""

import unittest
import importlib
from unittest import mock
from unittest.mock import patch, Mock, MagicMock

from pyvesync import VeSync
from pyvesync.helpers import Helpers


class TestVeSync(unittest.TestCase):
    """Test VeSync object initialization."""

    def setUp(self):
        """Setup VeSync argument cases."""
        self.vesync_1 = VeSync('sam@email.com', 'password', 'America/New_York')
        self.vesync_2 = VeSync('sam@email.com', 'password')
        self.vesync_3 = VeSync('sam@email.com', 'password', None)
        self.vesync_4 = VeSync('sam@email.com', 'password')
        self.vesync_5 = VeSync('', '')
        self.vesync_6 = VeSync(None, None, None)
        self.vesync_7 = VeSync(None, 'password')
        self.vesync_8 = VeSync('sam@email.com', None)
        self.vesync_9 = VeSync('sam@email.com', 'password', 1)

    def tearDown(self):
        """Clean up test."""
        pass

    def test_instance(self):
        """Test VeSync object is successfully initialized."""
        self.assertIsInstance(self.vesync_1, VeSync)

    def test_imports(self):
        """Test that __all__ contains only names that are actually exported."""
        modules = ['pyvesync.vesyncfan',
                   'pyvesync.vesyncbulb',
                   'pyvesync.vesyncoutlet',
                   'pyvesync.vesyncswitch']
        for mod in modules:
            import_mod = importlib.import_module(mod)

            missing = set(n for n in import_mod.__all__
                          if getattr(import_mod, n, None) is None)
            self.assertFalse(
                missing, msg="__all__ contains unresolved names: %s" % (
                    ", ".join(missing),))

    def test_username(self):
        """Test invalid username arguments."""
        self.assertEqual(self.vesync_1.username, 'sam@email.com')
        self.assertEqual(self.vesync_5.username, '')
        self.assertEqual(self.vesync_6.username, None)

        self.vesync_1.username = 'tom@email.com'
        self.assertEqual(self.vesync_1.username, 'tom@email.com')

    def test_password(self):
        """Test invalid password arguments."""
        self.assertEqual(self.vesync_1.password, 'password')
        self.assertEqual(self.vesync_5.password, '')
        self.assertEqual(self.vesync_6.password, None)

        self.vesync_1.password = 'other'
        self.assertEqual(self.vesync_1.password, 'other')

    def test_hash_password(self):
        """Test password hash method."""
        self.assertEqual(
            Helpers.hash_password(self.vesync_1.password),
            '5f4dcc3b5aa765d61d8327deb882cf99',
        )
        self.assertEqual(
            Helpers.hash_password(self.vesync_5.password),
            'd41d8cd98f00b204e9800998ecf8427e',
        )
        with self.assertRaises(AttributeError):
            Helpers.hash_password(self.vesync_6.password)

    def test_time_zone(self):
        """Test time zone argument handling."""
        self.assertEqual(self.vesync_1.time_zone, 'America/New_York')
        self.assertEqual(self.vesync_2.time_zone, 'America/New_York')
        self.assertEqual(self.vesync_3.time_zone, 'America/New_York')
        self.assertEqual(self.vesync_9.time_zone, 'America/New_York')

        self.vesync_1.time_zone = 'America/East'
        self.assertEqual(self.vesync_1.time_zone, 'America/East')

    def test_login(self):
        """Test login method."""
        mock_vesync = mock.Mock()
        mock_vesync.login.return_value = True
        self.assertTrue(mock_vesync.login())
        mock_vesync.login.return_value = False
        self.assertFalse(mock_vesync.login())

        with patch('pyvesync.helpers.Helpers.call_api') as mocked_post:
            d = {
                'result': {
                    'accountID': '12346536',
                    'userType': '1',
                    'token': 'somevaluehere',
                },
                'code': 0,
            }
            mocked_post.return_value = d

            data = self.vesync_1.login()
            body = Helpers.req_body_login(self.vesync_1)
            body['email'] = self.vesync_1.username
            body['password'] = Helpers.hash_password(self.vesync_1.password)
            mocked_post.assert_called_with('/cloud/v1/user/login', 'post',
                                           json_object=body)
            self.assertTrue(data)


class TestApiFunc:
    """Test call_api() method."""

    @patch('pyvesync.helpers.requests.get', autospec=True)
    def test_api_get(self, get_mock):
        """Test get api call."""
        get_mock.return_value = Mock(ok=True, status_code=200)
        get_mock.return_value.json.return_value = {'code': 0}

        mock_return = Helpers.call_api('/call/location', method='get')

        assert mock_return == {'code': 0}

    @patch('pyvesync.helpers.requests.post', autospec=True)
    def test_api_post(self, post_mock):
        """Test post api call."""
        post_mock.return_value = Mock(ok=True, status_code=200)
        post_mock.return_value.json.return_value = {'code': 0}

        mock_return = Helpers.call_api('/call/location', method='post')

        assert mock_return == {'code': 0}

    @patch('pyvesync.helpers.requests.put', autospec=True)
    def test_api_put(self, put_mock):
        """Test put api call."""
        put_mock.return_value = Mock(ok=True, status_code=200)
        put_mock.return_value.json.return_value = {'code': 0}

        mock_return = Helpers.call_api('/call/location', method='put')

        assert mock_return == {'code': 0}

    @patch('pyvesync.helpers.requests.get', autospec=True)
    def test_api_bad_response(self, api_mock):
        """Test bad API response handling."""
        api_mock.side_effect = MagicMock(status_code=400)
        mock_return = Helpers.call_api('/test/bad-response', method='get')
        print(api_mock.call_args_list)
        assert mock_return == None


if __name__ == '__main__':
    unittest.main()
