import json
from unittest import mock
from unittest.mock import patch
import unittest
import requests

from pyvesync.vesync import VeSync


def mocked_requests_post(*args, **kwargs):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data

    if args[0] == 'https://smartapi.vesync.com/cloud/v1/user/login':
        return MockResponse('{"traceId": "", "msg": "", "result": {"accountID": "12346536, "avatarIcon": "", "acceptLanguage": "", "gdprStatus": true, "nickName": "mynickname", "userType": "1", "token": "somevaluehere"}, "code": 0 }', 200)
    elif args[0] == 'https://smartapi.vesync.com/cloud/v1/deviceManaged/devices':
        return MockResponse({"key2": "value2"}, 200)

    return MockResponse(None, 404)


class TestVesync(unittest.TestCase):
    def setUp(self):
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
        pass

    def test_instance(self):
        self.assertIsInstance(self.vesync_1, VeSync)

    def test_username(self):
        self.assertEqual(self.vesync_1.username, 'sam@email.com')
        self.assertEqual(self.vesync_5.username, '')
        self.assertEqual(self.vesync_6.username, None)

        self.vesync_1.username = 'tom@email.com'
        self.assertEqual(self.vesync_1.username, 'tom@email.com')

    def test_password(self):
        self.assertEqual(self.vesync_1.password, 'password')
        self.assertEqual(self.vesync_5.password, '')
        self.assertEqual(self.vesync_6.password, None)

        self.vesync_1.password = 'other'
        self.assertEqual(self.vesync_1.password, 'other')
    
    def test_hash_password(self):
        self.assertEqual(self.vesync_1.hash_password(self.vesync_1.password), '5f4dcc3b5aa765d61d8327deb882cf99')
        self.assertEqual(self.vesync_5.hash_password(self.vesync_5.password), 'd41d8cd98f00b204e9800998ecf8427e')
        with self.assertRaises(AttributeError):
            self.vesync_6.hash_password(self.vesync_6.password)

    def test_time_zone(self):
        self.assertEqual(self.vesync_1.time_zone, 'America/New_York')
        self.assertEqual(self.vesync_2.time_zone, 'America/New_York')
        self.assertEqual(self.vesync_3.time_zone, 'America/New_York')
        self.assertEqual(self.vesync_9.time_zone, 'America/New_York')

        self.vesync_1.time_zone = 'America/East'
        self.assertEqual(self.vesync_1.time_zone, 'America/East')

    def test_login(self):
        mock_vesync = mock.Mock()
        mock_vesync.login.return_value = True
        self.assertTrue(mock_vesync.login())
        mock_vesync.login.return_value = False
        self.assertFalse(mock_vesync.login())

        with patch('pyvesync.vesync.VeSync.call_api') as mocked_post:
            d = json.loads('{"result": {"accountID": "12346536", "userType": "1", "token": "somevaluehere"}, "code": 0 }')
            mocked_post.return_value = (d, 200)

            data = self.vesync_1.login()
            body = self.vesync_1.get_body('login')
            body['email'] = self.vesync_1.username
            body['password'] = self.vesync_1.hash_password(self.vesync_1.password)
            mocked_post.assert_called_with('/cloud/v1/user/login', 'post', json=body)
            self.assertTrue(data)

    @mock.patch('pyvesync.vesync.requests.post', side_effect=mocked_requests_post)
    def test_login_call(self, mock_post):
        vesync = self.vesync_1
        response, status_code = vesync.call_api('/cloud/v1/user/login', 'post', '{}')
        self.assertEqual(response, '{"traceId": "", "msg": "", "result": {"accountID": "12346536, "avatarIcon": "", "acceptLanguage": "", "gdprStatus": true, "nickName": "mynickname", "userType": "1", "token": "somevaluehere"}, "code": 0 }')
        self.assertEqual(status_code, 200)

if __name__ == '__main__':
    unittest.main()
