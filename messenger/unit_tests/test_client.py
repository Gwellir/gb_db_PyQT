from unittest import TestCase
from datetime import datetime

from messenger.client import (check_settings, form_auth_message, form_text_message, form_join_message,
                              form_presence_message, parse_message)
from messenger.common.exceptions import NoAddressGivenError, PortOutOfRangeError


class TestClient(TestCase):
    """Test suite for messenger client script."""

    def test_check_settings(self):
        """Tests for CLI argument checker."""
        # both arguments valid
        self.assertEqual(check_settings('test.test 9999'.split()), ('test.test', 9999))
        # only host
        self.assertEqual(check_settings('test.test'.split()), ('test.test', 7777))
        # no arguments
        with self.assertRaises(NoAddressGivenError):
            check_settings(''.split())
        # port number above limit
        with self.assertRaises(PortOutOfRangeError):
            check_settings('test.test 77777'.split())
        # port number below limit
        with self.assertRaises(PortOutOfRangeError):
            check_settings('test.test 1023'.split())

    def test_form_auth_message(self):
        """Test for auth message generator."""
        test_obj = {
            'action': 'authenticate',
            'time': int(datetime.now().timestamp()),
            'user': {
                'account_name': 'Guest',
                'password': '12345678'
            }
        }
        self.assertEqual(form_auth_message('Guest', '12345678'), test_obj)

    def test_form_presence_message(self):
        """Test for presence message generator."""
        test_obj = {
            'action': 'presence',
            'time': int(datetime.now().timestamp()),
            'type': 'status',
            'user': {
                'account_name': 'Guest',
                'status': 'I am here!'
            }
        }
        self.assertEqual(form_presence_message('Guest', 'I am here!'), test_obj)

    def test_form_text_message(self):
        """Test for text message generator."""
        test_obj = {
            'action': 'msg',
            'time': int(datetime.now().timestamp()),
            'to': '#room',
            'from': 'Guest',
            'message': 'Testing messages!',
        }
        self.assertEqual(form_text_message('Guest', '#room', 'Testing messages!'), test_obj)

    def test_form_join_message(self):
        """Test for join message generator."""
        test_obj = {
            'action': 'join',
            'time': int(datetime.now().timestamp()),
            'room': '#room',
        }
        self.assertEqual(form_join_message('Guest', '#room'), test_obj)
        self.assertEqual(form_join_message('Guest', '+room'), None)

    def test_parse_message(self):
        """Test for client JIM message parser.

        Takes a response dict, performs actions based on its contents (returns corresponding values at the moment).
        """
        # Error 401 response
        test_obj_401 = {
            'time': 1593605102,
            'response': 401,
            'error': 'Требуется авторизация!',
        }
        self.assertEqual(parse_message(test_obj_401), 'Error: Требуется авторизация!')

        # 200 OK response
        test_obj_200 = {
            'time': 1593605102,
            'response': 200,
            'alert': 'Сообщение доставлено.',
        }
        self.assertEqual(parse_message(test_obj_200), 'Alert: Сообщение доставлено.')

        # message transfer
        test_obj_message = {
            'action': 'msg',
            'time': int(datetime.now().timestamp()),
            'to': '#room',
            'from': 'Guest',
            'message': 'Проверка!',
        }
        self.assertEqual(parse_message(test_obj_message), 'Message: Проверка!')

        # PROBE request
        # loopback = ConnLoopback('localhost', 7777)
        test_obj_probe = {
            'action': 'probe',
            'time': 1593605102,
        }
        self.assertEqual(parse_message(test_obj_probe), 'Probe received at 2020-07-01 15:05:02')
