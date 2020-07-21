import json
from datetime import datetime
from unittest import TestCase

from messenger.server import (check_settings, form_response, process_action, send_response, check_presence,
                              terminate_connection)
from messenger.common.constants import ENCODING
from messenger.common.exceptions import PortOutOfRangeError
from messenger.unit_tests.loopback import ConnLoopback


class TestServer(TestCase):
    """Test suite for server part of the messenger."""

    def test_check_settings(self):
        """Tests for CLI argument checker."""
        # both bind address and port given
        self.assertEqual(check_settings('test.test 9999'.split()), ('test.test', 9999))
        # only bind address given
        self.assertEqual(check_settings('test.test'.split()), ('test.test', 7777))
        # no options, using default values
        self.assertEqual(check_settings(''), ('', 7777))
        # wrong port numbers
        with self.assertRaises(PortOutOfRangeError):
            check_settings('test.test 77777'.split())
        with self.assertRaises(PortOutOfRangeError):
            check_settings('test.test 1023'.split())

    def test_form_response(self):
        """Tests for response builder function."""
        # Testing 200 OK alert reply
        response_obj = {
            'response': 200,
            'time': int(datetime.now().timestamp()),
            'alert': 'OK',
        }
        self.assertEqual(form_response(200), response_obj)

        # In case we didn't supply any code, default should be used
        self.assertEqual(form_response(), response_obj)

        # testing error response
        response_obj = {
            'response': 400,
            'time': int(datetime.now().timestamp()),
            'error': 'Incorrect request',
        }
        self.assertEqual(form_response(400), response_obj)

    def test_process_action(self):
        """Tests for server response code generator placeholder function."""
        test_obj_presence = {
            'action': 'presence',
            'time': 1593605102,
            'type': 'status',
            'user': {
                'account_name': 'Guest',
                'status': 'I am here!'
            }
        }
        self.assertEqual(process_action(test_obj_presence), 200)

        test_obj_auth = {
            'action': 'authenticate',
            'time': 1593605102,
            'user': {
                'account_name': 'Guest',
                'password': '12345678'
            }
        }
        self.assertEqual(process_action(test_obj_auth), 402)

        test_obj_join = {
            'action': 'join',
            'time': 1593605102,
            'room': '#room',
        }
        self.assertEqual(process_action(test_obj_join), 404)

        test_obj_message = {
            'action': 'msg',
            'time': 1593605102,
            'to': 'testuser',
            'from': 'Guest',
            'message': 'Testing messages!',
        }
        self.assertEqual(process_action(test_obj_message), 410)

        test_obj_broken = {
            'action': 'ping',
            'time': 1593605102,
            'user': 'testuser',
        }
        self.assertEqual(process_action(test_obj_broken), 500)

    def test_send_response(self):
        """Test for server-side placeholder message parser.

        Takes client message dict and replies with server response based on action (and results [TBD]).
        """
        loopback = ConnLoopback('localhost', 7777)

        test_obj_message = {
            'action': 'msg',
            'time': 1593605102,
            'to': 'testuser',
            'from': 'Guest',
            'message': 'Testing messages!',
        }
        send_response(test_obj_message, loopback.client)
        # only testing one random case, as case recognition is within another function
        check_data_response = loopback.client_get_data(1024).decode(ENCODING)
        check_obj_response = json.loads(check_data_response)
        test_obj_response = {
            'response': 410,
            'error': 'Target user is offline',
            'time': int(datetime.now().timestamp())
        }
        self.assertEqual(test_obj_response, check_obj_response)
        loopback.close()

    def test_check_presence(self):
        """Test for presence checker function.

        Gets first client message as dict, checks whether it is a valid presence JIM object.
        """
        test_obj_correct = {
            'action': 'presence',
            'time': 1593605102,
            'type': 'status',
            'user': {
                'account_name': 'Guest',
                'status': 'I am here!',
            }
        }
        self.assertTrue(check_presence(test_obj_correct))
        test_obj_wrong_action = {
            'action': 'msg',
            'time': 1593605102,
            'type': 'status',
            'user': {
                'account_name': 'Guest',
                'status': 'I am here!',
            }
        }
        self.assertFalse(check_presence(test_obj_wrong_action))
        test_obj_wrong_type = {
            'action': 'presence',
            'type': '',
            'time': 1593605102,
            'user': {
                'account_name': 'Guest',
                'status': 'I am here!',
            }
        }
        self.assertFalse(check_presence(test_obj_wrong_type))
        test_obj_no_acc_name = {
            'action': 'presence',
            'time': 1593605102,
            'type': 'status',
            'user': {
                'account_name': None,
                'status': 'I am here!',
            }
        }
        self.assertFalse(check_presence(test_obj_no_acc_name))
        test_obj_no_status = {
            'action': 'presence',
            'time': 1593605102,
            'type': 'status',
            'user': {
                'account_name': 'Guest',
                'status': '',
            }
        }
        self.assertFalse(check_presence(test_obj_no_status))

    def test_terminate_connection(self):
        """Test for connection termination function.

        Sends final response code and closes connection.
        """
        loopback = ConnLoopback('localhost', 7777)
        terminate_connection(loopback.client, 400)
        test_obj = json.loads(loopback.client_get_data(1024).decode(ENCODING))
        check_obj = {
            'response': 400,
            'error': 'Incorrect request',
            'time': int(datetime.now().timestamp())
        }
        self.assertEqual(check_obj, test_obj)
        loopback.close()
